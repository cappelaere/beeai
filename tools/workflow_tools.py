"""
Workflow Management Tools for Flo Agent

Tools for discovering, executing, and monitoring BeeAI workflows.
"""

import os
from datetime import timedelta

from asgiref.sync import sync_to_async
from beeai_framework.tools import StringToolOutput, tool

# Import workflow helpers
from workflow_helpers import (
    track_workflow_metrics,
)


# Django imports will be done lazily inside functions
def _setup_django():
    """Setup Django environment lazily when needed"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")
    import django

    if not django.apps.apps.ready:
        django.setup()


def _get_django_imports():
    """Import Django-related modules after Django is set up"""
    _setup_django()
    from agent_app.models import WorkflowRun
    from agent_app.utils import generate_short_run_id
    from agent_app.workflow_registry import REPO_ROOT, workflow_registry

    return WorkflowRun, workflow_registry, REPO_ROOT, generate_short_run_id


@tool
def list_workflows() -> StringToolOutput:
    """
    List all available workflows with their metadata.

    Returns a list of all registered workflows including their:
    - ID, name, and description
    - Icon and category
    - Estimated duration
    - Workflow number

    Use this when users ask "what workflows are available?" or
    "show me all workflows".
    """
    try:
        _, workflow_registry, _, _ = _get_django_imports()
        workflows = workflow_registry.get_all()

        if not workflows:
            return StringToolOutput(
                str(
                    {
                        "workflows": [],
                        "count": 0,
                        "message": "No workflows are currently registered",
                    }
                )
            )

        workflow_list = []
        for w in workflows:
            workflow_list.append(
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "icon": w.icon,
                    "category": w.category,
                    "estimated_duration": w.estimated_duration,
                    "workflow_number": w.workflow_number,
                }
            )

        # Sort by workflow number
        workflow_list.sort(key=lambda x: x["workflow_number"])

        return StringToolOutput(str({"workflows": workflow_list, "count": len(workflow_list)}))

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to list workflows: {str(e)}"}))


@tool
def get_workflow_detail(workflow_id: str) -> StringToolOutput:
    """
    Get detailed information about a specific workflow.

    Args:
        workflow_id: The unique identifier of the workflow (e.g., "bidder_onboarding")

    Returns complete workflow details including:
    - Full metadata (name, description, category, duration)
    - Input schema with required fields
    - Mermaid diagram for visualization
    - Documentation content (README.md and USER_STORY.md if available)

    Use this when users want to learn more about a specific workflow
    or need to understand what inputs are required.
    """
    try:
        _, workflow_registry, REPO_ROOT, _ = _get_django_imports()  # noqa: N806
        workflow = workflow_registry.get(workflow_id)

        if not workflow:
            return StringToolOutput(
                str(
                    {
                        "error": f"Workflow '{workflow_id}' not found",
                        "available_workflows": [w.id for w in workflow_registry.get_all()],
                    }
                )
            )

        metadata = workflow["metadata"]

        # Build response with metadata
        response = {
            "id": metadata.id,
            "name": metadata.name,
            "description": metadata.description,
            "icon": metadata.icon,
            "category": metadata.category,
            "estimated_duration": metadata.estimated_duration,
            "workflow_number": metadata.workflow_number,
            "input_schema": metadata.input_schema,
            "diagram_mermaid": metadata.diagram_mermaid,
        }

        # Try to load README.md
        workflow_dir = REPO_ROOT / "workflows" / workflow_id
        readme_path = workflow_dir / "README.md"
        if readme_path.exists():
            with readme_path.open() as f:
                response["readme"] = f.read()

        # Try to load USER_STORY.md
        user_story_path = workflow_dir / "USER_STORY.md"
        if user_story_path.exists():
            with user_story_path.open() as f:
                response["user_story"] = f.read()

        # Add documentation path if available
        if metadata.documentation_path:
            response["documentation_path"] = metadata.documentation_path

        return StringToolOutput(str(response))

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to get workflow details: {str(e)}"}))


@tool
def suggest_workflow(user_intent: str) -> StringToolOutput:
    """
    Intelligently suggest workflows based on user needs.

    Args:
        user_intent: Description of what the user wants to accomplish
                    (e.g., "verify a new bidder", "check property details")

    Returns a ranked list of recommended workflows with explanations
    of why each workflow might be suitable.

    Use this when users describe what they want to do but don't know
    which workflow to use.
    """
    try:
        _, workflow_registry, _, _ = _get_django_imports()
        workflows = workflow_registry.get_all()

        if not workflows:
            return StringToolOutput(
                str({"suggestions": [], "message": "No workflows available to suggest"})
            )

        # Convert user intent to lowercase for matching
        intent_lower = user_intent.lower()

        # Simple keyword matching for suggestions
        suggestions = []

        # Keywords for different workflows
        workflow_keywords = {
            "bidder_onboarding": [
                "bidder",
                "onboard",
                "verify",
                "compliance",
                "eligibility",
                "sam",
                "ofac",
                "registration",
                "approve",
                "new bidder",
            ],
            "property_due_diligence": [
                "property",
                "due diligence",
                "research",
                "title",
                "environmental",
                "inspection",
                "analysis",
                "assess",
                "evaluation",
            ],
        }

        for workflow in workflows:
            score = 0
            reasons = []

            # Check if workflow keywords match user intent
            if workflow.id in workflow_keywords:
                keywords = workflow_keywords[workflow.id]
                matched_keywords = [kw for kw in keywords if kw in intent_lower]
                score = len(matched_keywords)

                if matched_keywords:
                    reasons.append(f"Matches keywords: {', '.join(matched_keywords[:3])}")

            # Check category match
            if workflow.category.lower() in intent_lower:
                score += 2
                reasons.append(f"Category matches: {workflow.category}")

            # Check description match
            desc_words = workflow.description.lower().split()
            intent_words = intent_lower.split()
            common_words = set(desc_words) & set(intent_words)
            if common_words:
                score += len(common_words)
                reasons.append("Description relevance")

            if score > 0:
                suggestions.append(
                    {
                        "workflow_id": workflow.id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "icon": workflow.icon,
                        "category": workflow.category,
                        "relevance_score": score,
                        "reasons": reasons,
                        "estimated_duration": workflow.estimated_duration,
                    }
                )

        # Sort by relevance score
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit to top 3 suggestions
        suggestions = suggestions[:3]

        if not suggestions:
            # If no matches, return all workflows as general suggestions
            suggestions = [
                {
                    "workflow_id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "icon": w.icon,
                    "category": w.category,
                    "relevance_score": 0,
                    "reasons": ["General workflow - may be relevant"],
                    "estimated_duration": w.estimated_duration,
                }
                for w in workflows
            ]

        return StringToolOutput(
            str({"user_intent": user_intent, "suggestions": suggestions, "count": len(suggestions)})
        )

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to suggest workflows: {str(e)}"}))


@tool
async def list_workflow_runs(
    workflow_id: str | None = None, status: str | None = None, limit: int = 20
) -> StringToolOutput:
    """
    List past workflow executions with filtering options.

    Args:
        workflow_id: Optional filter by workflow type (e.g., "bidder_onboarding")
        status: Optional filter by status (pending, running, completed, failed, waiting_for_task)
        limit: Maximum number of results to return (default: 20, max: 100)

    Returns a list of workflow runs with:
    - Run ID, workflow name, and status
    - Start and completion timestamps
    - User ID who initiated the run

    Use this when users want to see "previous workflow runs" or
    "recent executions" or check status of workflows.
    """
    try:
        WorkflowRun, _, _, _ = _get_django_imports()  # noqa: N806

        # Limit cap
        limit = max(1, min(int(limit), 100))

        # Define sync function for database query
        def get_runs():
            # Build query
            queryset = WorkflowRun.objects.all()

            # Apply filters
            if workflow_id:
                queryset = queryset.filter(workflow_id=workflow_id)

            if status:
                # Validate status
                valid_statuses = [
                    WorkflowRun.STATUS_PENDING,
                    WorkflowRun.STATUS_RUNNING,
                    WorkflowRun.STATUS_COMPLETED,
                    WorkflowRun.STATUS_FAILED,
                    WorkflowRun.STATUS_CANCELLED,
                    WorkflowRun.STATUS_WAITING_FOR_TASK,
                ]
                if status in valid_statuses:
                    queryset = queryset.filter(status=status)

            # Order and limit
            queryset = queryset.order_by("-started_at", "-created_at")[:limit]

            # Serialize results
            runs = []
            for run in queryset:
                runs.append(
                    {
                        "run_id": run.run_id,
                        "workflow_id": run.workflow_id,
                        "workflow_name": run.workflow_name,
                        "status": run.status,
                        "user_id": run.user_id,
                        "created_at": run.created_at.isoformat() if run.created_at else None,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "has_error": bool(run.error_message),
                    }
                )
            return runs

        # Run database query in sync context (thread_sensitive=False to use thread pool)
        runs = await sync_to_async(get_runs, thread_sensitive=False)()

        return StringToolOutput(
            str(
                {
                    "runs": runs,
                    "count": len(runs),
                    "filters": {"workflow_id": workflow_id, "status": status, "limit": limit},
                }
            )
        )

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to list workflow runs: {str(e)}"}))


@tool
async def search_workflow_runs(
    workflow_id: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    user_id: int | None = None,
    limit: int = 20,
) -> StringToolOutput:
    """
    Search workflow runs with filters (workflow, status, date range).

    Args:
        workflow_id: Optional filter by workflow ID.
        status: Optional filter by status (pending, running, completed, failed, etc.).
        date_from: Optional ISO date or datetime; filter runs created on or after this.
        date_to: Optional ISO date or datetime; filter runs created on or before this.
        user_id: Optional filter by user (defaults to current user from environment).
        limit: Max results (default 20, max 100).

    Use when the user asks "find runs from last week", "completed runs for workflow X", etc.
    """
    try:
        _setup_django()
        from django.utils.dateparse import parse_datetime

        from agent_app.models import WorkflowRun

        uid = user_id if user_id is not None else int(os.environ.get("USER_ID", 9))
        limit = max(1, min(int(limit), 100))

        def do_search():
            qs = WorkflowRun.objects.filter(user_id=uid)
            if workflow_id:
                qs = qs.filter(workflow_id=workflow_id)
            if status:
                valid = [
                    WorkflowRun.STATUS_PENDING,
                    WorkflowRun.STATUS_RUNNING,
                    WorkflowRun.STATUS_COMPLETED,
                    WorkflowRun.STATUS_FAILED,
                    WorkflowRun.STATUS_CANCELLED,
                    WorkflowRun.STATUS_WAITING_FOR_TASK,
                ]
                if status in valid:
                    qs = qs.filter(status=status)
            if date_from:
                parsed = parse_datetime(date_from)
                if parsed:
                    qs = qs.filter(created_at__gte=parsed)
            if date_to:
                parsed = parse_datetime(date_to)
                if parsed:
                    qs = qs.filter(created_at__lte=parsed)
            runs = list(qs.order_by("-created_at")[:limit])
            return [
                {
                    "run_id": r.run_id,
                    "workflow_id": r.workflow_id,
                    "workflow_name": r.workflow_name,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "view_url": f"/workflows/runs/{r.run_id}/",
                }
                for r in runs
            ]

        runs = await sync_to_async(do_search, thread_sensitive=False)()
        return StringToolOutput(
            str(
                {
                    "runs": runs,
                    "count": len(runs),
                    "filters": {"workflow_id": workflow_id, "status": status},
                }
            )
        )
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to search workflow runs: {str(e)}"}))


@tool
async def get_run_detail(run_id: str) -> StringToolOutput:
    """
    Get complete details of a specific workflow run.

    Args:
        run_id: The unique 8-character run identifier (e.g., "a1b2c3d4")

    Returns full run information including:
    - Status and timestamps
    - Input data that was provided
    - Output data/results (if completed)
    - Progress information
    - Error messages (if failed)

    Use this when users want to see "results of run X" or
    "what happened in this workflow run".
    """
    try:
        WorkflowRun, _, _, _ = _get_django_imports()  # noqa: N806

        # Define sync function for database query
        def get_run():
            try:
                run = WorkflowRun.objects.get(run_id=run_id)

                # Build detailed response
                response = {
                    "run_id": run.run_id,
                    "workflow_id": run.workflow_id,
                    "workflow_name": run.workflow_name,
                    "status": run.status,
                    "user_id": run.user_id,
                    "input_data": run.input_data,
                    "output_data": run.output_data,
                    "progress_data": run.progress_data,
                    "error_message": run.error_message,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                }

                # Calculate duration if applicable
                if run.started_at and run.completed_at:
                    duration = run.completed_at - run.started_at
                    response["duration_seconds"] = duration.total_seconds()

                return response
            except WorkflowRun.DoesNotExist:
                return {
                    "error": f"Workflow run '{run_id}' not found",
                    "message": "Run ID may be invalid or the run may have been deleted",
                }

        # Run database query in sync context (thread_sensitive=False to use thread pool)
        response = await sync_to_async(get_run, thread_sensitive=False)()

        return StringToolOutput(str(response))

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to get run details: {str(e)}"}))


def _outcome_parts_completed(run) -> list:
    """Outcome parts for a completed run with output_data."""
    parts = []
    od = run.output_data
    if od.get("eligible") is True:
        parts.append("Eligible")
    elif od.get("eligible") is False:
        parts.append("Not eligible")
    if od.get("status"):
        parts.append(str(od["status"]))
    if od.get("summary") and not parts:
        summary = str(od["summary"])[:200]
        parts.append(summary + ("..." if len(str(od["summary"])) > 200 else ""))
    if not parts and od.get("executive_brief_markdown"):
        parts.append("Report generated")
    return parts


def _outcome_parts_failed(run) -> list:
    """Outcome parts for a failed run."""
    msg = f"Failed: {run.error_message[:150]}"
    if len(run.error_message) > 150:
        msg += "..."
    return [msg]


def _build_run_outcome_parts(run, run_id: str, HumanTask, WorkflowRun) -> list:
    """Build list of outcome description strings for a workflow run."""
    outcome_parts = []
    if run.status == WorkflowRun.STATUS_COMPLETED and run.output_data:
        outcome_parts = _outcome_parts_completed(run)
    elif run.status == WorkflowRun.STATUS_FAILED and run.error_message:
        outcome_parts = _outcome_parts_failed(run)
    elif run.status == WorkflowRun.STATUS_WAITING_FOR_TASK:
        open_count = HumanTask.objects.filter(
            workflow_run_id=run_id,
            status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
        ).count()
        outcome_parts = [f"{open_count} task(s) awaiting review"]
    elif run.status == WorkflowRun.STATUS_RUNNING:
        outcome_parts = ["Running"]
    elif run.status == WorkflowRun.STATUS_PENDING:
        outcome_parts = ["Pending (not started)"]
    elif run.status == WorkflowRun.STATUS_CANCELLED:
        outcome_parts = ["Cancelled"]

    completed_tasks = HumanTask.objects.filter(
        workflow_run_id=run_id, status=HumanTask.STATUS_COMPLETED
    ).count()
    if completed_tasks and run.status == WorkflowRun.STATUS_COMPLETED:
        outcome_parts.append(f"{completed_tasks} task(s) completed")

    return outcome_parts


@tool
async def get_workflow_run_summary(run_id: str) -> StringToolOutput:
    """
    Get a short, human-readable one-line summary of a workflow run.

    Args:
        run_id: The unique 8-character run identifier.

    Returns workflow name, status, and a brief outcome (e.g. "Eligible", "Not eligible",
    "1 approval task completed", "Failed: <reason>"). Use when the user asks
    "what happened with run X?" or "summarize run X" or "outcome of that run".
    """
    try:
        _setup_django()
        from agent_app.models import HumanTask, WorkflowRun

        def build_summary():
            try:
                run = WorkflowRun.objects.get(run_id=run_id)
            except WorkflowRun.DoesNotExist:
                return {"error": f"Workflow run '{run_id}' not found"}

            outcome_parts = _build_run_outcome_parts(run, run_id, HumanTask, WorkflowRun)
            return {
                "run_id": run.run_id,
                "workflow_name": run.workflow_name,
                "status": run.status,
                "summary_line": f"{run.workflow_name} — {run.status}: "
                + ("; ".join(outcome_parts) if outcome_parts else "—"),
                "view_url": f"/workflows/runs/{run_id}/",
            }

        result = await sync_to_async(build_summary, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to get run summary: {str(e)}"}))


@tool
async def rerun_workflow(run_id: str) -> StringToolOutput:
    """
    Start a new workflow run with the same workflow and input data as a previous run (clone).

    Args:
        run_id: The run ID to clone (source run).

    Returns the new run_id and view_url. The new run is created in pending state; user can
    start it from the run page or use manage_workflow_run(new_run_id, 'start').
    Use when the user says "run that again", "re-run run X", "clone run abc123".
    """
    try:
        WorkflowRun, workflow_registry, _, generate_short_run_id = _get_django_imports()  # noqa: N806

        def do_rerun():
            import os

            try:
                run = WorkflowRun.objects.get(run_id=run_id)
            except WorkflowRun.DoesNotExist:
                return {"error": f"Workflow run '{run_id}' not found"}

            workflow = workflow_registry.get(run.workflow_id)
            if not workflow:
                return {
                    "error": f"Workflow '{run.workflow_id}' not found; cannot re-run",
                }

            user_id = int(os.environ.get("USER_ID", 9))
            new_run_id = generate_short_run_id()
            input_data = run.input_data if isinstance(run.input_data, dict) else {}

            WorkflowRun.objects.create(
                run_id=new_run_id,
                workflow_id=run.workflow_id,
                workflow_name=run.workflow_name,
                status=WorkflowRun.STATUS_PENDING,
                user_id=user_id,
                input_data=input_data,
            )
            track_workflow_metrics(run.workflow_id, "pending")

            return {
                "success": True,
                "run_id": new_run_id,
                "workflow_id": run.workflow_id,
                "workflow_name": run.workflow_name,
                "message": f"New run '{new_run_id}' created with same inputs as {run_id}",
                "view_url": f"/workflows/runs/{new_run_id}/",
                "next_steps": "Open the run page to start it, or use manage_workflow_run to start from chat.",
            }

        result = await sync_to_async(do_rerun, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to re-run workflow: {str(e)}"}))


@tool
async def execute_workflow(workflow_id: str, input_data: dict) -> StringToolOutput:
    """
    Execute a workflow with the provided input data.

    Args:
        workflow_id: The workflow to execute (e.g., "bidder_onboarding")
        input_data: Dictionary of workflow inputs matching the workflow's schema

    Returns the run_id for tracking the execution.
    The workflow will run asynchronously.

    IMPORTANT: Before calling this tool, validate that input_data matches
    the workflow's input_schema (use get_workflow_detail to see schema).

    Use this when the user wants to "run a workflow" or "execute" or "start"
    a specific workflow after you've collected the required inputs.
    """
    try:
        WorkflowRun, workflow_registry, _, generate_short_run_id = _get_django_imports()  # noqa: N806

        # Validate workflow exists
        workflow = workflow_registry.get(workflow_id)
        if not workflow:
            return StringToolOutput(
                str(
                    {
                        "error": f"Workflow '{workflow_id}' not found",
                        "available_workflows": [w.id for w in workflow_registry.get_all()],
                    }
                )
            )

        metadata = workflow["metadata"]

        # Validate input_data is a dictionary
        if not isinstance(input_data, dict):
            return StringToolOutput(
                str(
                    {
                        "error": "input_data must be a dictionary",
                        "provided_type": str(type(input_data)),
                    }
                )
            )

        # Parse schema to find required fields
        # Schema format: {field_name: {type: ..., required: true/false, ...}}
        required_fields = [
            field_name
            for field_name, field_info in metadata.input_schema.items()
            if isinstance(field_info, dict) and field_info.get("required", False)
        ]
        missing_fields = [field for field in required_fields if field not in input_data]

        if missing_fields:
            return StringToolOutput(
                str(
                    {
                        "error": "Missing required input fields",
                        "missing_fields": missing_fields,
                        "required_fields": required_fields,
                        "provided_fields": list(input_data.keys()),
                    }
                )
            )

        # Define sync function for database operations
        def create_run():
            # Generate unique run ID
            run_id = generate_short_run_id()

            # Get user_id from environment
            import os

            user_id = int(os.environ.get("USER_ID", 9))

            # Create WorkflowRun record
            workflow_run = WorkflowRun.objects.create(
                run_id=run_id,
                workflow_id=workflow_id,
                workflow_name=metadata.name,
                status=WorkflowRun.STATUS_PENDING,
                user_id=user_id,
                input_data=input_data,
            )

            # Track metrics
            track_workflow_metrics(workflow_id, "pending")

            return {
                "success": True,
                "run_id": run_id,
                "workflow_id": workflow_id,
                "workflow_name": metadata.name,
                "status": workflow_run.status,
                "view_url": f"/workflows/runs/{run_id}/",
                "message": f"Workflow '{metadata.name}' has been queued",
                "important": "The workflow will start automatically when you view it. Please open the workflow run page to see execution.",
                "next_steps": f"Open this URL to view and execute: /workflows/runs/{run_id}/ or use get_run_detail('{run_id}') to check status.",
            }

        # Run database operation in sync context (use thread pool for workflow creation)
        result = await sync_to_async(create_run, thread_sensitive=False)()

        return StringToolOutput(str(result))

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to execute workflow: {str(e)}"}))


@tool
async def bulk_run_workflow(
    workflow_id: str,
    list_of_inputs: list[dict],
    max_runs: int = 20,
) -> StringToolOutput:
    """
    Create multiple workflow runs with different inputs (e.g. one run per bidder or property).

    Args:
        workflow_id: Workflow to run (e.g. "bidder_onboarding").
        list_of_inputs: List of input_data dicts; one run is created per item.
        max_runs: Maximum number of runs to create (default 20, cap 50).

    Returns list of run_id and view_url for each created run. Use when the user says
    "run bidder onboarding for these 5 companies" or "run workflow 1 for each of these properties".
    """
    try:
        WorkflowRun, workflow_registry, _, generate_short_run_id = _get_django_imports()  # noqa: N806

        workflow = workflow_registry.get(workflow_id)
        if not workflow:
            return StringToolOutput(
                str(
                    {
                        "error": f"Workflow '{workflow_id}' not found",
                        "available": [w.id for w in workflow_registry.get_all()],
                    }
                )
            )

        metadata = workflow["metadata"]
        required_fields = [
            f
            for f, info in (metadata.input_schema or {}).items()
            if isinstance(info, dict) and info.get("required", False)
        ]
        if not isinstance(list_of_inputs, list):
            return StringToolOutput(str({"error": "list_of_inputs must be a list of dicts"}))
        max_runs = max(1, min(int(max_runs), 50))
        to_create = list_of_inputs[:max_runs]
        user_id = int(os.environ.get("USER_ID", 9))

        def create_all():
            created = []
            for i, input_data in enumerate(to_create):
                if not isinstance(input_data, dict):
                    created.append({"error": f"Item {i + 1} is not a dict", "run_id": None})
                    continue
                missing = [f for f in required_fields if f not in input_data]
                if missing:
                    created.append(
                        {"error": f"Item {i + 1} missing fields: {missing}", "run_id": None}
                    )
                    continue
                run_id = generate_short_run_id()
                WorkflowRun.objects.create(
                    run_id=run_id,
                    workflow_id=workflow_id,
                    workflow_name=metadata.name,
                    status=WorkflowRun.STATUS_PENDING,
                    user_id=user_id,
                    input_data=input_data,
                )
                track_workflow_metrics(workflow_id, "pending")
                created.append({"run_id": run_id, "view_url": f"/workflows/runs/{run_id}/"})
            return {
                "workflow_id": workflow_id,
                "workflow_name": metadata.name,
                "requested": len(list_of_inputs),
                "created": len([c for c in created if c.get("run_id")]),
                "runs": created,
                "message": f"Created {len([c for c in created if c.get('run_id')])} run(s). Open each view_url to start.",
            }

        result = await sync_to_async(create_all, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to bulk run workflow: {str(e)}"}))


@tool
async def list_tasks(status: str | None = "open", user_id: int | None = None) -> StringToolOutput:
    """
    List human tasks that require attention.

    Args:
        status: Filter by status ("open", "in_progress", "completed", "cancelled"). Default: "open"
        user_id: Filter by user ID (defaults to environment USER_ID)

    Returns:
        JSON string with list of tasks and their details

    Example:
        list_tasks() - List all open tasks
        list_tasks(status="completed") - List completed tasks
        list_tasks(status="in_progress") - List tasks currently being worked on
    """
    try:
        _setup_django()
        from django.db.models import Q

        from agent_app.models import HumanTask

        async def get_tasks():
            # Build query
            query = Q(status=status) if status else Q()

            # Flo has admin access - can see all tasks, but prioritize assigned to user
            tasks = await sync_to_async(
                lambda: list(
                    HumanTask.objects.filter(query)
                    .select_related("workflow_run")
                    .order_by("-created_at")[:50]
                ),
                thread_sensitive=False,
            )()

            if not tasks:
                return {"tasks": [], "count": 0, "message": f"No {status} tasks found"}

            task_list = []
            for task in tasks:
                task_list.append(
                    {
                        "task_id": task.task_id,
                        "workflow_run_id": task.workflow_run.run_id,
                        "workflow_name": task.workflow_run.workflow_name,
                        "task_type": task.task_type,
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "assigned_to_user_id": task.assigned_to_user_id,
                        "required_role": task.required_role,
                        "created_at": task.created_at.isoformat(),
                        "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None,
                        "expires_at": task.expires_at.isoformat() if task.expires_at else None,
                        "completed_at": task.completed_at.isoformat()
                        if task.completed_at
                        else None,
                        "view_url": f"/workflows/tasks/{task.task_id}/",
                    }
                )

            return {"tasks": task_list, "count": len(task_list), "status_filter": status}

        result = await get_tasks()
        return StringToolOutput(str(result))

    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to list tasks: {str(e)}"}))


@tool
async def search_tasks(
    query: str | None = None,
    status: str | None = None,
    user_id: int | None = None,
    limit: int = 20,
) -> StringToolOutput:
    """
    Search tasks by text (title/description) and optional status.

    Args:
        query: Optional search string; matches task title or description (case-insensitive).
        status: Optional filter ("open", "in_progress", "completed", "cancelled").
        user_id: Optional filter by workflow owner (defaults to current user).
        limit: Max results (default 20, max 50).

    Use when the user asks "find tasks about approval", "my completed tasks", etc.
    """
    try:
        _setup_django()
        from django.db.models import Q

        from agent_app.models import HumanTask

        uid = user_id if user_id is not None else int(os.environ.get("USER_ID", 9))
        limit = max(1, min(int(limit), 50))

        def do_search():
            qs = HumanTask.objects.filter(workflow_run__user_id=uid).select_related("workflow_run")
            if status:
                qs = qs.filter(status=status)
            if query and query.strip():
                q = Q(title__icontains=query.strip()) | Q(description__icontains=query.strip())
                qs = qs.filter(q)
            tasks = list(qs.order_by("-created_at")[:limit])
            return [
                {
                    "task_id": t.task_id,
                    "workflow_run_id": t.workflow_run.run_id,
                    "workflow_name": t.workflow_run.workflow_name,
                    "title": t.title,
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "view_url": f"/workflows/tasks/{t.task_id}/",
                }
                for t in tasks
            ]

        tasks = await sync_to_async(do_search, thread_sensitive=False)()
        return StringToolOutput(str({"tasks": tasks, "count": len(tasks)}))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to search tasks: {str(e)}"}))


@tool
async def get_workflow_system_status(user_id: int | None = None) -> StringToolOutput:
    """
    Get workflow system health: run counts by status and a note about the scheduler.

    Args:
        user_id: If set, filter run counts to this user; otherwise all runs (admin view).

    Returns pending, running, waiting_for_task, completed_24h, failed_24h counts and a scheduler note.
    Use when the user asks "is everything okay?", "why isn't my schedule running?", "workflow system status".
    """
    try:
        _setup_django()
        from django.utils import timezone

        from agent_app.models import WorkflowRun

        now = timezone.now()
        day_ago = now - timedelta(hours=24)

        def get_status():
            base = WorkflowRun.objects
            if user_id is not None:
                base = base.filter(user_id=user_id)
            return {
                "workflow_runs": {
                    "pending": base.filter(status=WorkflowRun.STATUS_PENDING).count(),
                    "running": base.filter(status=WorkflowRun.STATUS_RUNNING).count(),
                    "waiting_for_task": base.filter(
                        status=WorkflowRun.STATUS_WAITING_FOR_TASK
                    ).count(),
                    "completed_24h": base.filter(
                        status=WorkflowRun.STATUS_COMPLETED, completed_at__gte=day_ago
                    ).count(),
                    "failed_24h": base.filter(
                        status=WorkflowRun.STATUS_FAILED, completed_at__gte=day_ago
                    ).count(),
                },
                "scheduler_note": "Scheduled workflows run via 'python manage.py run_scheduled_workflows' (e.g. cron). Check that this is running if schedules are not executing.",
            }

        result = await sync_to_async(get_status, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to get system status: {str(e)}"}))


@tool
async def get_my_work_summary(user_id: int | None = None) -> StringToolOutput:
    """
    Get a single summary of what needs the user's attention: pending tasks,
    recent workflow runs, next scheduled runs, and unread notification count.

    Args:
        user_id: User ID (defaults to current user from environment).

    Use when the user asks "what do I need to do?", "what's my workload?",
    "what's running?", "summary of my activity", or "what needs my attention?".
    """
    try:
        _setup_django()
        from agent_app.models import HumanTask, Notification, ScheduledWorkflow, WorkflowRun
        from agent_app.workflow_registry import workflow_registry

        uid = user_id if user_id is not None else int(os.environ.get("USER_ID", 9))

        def fetch_summary():
            # Pending tasks (open or in_progress, assigned to user or unassigned)
            tasks = list(
                HumanTask.objects.filter(
                    workflow_run__user_id=uid,
                    status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
                )
                .select_related("workflow_run")
                .order_by("-created_at")[:5]
            )
            pending_tasks = [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "workflow_name": t.workflow_run.workflow_name,
                    "status": t.status,
                    "view_url": f"/workflows/tasks/{t.task_id}/",
                }
                for t in tasks
            ]
            pending_count = HumanTask.objects.filter(
                workflow_run__user_id=uid,
                status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
            ).count()

            # Recent workflow runs (last 5)
            runs = list(WorkflowRun.objects.filter(user_id=uid).order_by("-created_at")[:5])
            recent_runs = [
                {
                    "run_id": r.run_id,
                    "workflow_name": r.workflow_name,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "view_url": f"/workflows/runs/{r.run_id}/",
                }
                for r in runs
            ]

            # Next scheduled runs (next 5)
            schedules = list(
                ScheduledWorkflow.objects.filter(user_id=uid, is_active=True).order_by(
                    "next_run_at"
                )[:5]
            )
            wf_names = {w.id: w.name for w in workflow_registry.get_all()}
            next_schedules = [
                {
                    "schedule_id": s.id,
                    "workflow_name": wf_names.get(s.workflow_id, s.workflow_id),
                    "run_name": s.run_name or "",
                    "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
                }
                for s in schedules
            ]

            # Unread notifications
            unread_count = Notification.objects.filter(user_id=uid, read_at__isnull=True).count()

            return {
                "pending_tasks": pending_tasks,
                "pending_tasks_count": pending_count,
                "recent_runs": recent_runs,
                "next_schedules": next_schedules,
                "unread_notifications": unread_count,
            }

        result = await sync_to_async(fetch_summary, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to get work summary: {str(e)}"}))


@tool
async def claim_task(task_id: str, user_id: int | None = None) -> StringToolOutput:
    """
    Claim a task to work on it.

    Args:
        task_id: The ID of the task to claim
        user_id: User ID claiming the task (defaults to environment USER_ID)

    Returns:
        JSON string with claim confirmation and task details

    Example:
        claim_task("abc123") - Claim task abc123
    """
    try:
        _setup_django()
        from django.utils import timezone

        from agent_app.models import HumanTask

        async def perform_claim():
            import os

            claimer_user_id = user_id or int(os.environ.get("USER_ID", 9))

            # Get the task
            task = await sync_to_async(HumanTask.objects.get, thread_sensitive=False)(
                task_id=task_id
            )

            # Check if already claimed by someone else
            if task.assigned_to_user_id and task.assigned_to_user_id != claimer_user_id:
                return {
                    "success": False,
                    "error": f"Task already claimed by user {task.assigned_to_user_id}",
                    "task_id": task_id,
                }

            # Check if not open
            if task.status != HumanTask.STATUS_OPEN:
                return {
                    "success": False,
                    "error": f"Task is {task.status}, cannot claim",
                    "task_id": task_id,
                }

            # Claim the task
            task.assigned_to_user_id = claimer_user_id
            task.claimed_at = timezone.now()
            task.status = HumanTask.STATUS_IN_PROGRESS
            await sync_to_async(task.save, thread_sensitive=False)()

            return {
                "success": True,
                "task_id": task_id,
                "assigned_to_user_id": claimer_user_id,
                "claimed_at": task.claimed_at.isoformat(),
                "status": task.status,
                "workflow_run_id": task.workflow_run.run_id,
                "workflow_name": task.workflow_run.workflow_name,
                "description": task.description,
                "form_schema": task.form_schema,
                "message": f"Task {task_id} claimed successfully",
                "next_step": f"Use submit_task('{task_id}', 'approved') or submit_task('{task_id}', 'denied') to complete",
            }

        result = await perform_claim()
        return StringToolOutput(str(result))

    except Exception as e:
        return StringToolOutput(
            str({"error": f"Failed to claim task: {str(e)}", "task_id": task_id})
        )


@tool
async def submit_task(
    task_id: str, decision: str, notes: str | None = None, user_id: int | None = None
) -> StringToolOutput:
    """
    Submit a decision for a human task.

    Args:
        task_id: The ID of the task to submit
        decision: Decision to submit ("approved" or "denied")
        notes: Optional notes explaining the decision
        user_id: User ID submitting (defaults to environment USER_ID)

    Returns:
        JSON string with submission confirmation

    Example:
        submit_task("abc123", "approved", "Bidder meets all requirements")
        submit_task("abc123", "denied", "Failed OFAC check")
    """
    try:
        _setup_django()
        from django.utils import timezone

        from agent_app.models import HumanTask

        # Validate decision
        decision = decision.lower()
        if decision not in ["approved", "denied", "approve", "deny"]:
            return StringToolOutput(
                str(
                    {
                        "error": f"Invalid decision '{decision}'. Must be 'approved' or 'denied'",
                        "task_id": task_id,
                    }
                )
            )

        # Normalize decision
        decision = "approved" if decision in ["approved", "approve"] else "denied"

        async def perform_submit():
            import os

            submitter_user_id = user_id or int(os.environ.get("USER_ID", 9))

            # Get the task
            task = await sync_to_async(
                HumanTask.objects.select_related("workflow_run").get, thread_sensitive=False
            )(task_id=task_id)

            # Check if already completed
            if task.status not in [HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]:
                return {
                    "success": False,
                    "error": f"Task is already {task.status}",
                    "task_id": task_id,
                }

            # Submit the task
            task.status = HumanTask.STATUS_COMPLETED
            task.completed_at = timezone.now()
            task.completed_by_user_id = submitter_user_id
            task.response_data = {
                "decision": decision,
                "notes": notes or "Submitted by Flo agent",
                "submitted_by": submitter_user_id,
                "submitted_at": timezone.now().isoformat(),
            }
            await sync_to_async(task.save, thread_sensitive=False)()

            # Try to notify workflow to resume
            try:
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                if channel_layer:
                    await channel_layer.group_send(
                        f"workflow_{task.workflow_run.run_id}",
                        {"type": "task_completed", "task_id": task_id, "decision": decision},
                    )
                    resume_status = "Workflow will resume automatically"
                else:
                    resume_status = "Workflow needs manual restart (no WebSocket)"
            except Exception as e:
                resume_status = f"Could not notify workflow: {str(e)}"

            return {
                "success": True,
                "task_id": task_id,
                "decision": decision,
                "completed_by_user_id": submitter_user_id,
                "completed_at": task.completed_at.isoformat(),
                "workflow_run_id": task.workflow_run.run_id,
                "workflow_name": task.workflow_run.workflow_name,
                "resume_status": resume_status,
                "message": f"Task {task_id} submitted with decision: {decision}",
                "view_url": f"/workflows/runs/{task.workflow_run.run_id}/",
                "next_step": f"Use get_run_detail('{task.workflow_run.run_id}') to check workflow status",
            }

        result = await perform_submit()
        return StringToolOutput(str(result))

    except Exception as e:
        return StringToolOutput(
            str({"error": f"Failed to submit task: {str(e)}", "task_id": task_id})
        )


@tool
async def manage_workflow_run(
    run_id: str, action: str, reason: str | None = None
) -> StringToolOutput:
    """
    Manage a workflow run lifecycle - start, cancel, or restart.

    Args:
        run_id: The unique 8-character run identifier (e.g., "a1b2c3d4")
        action: Action to perform ("start", "cancel", or "restart")
        reason: Optional reason for the action

    Returns:
        JSON string with action confirmation

    Actions:
        - start: Start a pending workflow run (triggers execution via WebSocket)
        - cancel: Cancel a pending, running, or waiting workflow
        - restart: Restart a failed or cancelled workflow with the same inputs

    Example:
        manage_workflow_run("a1b2c3d4", "start", "Starting from chat")
        manage_workflow_run("e5f6g7h8", "cancel", "User requested cancellation")
        manage_workflow_run("i9j0k1l2", "restart", "Retrying after fix")
    """
    try:
        WorkflowRun, workflow_registry, _, generate_short_run_id = _get_django_imports()  # noqa: N806
        from workflow_actions import cancel_workflow_run, restart_workflow_run, start_workflow_run

        # Validate action
        action = action.lower()
        if action not in ["start", "cancel", "restart"]:
            return StringToolOutput(
                str(
                    {
                        "error": f"Invalid action '{action}'. Must be 'start', 'cancel', or 'restart'",
                        "run_id": run_id,
                    }
                )
            )

        # Get user_id from environment
        import os

        user_id = int(os.environ.get("USER_ID", 9))

        # Get the workflow run
        run = await sync_to_async(WorkflowRun.objects.get, thread_sensitive=False)(run_id=run_id)

        # Route to appropriate action handler
        if action == "start":
            result = await start_workflow_run(run, workflow_registry)
        elif action == "cancel":
            result = await cancel_workflow_run(run, reason)
        elif action == "restart":
            result = await restart_workflow_run(run, generate_short_run_id, user_id, reason)

        return StringToolOutput(str(result))

    except Exception as e:
        return StringToolOutput(
            str(
                {
                    "error": f"Failed to manage workflow run: {str(e)}",
                    "run_id": run_id,
                    "action": action,
                }
            )
        )
