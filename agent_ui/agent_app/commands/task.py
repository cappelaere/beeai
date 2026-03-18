"""
/task command handler - Manage human tasks from command line
"""


def _handle_task_list(args, user_id, user_role):
    """List pending or all tasks."""
    from django.db import models
    from django.utils import timezone

    from agent_app.models import HumanTask

    show_all = len(args) > 1 and args[1] == "all"

    if show_all:
        tasks = HumanTask.objects.filter(
            models.Q(assigned_to_user_id=user_id) | models.Q(required_role=user_role)
        ).order_by("-created_at")[:50]
    else:
        tasks = (
            HumanTask.objects.filter(
                models.Q(status=HumanTask.STATUS_OPEN)
                | models.Q(status=HumanTask.STATUS_IN_PROGRESS)
            )
            .filter(models.Q(assigned_to_user_id=user_id) | models.Q(required_role=user_role))
            .order_by("-created_at")[:20]
        )

    if not tasks:
        msg = "📭 No tasks found.\n\n💡 Tasks appear here when workflows need human review."
        if not show_all:
            msg += "\n\nTip: Use /task list all to see completed/cancelled tasks"
        return {"content": msg, "metadata": {"command": "task list", "count": 0}}

    status_label = "All Tasks" if show_all else "Pending Tasks"
    lines = [f"📋 Your {status_label} ({tasks.count()}):", ""]

    for task in tasks:
        age = timezone.now() - task.created_at
        age_str = f"{age.seconds // 3600}h" if age.seconds >= 3600 else f"{age.seconds // 60}m"

        status_emoji = {
            "open": "🔷",
            "in_progress": "🔶",
            "completed": "✅",
            "cancelled": "❌",
            "expired": "⏰",
        }.get(task.status, "❓")

        lines.append(f"{status_emoji} Task {task.task_id} ({task.status})")
        lines.append(f"   Workflow: {task.workflow_run.workflow_name}")
        lines.append(f"   Run ID: {task.workflow_run.run_id}")
        lines.append(f"   Description: {task.description[:80]}")
        lines.append(f"   Created: {age_str} ago")
        lines.append("   Commands:")
        lines.append(f"     /task {task.task_id} - View details")
        if task.status == HumanTask.STATUS_OPEN:
            lines.append(f"     /task claim {task.task_id} - Claim task")
        if task.status in [HumanTask.STATUS_COMPLETED, HumanTask.STATUS_CANCELLED]:
            lines.append(f"     /task delete {task.task_id} - Delete task")
        lines.append("")

    footer = "💡 Use /task <task_id> to see full details and form fields"
    if not show_all:
        footer += "\n💡 Use /task list all to see completed/cancelled tasks"
    lines.append(footer)

    return {
        "content": "\n".join(lines),
        "metadata": {"command": "task list", "count": tasks.count(), "show_all": show_all},
    }


def _handle_task_claim(args, user_id, logger):
    """Claim a task."""
    from django.utils import timezone

    from agent_app.models import HumanTask

    if len(args) < 2:
        return {
            "content": "Usage: /task claim <task_id>",
            "metadata": {"error": True, "command": "task claim"},
        }

    task_id = args[1]

    try:
        task = HumanTask.objects.get(task_id=task_id)

        if task.status != HumanTask.STATUS_OPEN:
            return {
                "content": f"❌ Task {task_id} is already {task.status}.",
                "metadata": {"error": True, "command": "task claim"},
            }

        task.assigned_to_user_id = user_id
        task.claimed_at = timezone.now()
        task.status = HumanTask.STATUS_IN_PROGRESS
        task.save()

        logger.info(f"✓ Task {task_id} claimed by user {user_id}")

        return {
            "content": (
                f"✓ Task {task_id} claimed successfully!\n\n"
                f"Workflow: {task.workflow_run.workflow_name}\n"
                f"Run ID: {task.workflow_run.run_id}\n"
                f"Description: {task.description}\n\n"
                f"Next steps:\n"
                f"  /task {task_id} - View task details and form\n"
                f"  /task submit {task_id} approve - Approve\n"
                f"  /task submit {task_id} deny - Deny"
            ),
            "metadata": {"command": "task claim", "task_id": task_id, "claimed": True},
        }

    except HumanTask.DoesNotExist:
        return {
            "content": f"❌ Task {task_id} not found. Use /task list to see available tasks.",
            "metadata": {"error": True, "command": "task claim"},
        }


def _handle_task_delete(args, user_id, logger):
    """Delete a completed or cancelled task."""
    from agent_app.models import HumanTask

    if len(args) < 2:
        return {
            "content": "Usage: /task delete <task_id>",
            "metadata": {"error": True, "command": "task delete"},
        }

    task_id = args[1]

    try:
        task = HumanTask.objects.get(task_id=task_id)

        if task.status not in [
            HumanTask.STATUS_COMPLETED,
            HumanTask.STATUS_CANCELLED,
            HumanTask.STATUS_EXPIRED,
        ]:
            return {
                "content": f"❌ Cannot delete task {task_id} - task is {task.status}.\n\nOnly completed, cancelled, or expired tasks can be deleted.",
                "metadata": {"error": True, "command": "task delete"},
            }

        workflow_name = task.workflow_run.workflow_name
        run_id = task.workflow_run.run_id
        task.delete()

        logger.info(f"🗑️  Task {task_id} deleted by user {user_id}")

        return {
            "content": (
                f"✅ Task {task_id} deleted successfully!\n\n"
                f"Workflow: {workflow_name}\n"
                f"Run ID: {run_id}\n\n"
                f"The task has been permanently removed from the system."
            ),
            "metadata": {"command": "task delete", "task_id": task_id, "deleted": True},
        }

    except HumanTask.DoesNotExist:
        return {
            "content": f"❌ Task {task_id} not found. Use /task list all to see all tasks.",
            "metadata": {"error": True, "command": "task delete"},
        }


def _handle_task_submit(args, user_id, logger):
    """Submit a task decision."""
    from django.utils import timezone

    from agent_app.models import HumanTask

    if len(args) < 3:
        return {
            "content": "Usage: /task submit <task_id> <approve|deny>",
            "metadata": {"error": True, "command": "task submit"},
        }

    task_id = args[1]
    decision = args[2].lower()

    if decision not in ["approve", "deny", "approved", "denied"]:
        return {
            "content": f"❌ Invalid decision '{decision}'. Use 'approve' or 'deny'.",
            "metadata": {"error": True, "command": "task submit"},
        }

    decision = "approved" if decision in ["approve", "approved"] else "denied"

    try:
        task = HumanTask.objects.get(task_id=task_id)

        if task.status not in [HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]:
            return {
                "content": f"❌ Task {task_id} is already {task.status}.",
                "metadata": {"error": True, "command": "task submit"},
            }

        task.status = HumanTask.STATUS_COMPLETED
        task.completed_at = timezone.now()
        task.completed_by_user_id = user_id
        task.output_data = {
            "decision": decision,
            "notes": "Submitted via /task command",
            "submitted_by": user_id,
            "submitted_at": timezone.now().isoformat(),
        }
        task.save()

        logger.info(f"✓ Task {task_id} submitted with decision: {decision}")

        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"workflow_{task.workflow_run.run_id}",
                    {"type": "task_completed", "task_id": task_id, "decision": decision},
                )
                resume_msg = "\n\n🔄 Workflow will resume automatically."
            else:
                resume_msg = "\n\n⚠️  Workflow needs manual restart from UI."
        except Exception as e:
            logger.warning(f"Could not notify workflow: {e}")
            resume_msg = "\n\n⚠️  Please check workflow status in UI."

        return {
            "content": (
                f"✅ Task {task_id} submitted successfully!\n\n"
                f"Decision: {decision.upper()}\n"
                f"Workflow: {task.workflow_run.workflow_name}\n"
                f"Run ID: {task.workflow_run.run_id}{resume_msg}\n\n"
                f"View workflow: /workflows/runs/{task.workflow_run.run_id}/"
            ),
            "metadata": {
                "command": "task submit",
                "task_id": task_id,
                "decision": decision,
                "workflow_run_id": task.workflow_run.run_id,
            },
        }

    except HumanTask.DoesNotExist:
        return {
            "content": f"❌ Task {task_id} not found. Use /task list to see available tasks.",
            "metadata": {"error": True, "command": "task submit"},
        }
    except Exception as e:
        logger.error(f"Error submitting task: {e}", exc_info=True)
        return {
            "content": f"❌ Error submitting task: {str(e)}",
            "metadata": {"error": True, "command": "task submit"},
        }


def _handle_task_show(task_id):
    """Show task details."""
    from agent_app.models import HumanTask

    try:
        task = HumanTask.objects.get(task_id=task_id)

        form_fields = []
        if task.form_schema:
            for field_name, field_config in task.form_schema.items():
                field_type = field_config.get("type", "text")
                required = "✓" if field_config.get("required") else " "
                form_fields.append(
                    f"  [{required}] {field_name} ({field_type}): {field_config.get('label', field_name)}"
                )

        status_emoji = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}.get(
            task.status, "❓"
        )

        claimed_info = ""
        if task.assigned_to_user_id:
            claimed_info = f"Claimed by: User {task.assigned_to_user_id} at {task.claimed_at}\n"

        completed_info = ""
        if task.status == HumanTask.STATUS_COMPLETED:
            by_user = f" by User {task.completed_by_user_id}" if task.completed_by_user_id else ""
            completed_info = f"Completed: {task.completed_at}{by_user}\n"

        return {
            "content": (
                f"{status_emoji} Task {task.task_id}\n"
                f"{'=' * 60}\n\n"
                f"Status: {task.status}\n"
                f"Workflow: {task.workflow_run.workflow_name}\n"
                f"Run ID: {task.workflow_run.run_id}\n"
                f"Description: {task.description}\n"
                f"Created: {task.created_at}\n"
                f"{claimed_info}"
                f"{completed_info}\n"
                f"Form Fields:\n"
                + ("\n".join(form_fields) if form_fields else "  No form fields")
                + "\n\n"
                f"Commands:\n"
                f"  /task claim {task_id} - Claim this task\n"
                f"  /task submit {task_id} approve - Approve\n"
                f"  /task submit {task_id} deny - Deny\n\n"
                f"View in UI: /workflows/runs/{task.workflow_run.run_id}/"
            ),
            "metadata": {"command": "task show", "task_id": task_id, "status": task.status},
        }

    except HumanTask.DoesNotExist:
        return {
            "content": f"❌ Task {task_id} not found. Use /task list to see available tasks.",
            "metadata": {"error": True, "command": "task"},
        }


def handle_task(request, args, session_key):
    """
    Handle task-related commands.

    Commands:
        /task - List my pending tasks
        /task list - List my pending tasks
        /task list all - List all tasks (including completed)
        /task <task_id> - Show task details
        /task claim <task_id> - Claim a task
        /task submit <task_id> <decision> - Submit task decision (approve/deny)
        /task delete <task_id> - Delete a task

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    import logging

    from agent_app.constants import ANONYMOUS_USER_ID

    logger = logging.getLogger(__name__)
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    user_role = request.session.get("user_role", "admin")

    if not args or args[0] == "list":
        return _handle_task_list(args, user_id, user_role)

    if args[0] == "claim":
        return _handle_task_claim(args, user_id, logger)

    if args[0] == "delete" or args[0] == "remove":
        return _handle_task_delete(args, user_id, logger)

    if args[0] == "submit":
        return _handle_task_submit(args, user_id, logger)

    return _handle_task_show(args[0])
