"""
/schedule command handler - Schedule workflows to run once or on an interval.
"""

from datetime import datetime, timedelta

from django.utils import timezone

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import ScheduledWorkflow
from agent_app.workflow_registry import workflow_registry


def _workflow_id_from_arg(arg):
    """Resolve workflow number or id to workflow_id."""
    workflows = workflow_registry.get_all()
    if not workflows:
        return None, "No workflows in registry"
    arg = (arg or "").strip()
    if not arg:
        return None, "Workflow required"
    if arg.isdigit():
        n = int(arg)
        for w in workflows:
            if w.workflow_number == n:
                return w.id, None
        return None, f"Workflow #{n} not found. Use /workflow list to see numbers."
    for w in workflows:
        if w.id == arg:
            return w.id, None
    return None, f"Workflow '{arg}' not found."


def _handle_schedule_list(args, user_id):
    """List scheduled workflows for the user."""
    schedules = list(ScheduledWorkflow.objects.filter(user_id=user_id).order_by("next_run_at"))
    if not schedules:
        return {
            "content": (
                "📭 No scheduled workflows.\n\n"
                "💡 Create one with:\n"
                '  /schedule add <workflow_number> "Run name" at 2025-03-10 09:00\n'
                "  /schedule add <workflow_number> every 60\n"
                "Or use the Schedules page in the UI: /workflows/schedules/"
            ),
            "metadata": {"command": "schedule list", "count": 0},
        }
    lines = ["📅 Your scheduled workflows:", ""]
    for s in schedules:
        wf_name = s.workflow_id
        for w in workflow_registry.get_all():
            if w.id == s.workflow_id:
                wf_name = w.name
                break
        run_label = s.run_name or wf_name
        next_run = s.next_run_at.strftime("%Y-%m-%d %H:%M") if s.next_run_at else "—"
        interval = f"every {s.interval_minutes} min" if s.interval_minutes else "once"
        lines.append(f"  ID {s.id}: {run_label}")
        lines.append(f"    Workflow: {wf_name} | {interval} | next: {next_run}")
        lines.append(f"    /schedule show {s.id} | /schedule delete {s.id}")
        lines.append("")
    lines.append('💡 /schedule add <number> "name" at <datetime> | every <minutes>')
    return {
        "content": "\n".join(lines),
        "metadata": {"command": "schedule list", "count": len(schedules)},
    }


def _handle_schedule_show(args, user_id):
    """Show one schedule by id."""
    if len(args) < 2:
        return {
            "content": "Usage: /schedule show <id>",
            "metadata": {"error": True, "command": "schedule show"},
        }
    try:
        sid = int(args[1])
    except ValueError:
        return {
            "content": "Schedule id must be a number.",
            "metadata": {"error": True, "command": "schedule show"},
        }
    try:
        s = ScheduledWorkflow.objects.get(id=sid, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return {
            "content": f"Schedule {sid} not found.",
            "metadata": {"error": True, "command": "schedule show"},
        }
    wf_name = s.workflow_id
    for w in workflow_registry.get_all():
        if w.id == s.workflow_id:
            wf_name = w.name
            break
    lines = [
        f"📅 Schedule {s.id}",
        f"  Workflow: {wf_name} ({s.workflow_id})",
        f"  Run name: {s.run_name or '—'}",
        f"  Type: {s.schedule_type}",
        f"  Next run: {s.next_run_at.strftime('%Y-%m-%d %H:%M') if s.next_run_at else '—'}",
    ]
    if s.schedule_type == "once" and s.run_at:
        lines.append(f"  Run at: {s.run_at.strftime('%Y-%m-%d %H:%M')}")
    if s.interval_minutes:
        lines.append(f"  Interval: every {s.interval_minutes} minutes")
    lines.append(f"  Input data: {s.input_data}")
    lines.append(f"  Active: {s.is_active}")
    lines.append("")
    lines.append(f"  /schedule delete {s.id} | Edit in UI: /workflows/schedules/{s.id}/edit/")
    return {"content": "\n".join(lines), "metadata": {"command": "schedule show"}}


def _handle_schedule_delete(args, user_id):
    """Delete a schedule."""
    if len(args) < 2:
        return {
            "content": "Usage: /schedule delete <id>",
            "metadata": {"error": True, "command": "schedule delete"},
        }
    try:
        sid = int(args[1])
    except ValueError:
        return {
            "content": "Schedule id must be a number.",
            "metadata": {"error": True, "command": "schedule delete"},
        }
    try:
        s = ScheduledWorkflow.objects.get(id=sid, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return {
            "content": f"Schedule {sid} not found.",
            "metadata": {"error": True, "command": "schedule delete"},
        }
    s.delete()
    return {
        "content": f"✅ Schedule {sid} deleted.",
        "metadata": {"command": "schedule delete"},
    }


def _parse_quoted_run_name(args, i):
    """Parse optional quoted run name from args starting at i. Returns (run_name, next_index)."""
    run_name = ""
    if i < len(args) and args[i].startswith('"'):
        run_parts = [args[i].lstrip('"')]
        i += 1
        while i < len(args) and not run_parts[-1].endswith('"'):
            run_parts.append(args[i])
            i += 1
        if run_parts:
            run_parts[-1] = run_parts[-1].rstrip('"')
            run_name = " ".join(run_parts)
    return run_name, i


def _parse_at_datetime(args, i):
    """Parse 'at <datetime>' from args at i. Returns (run_at, None) or (None, error_msg)."""
    if i + 1 >= len(args):
        return None, "Provide date and time after 'at' (e.g. 2025-03-10 09:00)"
    date_str = " ".join(args[i + 1 :]).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt), None
        except ValueError:
            continue
    return None, "Could not parse date/time. Use YYYY-MM-DD HH:MM"


def _parse_every_interval(args, i):
    """Parse 'every <N>' from args at i. Returns (interval_minutes, None) or (None, error_msg)."""
    if i + 1 >= len(args):
        return None, "Provide interval after 'every' (e.g. 60 or 60 minutes)"
    try:
        n = int(args[i + 1])
    except ValueError:
        return None, "Interval must be a number (minutes)"
    if n < 1:
        return None, "Interval must be at least 1 minute"
    return n, None


def _parse_add_args(args):
    """
    Parse: add [workflow] [run_name] at <datetime> | every <N> [minutes]
    Returns (workflow_arg, run_name, schedule_type, run_at, interval_minutes) or (..., error_msg).
    """
    if len(args) < 2:
        return (
            None,
            None,
            None,
            None,
            None,
            "Usage: /schedule add <workflow> [run_name] at <datetime> | every <N> [minutes]",
        )
    workflow_arg = args[1]
    run_name, i = _parse_quoted_run_name(args, 2)
    if i >= len(args):
        return None, None, None, None, None, "Specify 'at <date time>' or 'every <N> [minutes]'"
    token = args[i].lower()
    if token == "at":
        run_at, err = _parse_at_datetime(args, i)
        if err:
            return None, None, None, None, None, err
        return workflow_arg, run_name, "once", run_at, None, None
    if token == "every":
        interval_minutes, err = _parse_every_interval(args, i)
        if err:
            return None, None, None, None, None, err
        return workflow_arg, run_name, "interval", None, interval_minutes, None
    return None, None, None, None, None, "Use 'at <datetime>' or 'every <N> [minutes]'"


def _handle_schedule_add(args, user_id):
    """Create a new schedule."""
    workflow_arg, run_name, schedule_type, run_at, interval_minutes, err = _parse_add_args(args)
    if err:
        return {"content": err, "metadata": {"error": True, "command": "schedule add"}}
    workflow_id, err = _workflow_id_from_arg(workflow_arg)
    if err:
        return {"content": err, "metadata": {"error": True, "command": "schedule add"}}
    now = timezone.now()
    if schedule_type == "once":
        if run_at.tzinfo is None:
            run_at = timezone.make_aware(run_at)
        next_run_at = run_at
        interval_minutes = None
        run_at_val = run_at
    else:
        next_run_at = now + timedelta(minutes=interval_minutes)
        run_at_val = None
    schedule = ScheduledWorkflow.objects.create(
        user_id=user_id,
        workflow_id=workflow_id,
        run_name=run_name,
        input_data={},
        schedule_type=schedule_type,
        run_at=run_at_val,
        interval_minutes=interval_minutes,
        next_run_at=next_run_at,
        is_active=True,
    )
    next_str = next_run_at.strftime("%Y-%m-%d %H:%M")
    return {
        "content": (
            f"✅ Schedule created (ID {schedule.id}). Next run: {next_str}\n"
            f"  /schedule show {schedule.id} | /workflows/schedules/"
        ),
        "metadata": {"command": "schedule add", "schedule_id": schedule.id},
    }


def _handle_schedule_edit(args, user_id):
    """Edit a schedule (minimal: point to UI)."""
    if len(args) < 2:
        return {
            "content": "Usage: /schedule edit <id>\n\nEdit in UI: /workflows/schedules/<id>/edit/",
            "metadata": {"error": True, "command": "schedule edit"},
        }
    try:
        sid = int(args[1])
    except ValueError:
        return {
            "content": "Schedule id must be a number.",
            "metadata": {"error": True, "command": "schedule edit"},
        }
    try:
        ScheduledWorkflow.objects.get(id=sid, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return {
            "content": f"Schedule {sid} not found.",
            "metadata": {"error": True, "command": "schedule edit"},
        }
    return {
        "content": f"Edit schedule {sid} in the UI: /workflows/schedules/{sid}/edit/",
        "metadata": {"command": "schedule edit"},
    }


def handle_schedule(request, args, session_key):
    """
    Handle /schedule commands: list, add, show, edit, delete.
    """
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    if not args:
        return {
            "content": (
                "Usage: /schedule list | add | show <id> | edit <id> | delete <id>\n"
                "  /schedule list - List your scheduled workflows\n"
                '  /schedule add <workflow> ["name"] at <date time> | every <N> minutes\n'
                "  /schedule show <id> - Show schedule details\n"
                "  /schedule edit <id> - Link to edit in UI\n"
                "  /schedule delete <id> - Delete a schedule"
            ),
            "metadata": {"command": "schedule"},
        }
    sub = args[0].lower()
    if sub == "list":
        return _handle_schedule_list(args, user_id)
    if sub == "show":
        return _handle_schedule_show(args, user_id)
    if sub == "delete":
        return _handle_schedule_delete(args, user_id)
    if sub == "add":
        return _handle_schedule_add(args, user_id)
    if sub == "edit":
        return _handle_schedule_edit(args, user_id)
    return {
        "content": f"Unknown subcommand: {sub}. Use /schedule list | add | show | edit | delete",
        "metadata": {"error": True, "command": "schedule"},
    }
