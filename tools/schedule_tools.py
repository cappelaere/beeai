"""
Schedule tools for Flo Agent – list, create, and delete scheduled workflows from chat.
"""

import os
from datetime import timedelta

from asgiref.sync import sync_to_async
from beeai_framework.tools import StringToolOutput, tool


def _setup_django():
    """Setup Django environment lazily when needed."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")
    import django

    if not django.apps.apps.ready:
        django.setup()


def _get_user_id():
    """Current user ID from environment (set by agent runner)."""
    return int(os.environ.get("USER_ID", 9))


@tool
async def list_schedules(user_id: int | None = None) -> StringToolOutput:
    """
    List the current user's scheduled workflows.

    Args:
        user_id: User ID (defaults to current user from environment).

    Returns a list of schedules with: id, workflow_id, workflow_name, run_name,
    schedule_type, next_run_at, interval_minutes, is_active, view_url.

    Use when the user asks "what's scheduled?", "list my schedules", or
    "when does workflow X run?".
    """
    try:
        _setup_django()
        from agent_app.models import ScheduledWorkflow
        from agent_app.workflow_registry import workflow_registry

        uid = user_id if user_id is not None else _get_user_id()

        def get_schedules():
            schedules = list(
                ScheduledWorkflow.objects.filter(user_id=uid).order_by("next_run_at")[:50]
            )
            workflow_names = {wf.id: wf.name for wf in workflow_registry.get_all()}
            return [
                {
                    "id": s.id,
                    "workflow_id": s.workflow_id,
                    "workflow_name": workflow_names.get(s.workflow_id, s.workflow_id),
                    "run_name": s.run_name or "",
                    "schedule_type": s.schedule_type,
                    "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
                    "run_at": s.run_at.isoformat() if s.run_at else None,
                    "interval_minutes": s.interval_minutes,
                    "is_active": s.is_active,
                    "view_url": f"/workflows/schedules/",
                }
                for s in schedules
            ]

        schedules = await sync_to_async(get_schedules, thread_sensitive=False)()
        return StringToolOutput(str({"schedules": schedules, "count": len(schedules)}))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to list schedules: {str(e)}"}))


def _parse_create_once(run_at: str | None, parse_datetime):
    """Parse run_at for once schedule. Returns (next_run_at, run_at_val) or (None, None, error)."""
    if not run_at:
        return (None, None, "run_at is required for schedule_type 'once' (ISO datetime)")
    parsed = parse_datetime(run_at)
    if parsed is None:
        return (None, None, "run_at must be a valid ISO datetime (e.g. 2025-03-15T09:00:00)")
    return (parsed, parsed, None)


def _parse_create_interval(
    interval_minutes, first_run_at: str | None, tz, parse_datetime, timedelta
) -> tuple:
    """Parse interval params. Returns (next_run_at, None, None) or (None, None, error)."""
    if interval_minutes is None:
        return (None, None, "interval_minutes is required for schedule_type 'interval'")
    try:
        interval_minutes_val = int(interval_minutes)
    except (TypeError, ValueError):
        return (None, None, "interval_minutes must be a positive integer")
    if interval_minutes_val < 1:
        return (None, None, "interval_minutes must be at least 1")
    now = tz.now()
    if first_run_at:
        parsed = parse_datetime(first_run_at)
        next_run_at = (
            parsed if parsed and parsed > now else now + timedelta(minutes=interval_minutes_val)
        )
    else:
        next_run_at = now + timedelta(minutes=interval_minutes_val)
    return (next_run_at, None, None)


@tool
async def create_schedule(
    workflow_id: str,
    schedule_type: str,
    run_name: str = "",
    run_at: str | None = None,
    interval_minutes: int | None = None,
    first_run_at: str | None = None,
    input_data: dict | None = None,
    timezone: str = "",
) -> StringToolOutput:
    """
    Create a scheduled workflow run.

    Args:
        workflow_id: Workflow ID (e.g. "bidder_onboarding", "bi_weekly_report").
        schedule_type: "once" or "interval".
        run_name: Optional name for the run (e.g. "Monthly report").
        run_at: For schedule_type "once", ISO datetime (e.g. "2025-03-15T09:00:00").
        interval_minutes: For schedule_type "interval", repeat every N minutes (e.g. 60, 1440).
        first_run_at: Optional for interval; ISO datetime for first run (otherwise starts soon).
        input_data: Optional dict of workflow input variables (default {}).
        timezone: Optional timezone string (e.g. "America/New_York").

    Returns the new schedule id and next_run_at. Use when the user says
    "schedule workflow 1 every Monday at 9am", "run the report once tomorrow at 10am", etc.
    """
    try:
        _setup_django()
        from django.utils import timezone as tz
        from django.utils.dateparse import parse_datetime

        from agent_app.models import ScheduledWorkflow
        from agent_app.workflow_registry import workflow_registry

        workflow_id = (workflow_id or "").strip()
        if not workflow_id:
            return StringToolOutput(str({"error": "workflow_id is required"}))
        wf = workflow_registry.get(workflow_id)
        if not wf:
            return StringToolOutput(
                str(
                    {
                        "error": f"Workflow '{workflow_id}' not found",
                        "available": [w.id for w in workflow_registry.get_all()],
                    }
                )
            )

        schedule_type = (schedule_type or "once").strip().lower()
        if schedule_type not in ("once", "interval"):
            return StringToolOutput(str({"error": "schedule_type must be 'once' or 'interval'"}))

        data = input_data if isinstance(input_data, dict) else {}
        run_name = (run_name or "").strip()
        tz_str = (timezone or "").strip()

        if schedule_type == "once":
            next_run_at, run_at_val, err = _parse_create_once(run_at, parse_datetime)
            if err:
                return StringToolOutput(str({"error": err}))
            interval_minutes_val = None
        else:
            next_run_at, _, err = _parse_create_interval(
                interval_minutes, first_run_at, tz, parse_datetime, timedelta
            )
            if err:
                return StringToolOutput(str({"error": err}))
            interval_minutes_val = int(interval_minutes)
            run_at_val = None

        def do_create():
            s = ScheduledWorkflow.objects.create(
                user_id=_get_user_id(),
                workflow_id=workflow_id,
                run_name=run_name,
                input_data=data,
                schedule_type=schedule_type,
                run_at=run_at_val,
                interval_minutes=interval_minutes_val,
                next_run_at=next_run_at,
                timezone=tz_str,
                is_active=True,
            )
            return {
                "success": True,
                "schedule_id": s.id,
                "workflow_id": workflow_id,
                "workflow_name": wf["metadata"].name,
                "run_name": run_name,
                "schedule_type": schedule_type,
                "next_run_at": next_run_at.isoformat(),
                "message": f"Schedule created (id={s.id}). Next run: {next_run_at.isoformat()}",
                "view_url": "/workflows/schedules/",
            }

        result = await sync_to_async(do_create, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to create schedule: {str(e)}"}))


@tool
async def delete_schedule(schedule_id: int) -> StringToolOutput:
    """
    Delete a scheduled workflow by id.

    Args:
        schedule_id: Schedule ID (from list_schedules).

    Use when the user says "cancel schedule 3", "delete my 9am report schedule", etc.
    """
    try:
        _setup_django()
        from agent_app.models import ScheduledWorkflow

        uid = _get_user_id()

        def do_delete():
            try:
                s = ScheduledWorkflow.objects.get(id=schedule_id, user_id=uid)
                s.delete()
                return {"success": True, "message": f"Schedule {schedule_id} deleted."}
            except ScheduledWorkflow.DoesNotExist:
                return {"error": f"Schedule {schedule_id} not found or not yours."}

        result = await sync_to_async(do_delete, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to delete schedule: {str(e)}"}))


def _apply_schedule_run_name(s, run_name) -> None:
    if run_name is not None:
        s.run_name = (run_name or "").strip()


def _apply_schedule_run_at_once(s, run_at, parse_datetime, type_once: str) -> dict | None:
    """Apply run_at for once schedule. Returns error dict or None."""
    if run_at is None or s.schedule_type != type_once:
        return None
    parsed = parse_datetime(run_at)
    if parsed is None:
        return {"error": "run_at must be a valid ISO datetime"}
    s.run_at = parsed
    s.next_run_at = parsed
    return None


def _apply_schedule_interval_minutes(s, interval_minutes, type_interval: str) -> dict | None:
    """Apply interval_minutes for interval schedule. Returns error dict or None."""
    if interval_minutes is None or s.schedule_type != type_interval:
        return None
    try:
        val = int(interval_minutes)
    except (TypeError, ValueError):
        return {"error": "interval_minutes must be a positive integer"}
    if val < 1:
        return {"error": "interval_minutes must be at least 1"}
    s.interval_minutes = val
    return None


def _apply_schedule_first_run_at(
    s, first_run_at, tz, parse_datetime, timedelta, type_interval: str
) -> None:
    if first_run_at is None or s.schedule_type != type_interval:
        return
    parsed = parse_datetime(first_run_at)
    now = tz.now()
    if parsed and parsed > now:
        s.next_run_at = parsed
    elif s.interval_minutes:
        s.next_run_at = now + timedelta(minutes=s.interval_minutes)


@tool
async def update_schedule(
    schedule_id: int,
    run_name: str | None = None,
    run_at: str | None = None,
    interval_minutes: int | None = None,
    first_run_at: str | None = None,
    is_active: bool | None = None,
) -> StringToolOutput:
    """
    Update an existing schedule by id.

    Args:
        schedule_id: Schedule ID (from list_schedules).
        run_name: Optional new run name.
        run_at: For once schedules, new ISO datetime.
        interval_minutes: For interval schedules, new interval (minutes).
        first_run_at: For interval schedules, optional new first run ISO datetime.
        is_active: Optional; True to enable, False to pause.

    Use when the user says "move my 9am report to 10am", "change schedule 3 to every 60 minutes", etc.
    """
    try:
        _setup_django()
        from django.utils import timezone as tz
        from django.utils.dateparse import parse_datetime

        from agent_app.models import ScheduledWorkflow

        uid = _get_user_id()

        def do_update():
            try:
                s = ScheduledWorkflow.objects.get(id=schedule_id, user_id=uid)
            except ScheduledWorkflow.DoesNotExist:
                return {"error": f"Schedule {schedule_id} not found or not yours."}

            _apply_schedule_run_name(s, run_name)
            if is_active is not None:
                s.is_active = bool(is_active)
            err = _apply_schedule_run_at_once(
                s, run_at, parse_datetime, ScheduledWorkflow.TYPE_ONCE
            )
            if err:
                return err
            err = _apply_schedule_interval_minutes(
                s, interval_minutes, ScheduledWorkflow.TYPE_INTERVAL
            )
            if err:
                return err
            _apply_schedule_first_run_at(
                s, first_run_at, tz, parse_datetime, timedelta, ScheduledWorkflow.TYPE_INTERVAL
            )

            s.save()
            return {
                "success": True,
                "schedule_id": schedule_id,
                "message": f"Schedule {schedule_id} updated.",
                "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            }

        result = await sync_to_async(do_update, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to update schedule: {str(e)}"}))


@tool
async def set_schedule_active(schedule_id: int, is_active: bool) -> StringToolOutput:
    """
    Pause or resume a schedule (toggle is_active).

    Args:
        schedule_id: Schedule ID (from list_schedules).
        is_active: True to resume/enable, False to pause.

    Use when the user says "pause schedule 3", "resume schedule 5", "turn off my 9am report".
    """
    return await update_schedule(schedule_id=schedule_id, is_active=is_active)
