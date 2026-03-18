"""
Tasks
9 functions
"""

import json
import logging

from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from agent_app.constants import ANONYMOUS_USER_ID

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


def task_list(request):
    """List all tasks accessible to the current user"""

    from django.db.models import Q
    from django.utils import timezone

    from agent_app.models import HumanTask

    # Get user info from session

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    user_role = request.session.get("user_role", "admin")

    # Role hierarchy: admin can see all, manager can see manager+user, user can see only user

    role_hierarchy = {
        HumanTask.ROLE_ADMIN: [HumanTask.ROLE_ADMIN, HumanTask.ROLE_MANAGER, HumanTask.ROLE_USER],
        HumanTask.ROLE_MANAGER: [HumanTask.ROLE_MANAGER, HumanTask.ROLE_USER],
        HumanTask.ROLE_USER: [HumanTask.ROLE_USER],
    }

    accessible_roles = role_hierarchy.get(user_role, [])

    # Get filter from query params

    status_filter = request.GET.get("status", "active")  # active, all

    # Base query

    tasks_query = HumanTask.objects.filter(required_role__in=accessible_roles).select_related(
        "workflow_run"
    )

    # Apply status filter

    if status_filter == "active":
        tasks_query = tasks_query.filter(
            Q(status=HumanTask.STATUS_OPEN)
            | Q(status=HumanTask.STATUS_IN_PROGRESS, assigned_to_user_id=user_id),
            expires_at__gt=timezone.now(),
        )

    tasks = tasks_query.order_by("-created_at")

    return render(
        request,
        "workflows/task_list.html",
        {
            "tasks": tasks,
            "status_filter": status_filter,
            "user_role": user_role,
            "page_title": "My Tasks",
        },
    )


def task_detail(request, task_id):
    """Display task details and form"""

    from django.http import HttpResponseForbidden, HttpResponseNotFound

    from agent_app.models import HumanTask

    # Get user info from session

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    user_role = request.session.get("user_role", "admin")

    try:
        task = HumanTask.objects.select_related("workflow_run").get(task_id=task_id)

        # Check if user can access this task

        if not task.can_be_claimed_by(user_id, user_role) and task.assigned_to_user_id != user_id:
            # Allow viewing if it's their assigned task

            if (
                task.status not in [HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]
                or task.assigned_to_user_id != user_id
            ):
                return HttpResponseForbidden("You don't have permission to view this task")

        # Serialize input_data as JSON for JavaScript

        input_data_json = json.dumps(task.input_data) if task.input_data else "{}"

        run_failure = None
        wr = task.workflow_run
        if wr and wr.status in (wr.STATUS_FAILED, wr.STATUS_CANCELLED):
            run_failure = wr.bpmn_failure_summary()

        bpmn_task_run_context = None
        if wr and wr.status in (wr.STATUS_WAITING_FOR_TASK, wr.STATUS_RUNNING):
            from agent_app.bpmn_run_diagnostics import (
                build_bpmn_task_run_context,
                is_bpmn_operator_view,
            )
            from agent_app.workflow_registry import workflow_registry

            wf = workflow_registry.get(wr.workflow_id)
            meta = wf.get("metadata") if wf else None
            has_xml = bool(
                meta and getattr(meta, "diagram_bpmn_xml", None) and str(meta.diagram_bpmn_xml).strip()
            )
            pd = wr.progress_data if isinstance(wr.progress_data, dict) else None
            if is_bpmn_operator_view(diagram_bpmn_xml=has_xml, progress_data=pd):
                bpmn_task_run_context = build_bpmn_task_run_context(pd, wr.status, wr.run_id)

        return render(
            request,
            "workflows/task_detail.html",
            {
                "task": task,
                "workflow_run_failure": run_failure,
                "bpmn_task_run_context": bpmn_task_run_context,
                "input_data_json": input_data_json,
                "can_claim": task.can_be_claimed_by(user_id, user_role),
                "is_assigned_to_me": task.assigned_to_user_id == user_id,
                "user_role": user_role,
                "page_title": f"Task: {task.title}",
            },
        )

    except HumanTask.DoesNotExist:
        return HttpResponseNotFound(f"Task '{task_id}' not found")


@require_http_methods(["POST"])
def task_claim(request, task_id):
    """Claim an open task"""

    from django.http import JsonResponse
    from django.utils import timezone

    from agent_app.models import HumanTask

    # Get user info from session

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    user_role = request.session.get("user_role", "admin")

    try:
        task = HumanTask.objects.get(task_id=task_id)

        # Check if user can claim this task

        if not task.can_be_claimed_by(user_id, user_role):
            if task.status != HumanTask.STATUS_OPEN:
                return JsonResponse(
                    {"success": False, "error": f"Task is already {task.status}"}, status=400
                )

            if task.is_expired():
                return JsonResponse({"success": False, "error": "Task has expired"}, status=400)

            return JsonResponse({"success": False, "error": "Insufficient permissions"}, status=403)

        # Claim the task

        task.status = HumanTask.STATUS_IN_PROGRESS

        task.assigned_to_user_id = user_id

        task.claimed_at = timezone.now()

        task.save()

        # Track metrics
        from agent_app.metrics_collector import workflow_tasks_total

        workflow_tasks_total.labels(task_type=task.task_type, status="claimed").inc()

        # Notify the user they were assigned
        from agent_app.notifications import create_task_assigned_notification

        create_task_assigned_notification(task, user_id)

        return JsonResponse({"success": True, "message": "Task claimed successfully"})

    except HumanTask.DoesNotExist:
        return JsonResponse({"success": False, "error": "Task not found"}, status=404)


@require_http_methods(["POST"])
@require_http_methods(["POST"])
def task_submit(request, task_id):
    """Submit completed task form"""

    from django.http import HttpResponseForbidden, HttpResponseNotFound
    from django.utils import timezone

    from agent_app.models import HumanTask, WorkflowRun

    # Get user info from session

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    request.session.get("user_role", "admin")

    try:
        task = HumanTask.objects.select_related("workflow_run").get(task_id=task_id)

        # Verify task can be submitted

        if task.status not in [HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]:
            return HttpResponseForbidden(f"Cannot submit task with status: {task.status}")

        if task.is_expired():
            task.status = HumanTask.STATUS_EXPIRED

            task.save()

            return HttpResponseForbidden("Task has expired")

        # Verify user has permission

        if task.status == HumanTask.STATUS_IN_PROGRESS and task.assigned_to_user_id != user_id:
            return HttpResponseForbidden("This task is assigned to another user")

        # Parse form data

        try:
            form_data = json.loads(request.body)

        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON data", status=400)

        # Update task

        task.status = HumanTask.STATUS_COMPLETED

        task.output_data = form_data

        task.completed_at = timezone.now()

        task.completed_by_user_id = user_id

        if not task.assigned_to_user_id:
            task.assigned_to_user_id = user_id

            task.claimed_at = timezone.now()

        task.save()

        # Track metrics

        from agent_app.metrics_collector import workflow_tasks_total

        workflow_tasks_total.labels(task_type=task.task_type, status="completed").inc()

        # Update workflow run status to trigger resume

        workflow_run = task.workflow_run

        if workflow_run.status == WorkflowRun.STATUS_WAITING_FOR_TASK:
            # Check if all tasks for this workflow are completed

            pending_tasks = (
                HumanTask.objects.filter(
                    workflow_run=workflow_run,
                    status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
                )
                .exclude(task_id=task_id)
                .count()
            )

            if pending_tasks == 0:
                # All tasks completed, mark workflow as pending to trigger resume

                workflow_run.status = WorkflowRun.STATUS_PENDING

                workflow_run.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Task completed successfully",
                "redirect_url": f"/workflows/runs/{workflow_run.run_id}/",
            }
        )

    except HumanTask.DoesNotExist:
        return HttpResponseNotFound(f"Task '{task_id}' not found")


@require_http_methods(["POST"])
@require_http_methods(["POST"])
def task_cancel(request, task_id):
    """Cancel a task (admin only)"""

    from django.http import HttpResponseForbidden, HttpResponseNotFound
    from django.utils import timezone

    from agent_app.models import HumanTask, WorkflowRun

    # Get user info from session

    request.session.get("user_id", ANONYMOUS_USER_ID)

    user_role = request.session.get("user_role", "admin")

    # Only admins can cancel tasks

    if user_role != "admin":
        return HttpResponseForbidden("Only administrators can cancel tasks")

    try:
        task = HumanTask.objects.select_related("workflow_run").get(task_id=task_id)

        # Can only cancel open or in_progress tasks

        if task.status not in [HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]:
            return HttpResponseForbidden(f"Cannot cancel task with status: {task.status}")

        # Update task status

        task.status = HumanTask.STATUS_CANCELLED

        task.completed_at = timezone.now()

        task.save()

        # Update workflow to failed

        workflow_run = task.workflow_run

        if workflow_run.status == WorkflowRun.STATUS_WAITING_FOR_TASK:
            workflow_run.status = WorkflowRun.STATUS_FAILED

            workflow_run.error_message = f"Task {task_id} was cancelled by administrator"

            workflow_run.completed_at = timezone.now()

            workflow_run.save()

            from agent_app.notifications import create_workflow_status_notification

            create_workflow_status_notification(
                workflow_run.user_id,
                workflow_run.run_id,
                workflow_run.workflow_name,
                "failed",
                workflow_run.error_message or "",
            )

        return redirect("task_list")

    except HumanTask.DoesNotExist:
        return HttpResponseNotFound(f"Task '{task_id}' not found")


@require_http_methods(["POST"])
def task_delete(request, task_id):
    """Delete a task (admin only)"""

    from agent_app.models import HumanTask

    user_role = request.session.get("user_role", "admin")

    if user_role != "admin":
        return JsonResponse(
            {"success": False, "error": "Only administrators can delete tasks"}, status=403
        )

    try:
        task = HumanTask.objects.get(task_id=task_id)
        task.delete()

        logger.info(f"Task {task_id} deleted by admin")

        return JsonResponse({"success": True, "message": "Task deleted successfully"})

    except HumanTask.DoesNotExist:
        return JsonResponse({"success": False, "error": "Task not found"}, status=404)


def task_count_api(request):
    """API endpoint to get task count for badge"""

    from django.db.models import Q
    from django.http import JsonResponse
    from django.utils import timezone

    from agent_app.models import HumanTask

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    user_role = request.session.get("user_role", "admin")

    # Role hierarchy: admin can see all, manager can see manager+user, user can see only user

    role_hierarchy = {
        HumanTask.ROLE_ADMIN: [HumanTask.ROLE_ADMIN, HumanTask.ROLE_MANAGER, HumanTask.ROLE_USER],
        HumanTask.ROLE_MANAGER: [HumanTask.ROLE_MANAGER, HumanTask.ROLE_USER],
        HumanTask.ROLE_USER: [HumanTask.ROLE_USER],
    }

    accessible_roles = role_hierarchy.get(user_role, [])

    count = HumanTask.objects.filter(
        Q(status=HumanTask.STATUS_OPEN)
        | Q(status=HumanTask.STATUS_IN_PROGRESS, assigned_to_user_id=user_id),
        required_role__in=accessible_roles,
        expires_at__gt=timezone.now(),
    ).count()

    return JsonResponse({"count": count})


def task_template_preview(request, template_id):
    """Preview a task form template"""

    # Validate template_id

    valid_templates = ["approval", "review", "data_collection", "verification"]

    if template_id not in valid_templates:
        return HttpResponseNotFound(f"Template '{template_id}' not found")

    # Create a mock task object for preview

    class MockTask:
        def __init__(self, data):

            for key, value in data.items():
                setattr(self, key, value)

    mock_task = MockTask(
        {
            "task_id": "preview",
            "task_type": template_id,
            "title": f"Preview: {template_id.replace('_', ' ').title()} Form",
            "status": "open",
            "input_data": {
                "bidder_name": "John Doe",
                "property_id": 12345,
                "sam_check": "PASSED",
                "ofac_check": "PASSED",
                "is_eligible": True,
                "risk_factors": [],
                "compliance_summary": "All checks passed",
                "recommendation_options": [
                    "Improve documentation",
                    "Add more details",
                    "Verify data sources",
                ],
                "fields": [
                    {
                        "name": "full_name",
                        "label": "Full Name",
                        "type": "text",
                        "required": True,
                        "placeholder": "Enter full name",
                    },
                    {
                        "name": "amount",
                        "label": "Amount",
                        "type": "number",
                        "required": True,
                        "min": 0,
                    },
                    {"name": "date", "label": "Date", "type": "date", "required": True},
                ],
            },
        }
    )

    # Render just the form template

    from django.template.loader import render_to_string

    form_html = render_to_string(f"workflows/task_forms/{template_id}.html", {"task": mock_task})

    return HttpResponse(f"""

        <div style="padding: 1rem;">

            <div style="background: #fff3e0; border-left: 4px solid #ff9800; padding: 1rem; margin-bottom: 1.5rem; border-radius: 4px;">

                <strong>Preview Mode</strong>

                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">

                    This is a preview of the {template_id.replace("_", " ")} form template with sample data.

                    In actual use, the form will be populated with real workflow context.

                </p>

            </div>

            {form_html}

        </div>

    """)


def task_templates(request):
    """Display available task form templates"""

    # Get user role for access control display

    user_role = request.session.get("user_role", "admin")

    # Define template metadata

    templates = [
        {
            "id": "approval",
            "name": "Approval",
            "description": "Binary approve/deny decision with comments and confidence rating",
            "icon": "✓",
            "fields": [
                {"name": "Decision", "type": "Radio (Approve/Deny)", "required": True},
                {
                    "name": "Comments",
                    "type": "Textarea",
                    "required": "Conditional (required for deny)",
                },
                {"name": "Confidence", "type": "Star Rating (1-5)", "required": False},
            ],
            "use_cases": [
                "Bidder approval",
                "Contract approval",
                "Purchase approval",
                "Policy exceptions",
            ],
        },
        {
            "id": "review",
            "name": "Review",
            "description": "Quality assessment with star rating and detailed feedback",
            "icon": "⭐",
            "fields": [
                {"name": "Rating", "type": "Star Rating (1-5)", "required": True},
                {"name": "Feedback", "type": "Textarea", "required": True},
                {"name": "Recommendations", "type": "Checkboxes", "required": False},
            ],
            "use_cases": [
                "Document review",
                "Quality assessment",
                "Performance review",
                "Content moderation",
            ],
        },
        {
            "id": "data_collection",
            "name": "Data Collection",
            "description": "Dynamic form with configurable fields for gathering information",
            "icon": "📋",
            "fields": [
                {
                    "name": "Dynamic Fields",
                    "type": "Configured via input_data",
                    "required": "Variable",
                },
            ],
            "supported_types": ["text", "number", "date", "select", "checkbox", "textarea"],
            "use_cases": [
                "Survey responses",
                "Registration data",
                "Property details",
                "Custom forms",
            ],
        },
        {
            "id": "verification",
            "name": "Verification",
            "description": "Verify information with pass/fail/flag result and supporting documentation",
            "icon": "🔍",
            "fields": [
                {"name": "Result", "type": "Radio (Pass/Fail/Flag)", "required": True},
                {"name": "Notes", "type": "Textarea", "required": True},
                {"name": "Attachments", "type": "File Upload", "required": False},
            ],
            "use_cases": [
                "Identity verification",
                "Document verification",
                "Compliance checks",
                "Quality control",
            ],
        },
    ]

    return render(
        request,
        "workflows/task_templates.html",
        {"templates": templates, "user_role": user_role, "page_title": "Task Templates"},
    )
