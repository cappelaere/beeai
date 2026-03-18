"""
Django Channels consumers for WebSocket-based workflow execution
"""

import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.bpmn_engine import can_run_with_bpmn_engine
from agent_app.task_service import get_completed_tasks, get_pending_tasks
from agent_app.workflow_runner import execute_workflow_run, resume_bpmn_after_pause

logger = logging.getLogger(__name__)


class WorkflowConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for asynchronous workflow execution.

    Handles:
    - Real-time progress updates during workflow execution
    - Persistent storage of workflow state in database
    - Graceful handling of disconnections (workflow continues running)
    """

    async def connect(self):
        """Accept WebSocket connection and validate run_id"""
        self.run_id = self.scope["url_route"]["kwargs"]["run_id"]

        # Get user_id from session (default to ANONYMOUS_USER_ID when not set)
        self.user_id = self.scope.get("session", {}).get("user_id", ANONYMOUS_USER_ID)

        # Join workflow group for broadcast messages
        self.group_name = f"workflow_{self.run_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the connection
        await self.accept()

        logger.info(f"WebSocket connected for run_id: {self.run_id}, user_id: {self.user_id}")

        # Check if workflow run exists
        workflow_run = await self.get_workflow_run(self.run_id)

        if not workflow_run:
            await self.send_json(
                {"type": "error", "message": f"Workflow run {self.run_id} not found"}
            )
            await self.close()
            return

        # Check if user has access to this workflow run
        if workflow_run.user_id != self.user_id:
            await self.send_json(
                {"type": "error", "message": "Unauthorized access to workflow run"}
            )
            await self.close()
            return

        # If workflow is pending, start execution (or resume if progress_data exists)
        if workflow_run.status == "pending":
            logger.info(
                f"Workflow {workflow_run.run_id} is pending, has_progress_data={bool(workflow_run.progress_data)}"
            )
            if workflow_run.progress_data:
                # This is a resumed workflow after task completion
                logger.info(f"Resuming workflow {workflow_run.run_id} from saved state")
                await self.send_json(
                    {
                        "type": "status",
                        "status": "resuming",
                        "message": "Task completed, resuming workflow",
                    }
                )
                await self.resume_workflow_execution(workflow_run)
            else:
                # Normal new execution
                await self.start_workflow_execution(workflow_run)
        elif workflow_run.status in (
            "waiting_for_bpmn_timer",
            "waiting_for_bpmn_message",
        ):
            pd = workflow_run.progress_data or {}
            eng = pd.get("engine_state") or {}
            bew = eng.get("bpmn_event_wait") if isinstance(eng.get("bpmn_event_wait"), dict) else {}
            await self.send_json(
                {
                    "type": "waiting_bpmn_event",
                    "wait_kind": pd.get("bpmn_intermediate_wait_kind")
                    or ("timer" if workflow_run.status == "waiting_for_bpmn_timer" else "message"),
                    "next_step": pd.get("next_step"),
                    "bpmn_event_wait": bew,
                    "message": (
                        "Waiting for BPMN timer; use Resume on the run page when ready."
                        if workflow_run.status == "waiting_for_bpmn_timer"
                        else "Waiting for BPMN message; satisfy message then resume."
                    ),
                }
            )
        elif workflow_run.status == "waiting_for_task":
            # Workflow is waiting for human task completion
            pending_tasks = await get_pending_tasks(workflow_run.run_id)
            completed_tasks = await get_completed_tasks(workflow_run.run_id)

            if completed_tasks:
                # Tasks completed, mark as pending to trigger resume
                await self.update_workflow_status(workflow_run.run_id, "pending")
                await self.send_json(
                    {
                        "type": "status",
                        "status": "resuming",
                        "message": "Tasks completed, resuming workflow",
                    }
                )
                # Reload workflow_run to get updated status
                workflow_run = await self.get_workflow_run(workflow_run.run_id)
                await self.resume_workflow_execution(workflow_run)
            else:
                # Still waiting for tasks
                await self.send_json(
                    {
                        "type": "waiting",
                        "status": "waiting_for_task",
                        "pending_tasks": [
                            {
                                "id": t.task_id,
                                "title": t.title,
                                "url": f"/workflows/tasks/{t.task_id}/",
                            }
                            for t in pending_tasks
                        ],
                        "message": f"Workflow is waiting for {len(pending_tasks)} task(s) to be completed",
                    }
                )
        elif workflow_run.status == "running":
            # Reconnection to running workflow
            await self.send_json(
                {
                    "type": "reconnected",
                    "status": "running",
                    "progress": workflow_run.progress_data or {},
                }
            )
        elif workflow_run.status == "completed":
            # Already completed, send final results
            await self.send_json({"type": "complete", "result": workflow_run.output_data})
        elif workflow_run.status == "failed":
            pd = workflow_run.progress_data or {}
            eng = pd.get("engine_state") or {}
            payload = {
                "type": "error",
                "message": workflow_run.error_message,
                "failure_reason": pd.get("failure_reason"),
                "failed_node_id": pd.get("failed_node_id"),
                "last_successful_node_id": pd.get("last_successful_node_id"),
                "condition_failure_metadata": pd.get("condition_failure_metadata"),
            }
            if pd.get("failure_reason") == "timeout":
                payload["timeout_seconds"] = pd.get("timeout_seconds")
                payload["timed_out_at"] = pd.get("timed_out_at")
            if isinstance(eng, dict) and (
                eng.get("pending_joins") or len(eng.get("active_tokens") or []) > 1
            ):
                payload["engine_state"] = {
                    "active_tokens": eng.get("active_tokens"),
                    "pending_joins": eng.get("pending_joins"),
                }
            await self.send_json(payload)
        elif workflow_run.status == "cancelled":
            pd = workflow_run.progress_data or {}
            eng = pd.get("engine_state") or {}
            payload = {
                "type": "cancelled",
                "message": workflow_run.error_message or "Workflow execution cancelled",
                "failure_reason": pd.get("failure_reason") or "cancelled",
                "cancelled_at": pd.get("cancelled_at"),
                "last_successful_node_id": pd.get("last_successful_node_id"),
            }
            if isinstance(eng, dict):
                payload["engine_state"] = {
                    "active_tokens": eng.get("active_tokens"),
                    "pending_joins": eng.get("pending_joins"),
                }
            await self.send_json(payload)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave workflow group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected for run_id: {self.run_id}, code: {close_code}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages (optional for future commands)"""
        try:
            data = json.loads(text_data)
            command = data.get("command")

            if command == "cancel":
                # Cancel workflow execution
                await self.cancel_workflow()
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid message format"})

    async def start_workflow_execution(self, workflow_run):
        """Execute the workflow asynchronously and stream updates via shared runner."""

        async def send_message(msg_type, payload):
            if msg_type == "status":
                await self.send_json({"type": "status", "status": payload})
            elif msg_type == "step":
                await self.send_json({"type": "step", "step": payload})
            elif msg_type == "complete":
                await self.send_json({"type": "complete", "result": payload})
            elif msg_type == "error":
                if isinstance(payload, dict):
                    await self.send_json({"type": "error", **payload})
                else:
                    await self.send_json({"type": "error", "message": payload})
            elif msg_type == "task_created":
                await self.send_json({"type": "task_created", **payload})
            elif msg_type == "progress":
                await self.send_json({"type": "progress", **payload})

        await execute_workflow_run(workflow_run.run_id, send_message=send_message)

    def _reconstruct_state(self, state_class_name, state_data):
        """Reconstruct workflow state from saved data."""
        if state_class_name == "BidderOnboardingState":
            from workflows.bidder_onboarding.workflow import BidderOnboardingState

            return BidderOnboardingState.model_validate(state_data)
        if state_class_name == "PropertyDueDiligenceState":
            from workflows.property_due_diligence.workflow import PropertyDueDiligenceState

            return PropertyDueDiligenceState.model_validate(state_data)
        raise ValueError(f"Unknown state class: {state_class_name}")

    def _build_base_result_dict(self, state):
        """Build base result dictionary from workflow state."""
        return {
            "checks_performed": state.checks_performed,
            "workflow_steps": state.workflow_steps,
            "timestamp": state.timestamp,
            "risk_factors": getattr(state, "risk_factors", []),
        }

    def _add_bidder_onboarding_fields(self, result_dict, state):
        """Add bidder onboarding specific fields to result."""
        result_dict["status"] = state.approval_status
        result_dict["eligible"] = state.is_eligible
        result_dict["requires_review"] = state.requires_manual_review
        result_dict["summary"] = state.compliance_summary
        result_dict["bid_limit"] = state.bid_limit
        if hasattr(state, "human_review_result") and state.human_review_result:
            result_dict["human_review"] = state.human_review_result

    def _add_due_diligence_fields(self, result_dict, state):
        """Add property due diligence specific fields to result."""
        result_dict["findings_summary"] = state.findings_summary
        result_dict["recommendations"] = state.recommendations
        result_dict["risk_level"] = state.risk_level
        result_dict["property_details"] = state.property_details
        result_dict["comparable_sales"] = state.comparable_sales
        result_dict["documents_found"] = state.documents_found
        result_dict["compliance_checks"] = state.compliance_checks
        result_dict["auction_history"] = state.auction_history

    def _prepare_result_data(self, state):
        """Prepare complete result dictionary from workflow state."""
        result_dict = self._build_base_result_dict(state)

        if hasattr(state, "approval_status"):
            self._add_bidder_onboarding_fields(result_dict, state)

        if hasattr(state, "findings_summary"):
            self._add_due_diligence_fields(result_dict, state)

        return result_dict

    async def _execute_workflow_steps(self, executor_instance, state, start_step):
        """Execute workflow steps starting from a given step."""
        current_step = start_step
        while current_step:
            step_method = getattr(executor_instance, current_step, None)
            if not step_method:
                logger.error(f"Step method {current_step} not found")
                break

            await self.send_json({"type": "step", "step": current_step})
            next_step_name = await step_method(state)

            if current_step not in state.workflow_steps:
                state.workflow_steps.append(current_step)

            current_step = next_step_name
            await asyncio.sleep(0.1)

    async def resume_workflow_execution(self, workflow_run):
        """Resume workflow from saved state after task completion"""
        try:
            await self.update_workflow_status(
                workflow_run.run_id, "running", started_at=timezone.now()
            )
            await self.send_json({"type": "status", "status": "running"})

            progress_data = workflow_run.progress_data
            next_step = progress_data["next_step"]

            logger.info(f"Resuming workflow {workflow_run.run_id} from step {next_step}")

            from agent_app.workflow_registry import workflow_registry

            workflow = workflow_registry.get(workflow_run.workflow_id)

            if not workflow:
                raise ValueError(f"Workflow {workflow_run.workflow_id} not found in registry")

            if can_run_with_bpmn_engine(workflow_run.workflow_id):

                async def after_restore(st, wr):
                    completed_tasks = await get_completed_tasks(wr.run_id)
                    for task in completed_tasks:
                        if task.task_type == "approval":
                            st.human_review_result = task.output_data
                            logger.info("Injected approval task %s result into state", task.task_id)

                async def send_resume(msg_type, payload):
                    if msg_type == "step":
                        await self.send_json({"type": "step", "step": payload})
                    elif msg_type == "complete":
                        await self.send_json({"type": "complete", "result": payload})
                    elif msg_type == "task_created":
                        await self.send_json({"type": "task_created", **payload})
                    elif msg_type == "error":
                        if isinstance(payload, dict):
                            await self.send_json({"type": "error", **payload})
                        else:
                            await self.send_json({"type": "error", "message": payload})

                await resume_bpmn_after_pause(
                    workflow_run,
                    send_message=send_resume,
                    after_state_restore=after_restore,
                )
            else:
                state_class_name = progress_data["state_class"]
                state_data = progress_data["state_data"]
                state = self._reconstruct_state(state_class_name, state_data)

                completed_tasks = await get_completed_tasks(workflow_run.run_id)
                for task in completed_tasks:
                    if task.task_type == "approval":
                        state.human_review_result = task.output_data
                        logger.info(f"Injected approval task {task.task_id} result into state")

                executor = workflow["executor"]
                if hasattr(executor, "__init__"):
                    executor_instance = executor.__class__(run_id=workflow_run.run_id)
                else:
                    executor_instance = executor

                await self._execute_workflow_steps(executor_instance, state, next_step)

                result_dict = self._prepare_result_data(state)

                await self.update_workflow_status(
                    workflow_run.run_id,
                    "completed",
                    completed_at=timezone.now(),
                    output_data=result_dict,
                )

                await self.send_json({"type": "complete", "result": result_dict})
                logger.info(f"Workflow {self.run_id} resumed and completed successfully")

        except Exception as e:
            logger.error(f"Error resuming workflow {workflow_run.run_id}: {e}", exc_info=True)

            await self.update_workflow_status(
                workflow_run.run_id, "failed", completed_at=timezone.now(), error_message=str(e)
            )

            await self.send_json({"type": "error", "message": f"Error resuming workflow: {str(e)}"})

    async def cancel_workflow(self):
        """Cancel the running workflow"""
        await self.update_workflow_status(self.run_id, "cancelled", completed_at=timezone.now())
        await self.send_json({"type": "cancelled", "message": "Workflow execution cancelled"})

    async def send_json(self, data):
        """Helper to send JSON data"""
        await self.send(text_data=json.dumps(data))

    async def workflow_message(self, event):
        """
        Handler for broadcast messages from channel layer.
        Called when a workflow started from command line sends progress updates.

        Only forwards messages if the user_id matches the connected user.
        """
        # Check if message is for this user
        event_user_id = event.get("user_id")
        if event_user_id is not None and event_user_id != self.user_id:
            # Message is for a different user, ignore it
            logger.debug(
                f"Ignoring workflow message for user {event_user_id}, connected user is {self.user_id}"
            )
            return

        # Extract message data
        message_type = event.get("message_type")

        # Forward the message to the WebSocket client
        if message_type == "status":
            await self.send_json({"type": "status", "status": event.get("status")})
        elif message_type == "progress":
            # Real-time progress text from workflow print statements
            await self.send_json({"type": "progress", "text": event.get("text")})
        elif message_type == "step":
            await self.send_json({"type": "step", "step": event.get("step")})
        elif message_type == "complete":
            await self.send_json({"type": "complete", "result": event.get("result")})
        elif message_type == "waiting":
            await self.send_json(
                {
                    "type": "waiting",
                    "status": event.get("status"),
                    "pending_tasks": event.get("pending_tasks", []),
                    "message": event.get("message"),
                }
            )
        elif message_type == "error":
            await self.send_json({"type": "error", "message": event.get("message")})

    @database_sync_to_async
    def get_workflow_run(self, run_id):
        """Retrieve workflow run from database"""
        from .models import WorkflowRun

        try:
            return WorkflowRun.objects.get(run_id=run_id)
        except WorkflowRun.DoesNotExist:
            return None

    @database_sync_to_async
    def update_workflow_status(self, run_id, status, **kwargs):
        """Update workflow run status and optional fields"""

        from agent_app.metrics_collector import (
            workflow_execution_duration_seconds,
            workflow_runs_total,
        )

        from .models import WorkflowRun

        update_fields = {"status": status}
        update_fields.update(kwargs)

        # Get workflow run to track metrics
        try:
            workflow_run = WorkflowRun.objects.get(run_id=run_id)
            workflow_id = workflow_run.workflow_id

            # Track status transitions in Prometheus
            workflow_runs_total.labels(workflow_id=workflow_id, status=status).inc()

            # Track execution duration for completed workflows
            if status == "completed" and workflow_run.started_at and "completed_at" in kwargs:
                duration = (kwargs["completed_at"] - workflow_run.started_at).total_seconds()
                workflow_execution_duration_seconds.labels(workflow_id=workflow_id).observe(
                    duration
                )

            # Update the workflow run
            WorkflowRun.objects.filter(run_id=run_id).update(**update_fields)

            # Notify user when workflow completes or fails
            if status in ("completed", "failed"):
                from agent_app.notifications import create_workflow_status_notification

                create_workflow_status_notification(
                    workflow_run.user_id,
                    run_id,
                    workflow_run.workflow_name,
                    status,
                    kwargs.get("error_message", ""),
                )

        except Exception as e:
            logger.warning(f"Could not track workflow metrics: {e}")
            # Still perform update if get failed
            WorkflowRun.objects.filter(run_id=run_id).update(**update_fields)

    @database_sync_to_async
    def update_workflow_progress(self, run_id, progress_data):
        """Update workflow run progress data"""
        from .models import WorkflowRun

        WorkflowRun.objects.filter(run_id=run_id).update(progress_data=progress_data)
