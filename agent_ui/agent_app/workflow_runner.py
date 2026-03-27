"""
Shared workflow execution logic for WebSocket consumer and scheduled runs.

Execution is BPMN-only: workflows must have BPMN, bindings, and a state class.
Legacy executor.run() is not supported.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from beeai_framework.errors import FrameworkError
from channels.db import database_sync_to_async
from django.utils import timezone

from agent_app.bpmn_engine import (
    BpmnEngineError,
    _get_bindings_and_bpmn,
    can_run_with_bpmn_engine,
    create_initial_state_from_inputs,
    current_node_ids_for_progress,
    get_next_step_for_resume,
    normalize_engine_state,
    run_bpmn_workflow,
)
from agent_app.task_service import BpmnIntermediateWaitError, TaskPendingError

logger = logging.getLogger(__name__)


def build_result_dict_from_state(result, workflow_id):
    """Build result dict from workflow result state for API/DB storage."""
    state = result.state
    result_dict = {
        "workflow_steps": getattr(state, "workflow_steps", []),
        "checks_performed": getattr(state, "checks_performed", []),
        "timestamp": getattr(state, "timestamp", None),
        "risk_factors": getattr(state, "risk_factors", []),
    }
    if workflow_id == "bi_weekly_report":
        result_dict["status"] = "Completed"
        result_dict["executive_brief_markdown"] = getattr(state, "executive_brief_markdown", "")
        result_dict["portfolio_totals"] = getattr(state, "portfolio_totals", {})
        result_dict["top_performers"] = getattr(state, "top_performers", [])
        result_dict["properties_needing_attention"] = getattr(
            state, "properties_needing_attention", []
        )
        result_dict["funnel"] = getattr(state, "funnel", {})
        result_dict["week_over_week_trend"] = getattr(state, "week_over_week_trend", {})
        result_dict["auction_readiness"] = getattr(state, "auction_readiness", [])
        result_dict["recommended_actions"] = getattr(state, "recommended_actions", [])
    elif hasattr(state, "approval_status"):
        result_dict["status"] = state.approval_status
        result_dict["eligible"] = state.is_eligible
        result_dict["requires_review"] = state.requires_manual_review
        result_dict["summary"] = state.compliance_summary
        result_dict["bid_limit"] = state.bid_limit
    if hasattr(state, "findings_summary"):
        result_dict["findings_summary"] = state.findings_summary
        result_dict["recommendations"] = state.recommendations
        result_dict["risk_level"] = state.risk_level
        result_dict["property_details"] = state.property_details
        result_dict["comparable_sales"] = state.comparable_sales
        result_dict["documents_found"] = state.documents_found
        result_dict["compliance_checks"] = state.compliance_checks
        result_dict["auction_history"] = state.auction_history
    # Default status for workflows that complete without a specific status (e.g. property_due_diligence)
    if "status" not in result_dict:
        result_dict["status"] = "Completed"
    return result_dict


def _update_workflow_status_sync(run_id, status, **kwargs):
    """Update workflow run status (sync, for use from async via database_sync_to_async)."""
    from agent_app.metrics_collector import (
        workflow_execution_duration_seconds,
        workflow_runs_total,
    )
    from agent_app.models import WorkflowRun
    from agent_app.notifications import create_workflow_status_notification

    update_fields = {"status": status, **kwargs}
    try:
        workflow_run = WorkflowRun.objects.get(run_id=run_id)
        workflow_id = workflow_run.workflow_id
        workflow_runs_total.labels(workflow_id=workflow_id, status=status).inc()
        if status == "completed" and workflow_run.started_at and "completed_at" in kwargs:
            duration = (kwargs["completed_at"] - workflow_run.started_at).total_seconds()
            workflow_execution_duration_seconds.labels(workflow_id=workflow_id).observe(duration)
        WorkflowRun.objects.filter(run_id=run_id).update(**update_fields)
        if status in ("completed", "failed", "cancelled"):
            create_workflow_status_notification(
                workflow_run.user_id,
                run_id,
                workflow_run.workflow_name,
                status,
                kwargs.get("error_message", ""),
            )
    except Exception as e:
        logger.warning("Could not track workflow metrics: %s", e)
        WorkflowRun.objects.filter(run_id=run_id).update(**update_fields)


def _update_workflow_progress_sync(run_id, progress_data):
    """Update workflow run progress data (sync).

    progress_data may include BPMN animation fields for run_detail UI:
    - completed_node_ids: list of BPMN element ids that finished
    - current_node_ids: list of active BPMN element ids (one or more; parallel-ready)
    - failed_node_id: single element id that failed (if any)
    """
    from agent_app.models import WorkflowRun

    WorkflowRun.objects.filter(run_id=run_id).update(progress_data=progress_data)


def _execution_abort_reason_sync(run_id: str) -> str | None:
    """
    Return 'cancelled' if run is cancelled in DB, 'timeout' if past execution_timeout_seconds
    deadline (from WorkflowRun.created_at), else None.
    """
    from agent_app.models import WorkflowRun

    wr = WorkflowRun.objects.get(run_id=run_id)
    if wr.status == WorkflowRun.STATUS_CANCELLED:
        return "cancelled"
    inp = wr.input_data or {}
    raw = inp.get("execution_timeout_seconds")
    try:
        ts = int(raw) if raw is not None else 0
    except (TypeError, ValueError):
        ts = 0
    if ts > 0:
        deadline = wr.created_at + timedelta(seconds=ts)
        if timezone.now() >= deadline:
            return "timeout"
    return None


def _progress_data_for_bpmn_engine_error(
    e: BpmnEngineError,
    *,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    """Build progress_data dict from BpmnEngineError; enriches cancel/timeout fields."""
    engine_state = getattr(e.state, "_bpmn_engine_state", None)
    meta = dict(e.condition_failure_metadata or {})
    progress_data: dict[str, Any] = {
        "engine_state": engine_state,
        "failed_node_id": e.failed_node_id,
        "failure_reason": e.failure_reason,
        "condition_failure_metadata": meta,
    }
    if engine_state:
        progress_data["last_successful_node_id"] = engine_state.get("last_successful_node_id")
        progress_data["completed_node_ids"] = list(engine_state.get("completed_node_ids") or [])
        cur = current_node_ids_for_progress(engine_state)
        if cur:
            progress_data["current_node_ids"] = cur
    if e.failure_reason == "cancelled":
        progress_data["cancelled_at"] = meta.get("cancelled_at")
    elif e.failure_reason == "timeout":
        progress_data["timed_out_at"] = meta.get("timed_out_at")
        progress_data["timeout_seconds"] = timeout_seconds
    elif e.failure_reason == "retry_exhausted":
        progress_data["bpmn_max_task_retries"] = meta.get("bpmn_max_task_retries")
        progress_data["retry_attempts"] = meta.get("retry_attempts")
        progress_data["retry_exhausted_branch_id"] = meta.get("branch_id")
    return progress_data


def _parse_execution_timeout_seconds(input_data: dict | None) -> int | None:
    if not input_data:
        return None
    raw = input_data.get("execution_timeout_seconds")
    try:
        n = int(raw)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def _parse_bpmn_max_task_retries(input_data: dict | None) -> int:
    if not input_data:
        return 0
    raw = input_data.get("bpmn_max_task_retries")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


async def _run_executor_to_completion(
    workflow_run, executor_instance, input_data, run_id, send_message
):
    """Run workflow via BPMN engine. Raises FrameworkError, TaskPendingError, or Exception."""
    workflow_id = workflow_run.workflow_id

    # Early readiness (see can_run_with_bpmn_engine docstring); not a legacy fallback gate.
    if not can_run_with_bpmn_engine(workflow_id):
        error_msg = (
            f"Workflow '{workflow_id}' is not BPMN-ready. "
            "Only BPMN-driven execution is supported (diagram + bindings + state class)."
        )
        await database_sync_to_async(_update_workflow_status_sync)(
            run_id, "failed", completed_at=timezone.now(), error_message=error_msg
        )
        if send_message:
            await send_message("error", error_msg)
        raise RuntimeError(error_msg)

    async def execution_check():
        return await database_sync_to_async(_execution_abort_reason_sync)(run_id)

    max_task_retries = _parse_bpmn_max_task_retries(input_data)
    try:
        bpmn, bindings = _get_bindings_and_bpmn(workflow_id)
        state = create_initial_state_from_inputs(workflow_id, input_data)
        await run_bpmn_workflow(
            executor_instance,
            state,
            bpmn,
            bindings,
            send_message=send_message,
            execution_check=execution_check,
            max_task_retries=max_task_retries,
        )
        result = type("Result", (), {"state": state})()
    except TaskPendingError as e:
        # Preserve BPMN next step for resume so diagram order is followed
        next_step = get_next_step_for_resume(e.state) or e.next_step
        if next_step is not None:
            e.next_step = next_step
        raise

    result_dict = build_result_dict_from_state(result, workflow_id)
    completed_node_ids = getattr(result.state, "workflow_steps", [])
    engine_state = getattr(result.state, "_bpmn_engine_state", None)
    progress_payload = {
        "completed_node_ids": completed_node_ids,
        "failed_node_id": None,
        "engine_state": engine_state,
    }
    await database_sync_to_async(_update_workflow_progress_sync)(run_id, progress_payload)
    await database_sync_to_async(_update_workflow_status_sync)(
        run_id,
        "completed",
        completed_at=timezone.now(),
        output_data=result_dict,
    )
    if send_message:
        await send_message("complete", result_dict)
    logger.info("Workflow %s completed successfully", run_id)


def _build_progress_sender(run_id: str, send_message):
    async def wrapped_send(msg_type, payload):
        if (
            msg_type == "progress"
            and isinstance(payload, dict)
            and ("completed_node_ids" in payload or "current_node_ids" in payload)
        ):
            await database_sync_to_async(_update_workflow_progress_sync)(run_id, payload)
        if send_message:
            await send_message(msg_type, payload)

    return wrapped_send


async def _handle_missing_workflow_or_executor(
    workflow_run, run_id: str, send_message
) -> tuple[Any, Any] | None:
    from agent_app.workflow_registry import workflow_registry

    workflow = workflow_registry.get(workflow_run.workflow_id)
    if not workflow:
        await database_sync_to_async(_update_workflow_status_sync)(
            run_id,
            "failed",
            completed_at=timezone.now(),
            error_message=f"Workflow {workflow_run.workflow_id} not found in registry",
        )
        if send_message:
            await send_message("error", "Workflow not found in registry")
        return None

    executor = workflow.get("executor")
    if executor is None:
        error_msg = (
            f"Workflow '{workflow_run.workflow_id}' has no executor. "
            "Ensure the workflow class is exported in workflows.<id>.__init__.py."
        )
        await database_sync_to_async(_update_workflow_status_sync)(
            run_id, "failed", completed_at=timezone.now(), error_message=error_msg
        )
        if send_message:
            await send_message("error", error_msg)
        return None
    return workflow, executor


async def _handle_framework_pause_exception(run_id: str, err: FrameworkError, send_message) -> bool:
    if isinstance(err.__cause__, TaskPendingError):
        cause = err.__cause__
        next_step = get_next_step_for_resume(cause.state) or cause.next_step
        await _handle_workflow_paused(run_id, cause, send_message, next_step_override=next_step)
        return True
    if isinstance(err.__cause__, BpmnIntermediateWaitError):
        await _handle_workflow_bpmn_intermediate_wait(
            run_id, err.__cause__, send_message=send_message
        )
        return True
    return False


async def _handle_bpmn_engine_error(
    run_id: str,
    err: BpmnEngineError,
    *,
    input_data: dict | None,
    send_message,
    context_label: str,
    always_structured_error_payload: bool = False,
) -> None:
    logger.error("%s for %s: %s", context_label, run_id, err, exc_info=True)
    ts = _parse_execution_timeout_seconds(input_data)
    progress_data = _progress_data_for_bpmn_engine_error(
        err, timeout_seconds=ts if err.failure_reason == "timeout" else None
    )
    await database_sync_to_async(_update_workflow_progress_sync)(run_id, progress_data)
    terminal_status = "cancelled" if err.failure_reason == "cancelled" else "failed"
    await database_sync_to_async(_update_workflow_status_sync)(
        run_id, terminal_status, completed_at=timezone.now(), error_message=str(err)
    )
    if send_message:
        if always_structured_error_payload or err.failure_reason in (
            "cancelled",
            "timeout",
            "retry_exhausted",
        ):
            await send_message(
                "error",
                {
                    "message": str(err),
                    "failure_reason": err.failure_reason,
                    "failed_node_id": err.failed_node_id,
                    "condition_failure_metadata": err.condition_failure_metadata or {},
                    "engine_state": progress_data.get("engine_state"),
                },
            )
        else:
            await send_message("error", str(err))


async def _handle_unexpected_execution_error(
    run_id: str, err: Exception, *, send_message, context_label: str
) -> None:
    logger.error("%s for %s: %s", context_label, run_id, err, exc_info=True)
    await database_sync_to_async(_update_workflow_status_sync)(
        run_id, "failed", completed_at=timezone.now(), error_message=str(err)
    )
    if send_message:
        await send_message("error", str(err))


async def execute_workflow_run(run_id: str, *, send_message=None):
    """
    Execute a workflow run (create/use WorkflowRun already exists).

    Used by WebSocket consumer and by the scheduler management command.
    send_message: optional async callback (msg_type: str, payload) for progress.
    """
    from agent_app.models import WorkflowRun

    workflow_run = await database_sync_to_async(WorkflowRun.objects.get)(run_id=run_id)
    await database_sync_to_async(_update_workflow_status_sync)(
        run_id, "running", started_at=timezone.now()
    )
    if send_message:
        await send_message("status", "running")

    wrapped_send = _build_progress_sender(run_id, send_message)
    resolved = await _handle_missing_workflow_or_executor(workflow_run, run_id, send_message)
    if resolved is None:
        return
    _, executor = resolved

    input_data = workflow_run.input_data or {}
    executor_instance = (
        executor.__class__(run_id=run_id) if hasattr(executor, "__init__") else executor
    )

    try:
        await _run_executor_to_completion(
            workflow_run, executor_instance, input_data, run_id, wrapped_send
        )
    except FrameworkError as e:
        if not await _handle_framework_pause_exception(run_id, e, send_message):
            raise
    except BpmnIntermediateWaitError as e:
        await _handle_workflow_bpmn_intermediate_wait(run_id, e, send_message=send_message)
    except TaskPendingError as e:
        next_step = get_next_step_for_resume(e.state) or e.next_step
        await _handle_workflow_paused(run_id, e, send_message, next_step_override=next_step)
    except BpmnEngineError as e:
        await _handle_bpmn_engine_error(
            run_id,
            e,
            input_data=input_data,
            send_message=send_message,
            context_label="BPMN engine error",
        )
    except Exception as e:
        await _handle_unexpected_execution_error(
            run_id, e, send_message=send_message, context_label="Workflow execution error"
        )


async def _handle_workflow_paused(
    run_id, task_exception, send_message=None, next_step_override=None
):
    """Save progress and update status when workflow pauses for a task."""
    state_data = task_exception.state.model_dump()
    next_step = next_step_override if next_step_override is not None else task_exception.next_step
    engine_state = getattr(task_exception.state, "_bpmn_engine_state", None)
    completed_node_ids = list(engine_state["completed_node_ids"]) if engine_state else []
    current_node_ids = current_node_ids_for_progress(engine_state) if engine_state else []
    progress_data = {
        "state_class": task_exception.state.__class__.__name__,
        "state_data": state_data,
        "pending_tasks": [task_exception.task_id],
        "next_step": next_step,
        "paused_at": datetime.now(UTC).isoformat(),
        "completed_node_ids": completed_node_ids,
        "current_node_ids": current_node_ids,
        "failed_node_id": None,
        "engine_state": engine_state,
    }
    await database_sync_to_async(_update_workflow_progress_sync)(run_id, progress_data)
    await database_sync_to_async(_update_workflow_status_sync)(run_id, "waiting_for_task")
    if send_message:
        await send_message(
            "task_created",
            {
                "task_id": task_exception.task_id,
                "task_type": task_exception.task_type,
                "message": f"Workflow paused - waiting for {task_exception.task_type} task",
                "task_url": f"/workflows/tasks/{task_exception.task_id}/",
            },
        )
    logger.info("Workflow %s state saved, waiting for task", run_id)


async def _handle_workflow_bpmn_intermediate_wait(
    run_id, wait_exc: BpmnIntermediateWaitError, send_message=None
):
    """Persist progress when paused on intermediateCatchEvent (timer or message), PAR-015."""
    st = wait_exc.state
    if hasattr(st, "model_dump") and callable(st.model_dump):
        state_data = st.model_dump()
    else:
        state_data = {"workflow_steps": list(getattr(st, "workflow_steps", []) or [])}
    next_step = wait_exc.next_step
    engine_state = getattr(wait_exc.state, "_bpmn_engine_state", None)
    completed_node_ids = list(engine_state["completed_node_ids"]) if engine_state else []
    current_node_ids = current_node_ids_for_progress(engine_state) if engine_state else []
    progress_data = {
        "state_class": wait_exc.state.__class__.__name__,
        "state_data": state_data,
        "pending_tasks": [],
        "next_step": next_step,
        "paused_at": datetime.now(UTC).isoformat(),
        "completed_node_ids": completed_node_ids,
        "current_node_ids": current_node_ids,
        "failed_node_id": None,
        "engine_state": engine_state,
        "bpmn_intermediate_wait_kind": wait_exc.wait_kind,
    }
    await database_sync_to_async(_update_workflow_progress_sync)(run_id, progress_data)
    st = "waiting_for_bpmn_timer" if wait_exc.wait_kind == "timer" else "waiting_for_bpmn_message"
    await database_sync_to_async(_update_workflow_status_sync)(run_id, st)
    if send_message:
        await send_message(
            "bpmn_intermediate_wait",
            {
                "wait_kind": wait_exc.wait_kind,
                "next_step": next_step,
                "message": f"Waiting for BPMN {wait_exc.wait_kind} at {next_step}",
            },
        )
    logger.info(
        "Workflow %s paused on intermediate catch (%s) at %s",
        run_id,
        wait_exc.wait_kind,
        next_step,
    )


def reconstruct_workflow_state_for_resume(
    workflow_id: str, state_class_name: str, state_data: dict
) -> Any:
    """
    Restore workflow state from persisted progress_data (Pydantic model_validate).
    """
    from importlib import import_module

    try:
        mod = import_module(f"workflows.{workflow_id}.workflow")
    except ImportError as e:
        raise ValueError(f"Cannot load workflows.{workflow_id}.workflow for resume: {e}") from e
    cls = getattr(mod, state_class_name, None)
    if cls is None:
        raise ValueError(
            f"State class {state_class_name!r} not found in workflows.{workflow_id}.workflow"
        )
    if not hasattr(cls, "model_validate"):
        raise ValueError(f"{state_class_name} is not a Pydantic model")
    return cls.model_validate(state_data or {})


async def _prepare_resume_context(workflow_run, *, after_state_restore=None) -> dict[str, Any]:
    from agent_app.models import WorkflowRun
    from agent_app.workflow_registry import workflow_registry

    workflow_id = workflow_run.workflow_id
    if not can_run_with_bpmn_engine(workflow_id):
        raise ValueError(f"Workflow {workflow_id} is not BPMN-ready")

    fresh = await database_sync_to_async(WorkflowRun.objects.get)(run_id=workflow_run.run_id)
    if fresh.status == WorkflowRun.STATUS_CANCELLED:
        raise ValueError("Cannot resume a cancelled workflow run.")

    pd = workflow_run.progress_data or {}
    next_step = pd.get("next_step")
    if not next_step:
        raise ValueError("progress_data missing next_step")
    state_class_name = pd.get("state_class")
    if not state_class_name:
        raise ValueError("progress_data missing state_class")

    state = reconstruct_workflow_state_for_resume(
        workflow_id, state_class_name, pd.get("state_data") or {}
    )
    state.__dict__["_bpmn_engine_state"] = normalize_engine_state(pd.get("engine_state"))

    if after_state_restore is not None:
        await after_state_restore(state, workflow_run)

    workflow = workflow_registry.get(workflow_id)
    if not workflow or not workflow.get("executor"):
        raise ValueError(f"No executor for workflow {workflow_id}")

    executor = workflow["executor"]
    executor_instance = (
        executor.__class__(run_id=workflow_run.run_id)
        if hasattr(executor, "__init__")
        else executor
    )
    bpmn, bindings = _get_bindings_and_bpmn(workflow_id)
    return {
        "workflow_id": workflow_id,
        "run_id": workflow_run.run_id,
        "input_data": workflow_run.input_data or {},
        "next_step": next_step,
        "state": state,
        "executor_instance": executor_instance,
        "bpmn": bpmn,
        "bindings": bindings,
    }


def _build_execution_check(run_id: str):
    async def execution_check():
        return await database_sync_to_async(_execution_abort_reason_sync)(run_id)

    return execution_check


async def _run_resumed_workflow_or_handle_pause(
    *,
    run_id: str,
    workflow_ctx: dict[str, Any],
    send_message,
) -> bool:
    max_task_retries = _parse_bpmn_max_task_retries(workflow_ctx["input_data"])
    try:
        await run_bpmn_workflow(
            workflow_ctx["executor_instance"],
            workflow_ctx["state"],
            workflow_ctx["bpmn"],
            workflow_ctx["bindings"],
            start_from_task_id=workflow_ctx["next_step"],
            send_message=_build_progress_sender(run_id, send_message),
            execution_check=_build_execution_check(run_id),
            max_task_retries=max_task_retries,
        )
        return False
    except FrameworkError as e:
        if await _handle_framework_pause_exception(run_id, e, send_message):
            return True
        raise
    except BpmnIntermediateWaitError as e:
        await _handle_workflow_bpmn_intermediate_wait(run_id, e, send_message=send_message)
        return True
    except TaskPendingError as e:
        nxt = get_next_step_for_resume(e.state) or e.next_step
        await _handle_workflow_paused(run_id, e, send_message, next_step_override=nxt)
        return True
    except BpmnEngineError as e:
        await _handle_bpmn_engine_error(
            run_id,
            e,
            input_data=workflow_ctx["input_data"],
            send_message=send_message,
            context_label="BPMN engine error on resume",
            always_structured_error_payload=True,
        )
        return True
    except Exception as e:
        await _handle_unexpected_execution_error(
            run_id,
            e,
            send_message=send_message,
            context_label="Error during resumed BPMN run",
        )
        return True


async def _complete_resumed_workflow(
    *,
    run_id: str,
    workflow_id: str,
    state: Any,
    send_message,
) -> None:
    result = type("Result", (), {"state": state})()
    result_dict = build_result_dict_from_state(result, workflow_id)
    progress_payload = {
        "completed_node_ids": getattr(state, "workflow_steps", []),
        "failed_node_id": None,
        "engine_state": getattr(state, "_bpmn_engine_state", None),
    }
    await database_sync_to_async(_update_workflow_progress_sync)(run_id, progress_payload)
    await database_sync_to_async(_update_workflow_status_sync)(
        run_id,
        "completed",
        completed_at=timezone.now(),
        output_data=result_dict,
    )
    if send_message:
        await send_message("complete", result_dict)
    logger.info("Workflow %s resumed and completed via BPMN runner", run_id)


async def resume_bpmn_after_pause(
    workflow_run,
    *,
    send_message=None,
    after_state_restore=None,
):
    """
    Resume a BPMN workflow from progress_data after human task (or equivalent pause).
    Used by the WebSocket consumer and testable end-to-end against WorkflowRun.

    after_state_restore: optional async callable(state, workflow_run) e.g. to inject
    human task results into state.
    """
    workflow_ctx = await _prepare_resume_context(
        workflow_run, after_state_restore=after_state_restore
    )
    run_id = workflow_ctx["run_id"]
    was_handled = await _run_resumed_workflow_or_handle_pause(
        run_id=run_id,
        workflow_ctx=workflow_ctx,
        send_message=send_message,
    )
    if was_handled:
        return
    await _complete_resumed_workflow(
        run_id=run_id,
        workflow_id=workflow_ctx["workflow_id"],
        state=workflow_ctx["state"],
        send_message=send_message,
    )
