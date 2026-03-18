"""
Workflows
12 functions (includes version control)
"""

import json
import logging
import os
from pathlib import Path

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect, render
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods

from agent_app.constants import ANONYMOUS_USER_ID

logger = logging.getLogger(__name__)

# Updated: 2026-03-03 - Added workflow version control and editor


def workflows_list(request):
    """Show list of all available workflows"""

    from agent_app.models import UserPreference
    from agent_app.workflow_registry import workflow_registry

    workflows = workflow_registry.get_all()

    workflows_data = [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "icon": w.icon,
            "category": w.category,
            "estimated_duration": w.estimated_duration,
            "workflow_number": w.workflow_number,
            "documentation_path": w.documentation_path,
        }
        for w in workflows
    ]

    user_role = request.session.get("user_role", "user")

    # Get favorite workflows for the current user
    favorite_workflows = []
    try:
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

        user_pref = UserPreference.objects.filter(session_key=session_key, user_id=user_id).first()

        if user_pref and user_pref.favorite_workflows:
            favorite_workflow_ids = json.loads(user_pref.favorite_workflows or "[]")

            for workflow_meta in workflows:
                if workflow_meta.id in favorite_workflow_ids:
                    favorite_workflows.append(
                        {
                            "id": workflow_meta.id,
                            "name": workflow_meta.name,
                        }
                    )
    except Exception as e:
        logger.error("Error loading favorite workflows: %s", e, exc_info=True)

    favorite_workflows_json = json.dumps(favorite_workflows)

    return render(
        request,
        "workflows/list.html",
        {
            "workflows": workflows_data,
            "page_title": "Workflows",
            "user_role": user_role,
            "favorite_workflows_json": favorite_workflows_json,
        },
    )


def workflow_detail(request, workflow_id):
    """Show workflow detail page with diagram and execution form"""

    from django.http import HttpResponseNotFound

    from agent_app.models import WorkflowRun
    from agent_app.workflow_registry import workflow_registry

    workflow = workflow_registry.get(workflow_id)

    if not workflow:
        return HttpResponseNotFound("Workflow not found")

    metadata = workflow["metadata"]

    # Latest run progress for diagram coloring (completed/failed run for this workflow + user)
    progress_node_ids = {"completed_node_ids": [], "current_node_ids": [], "failed_node_id": None}
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    latest_run = (
        WorkflowRun.objects.filter(workflow_id=workflow_id, user_id=user_id)
        .order_by("-started_at")
        .first()
    )
    if latest_run and latest_run.status in ("completed", "failed", "cancelled"):
        if latest_run.progress_data:
            progress_node_ids["completed_node_ids"] = (
                latest_run.progress_data.get("completed_node_ids") or []
            )
            progress_node_ids["failed_node_id"] = latest_run.progress_data.get("failed_node_id")
        if not progress_node_ids["completed_node_ids"] and latest_run.output_data:
            progress_node_ids["completed_node_ids"] = (
                latest_run.output_data.get("workflow_steps") or []
            )

    latest_run_failure = None
    if latest_run and latest_run.status in ("failed", "cancelled"):
        latest_run_failure = latest_run.bpmn_failure_summary()

    return render(
        request,
        "workflows/detail.html",
        {
            "workflow": {
                "id": metadata.id,
                "name": metadata.name,
                "description": metadata.description,
                "icon": metadata.icon,
                "diagram_mermaid": metadata.diagram_mermaid,
                "diagram_bpmn_xml": getattr(metadata, "diagram_bpmn_xml", None) or "",
                "input_schema": metadata.input_schema,
                "category": metadata.category,
                "estimated_duration": metadata.estimated_duration,
                "workflow_number": metadata.workflow_number,
                "documentation_path": metadata.documentation_path,
            },
            "progress_node_ids": progress_node_ids,
            "latest_run_failure": latest_run_failure,
            "page_title": metadata.name,
        },
    )


def schedule_list(request):
    """List scheduled workflows for the current user."""
    from agent_app.models import ScheduledWorkflow
    from agent_app.workflow_registry import workflow_registry

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    schedules = list(ScheduledWorkflow.objects.filter(user_id=user_id).order_by("next_run_at"))
    workflow_names = {}
    for w in workflow_registry.get_all():
        workflow_names[w.id] = w.name
    schedule_rows = []
    for s in schedules:
        schedule_rows.append(
            {
                "id": s.id,
                "workflow_id": s.workflow_id,
                "workflow_name": workflow_names.get(s.workflow_id, s.workflow_id),
                "run_name": s.run_name or "",
                "schedule_type": s.schedule_type,
                "run_at": s.run_at,
                "interval_minutes": s.interval_minutes,
                "next_run_at": s.next_run_at,
                "is_active": s.is_active,
            }
        )
    return render(
        request,
        "workflows/schedule_list.html",
        {
            "schedules": schedule_rows,
            "page_title": "Scheduled Workflows",
        },
    )


def schedule_form(request, schedule_id=None):
    """Create or edit a scheduled workflow. schedule_id None = create."""
    from agent_app.models import ScheduledWorkflow
    from agent_app.workflow_registry import workflow_registry

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    workflows = workflow_registry.get_all()
    workflows_data = [
        {"id": w.id, "name": w.name, "workflow_number": w.workflow_number} for w in workflows
    ]
    preset_workflow_id = request.GET.get("workflow_id", "").strip()
    schedule = None
    schedule_input_json = "{}"
    if schedule_id is not None:
        try:
            schedule = ScheduledWorkflow.objects.get(id=schedule_id, user_id=user_id)
        except ScheduledWorkflow.DoesNotExist:
            return HttpResponseNotFound("Schedule not found")
        preset_workflow_id = schedule.workflow_id
        schedule_input_json = json.dumps(schedule.input_data or {}, indent=2)

    return render(
        request,
        "workflows/schedule_form.html",
        {
            "workflows": workflows_data,
            "schedule": schedule,
            "schedule_input_json": schedule_input_json,
            "preset_workflow_id": preset_workflow_id,
            "page_title": "Edit Schedule" if schedule else "Schedule Workflow",
        },
    )


def workflow_edit(request, workflow_id):
    """Edit existing workflow with version control"""
    from agent_app.version_manager import version_manager
    from agent_app.workflow_context import normalize_bindings, validate_bpmn_bindings_context
    from agent_app.workflow_registry import workflow_registry
    import yaml

    # Check admin permission
    if request.session.get("user_role") != "admin":
        return HttpResponseForbidden("Admin access required")

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        return HttpResponseNotFound(f"Workflow '{workflow_id}' not found")

    metadata = workflow["metadata"]

    # Get workflow files from filesystem (use version folder when present for BPMN)
    workflows_base = Path(__file__).parent.parent.parent.parent / "workflows"
    workflow_path = workflows_base / workflow_id
    assets_path = getattr(metadata, "current_version_path", None) or workflow_path

    # Read current file contents (metadata always from workflow root; diagram/code from assets_path)
    file_contents = {}
    files_from_root = ["metadata.yaml", "USER_STORY.md", "documentation.md"]
    files_from_assets = ["workflow.bpmn", "bpmn-bindings.yaml"]
    for filename in files_from_root:
        file_path = workflow_path / filename
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                file_contents[filename] = f.read()
        else:
            file_contents[filename] = ""
    for filename in files_from_assets:
        file_path = assets_path / filename
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                file_contents[filename] = f.read()
        else:
            file_contents[filename] = ""

    # Get version history
    versions = version_manager.get_version_history(workflow_id)
    current_version = versions.filter(is_current=True).first() if versions.exists() else None
    bindings_yaml = file_contents.get("bpmn-bindings.yaml", "")
    bindings_dict = normalize_bindings(
        yaml.safe_load(bindings_yaml) or {},
        workflow_id=metadata.id,
    )
    validation_context = {
        "workflow": {"id": metadata.id},
        "bindings": bindings_dict,
        "bpmn": {"elements": {}, "ordered_service_task_ids": []},
        "code": {"handler_names": []},
    }
    try:
        from agent_app.workflow_context import get_workflow_context

        validation_context = get_workflow_context(metadata.id)
    except Exception:
        logger.exception(
            "get_workflow_context failed for workflow_id=%s, using reduced validation context",
            metadata.id,
        )
    bindings_validation = validate_bpmn_bindings_context(validation_context)

    return render(
        request,
        "workflows/edit.html",
        {
            "workflow": {
                "id": metadata.id,
                "name": metadata.name,
                "description": metadata.description,
                "icon": metadata.icon,
                "category": metadata.category,
                "estimated_duration": metadata.estimated_duration,
                "input_schema": getattr(metadata, "input_schema", None) or {},
            },
            "file_contents": file_contents,
            "file_contents_bpmn_xml": file_contents.get("workflow.bpmn", ""),
            "initial_bindings_json": json.dumps(bindings_dict),
            "bindings_validation_json": json.dumps(bindings_validation),
            "initial_user_story": file_contents.get("USER_STORY.md", ""),
            "initial_documentation": file_contents.get("documentation.md", ""),
            "current_version": current_version,
            "version_count": versions.count(),
            "workflow_input_schema_json": json.dumps(getattr(metadata, "input_schema", None) or {}),
            "workflow_outputs_json": json.dumps(getattr(metadata, "outputs", None) or []),
            "page_title": f"Edit: {metadata.name}",
        },
    )


@xframe_options_sameorigin
def workflow_diagram_editor_frame(request, workflow_id):
    """Standalone BPMN modeler page (same as bpmn-js-examples starter). Diagram loaded from diagram_xml_url. Allowed in iframe from same origin (edit page)."""
    from django.urls import reverse
    from agent_app.workflow_registry import workflow_registry

    if request.session.get("user_role") != "admin":
        return HttpResponseForbidden("Admin access required")

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        return HttpResponseNotFound(f"Workflow '{workflow_id}' not found")

    diagram_xml_url = request.build_absolute_uri(
        reverse("workflow_diagram_xml", args=[workflow_id])
    )
    return render(
        request,
        "workflows/diagram_editor_frame.html",
        {"workflow_id": workflow_id, "diagram_xml_url": diagram_xml_url},
        content_type="text/html; charset=utf-8",
    )


def workflow_diagram_xml(request, workflow_id):
    """Return the workflow's BPMN XML for the diagram editor iframe (avoids embedding XML in HTML)."""
    from agent_app.workflow_registry import workflow_registry

    if request.session.get("user_role") != "admin":
        return HttpResponseForbidden("Admin access required")

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        return HttpResponseNotFound(f"Workflow '{workflow_id}' not found")

    metadata = workflow["metadata"]
    workflows_base = Path(__file__).parent.parent.parent.parent / "workflows"
    assets_path = getattr(metadata, "current_version_path", None) or (workflows_base / workflow_id)
    bpmn_file = assets_path / "workflow.bpmn"
    if not bpmn_file.exists():
        minimal = '<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" targetNamespace="http://bpmn.io/schema/bpmn" id="Definitions_1"><bpmn:process id="Process_1" isExecutable="true"/><bpmndi:BPMNDiagram id="BPMNDiagram_1"><bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1"/></bpmndi:BPMNDiagram></bpmn:definitions>'
        return HttpResponse(minimal, content_type="application/xml; charset=utf-8")
    bpmn_xml = bpmn_file.read_text(encoding="utf-8")
    return HttpResponse(bpmn_xml, content_type="application/xml; charset=utf-8")


def workflow_versions(request, workflow_id):
    """Display version history for workflow"""
    from agent_app.version_manager import version_manager
    from agent_app.workflow_registry import workflow_registry

    # Check admin permission
    if request.session.get("user_role") != "admin":
        return HttpResponseForbidden("Admin access required")

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        return HttpResponseNotFound(f"Workflow '{workflow_id}' not found")

    metadata = workflow["metadata"]
    versions = version_manager.get_version_history(workflow_id)

    # Prepare version data with previous version number for comparison
    versions_data = []
    prev_version = None
    for version in versions:
        versions_data.append(
            {
                "version": version,
                "prev_version_number": prev_version.version_number if prev_version else None,
            }
        )
        prev_version = version

    return render(
        request,
        "workflows/versions.html",
        {
            "workflow": {
                "id": metadata.id,
                "name": metadata.name,
                "icon": metadata.icon,
            },
            "versions_data": versions_data,
            "page_title": f"Versions: {metadata.name}",
        },
    )


def workflow_version_compare(request, workflow_id, version1, version2):
    """Compare two versions of a workflow"""
    from agent_app.version_manager import version_manager
    from agent_app.workflow_registry import workflow_registry

    # Check admin permission
    if request.session.get("user_role") != "admin":
        return HttpResponseForbidden("Admin access required")

    workflow = workflow_registry.get(workflow_id)
    if not workflow:
        return HttpResponseNotFound(f"Workflow '{workflow_id}' not found")

    metadata = workflow["metadata"]

    try:
        # Get version objects
        version1_obj = version_manager.get_version(workflow_id, version1)
        version2_obj = version_manager.get_version(workflow_id, version2)

        if not version1_obj or not version2_obj:
            return HttpResponseNotFound("One or both versions not found")

        # Generate diffs
        diffs = version_manager.compare_versions(workflow_id, version1, version2)

        return render(
            request,
            "workflows/version_compare.html",
            {
                "workflow": {
                    "id": metadata.id,
                    "name": metadata.name,
                    "icon": metadata.icon,
                },
                "version1": version1_obj,
                "version2": version2_obj,
                "diffs": diffs,
                "page_title": f"Compare Versions: {metadata.name}",
            },
        )
    except Exception as e:
        logger.exception("Error comparing versions: %s", e)
        return HttpResponseNotFound("Resource not found.")


@require_http_methods(["POST"])
def workflow_execute(request, workflow_id):
    """

    Create a workflow run and return run_id for WebSocket connection.



    The actual execution happens asynchronously via WebSocket consumer.

    """

    import logging

    from django.http import HttpResponseBadRequest, HttpResponseNotFound

    from agent_app.models import WorkflowRun
    from agent_app.utils import generate_short_run_id
    from agent_app.workflow_registry import workflow_registry

    logger = logging.getLogger(__name__)

    workflow = workflow_registry.get(workflow_id)

    if not workflow:
        return HttpResponseNotFound("Workflow not found")

    # Parse input from request

    try:
        input_data = json.loads(request.body)

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON input")

    try:
        # Generate unique run_id

        run_id = generate_short_run_id()

        # Get user_id from session (default to 9)

        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

        # Create workflow run record

        WorkflowRun.objects.create(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_name=workflow["metadata"].name,
            status="pending",
            user_id=user_id,
            input_data=input_data,
        )

        logger.info(f"Created workflow run {run_id} for user {user_id}")

        # Track metrics

        from agent_app.metrics_collector import workflow_runs_total

        workflow_runs_total.labels(workflow_id=workflow_id, status="pending").inc()

        # Return run_id and WebSocket URL

        return JsonResponse(
            {
                "success": True,
                "run_id": run_id,
                "websocket_url": f"/ws/workflow/{run_id}/",
                "message": "Workflow execution initiated",
            }
        )

    except Exception:
        from agent_app.http_utils import json_response_500

        return json_response_500("Error creating workflow run")


def workflow_export(request, workflow_id):
    """Export workflow results as JSON"""

    from datetime import UTC, datetime

    from django.http import HttpResponseBadRequest

    format_type = request.GET.get("format", "json")

    result_data = request.session.get(f"workflow_result_{workflow_id}", {})

    if format_type == "json":
        # Return JSON response

        response = JsonResponse(result_data, safe=False)

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

        response["Content-Disposition"] = (
            f'attachment; filename="workflow_{workflow_id}_{timestamp}.json"'
        )

        return response

    return HttpResponseBadRequest("Unsupported export format")


def workflow_documentation(request, workflow_id):
    """Display workflow documentation from markdown file"""

    from pathlib import Path

    import markdown
    from django.http import HttpResponseNotFound

    from agent_app.workflow_registry import REPO_ROOT, workflow_registry

    workflow = workflow_registry.get(workflow_id)

    if not workflow:
        return HttpResponseNotFound("Workflow not found")

    metadata = workflow["metadata"]

    # Check if documentation path exists

    if not metadata.documentation_path:
        return HttpResponseNotFound("Documentation not available for this workflow")

    # Read markdown file

    doc_path = Path(REPO_ROOT) / metadata.documentation_path

    if not doc_path.exists():
        return HttpResponseNotFound(f"Documentation file not found: {metadata.documentation_path}")

    try:
        import re

        with open(doc_path, encoding="utf-8") as f:
            markdown_content = f.read()

        # Replace the first Mermaid diagram with the corrected one from workflow_registry

        # This ensures we use the same working diagram everywhere (workflow page and docs page)

        if metadata.diagram_mermaid:
            # Find and replace only the first mermaid block in the markdown

            markdown_content = re.sub(
                r"```mermaid\n.*?```",
                f"```mermaid\n{metadata.diagram_mermaid}\n```",
                markdown_content,
                count=1,  # Only replace the first occurrence
                flags=re.DOTALL,
            )

        # Convert markdown to HTML with extensions

        html_content = markdown.markdown(
            markdown_content, extensions=["fenced_code", "tables", "toc", "nl2br", "sane_lists"]
        )

        # Post-process to convert Mermaid code blocks to proper format

        # Convert <code class="language-mermaid"> to <pre class="mermaid">

        html_content = re.sub(
            r'<pre><code class="language-mermaid">(.*?)</code></pre>',
            r'<pre class="mermaid">\1</pre>',
            html_content,
            flags=re.DOTALL,
        )

        # Add Section 508 compliant CSS classes to headings

        # Handle headings with or without existing attributes (id, etc.)

        html_content = re.sub(
            r"<h1(\s[^>]*)?>",
            lambda m: f'<h1{m.group(1) or ""} class="doc-section-title">',
            html_content,
        )

        html_content = re.sub(
            r"<h2(\s[^>]*)?>",
            lambda m: f'<h2{m.group(1) or ""} class="doc-section-heading">',
            html_content,
        )

        html_content = re.sub(
            r"<h3(\s[^>]*)?>",
            lambda m: f'<h3{m.group(1) or ""} class="doc-subsection-heading">',
            html_content,
        )

        html_content = re.sub(
            r"<h4(\s[^>]*)?>",
            lambda m: f'<h4{m.group(1) or ""} class="doc-minor-heading">',
            html_content,
        )

        return render(
            request,
            "workflows/documentation.html",
            {
                "workflow": metadata,
                "content": html_content,
                "page_title": f"{metadata.name} - Documentation",
            },
        )

    except Exception as e:
        logger.exception("Error reading documentation for workflow_id=%s: %s", workflow_id, e)
        return HttpResponseNotFound("Resource not found.")


def workflow_user_story(request, workflow_id):
    """Display the user story for a specific workflow"""

    import re

    import markdown

    from agent_app.workflow_registry import REPO_ROOT, workflow_registry

    workflow = workflow_registry.get(workflow_id)

    if not workflow:
        return HttpResponseNotFound(f"Workflow '{workflow_id}' not found")

    metadata = workflow["metadata"]

    # Path to user story file (workflows at repo root, same as workflow_edit/documentation)
    user_story_path = REPO_ROOT / "workflows" / workflow_id / "USER_STORY.md"

    if not user_story_path.exists():
        html_content = (
            "<p class='doc-section-heading'>No user story yet</p>"
            "<p>Add a <code>USER_STORY.md</code> file in this workflow's folder to describe "
            "business value and requirements.</p>"
        )
    else:
        try:
            with user_story_path.open(encoding="utf-8") as f:
                markdown_content = f.read()

            # Convert markdown to HTML with extensions
            html_content = markdown.markdown(
                markdown_content, extensions=["fenced_code", "tables", "toc", "nl2br", "sane_lists"]
            )

            # Add Section 508 compliant CSS classes to headings
            html_content = re.sub(
                r"<h1(\s[^>]*)?>",
                lambda m: f'<h1{m.group(1) or ""} class="doc-section-title">',
                html_content,
            )
            html_content = re.sub(
                r"<h2(\s[^>]*)?>",
                lambda m: f'<h2{m.group(1) or ""} class="doc-section-heading">',
                html_content,
            )
            html_content = re.sub(
                r"<h3(\s[^>]*)?>",
                lambda m: f'<h3{m.group(1) or ""} class="doc-subsection-heading">',
                html_content,
            )
            html_content = re.sub(
                r"<h4(\s[^>]*)?>",
                lambda m: f'<h4{m.group(1) or ""} class="doc-minor-heading">',
                html_content,
            )
        except Exception as e:
            logger.exception("Error reading user story for workflow_id=%s: %s", workflow_id, e)
            return HttpResponseNotFound("Resource not found.")

    can_generate_draft = request.session.get("user_role") == "admin"
    return render(
        request,
        "workflows/user_story.html",
        {
            "workflow": metadata,
            "content": html_content,
            "page_title": f"{metadata.name} - User Story",
            "can_generate_draft": can_generate_draft,
        },
    )


def workflow_runs_list(request):
    """Display list of all workflow runs for the current user with pagination"""

    from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

    from agent_app.models import WorkflowRun

    # Always sync user_id from environment (to handle .env changes)

    env_user_id = os.environ.get("USER_ID")

    if env_user_id:
        request.session["user_id"] = int(env_user_id)

    elif "user_id" not in request.session:
        request.session["user_id"] = ANONYMOUS_USER_ID

    # Get user_id from session

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Get filter parameters

    status_filter = request.GET.get("status", "all")

    workflow_filter = request.GET.get("workflow", "all")

    # Per-page: allow 10, 25, 50, 100

    per_page_raw = request.GET.get("per_page", "10")

    allowed_per_page = (10, 25, 50, 100)

    try:
        per_page = int(per_page_raw)
        if per_page not in allowed_per_page:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    # Query workflow runs for this user

    # Order by created_at descending (most recent first)

    runs_query = WorkflowRun.objects.filter(user_id=user_id)

    # Apply status filter

    if status_filter != "all":
        runs_query = runs_query.filter(status=status_filter)

    # Apply workflow filter

    if workflow_filter != "all":
        runs_query = runs_query.filter(workflow_id=workflow_filter)

    runs_query = runs_query.order_by("-created_at")

    # Debug logging

    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"Workflow runs list: user_id={user_id}, found {runs_query.count()} runs")

    # Pagination

    paginator = Paginator(runs_query, per_page)

    page = request.GET.get("page", 1)

    try:
        runs = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page

        runs = paginator.page(1)

    except EmptyPage:
        # If page is out of range, deliver last page

        runs = paginator.page(paginator.num_pages)

    # Get unique workflow IDs for filter dropdown

    all_workflows = (
        WorkflowRun.objects.filter(user_id=user_id)
        .values_list("workflow_id", "workflow_name")
        .distinct()
        .order_by("workflow_name")
    )

    return render(
        request,
        "workflows/runs_list.html",
        {
            "runs": runs,
            "paginator": paginator,
            "page_obj": runs,
            "status_filter": status_filter,
            "workflow_filter": workflow_filter,
            "per_page": per_page,
            "all_workflows": all_workflows,
            "page_title": "Previous Workflow Runs",
        },
    )


def _step_id_to_name(step_id):
    """Format step ID to human-readable name (e.g. get_active_properties -> Get active properties)."""
    if not step_id or not isinstance(step_id, str):
        return str(step_id) if step_id else ""
    return step_id.replace("_", " ").replace("-", " ").title()


def _current_node_display(current_node_ids):
    """Human-readable active BPMN nodes (may be multiple for parallel branches)."""
    if not current_node_ids:
        return "—"
    ids = current_node_ids if isinstance(current_node_ids, list) else [current_node_ids]
    parts = [f"{_step_id_to_name(nid)} ({nid})" for nid in ids if nid]
    return ", ".join(parts) if parts else "—"


def _compute_join_aware_progress(engine_state, current_node_ids):
    """
    Display metadata for parallel fork/join (PAR-008). Raw BPMN ids preserved in engine_state;
    these fields are UI-oriented. When not parallel, show_parallel_panel is False (no clutter).
    """
    base = {
        "waiting_join_ids": [],
        "pending_join_count": 0,
        "active_branch_ids": [],
        "parallel_state_summary": None,
        "nodes_waiting_at_join": [],
        "show_parallel_panel": False,
    }
    if not engine_state or not isinstance(engine_state, dict):
        return base

    pj_raw = engine_state.get("pending_joins")
    if not isinstance(pj_raw, dict):
        pj_raw = {}
    tokens = engine_state.get("active_tokens")
    if not isinstance(tokens, list):
        tokens = []

    waiting_join_ids = sorted(str(k) for k in pj_raw.keys())
    pending_join_count = len(waiting_join_ids)

    branch_ids_set = set()
    for t in tokens:
        if isinstance(t, dict) and t.get("branch_id"):
            branch_ids_set.add(str(t["branch_id"]))
    active_branch_ids = sorted(branch_ids_set)

    nodes_waiting = []
    for t in tokens:
        if not isinstance(t, dict):
            continue
        cid = t.get("current_element_id")
        if cid and str(cid) in pj_raw:
            nodes_waiting.append(str(cid))
    nodes_waiting_at_join = sorted(set(nodes_waiting))

    cids = current_node_ids if isinstance(current_node_ids, list) else []
    cids = [str(x) for x in cids if x is not None and str(x).strip()]
    multi_ids = len(cids) > 1
    multi_branch = len(active_branch_ids) > 1

    show_parallel_panel = bool(
        pending_join_count or multi_ids or multi_branch or nodes_waiting_at_join
    )

    parallel_state_summary = None
    if pending_join_count:
        parts = []
        for jid in waiting_join_ids:
            info = pj_raw.get(jid) or {}
            if not isinstance(info, dict):
                info = {}
            arr = info.get("arrived_branch_ids") or []
            exp = info.get("expected_branch_ids") or []
            na = len(arr) if isinstance(arr, list) else 0
            ne = len(exp) if isinstance(exp, list) else 0
            parts.append(f"{jid} ({na}/{ne} branches at join)")
        parallel_state_summary = (
            "Waiting at parallel join — "
            + "; ".join(parts)
            + ". Other branches must still reach the join."
        )
    elif multi_ids:
        parallel_state_summary = (
            f"{len(cids)} parallel branches are active; they merge at the next parallel join."
        )

    if not show_parallel_panel:
        parallel_state_summary = None

    base.update(
        {
            "waiting_join_ids": waiting_join_ids,
            "pending_join_count": pending_join_count,
            "active_branch_ids": active_branch_ids,
            "parallel_state_summary": parallel_state_summary,
            "nodes_waiting_at_join": nodes_waiting_at_join,
            "show_parallel_panel": show_parallel_panel,
        }
    )
    return base


def _current_node_ids_from_engine_state(engine_state):
    if not engine_state or not isinstance(engine_state, dict):
        return []
    out = []
    for t in engine_state.get("active_tokens") or []:
        if isinstance(t, dict) and t.get("current_element_id"):
            out.append(str(t["current_element_id"]))
    return out


def _build_progress_info(workflow_run):
    """Extract progress info for pending/waiting/completed/failed workflows."""
    if workflow_run.status in [
        "pending",
        "waiting_for_task",
        "waiting_for_bpmn_timer",
        "waiting_for_bpmn_message",
    ] and workflow_run.progress_data:
        pd = workflow_run.progress_data
        state_data = pd.get("state_data", {})
        raw_steps = state_data.get("workflow_steps", [])
        cids = pd.get("current_node_ids") or []
        if not isinstance(cids, list):
            cids = [cids] if cids else []
        cids = [str(x) for x in cids if x is not None and str(x).strip()]
        eng = pd.get("engine_state") or {}
        jp = _compute_join_aware_progress(eng, cids)
        bew = eng.get("bpmn_event_wait") if isinstance(eng, dict) else {}
        if not isinstance(bew, dict):
            bew = {}
        sp_ctx = None
        if isinstance(eng, dict):
            st = eng.get("subprocess_stack") or []
            if isinstance(st, list) and st:
                fr = st[-1] if isinstance(st[-1], dict) else {}
                sp_ctx = (fr.get("name") or fr.get("subprocess_id") or "").strip() or None
        return {
            "completed_steps": [_step_id_to_name(s) for s in raw_steps],
            "next_step": pd.get("next_step"),
            "paused_at": pd.get("paused_at"),
            "pending_tasks": pd.get("pending_tasks", []),
            "completed_node_ids": pd.get("completed_node_ids", []),
            "current_node_ids": cids,
            "current_node_display": _current_node_display(cids),
            "failed_node_id": pd.get("failed_node_id"),
            "bpmn_event_wait": bew,
            "bpmn_intermediate_wait_kind": pd.get("bpmn_intermediate_wait_kind"),
            "subprocess_context": sp_ctx,
            **jp,
        }
    if workflow_run.status in ["completed", "failed", "cancelled"]:
        completed_node_ids = []
        failed_node_id = None
        failure_reason = None
        last_successful_node_id = None
        condition_failure_metadata = None
        cancelled_at = None
        timeout_seconds = None
        timed_out_at = None
        if workflow_run.progress_data:
            pd = workflow_run.progress_data
            completed_node_ids = pd.get("completed_node_ids", [])
            failed_node_id = pd.get("failed_node_id")
            failure_reason = pd.get("failure_reason")
            last_successful_node_id = pd.get("last_successful_node_id")
            condition_failure_metadata = pd.get("condition_failure_metadata")
            cancelled_at = pd.get("cancelled_at")
            timeout_seconds = pd.get("timeout_seconds")
            timed_out_at = pd.get("timed_out_at")
        if not completed_node_ids and workflow_run.output_data:
            completed_node_ids = workflow_run.output_data.get("workflow_steps", [])
        base_done = {
            "completed_node_ids": completed_node_ids,
            "completed_steps": [_step_id_to_name(s) for s in completed_node_ids],
            "failed_node_id": failed_node_id,
            "failed_step_name": _step_id_to_name(failed_node_id) if failed_node_id else None,
            "failure_reason": failure_reason,
            "last_successful_node_id": last_successful_node_id,
            "condition_failure_metadata": condition_failure_metadata,
            "cancelled_at": cancelled_at,
            "timeout_seconds": timeout_seconds,
            "timed_out_at": timed_out_at,
        }
        if workflow_run.status == "completed":
            base_done["current_node_ids"] = []
            base_done["current_node_display"] = "—"
            base_done.update(_compute_join_aware_progress({}, []))
            return base_done
        eng = (workflow_run.progress_data or {}).get("engine_state") or {}
        cur_from_eng = _current_node_ids_from_engine_state(eng)
        jp = _compute_join_aware_progress(eng, cur_from_eng)
        base_done["current_node_ids"] = cur_from_eng
        base_done["current_node_display"] = _current_node_display(cur_from_eng)
        base_done.update(jp)
        return base_done
    if workflow_run.status == "running" and workflow_run.progress_data:
        pd = workflow_run.progress_data
        cids = pd.get("current_node_ids") or []
        if not isinstance(cids, list):
            cids = [cids] if cids else []
        cids = [str(x) for x in cids if x is not None and str(x).strip()]
        eng = pd.get("engine_state") or {}
        if not cids and eng:
            cids = _current_node_ids_from_engine_state(eng)
        jp = _compute_join_aware_progress(eng, cids)
        lre = eng.get("last_retryable_error") if isinstance(eng, dict) else None
        sp_ctx = None
        if isinstance(eng, dict):
            st = eng.get("subprocess_stack") or []
            if isinstance(st, list) and st:
                fr = st[-1] if isinstance(st[-1], dict) else {}
                sp_ctx = (fr.get("name") or fr.get("subprocess_id") or "").strip() or None
        return {
            "completed_node_ids": pd.get("completed_node_ids", []),
            "completed_steps": [_step_id_to_name(s) for s in (pd.get("completed_node_ids") or [])],
            "current_node_ids": cids,
            "current_node_display": _current_node_display(cids),
            "failed_node_id": None,
            "subprocess_context": sp_ctx,
            "retrying_task_id": pd.get("retrying_task_id"),
            "retry_attempt": pd.get("retry_attempt"),
            "bpmn_max_task_retries": pd.get("bpmn_max_task_retries"),
            "last_retryable_error": lre if isinstance(lre, dict) else None,
            **jp,
        }
    return None


def _build_tasks_json(workflow_run):
    """Serialize tasks for a workflow run to JSON."""
    from agent_app.models import HumanTask

    tasks = HumanTask.objects.filter(workflow_run=workflow_run).order_by("created_at")
    tasks_data = [
        {
            "task_id": t.task_id,
            "title": t.title,
            "task_type": t.task_type,
            "status": t.status,
            "completed_by_user_id": t.completed_by_user_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "output_data": t.output_data,
        }
        for t in tasks
    ]
    return json.dumps(tasks_data)


def _resolve_results_template(workflow_id):
    """Resolve per-workflow result fragment template path."""
    try:
        get_template(f"{workflow_id}/run_result.html")
        return f"{workflow_id}/run_result.html"
    except TemplateDoesNotExist:
        return "workflows/run_detail/results/default.html"


def _build_progress_node_ids_json(progress_info):
    """Build JSON-serialized progress node IDs for BPMN diagram."""
    if not progress_info:
        return {"completed_node_ids": "[]", "current_node_ids": "[]", "failed_node_id": "null"}
    return {
        "completed_node_ids": json.dumps(progress_info.get("completed_node_ids") or []),
        "current_node_ids": json.dumps(progress_info.get("current_node_ids") or []),
        "failed_node_id": (
            json.dumps(progress_info.get("failed_node_id"))
            if progress_info.get("failed_node_id")
            else "null"
        ),
    }


def workflow_run_detail(request, run_id):
    """Display details of a specific workflow run"""
    from agent_app.models import WorkflowRun

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    try:
        workflow_run = WorkflowRun.objects.get(run_id=run_id)
        if workflow_run.user_id != user_id:
            return HttpResponseForbidden("You don't have access to this workflow run")

        duration = None
        if workflow_run.started_at and workflow_run.completed_at:
            duration = (workflow_run.completed_at - workflow_run.started_at).total_seconds()

        output_data_json = (
            json.dumps(workflow_run.output_data) if workflow_run.output_data else "null"
        )

        from agent_app.workflow_registry import workflow_registry

        workflow = workflow_registry.get(workflow_run.workflow_id)
        workflow_metadata = workflow.get("metadata") if workflow else None
        diagram_mermaid = workflow_metadata.diagram_mermaid if workflow_metadata else None
        diagram_bpmn_xml = (
            getattr(workflow_metadata, "diagram_bpmn_xml", None) if workflow_metadata else None
        )

        progress_info = _build_progress_info(workflow_run)
        tasks_json = _build_tasks_json(workflow_run)
        results_include_template = _resolve_results_template(workflow_run.workflow_id)
        progress_node_ids_json = _build_progress_node_ids_json(progress_info)

        from agent_app.bpmn_run_diagnostics import build_operator_diagnostics, is_bpmn_operator_view

        _has_bpmn_xml = bool(diagram_bpmn_xml and str(diagram_bpmn_xml).strip())
        _pd = workflow_run.progress_data if isinstance(workflow_run.progress_data, dict) else None
        bpmn_operator = None
        bpmn_progress_json = ""
        if is_bpmn_operator_view(diagram_bpmn_xml=_has_bpmn_xml, progress_data=_pd):
            bpmn_operator = build_operator_diagnostics(_pd, workflow_run.status)
            if _pd is not None:
                try:
                    bpmn_progress_json = json.dumps(_pd, indent=2, default=str)
                except (TypeError, ValueError):
                    bpmn_progress_json = str(_pd)
        else:
            bpmn_progress_json = ""
        # Raw dict for json_script so diagram gets valid data without template escaping issues
        progress_node_ids = {
            "completed_node_ids": (progress_info or {}).get("completed_node_ids") or [],
            "current_node_ids": (progress_info or {}).get("current_node_ids") or [],
            "failed_node_id": (progress_info or {}).get("failed_node_id"),
        }

        return render(
            request,
            "workflows/run_detail.html",
            {
                "run": workflow_run,
                "duration": duration,
                "output_data_json": output_data_json,
                "diagram_mermaid": diagram_mermaid,
                "diagram_bpmn_xml": diagram_bpmn_xml or "",
                "progress_info": progress_info,
                "progress_node_ids_json": progress_node_ids_json,
                "progress_node_ids": progress_node_ids,
                "tasks_json": tasks_json,
                "results_include_template": results_include_template,
                "page_title": f"Workflow Run: {workflow_run.run_id}",
                "bpmn_operator": bpmn_operator,
                "bpmn_progress_json": bpmn_progress_json,
            },
        )
    except WorkflowRun.DoesNotExist:
        return HttpResponseNotFound(f"Workflow run '{run_id}' not found")


@require_http_methods(["POST"])
def workflow_run_delete(request, run_id):
    """Delete a workflow run"""

    from django.http import HttpResponseForbidden
    from django.utils import timezone

    from agent_app.models import WorkflowRun

    # Get user_id from session (default to 9)

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    try:
        workflow_run = WorkflowRun.objects.get(run_id=run_id)

        # Check user access

        if workflow_run.user_id != user_id:
            return HttpResponseForbidden("You don't have access to this workflow run")

        # If still running, mark as cancelled instead of deleting

        if workflow_run.status == "running":
            workflow_run.status = "cancelled"

            workflow_run.completed_at = timezone.now()

            workflow_run.save()

        else:
            # Delete the run

            workflow_run.delete()

        return redirect("workflow_runs_list")

    except WorkflowRun.DoesNotExist:
        return HttpResponseNotFound(f"Workflow run '{run_id}' not found")


@require_http_methods(["POST"])
def workflow_runs_bulk_delete(request):
    """Delete multiple workflow runs. Expects run_ids in POST."""
    from django.http import HttpResponseForbidden
    from django.utils import timezone

    from agent_app.models import WorkflowRun

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    run_ids = request.POST.getlist("run_ids") or []
    if not run_ids:
        return redirect("workflow_runs_list")

    for run_id in run_ids:
        try:
            workflow_run = WorkflowRun.objects.get(run_id=run_id)
            if workflow_run.user_id != user_id:
                continue
            if workflow_run.status == "running":
                workflow_run.status = "cancelled"
                workflow_run.completed_at = timezone.now()
                workflow_run.save()
            else:
                workflow_run.delete()
        except WorkflowRun.DoesNotExist:
            logger.debug("WorkflowRun already deleted or not found for cancel")

    return redirect("workflow_runs_list")


@require_http_methods(["GET", "POST"])
def workflow_run_resume_bpmn(request, run_id):
    """
    Resume after intermediateCatchEvent (timer/message) wait (PAR-015).
    POST: optional JSON body {"satisfy_intermediate_message": "<key>"} for message catch.
    """
    import asyncio

    from django.utils import timezone

    from agent_app.bpmn_engine import normalize_engine_state
    from agent_app.models import WorkflowRun
    from agent_app.workflow_runner import resume_bpmn_after_pause

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    try:
        workflow_run = WorkflowRun.objects.get(run_id=run_id)
    except WorkflowRun.DoesNotExist:
        return HttpResponseNotFound("Run not found")
    if workflow_run.user_id != user_id:
        return HttpResponseForbidden("Access denied")

    allowed = frozenset(
        {
            WorkflowRun.STATUS_WAITING_BPMN_TIMER,
            WorkflowRun.STATUS_WAITING_BPMN_MESSAGE,
        }
    )
    if workflow_run.status not in allowed:
        if request.method == "GET":
            return redirect("workflow_run_detail", run_id=run_id)
        return JsonResponse(
            {"error": "Run is not waiting on BPMN timer or message."}, status=400
        )

    if request.method == "GET":
        return redirect("workflow_run_detail", run_id=run_id)

    sk = None
    ct = (request.content_type or "").lower()
    if request.body and "application/json" in ct:
        try:
            body = json.loads(request.body.decode() or "{}")
            sk = body.get("satisfy_intermediate_message")
        except json.JSONDecodeError:
            pass
    if not sk and request.POST:
        sk = request.POST.get("satisfy_intermediate_message")
    if sk:
        pd = dict(workflow_run.progress_data or {})
        eng = normalize_engine_state(pd.get("engine_state"))
        acc = list(eng.get("satisfied_intermediate_messages") or [])
        s = str(sk).strip()
        if s and s not in acc:
            acc.append(s)
        eng["satisfied_intermediate_messages"] = acc
        pd["engine_state"] = eng
        workflow_run.progress_data = pd
        workflow_run.save(update_fields=["progress_data"])
        workflow_run.refresh_from_db()

    workflow_run.status = WorkflowRun.STATUS_RUNNING
    workflow_run.started_at = timezone.now()
    workflow_run.save(update_fields=["status", "started_at"])

    asyncio.run(resume_bpmn_after_pause(workflow_run, send_message=None))
    return redirect("workflow_run_detail", run_id=run_id)


def workflow_studio(request):
    """Display the workflow studio page for creating new workflows (admin only)."""
    from agents.base import get_workflow_studio_model_options

    user_role = request.session.get("user_role", "user")
    if user_role != "admin":
        return redirect("workflows_list")

    return render(
        request,
        "workflows/studio.html",
        {"workflow_studio_models": get_workflow_studio_model_options()},
    )
