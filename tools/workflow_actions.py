"""
Action handlers for workflow run management.

This module contains the extracted action handlers for managing workflow runs,
reducing complexity in workflow_tools.py.
"""

import sys
import traceback
from typing import Any

from asgiref.sync import sync_to_async
from django.utils import timezone
from workflow_helpers import (
    WebSocketPrintCapture,
    broadcast_workflow_complete,
    broadcast_workflow_status,
    broadcast_workflow_steps,
    broadcast_workflow_waiting,
    track_workflow_metrics,
)


async def _get_pending_tasks(run_id: str) -> list:
    """Get pending tasks for a workflow run."""
    from agent_app.models import HumanTask

    def get_tasks():
        tasks = HumanTask.objects.filter(
            workflow_run_id=run_id, status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]
        )
        return [
            {
                "task_id": t.task_id,
                "title": t.title,
                "description": t.description,
                "task_type": t.task_type,
                "view_url": f"/workflows/tasks/{t.task_id}/",
            }
            for t in tasks
        ]

    return await sync_to_async(get_tasks, thread_sensitive=False)()


async def _handle_workflow_success(
    run, result, channel_layer, run_id: str, workflow_user_id: int
) -> dict[str, Any]:
    """Handle successful workflow execution."""
    # Broadcast step events to any connected clients
    await broadcast_workflow_steps(
        channel_layer, run_id, workflow_user_id, result.state.workflow_steps
    )

    # Prepare result data
    result_dict = {
        "checks_performed": result.state.checks_performed,
        "workflow_steps": result.state.workflow_steps,
        "timestamp": result.state.timestamp,
        "risk_factors": getattr(result.state, "risk_factors", []),
    }

    # Add workflow-specific fields
    if hasattr(result.state, "approval_status"):
        result_dict["status"] = result.state.approval_status
        result_dict["eligible"] = result.state.is_eligible
        result_dict["requires_review"] = result.state.requires_manual_review
        result_dict["summary"] = result.state.compliance_summary
        result_dict["bid_limit"] = result.state.bid_limit

    # Update workflow with results
    run.status = run.STATUS_COMPLETED
    run.output_data = result_dict
    run.completed_at = timezone.now()
    await sync_to_async(run.save, thread_sensitive=False)()

    # Broadcast completion event
    await broadcast_workflow_complete(channel_layer, run_id, workflow_user_id, result_dict)

    # Track completion metrics
    if run.started_at and run.completed_at:
        duration = (run.completed_at - run.started_at).total_seconds()
        track_workflow_metrics(run.workflow_id, "completed", duration)
    else:
        track_workflow_metrics(run.workflow_id, "completed")

    return {
        "success": True,
        "action": "start",
        "run_id": run_id,
        "workflow_id": run.workflow_id,
        "workflow_name": run.workflow_name,
        "previous_status": "pending",
        "new_status": "completed",
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat(),
        "duration_seconds": (run.completed_at - run.started_at).total_seconds(),
        "result": result_dict,
        "view_url": f"/workflows/runs/{run_id}/",
        "message": f"Workflow run {run_id} completed successfully!",
        "note": "Results are included above. View full details at the URL.",
    }


async def _handle_task_pending(
    run, task_exc, channel_layer, run_id: str, workflow_user_id: int
) -> dict[str, Any]:
    """Handle TaskPendingException when workflow is waiting for human task."""
    next_step = getattr(task_exc, "next_step", "unknown")

    # Update workflow status to waiting_for_task
    run.status = run.STATUS_WAITING_FOR_TASK
    # Save the state for resumption
    state_dict = task_exc.state.model_dump() if hasattr(task_exc.state, "model_dump") else {}
    run.progress_data = {
        "state": state_dict,
        "next_step": next_step,
        "paused_at": timezone.now().isoformat(),
    }
    await sync_to_async(run.save, thread_sensitive=False)()

    # Get pending tasks for this workflow
    pending_tasks = await _get_pending_tasks(run_id)

    # Broadcast waiting status to connected clients
    await broadcast_workflow_waiting(
        channel_layer,
        run_id,
        workflow_user_id,
        pending_tasks,
        f"Workflow is waiting for {len(pending_tasks)} task(s) to be completed",
    )

    return {
        "success": True,
        "action": "start",
        "run_id": run_id,
        "workflow_id": run.workflow_id,
        "workflow_name": run.workflow_name,
        "previous_status": "pending",
        "new_status": "waiting_for_task",
        "started_at": run.started_at.isoformat(),
        "pending_tasks": pending_tasks,
        "task_count": len(pending_tasks),
        "view_url": f"/workflows/runs/{run_id}/",
        "message": f"Workflow run {run_id} is waiting for {len(pending_tasks)} human task(s) to be completed",
        "note": "Use list_tasks() to see pending tasks, then claim and submit a decision to continue the workflow.",
    }


async def _handle_workflow_error(run, error: Exception, run_id: str) -> dict[str, Any]:
    """Handle workflow execution error."""
    # Capture full traceback for debugging
    error_traceback = traceback.format_exc()
    error_detail = f"{type(error).__name__}: {str(error)}"

    # Update workflow with failure
    run.status = run.STATUS_FAILED
    run.error_message = f"{error_detail}\n\nFull traceback:\n{error_traceback}"
    run.completed_at = timezone.now()
    await sync_to_async(run.save, thread_sensitive=False)()

    # Track failure metrics
    track_workflow_metrics(run.workflow_id, "failed")

    return {
        "success": False,
        "action": "start",
        "run_id": run_id,
        "workflow_id": run.workflow_id,
        "workflow_name": run.workflow_name,
        "status": "failed",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_traceback": error_traceback,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "view_url": f"/workflows/runs/{run_id}/",
        "message": f"Workflow run {run_id} failed during execution",
        "debug_info": "Full error details have been saved to the workflow run. Check the view_url for complete information.",
    }


async def _execute_workflow_with_capture(
    executor_instance, run, channel_layer, run_id: str, workflow_user_id: int
) -> tuple[Any, Any]:
    """Execute workflow via BPMN engine only. Returns (result, None) or (None, TaskPendingException)."""
    from agent_app.bpmn_engine import (
        can_run_with_bpmn_engine,
        create_initial_state_from_inputs,
        run_bpmn_workflow,
        _get_bindings_and_bpmn,
    )
    from agent_app.task_service import TaskPendingException

    workflow_id = run.workflow_id
    if not can_run_with_bpmn_engine(workflow_id):
        raise RuntimeError(
            f"Workflow '{workflow_id}' is not BPMN-ready. Only BPMN-driven execution is supported."
        )

    # Capture stdout to broadcast progress messages
    original_stdout = sys.stdout
    group_name = f"workflow_{run_id}"
    sys.stdout = WebSocketPrintCapture(channel_layer, group_name, workflow_user_id, original_stdout)

    try:
        bpmn, bindings = _get_bindings_and_bpmn(workflow_id)
        state = create_initial_state_from_inputs(workflow_id, run.input_data or {})
        await run_bpmn_workflow(executor_instance, state, bpmn, bindings, send_message=None)
        result = type("Result", (), {"state": state})()
        sys.stdout = original_stdout
        return result, None
    except TaskPendingException as task_exc:
        sys.stdout = original_stdout
        return None, task_exc
    except Exception:
        sys.stdout = original_stdout
        raise


async def start_workflow_run(run, workflow_registry) -> dict[str, Any]:
    """Handle starting a pending workflow run."""
    WorkflowRun = run.__class__  # noqa: N806
    run_id = run.run_id

    # Can only start pending workflows
    if run.status != WorkflowRun.STATUS_PENDING:
        return {
            "success": False,
            "error": f"Cannot start workflow in '{run.status}' status. Only pending workflows can be started.",
            "run_id": run_id,
            "current_status": run.status,
        }

    # Get workflow from registry
    workflow = workflow_registry.get(run.workflow_id)
    if not workflow:
        return {
            "success": False,
            "error": f"Workflow '{run.workflow_id}' not found in registry",
            "run_id": run_id,
        }

    # Mark as running
    run.status = WorkflowRun.STATUS_RUNNING
    run.started_at = timezone.now()
    await sync_to_async(run.save, thread_sensitive=False)()

    # Track metrics
    track_workflow_metrics(run.workflow_id, "running")

    # Execute workflow directly (await it to preserve Django context)
    executor = workflow["executor"]

    # Create new executor instance with run_id
    executor_class = executor.__class__
    executor_instance = executor_class(run_id=run_id)

    # Get channel layer for broadcasting progress
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()

    # Get user_id for the workflow
    workflow_user_id = run.user_id

    # Broadcast initial status
    await broadcast_workflow_status(channel_layer, run_id, workflow_user_id, "running")

    # Execute the workflow with capture
    result, task_exc = await _execute_workflow_with_capture(
        executor_instance, run, channel_layer, run_id, workflow_user_id
    )

    if task_exc:
        # Workflow is waiting for human task
        return await _handle_task_pending(run, task_exc, channel_layer, run_id, workflow_user_id)
    if result:
        # Workflow completed successfully
        return await _handle_workflow_success(run, result, channel_layer, run_id, workflow_user_id)
    # This shouldn't happen, but handle gracefully
    return {"success": False, "error": "Unexpected workflow execution result", "run_id": run_id}


async def cancel_workflow_run(run, reason: str = None) -> dict[str, Any]:
    """Handle cancelling a workflow run."""
    WorkflowRun = run.__class__  # noqa: N806
    run_id = run.run_id

    # Can cancel if pending, running, or waiting
    if run.status not in [
        WorkflowRun.STATUS_PENDING,
        WorkflowRun.STATUS_RUNNING,
        WorkflowRun.STATUS_WAITING_FOR_TASK,
    ]:
        return {
            "success": False,
            "error": f"Cannot cancel workflow in '{run.status}' status",
            "run_id": run_id,
            "current_status": run.status,
        }

    # Cancel the workflow
    old_status = run.status
    run.status = WorkflowRun.STATUS_CANCELLED
    run.completed_at = timezone.now()
    if not run.error_message:
        run.error_message = reason or "Cancelled by user"
    await sync_to_async(run.save, thread_sensitive=False)()

    # Track metrics
    track_workflow_metrics(run.workflow_id, "cancelled")

    # Try to notify via WebSocket
    try:
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer:
            await channel_layer.group_send(
                f"workflow_{run_id}",
                {
                    "type": "workflow_cancelled",
                    "run_id": run_id,
                    "reason": reason or "Cancelled by user",
                },
            )
            notification_status = "Workflow notified of cancellation"
        else:
            notification_status = "No WebSocket available"
    except Exception as e:
        notification_status = f"Could not notify: {str(e)}"

    return {
        "success": True,
        "action": "cancel",
        "run_id": run_id,
        "workflow_id": run.workflow_id,
        "workflow_name": run.workflow_name,
        "previous_status": old_status,
        "new_status": run.status,
        "cancelled_at": run.completed_at.isoformat(),
        "reason": reason or "Cancelled by user",
        "notification_status": notification_status,
        "message": f"Workflow run {run_id} has been cancelled",
    }


async def restart_workflow_run(
    run, generate_short_run_id, user_id: int, reason: str = None
) -> dict[str, Any]:
    """Handle restarting a failed or cancelled workflow run."""
    WorkflowRun = run.__class__  # noqa: N806
    run_id = run.run_id

    # Can restart if failed or cancelled
    if run.status not in [WorkflowRun.STATUS_FAILED, WorkflowRun.STATUS_CANCELLED]:
        return {
            "success": False,
            "error": f"Cannot restart workflow in '{run.status}' status. Only failed or cancelled workflows can be restarted.",
            "run_id": run_id,
            "current_status": run.status,
        }

    # Create a new run with same inputs
    new_run_id = generate_short_run_id()
    new_run = await sync_to_async(WorkflowRun.objects.create, thread_sensitive=False)(
        run_id=new_run_id,
        workflow_id=run.workflow_id,
        workflow_name=run.workflow_name,
        status=WorkflowRun.STATUS_PENDING,
        user_id=user_id,
        input_data=run.input_data,
    )

    # Track metrics
    track_workflow_metrics(new_run.workflow_id, "pending")

    return {
        "success": True,
        "action": "restart",
        "original_run_id": run_id,
        "new_run_id": new_run_id,
        "workflow_id": new_run.workflow_id,
        "workflow_name": new_run.workflow_name,
        "status": new_run.status,
        "input_data": new_run.input_data,
        "reason": reason or "Restarted by user",
        "view_url": f"/workflows/runs/{new_run_id}/",
        "message": f"Created new workflow run {new_run_id} (restart of {run_id})",
        "next_step": f"Open /workflows/runs/{new_run_id}/ to start execution or use get_run_detail('{new_run_id}')",
    }
