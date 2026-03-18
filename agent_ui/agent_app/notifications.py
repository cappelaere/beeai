"""
Create and manage in-app notifications for tasks and workflows.
"""

from django.utils import timezone

from agent_app.models import HumanTask, Notification


def create_task_assigned_notification(task: HumanTask, user_id: int) -> Notification:
    """Create a notification when a task is claimed/assigned to a user."""
    return Notification.objects.create(
        user_id=user_id,
        kind=Notification.KIND_TASK_ASSIGNED,
        title="Task assigned to you",
        message=f'"{task.title}" is now assigned to you. Complete it before it expires.',
        task_id=task.task_id,
        workflow_run_id=task.workflow_run_id,
    )


def create_workflow_status_notification(
    user_id: int,
    run_id: str,
    workflow_name: str,
    status: str,
    error_message: str = "",
) -> Notification | None:
    """Create a notification when a workflow completes or fails. status must be 'completed' or 'failed'."""
    if status == "completed":
        kind = Notification.KIND_WORKFLOW_COMPLETED
        title = "Workflow completed"
        message = f'"{workflow_name}" finished successfully.'
    elif status == "failed":
        kind = Notification.KIND_WORKFLOW_FAILED
        title = "Workflow failed"
        message = f'"{workflow_name}" failed.'
        if error_message:
            message += f" {error_message[:200]}"
    else:
        return None
    return Notification.objects.create(
        user_id=user_id,
        kind=kind,
        title=title,
        message=message,
        workflow_run_id=run_id,
    )


def ensure_due_soon_notifications_for_user(user_id: int, hours_ahead: int = 24) -> None:
    """
    Create task_due_soon notifications for tasks assigned to user that expire within hours_ahead.
    Idempotent: skips if a due_soon notification for the same task was already created recently.
    """
    now = timezone.now()
    from datetime import timedelta

    window_end = now + timedelta(hours=hours_ahead)
    tasks = HumanTask.objects.filter(
        assigned_to_user_id=user_id,
        status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
        expires_at__gt=now,
        expires_at__lte=window_end,
    ).select_related("workflow_run")
    recent_cutoff = now - timedelta(hours=hours_ahead)
    for task in tasks:
        if Notification.objects.filter(
            user_id=user_id,
            kind=Notification.KIND_TASK_DUE_SOON,
            task_id=task.task_id,
            created_at__gte=recent_cutoff,
        ).exists():
            continue
        Notification.objects.create(
            user_id=user_id,
            kind=Notification.KIND_TASK_DUE_SOON,
            title="Task due soon",
            message=f'"{task.title}" expires at {task.expires_at.strftime("%Y-%m-%d %H:%M")}.',
            task_id=task.task_id,
            workflow_run_id=task.workflow_run_id,
        )
