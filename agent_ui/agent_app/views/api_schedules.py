"""
API endpoints for workflow schedule CRUD.
"""

import json
import logging
from datetime import timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import ScheduledWorkflow
from agent_app.workflow_registry import workflow_registry

logger = logging.getLogger(__name__)


def _user_id(request):
    return request.session.get("user_id", ANONYMOUS_USER_ID)


def _schedule_to_dict(s):
    return {
        "id": s.id,
        "workflow_id": s.workflow_id,
        "run_name": s.run_name or "",
        "input_data": s.input_data or {},
        "schedule_type": s.schedule_type,
        "run_at": s.run_at.isoformat() if s.run_at else None,
        "interval_minutes": s.interval_minutes,
        "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
        "timezone": s.timezone or "",
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def schedule_list_or_create_api(request):
    """GET: list schedules. POST: create schedule."""
    if request.method == "GET":
        return schedule_list_api(request)
    if request.method == "POST":
        return schedule_create_api(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@require_http_methods(["GET"])
def schedule_list_api(request):
    """List scheduled workflows for the current user."""
    user_id = _user_id(request)
    include_inactive = request.GET.get("include_inactive", "").lower() in ("1", "true", "yes")
    qs = ScheduledWorkflow.objects.filter(user_id=user_id).order_by("next_run_at")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    schedules = [_schedule_to_dict(s) for s in qs]
    return JsonResponse({"schedules": schedules})


def _validate_workflow_and_common(data):
    """Return (err_response, None, ...) or (None, workflow_id, run_name, input_data, schedule_type, tz_str)."""
    workflow_id = (data.get("workflow_id") or "").strip()
    if not workflow_id:
        return (
            JsonResponse({"error": "workflow_id is required"}, status=400),
            None,
            None,
            None,
            None,
            None,
        )
    if not workflow_registry.get(workflow_id):
        return (
            JsonResponse({"error": f"Workflow '{workflow_id}' not found in registry"}, status=400),
            None,
            None,
            None,
            None,
            None,
        )
    schedule_type = (data.get("schedule_type") or "").strip() or "once"
    if schedule_type not in (ScheduledWorkflow.TYPE_ONCE, ScheduledWorkflow.TYPE_INTERVAL):
        return (
            JsonResponse({"error": "schedule_type must be 'once' or 'interval'"}, status=400),
            None,
            None,
            None,
            None,
            None,
        )
    input_data = data.get("input_data")
    if input_data is None:
        input_data = {}
    if not isinstance(input_data, dict):
        return (
            JsonResponse({"error": "input_data must be a JSON object"}, status=400),
            None,
            None,
            None,
            None,
            None,
        )
    run_name = (data.get("run_name") or "").strip()
    tz_str = (data.get("timezone") or "").strip()
    return None, workflow_id, run_name, input_data, schedule_type, tz_str


def _build_once_payload(data, workflow_id, run_name, input_data, tz_str):
    """Return (None, payload) or (JsonResponse_error, None) for schedule_type once."""
    from django.utils.dateparse import parse_datetime

    run_at_str = data.get("run_at")
    if not run_at_str:
        return JsonResponse(
            {"error": "run_at is required for schedule_type 'once'"}, status=400
        ), None
    run_at = parse_datetime(run_at_str)
    if run_at is None:
        return JsonResponse({"error": "run_at must be a valid ISO datetime"}, status=400), None
    return None, {
        "workflow_id": workflow_id,
        "run_name": run_name,
        "input_data": input_data,
        "schedule_type": ScheduledWorkflow.TYPE_ONCE,
        "run_at": run_at,
        "interval_minutes": None,
        "next_run_at": run_at,
        "timezone": tz_str,
    }


def _build_interval_payload(data, workflow_id, run_name, input_data, tz_str):
    """Return (None, payload) or (JsonResponse_error, None) for schedule_type interval."""
    from django.utils import timezone as tz
    from django.utils.dateparse import parse_datetime

    interval_minutes = data.get("interval_minutes")
    if interval_minutes is None:
        return JsonResponse(
            {"error": "interval_minutes is required for schedule_type 'interval'"}, status=400
        ), None
    try:
        interval_minutes = int(interval_minutes)
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "interval_minutes must be a positive integer"}, status=400
        ), None
    if interval_minutes < 1:
        return JsonResponse({"error": "interval_minutes must be at least 1"}, status=400), None
    now = tz.now()
    first_run = data.get("first_run_at")
    if first_run:
        parsed = parse_datetime(first_run)
        next_run_at = (
            parsed if parsed and parsed > now else now + timedelta(minutes=interval_minutes)
        )
    else:
        next_run_at = now + timedelta(minutes=interval_minutes)
    return None, {
        "workflow_id": workflow_id,
        "run_name": run_name,
        "input_data": input_data,
        "schedule_type": ScheduledWorkflow.TYPE_INTERVAL,
        "run_at": None,
        "interval_minutes": interval_minutes,
        "next_run_at": next_run_at,
        "timezone": tz_str,
    }


def _validate_create_payload(data):
    """Validate create body; return (None, payload_dict) or (JsonResponse_error, None)."""
    err, workflow_id, run_name, input_data, schedule_type, tz_str = _validate_workflow_and_common(
        data
    )
    if err:
        return err, None
    if schedule_type == ScheduledWorkflow.TYPE_ONCE:
        return _build_once_payload(data, workflow_id, run_name, input_data, tz_str)
    return _build_interval_payload(data, workflow_id, run_name, input_data, tz_str)


@require_http_methods(["POST"])
def schedule_create_api(request):
    """Create a new scheduled workflow."""
    user_id = _user_id(request)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    err_resp, payload = _validate_create_payload(data)
    if err_resp:
        return err_resp
    schedule = ScheduledWorkflow.objects.create(
        user_id=user_id,
        is_active=True,
        **payload,
    )
    return JsonResponse(_schedule_to_dict(schedule), status=201)


@require_http_methods(["GET"])
def schedule_detail_api(request, schedule_id):
    """Get a single schedule by id."""
    user_id = _user_id(request)
    try:
        schedule = ScheduledWorkflow.objects.get(id=schedule_id, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    return JsonResponse(_schedule_to_dict(schedule))


def _apply_workflow_id(schedule, data):
    """Apply workflow_id if present. Returns None or JsonResponse error."""
    if "workflow_id" not in data:
        return None
    wf_id = (data.get("workflow_id") or "").strip()
    if wf_id and not workflow_registry.get(wf_id):
        return JsonResponse({"error": f"Workflow '{wf_id}' not found in registry"}, status=400)
    schedule.workflow_id = wf_id or schedule.workflow_id
    return None


def _apply_input_data(schedule, data):
    """Apply input_data if present. Returns None or JsonResponse error."""
    if "input_data" not in data:
        return None
    v = data["input_data"]
    if not isinstance(v, dict):
        return JsonResponse({"error": "input_data must be a JSON object"}, status=400)
    schedule.input_data = v
    return None


def _apply_schedule_type(schedule, data):
    """Apply schedule_type if present. Returns None or JsonResponse error."""
    if "schedule_type" not in data:
        return None
    st = (data.get("schedule_type") or "").strip()
    if st not in (ScheduledWorkflow.TYPE_ONCE, ScheduledWorkflow.TYPE_INTERVAL):
        return JsonResponse({"error": "schedule_type must be 'once' or 'interval'"}, status=400)
    schedule.schedule_type = st
    return None


def _apply_run_at(schedule, data):
    """Apply run_at if present."""
    if "run_at" not in data:
        return
    from django.utils.dateparse import parse_datetime

    run_at_str = data.get("run_at")
    if run_at_str:
        schedule.run_at = parse_datetime(run_at_str)
        if schedule.schedule_type == ScheduledWorkflow.TYPE_ONCE:
            schedule.next_run_at = schedule.run_at
    else:
        schedule.run_at = None


def _apply_interval_minutes(schedule, data):
    """Apply interval_minutes if present. Returns None or JsonResponse error."""
    if "interval_minutes" not in data:
        return None
    v = data["interval_minutes"]
    if v is None:
        return None
    try:
        schedule.interval_minutes = int(v)
    except (TypeError, ValueError):
        return JsonResponse({"error": "interval_minutes must be a positive integer"}, status=400)
    if schedule.interval_minutes < 1:
        return JsonResponse({"error": "interval_minutes must be at least 1"}, status=400)
    return None


def _apply_schedule_update(schedule, data):
    """Apply update fields from data to schedule. Returns None or JsonResponse error."""
    err = _apply_workflow_id(schedule, data)
    if err:
        return err
    if "run_name" in data:
        schedule.run_name = (data.get("run_name") or "").strip()
    err = _apply_input_data(schedule, data)
    if err:
        return err
    err = _apply_schedule_type(schedule, data)
    if err:
        return err
    _apply_run_at(schedule, data)
    err = _apply_interval_minutes(schedule, data)
    if err:
        return err
    if "timezone" in data:
        schedule.timezone = (data.get("timezone") or "").strip()
    if "is_active" in data:
        schedule.is_active = bool(data.get("is_active"))
    return None


@require_http_methods(["PUT", "PATCH"])
def schedule_update_api(request, schedule_id):
    """Update a schedule."""
    user_id = _user_id(request)
    try:
        schedule = ScheduledWorkflow.objects.get(id=schedule_id, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    err = _apply_schedule_update(schedule, data)
    if err:
        return err
    schedule.save()
    return JsonResponse(_schedule_to_dict(schedule))


@require_http_methods(["DELETE"])
def schedule_delete_api(request, schedule_id):
    """Delete a schedule."""
    user_id = _user_id(request)
    try:
        schedule = ScheduledWorkflow.objects.get(id=schedule_id, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)
    schedule.delete()
    return JsonResponse({"success": True}, status=200)


@require_http_methods(["POST"])
def schedule_run_now_api(request, schedule_id):
    """Run a scheduled workflow immediately without changing the schedule."""
    import threading

    from agent_app.models import WorkflowRun
    from agent_app.utils import generate_short_run_id
    from agent_app.workflow_runner import execute_workflow_run

    user_id = _user_id(request)
    try:
        schedule = ScheduledWorkflow.objects.get(id=schedule_id, user_id=user_id)
    except ScheduledWorkflow.DoesNotExist:
        return JsonResponse({"error": "Schedule not found"}, status=404)

    workflow = workflow_registry.get(schedule.workflow_id)
    if not workflow:
        return JsonResponse(
            {"error": f"Workflow '{schedule.workflow_id}' not found in registry"}, status=400
        )

    run_id = generate_short_run_id()
    WorkflowRun.objects.create(
        run_id=run_id,
        workflow_id=schedule.workflow_id,
        workflow_name=workflow["metadata"].name,
        status=WorkflowRun.STATUS_PENDING,
        user_id=schedule.user_id,
        input_data=schedule.input_data or {},
    )

    def run_in_thread():
        import asyncio

        try:
            asyncio.run(execute_workflow_run(run_id, send_message=None))
        except Exception as e:
            logger.exception("Run-now for schedule %s failed: %s", schedule_id, e)

    thread = threading.Thread(target=run_in_thread, daemon=False)
    thread.start()

    return JsonResponse(
        {
            "success": True,
            "run_id": run_id,
            "run_url": f"/workflows/runs/{run_id}/",
        }
    )
