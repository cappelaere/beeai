"""
/workflow command handler - List and execute BeeAI workflows
"""


def _parse_workflow_runs_filter(args, user_id, user_role):
    """Parse filter arguments for workflow runs."""
    filter_user_id = user_id
    filter_label = "Your"

    if len(args) > 1:
        if args[1] == "all" and user_role == "admin":
            filter_user_id = None
            filter_label = "All"
        elif args[1] == "user" and len(args) > 2 and user_role == "admin":
            try:
                filter_user_id = int(args[2])
                filter_label = f"User {filter_user_id}'s"
            except ValueError:
                return (
                    None,
                    None,
                    {
                        "content": f"Error: Invalid user_id '{args[2]}'",
                        "metadata": {"error": True, "command": "workflow runs"},
                    },
                )
        elif args[1] in ["all", "user"] and user_role != "admin":
            return (
                None,
                None,
                {
                    "content": "❌ Permission denied: Only admins can view other users' workflow runs.",
                    "metadata": {"error": True, "command": "workflow runs"},
                },
            )

    return filter_user_id, filter_label, None


def _format_workflow_run(run, filter_user_id):
    """Format a single workflow run for display."""
    from django.utils import timezone

    from agent_app.models import WorkflowRun

    age = timezone.now() - run.created_at
    age_str = f"{age.seconds // 3600}h" if age.seconds >= 3600 else f"{age.seconds // 60}m"

    status_emoji = {
        "pending": "⏳",
        "running": "▶️",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫",
        "waiting_for_task": "⏸️",
    }.get(run.status, "❓")

    user_info = f" | User {run.user_id}" if filter_user_id is None else ""

    lines = [
        f"{status_emoji} Run {run.run_id} ({run.status})",
        f"   Workflow: {run.workflow_name}{user_info}",
        f"   Created: {age_str} ago",
    ]

    if run.status == WorkflowRun.STATUS_COMPLETED and run.get_duration():
        duration = run.get_duration()
        duration_str = f"{duration:.2f}s" if duration < 60 else f"{duration / 60:.1f}m"
        lines.append(f"   Duration: {duration_str}")

    if run.status == WorkflowRun.STATUS_FAILED and run.error_message:
        error_preview = (
            run.error_message[:60] + "..." if len(run.error_message) > 60 else run.error_message
        )
        lines.append(f"   Error: {error_preview}")

    lines.append("   Commands:")
    lines.append(f"     View: /workflows/runs/{run.run_id}/")
    if run.status not in [WorkflowRun.STATUS_COMPLETED, WorkflowRun.STATUS_FAILED]:
        lines.append("     Cancel: Visit web UI")
    lines.append("")

    return lines


def _handle_workflow_runs(args, user_id, user_role):
    """List workflow runs."""
    from agent_app.models import WorkflowRun

    filter_user_id, filter_label, error = _parse_workflow_runs_filter(args, user_id, user_role)
    if error:
        return error

    if filter_user_id is None:
        runs = WorkflowRun.objects.all().order_by("-created_at")[:20]
    else:
        runs = WorkflowRun.objects.filter(user_id=filter_user_id).order_by("-created_at")[:20]

    if not runs:
        return {
            "content": f"📭 No workflow runs found for {filter_label.lower()}.\n\n💡 Execute workflows using: /workflow execute <number>",
            "metadata": {"command": "workflow runs", "count": 0},
        }

    lines = [f"🔄 {filter_label} Workflow Runs ({runs.count()}):", ""]

    for run in runs:
        lines.extend(_format_workflow_run(run, filter_user_id))

    footer = ["Commands:", "  /workflow runs - Your workflow runs"]
    if user_role == "admin":
        footer.extend(
            [
                "  /workflow runs all - All users' runs (admin)",
                "  /workflow runs user <id> - Specific user's runs (admin)",
            ]
        )
    footer.append("\n💡 View in web UI: /workflows/runs/")
    lines.extend(footer)

    return {
        "content": "\n".join(lines),
        "metadata": {
            "command": "workflow runs",
            "count": runs.count(),
            "filter_user_id": filter_user_id,
        },
    }


def _handle_workflow_list(args, workflows):
    """List all workflows or show details of a specific workflow."""
    if len(args) > 1:
        try:
            workflow_num = int(args[1])
            workflow = next((w for w in workflows if w.workflow_number == workflow_num), None)

            if not workflow:
                return {
                    "content": f"Error: Workflow #{workflow_num} not found",
                    "metadata": {"error": True, "command": "workflow list"},
                }

            inputs = []
            for field_name, field_config in workflow.input_schema.items():
                required = "required" if field_config.get("required") else "optional"
                inputs.append(f"  - {field_name} ({field_config.get('type')}) - {required}")

            return {
                "content": (
                    f"Workflow #{workflow.workflow_number}: {workflow.name}\n\n"
                    f"Icon: {workflow.icon}\n"
                    f"Category: {workflow.category}\n"
                    f"Duration: {workflow.estimated_duration}\n"
                    f"Name: {workflow.id}\n"
                    f"Description: {workflow.description}\n\n"
                    f"Input Fields:\n" + "\n".join(inputs) + "\n\n"
                    f"Execute: /workflow execute {workflow.workflow_number}\n"
                    f"View UI: /workflows/{workflow.id}/\n"
                    f"Documentation: /workflows/{workflow.id}/docs/"
                ),
                "metadata": {"command": "workflow list detail", "workflow_id": workflow.id},
            }
        except ValueError:
            return {
                "content": f"Error: Invalid workflow number '{args[1]}'",
                "metadata": {"error": True, "command": "workflow list"},
            }

    lines = ["Available Workflows:\n"]
    for wf in sorted(workflows, key=lambda x: x.workflow_number):
        lines.append(
            f"  {wf.icon} #{wf.workflow_number} - {wf.name}\n"
            f"      Category: {wf.category} | Duration: {wf.estimated_duration}\n"
            f"      {wf.description[:100]}...\n"
        )

    lines.append("\nCommands:")
    lines.append("  /workflow <number> - Show details")
    lines.append("  /workflow execute <number> - Execute workflow")

    return {
        "content": "\n".join(lines),
        "metadata": {"command": "workflow list", "count": len(workflows)},
    }


def _handle_workflow_execute(args, workflows):
    """Prepare workflow for execution."""
    if len(args) < 2:
        return {
            "content": "Usage: /workflow execute <number> [input args...]\n\nExamples:\n  /workflow execute 1 - Start workflow #1 (will prompt for inputs)\n  Ask Flo: 'Run workflow 1 for ABC Corp on property 12345' - Use natural language",
            "metadata": {"error": True, "command": "workflow execute"},
        }

    try:
        workflow_num = int(args[1])
        workflow = next((w for w in workflows if w.workflow_number == workflow_num), None)

        if not workflow:
            return {
                "content": f"Error: Workflow #{workflow_num} not found. Use /workflow list to see available workflows.",
                "metadata": {"error": True, "command": "workflow execute"},
            }

        required_fields = []
        optional_fields = []

        for field_name, field_config in workflow.input_schema.items():
            field_label = field_config.get("label", field_name)
            field_type = field_config.get("type", "text")

            if field_config.get("required"):
                required_fields.append(f"  ✓ {field_label} ({field_type})")
            else:
                optional_fields.append(f"    {field_label} ({field_type})")

        return {
            "content": (
                f"🚀 Starting Workflow #{workflow.workflow_number}: {workflow.name}\n"
                f"{'=' * 60}\n\n"
                f"Required Inputs:\n"
                + "\n".join(required_fields)
                + "\n\n"
                + (
                    "Optional Inputs:\n" + "\n".join(optional_fields) + "\n\n"
                    if optional_fields
                    else ""
                )
                + f"📝 How to execute:\n\n"
                f"Option 1 - Ask Flo (Recommended):\n"
                f"  'Run workflow {workflow_num} for [your inputs]'\n"
                f"  Example: 'Run workflow {workflow_num} for ABC Corp on property 12345'\n\n"
                f"Option 2 - Use UI:\n"
                f"  Visit: /workflows/{workflow.id}/\n\n"
                f"Option 3 - Switch to Flo:\n"
                f"  Type: @flo run workflow {workflow_num} [your inputs]"
            ),
            "metadata": {
                "command": "workflow execute",
                "workflow_id": workflow.id,
                "workflow_number": workflow.workflow_number,
                "suggest_agent": "flo",
            },
        }

    except ValueError:
        return {
            "content": f"Error: Invalid workflow number '{args[1]}'",
            "metadata": {"error": True, "command": "workflow execute"},
        }


def _handle_workflow_show(args, workflows):
    """Show workflow details by number."""
    try:
        workflow_num = int(args[0])
        workflow = next((w for w in workflows if w.workflow_number == workflow_num), None)

        if not workflow:
            return {
                "content": f"Error: Workflow #{workflow_num} not found. Use /workflow list to see available workflows.",
                "metadata": {"error": True, "command": "workflow"},
            }

        inputs = []
        for field_name, field_config in workflow.input_schema.items():
            required = "✓" if field_config.get("required") else " "
            inputs.append(
                f"  [{required}] {field_name} ({field_config.get('type')}): {field_config.get('label')}"
            )

        return {
            "content": (
                f"{workflow.icon} Workflow #{workflow.workflow_number}: {workflow.name}\n"
                f"{'=' * 60}\n\n"
                f"Category: {workflow.category}\n"
                f"Duration: {workflow.estimated_duration}\n"
                f"Name: {workflow.id}\n\n"
                f"Description:\n{workflow.description}\n\n"
                f"Input Fields:\n" + "\n".join(inputs) + "\n\n"
                f"Commands:\n"
                f"  /workflow execute {workflow.workflow_number} - Open workflow UI\n"
                f"  /workflows/{workflow.id}/ - Direct link\n"
                f"  /workflows/{workflow.id}/docs/ - Documentation"
            ),
            "metadata": {"command": "workflow show", "workflow_id": workflow.id},
        }

    except ValueError:
        return {
            "content": f"Error: Unknown workflow command '{args[0]}'. Use /workflow list for available workflows.",
            "metadata": {"error": True, "command": "workflow"},
        }


def handle_workflow(request, args, session_key):
    """
    Handle workflow-related commands.

    Commands:
        /workflow list - List all available workflows
        /workflow runs - List my workflow runs
        /workflow runs all - List all workflow runs (admin only)
        /workflow runs user <user_id> - List runs for specific user (admin only)
        /workflow <number> - Show workflow details
        /workflow execute <number> - Execute workflow (interactive)

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.workflow_registry import workflow_registry

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    user_role = request.session.get("user_role", "admin")

    if not args:
        return {
            "content": "Usage: /workflow list|runs|<number>|execute <number>",
            "metadata": {"error": True, "command": "workflow"},
        }

    if args[0] == "runs":
        return _handle_workflow_runs(args, user_id, user_role)

    if args[0] == "list":
        workflows = workflow_registry.get_all()
        if not workflows:
            return {"content": "No workflows available.", "metadata": {"command": "workflow list"}}
        return _handle_workflow_list(args, workflows)

    if args[0] == "execute" or args[0] == "run" or args[0] == "start":
        workflows = workflow_registry.get_all()
        return _handle_workflow_execute(args, workflows)

    workflows = workflow_registry.get_all()
    return _handle_workflow_show(args, workflows)
