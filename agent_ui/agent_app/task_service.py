"""
Service for managing human tasks in workflows

This module provides functionality for creating and managing human tasks
that pause workflow execution and resume when completed.
"""

import logging
from datetime import timedelta

from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)


class TaskPendingError(Exception):
    """
    Exception raised when workflow needs to wait for human task completion.

    This signals the consumer to:
    1. Serialize the current workflow state
    2. Save state to database
    3. Exit cleanly
    """

    def __init__(self, task_id: str, task_type: str, state, next_step: str):
        self.task_id = task_id
        self.task_type = task_type
        self.state = state  # Current workflow state (Pydantic model)
        self.next_step = next_step  # Step name to resume from after task completion
        super().__init__(f"Workflow paused, waiting for task {task_id}")


class BpmnRetryableTaskError(Exception):
    """
    Transient handler failure: BPMN engine may re-invoke the same task up to
    bpmn_max_task_retries (see BPMN_ENGINE_REVIEW §9). Other exceptions fail immediately.
    """

    def __init__(self, message: str = "Retryable task failure"):
        super().__init__(message)


class BpmnModeledBoundaryError(Exception):
    """
    Handler signals: take the interrupting error boundary path attached to this BPMN task
    (PAR-014). Only if the task has a modeled boundaryErrorEvent; otherwise the run fails
    as handler_error.
    """

    def __init__(self, message: str = "Modeled boundary error"):
        super().__init__(message)


class BpmnIntermediateWaitError(Exception):
    """
    BPMN intermediateCatchEvent (timer or message) not satisfied; runner persists progress
    and sets status to waiting_for_bpmn_timer / waiting_for_bpmn_message (PAR-015).
    """

    def __init__(self, state, next_step: str, wait_kind: str):
        self.state = state
        self.next_step = next_step
        self.wait_kind = wait_kind  # "timer" | "message"
        super().__init__(f"Workflow paused on intermediate catch ({wait_kind}) at {next_step}")


async def create_human_task(
    workflow_run_id: str,
    task_type: str,
    title: str,
    description: str,
    state,
    next_step: str,
    required_role: str = "user",
    input_data: dict = None,
) -> None:
    """
    Create a human task and pause workflow execution.

    This function:
    1. Generates a unique task_id
    2. Creates HumanTask database record
    3. Updates WorkflowRun status to 'waiting_for_task'
    4. Raises TaskPendingError with state for serialization

    Args:
        workflow_run_id: ID of the parent workflow run
        task_type: Type of task (approval, review, data_collection, verification)
        title: Human-readable task title
        description: Task instructions/context
        state: Current workflow state (Pydantic model) to be serialized
        next_step: Step name to resume from after task completion
        required_role: Role required to complete task (user, manager, admin)
        input_data: Context data to display in task form

    Raises:
        TaskPendingError: Always raised to signal workflow pause
    """
    from .utils import generate_short_run_id

    @database_sync_to_async
    def create_task_db():
        from .models import HumanTask, WorkflowRun

        # Generate unique task_id
        task_id = generate_short_run_id()

        logger.info(f"Creating human task {task_id} for workflow {workflow_run_id}")

        # Create HumanTask record
        HumanTask.objects.create(
            task_id=task_id,
            workflow_run_id=workflow_run_id,
            task_type=task_type,
            status=HumanTask.STATUS_OPEN,
            required_role=required_role,
            title=title,
            description=description,
            input_data=input_data or {},
            expires_at=timezone.now() + timedelta(days=7),
        )

        # Track metrics
        try:
            from agent_app.metrics_collector import workflow_tasks_total

            workflow_tasks_total.labels(task_type=task_type, status="created").inc()
        except Exception as e:
            logger.warning(f"Could not track task metrics: {e}")

        # Update WorkflowRun status to waiting
        WorkflowRun.objects.filter(run_id=workflow_run_id).update(
            status=WorkflowRun.STATUS_WAITING_FOR_TASK
        )

        logger.info(f"Task {task_id} created, workflow {workflow_run_id} now waiting")

        return task_id

    task_id = await create_task_db()

    # Raise exception to pause workflow with state for serialization
    raise TaskPendingError(task_id, task_type, state, next_step)


@database_sync_to_async
def get_pending_tasks(workflow_run_id: str):
    """Get all pending tasks for a workflow run"""
    from .models import HumanTask

    return list(
        HumanTask.objects.filter(
            workflow_run_id=workflow_run_id,
            status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
        )
    )


@database_sync_to_async
def get_completed_tasks(workflow_run_id: str):
    """Get all completed tasks for a workflow run"""
    from .models import HumanTask

    return list(
        HumanTask.objects.filter(workflow_run_id=workflow_run_id, status=HumanTask.STATUS_COMPLETED)
    )


@database_sync_to_async
def get_task_count_for_user(user_id: int, user_role: str):
    """Get count of open/in-progress tasks accessible to user"""
    from django.db.models import Q
    from django.utils import timezone

    from .models import HumanTask

    # Role hierarchy: admin can see all, manager can see manager+user, user can see only user
    role_hierarchy = {
        HumanTask.ROLE_ADMIN: [HumanTask.ROLE_ADMIN, HumanTask.ROLE_MANAGER, HumanTask.ROLE_USER],
        HumanTask.ROLE_MANAGER: [HumanTask.ROLE_MANAGER, HumanTask.ROLE_USER],
        HumanTask.ROLE_USER: [HumanTask.ROLE_USER],
    }

    accessible_roles = role_hierarchy.get(user_role, [])

    return HumanTask.objects.filter(
        Q(status=HumanTask.STATUS_OPEN)
        | Q(status=HumanTask.STATUS_IN_PROGRESS, assigned_to_user_id=user_id),
        required_role__in=accessible_roles,
        expires_at__gt=timezone.now(),
    ).count()
