"""
Management command to generate a draft USER_STORY.md for an existing workflow using the LLM.
"""

from django.core.management.base import BaseCommand

from agent_app.views.api_workflows import (
    REPO_ROOT,
    _generate_user_story,
    _get_service_task_ids_for_workflow,
)
from agent_app.workflow_registry import workflow_registry


class Command(BaseCommand):
    help = "Generate a draft USER_STORY.md for a workflow using the LLM (business value first)"

    def add_arguments(self, parser):
        parser.add_argument(
            "workflow_id",
            type=str,
            help="Workflow ID (e.g. dap_report)",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="claude-sonnet-4",
            help="Model short key for generation (default: claude-sonnet-4)",
        )

    def handle(self, *args, **options):
        workflow_id = options["workflow_id"]
        model = options["model"]

        workflow = workflow_registry.get(workflow_id)
        if not workflow:
            self.stdout.write(self.style.ERROR(f"Workflow '{workflow_id}' not found"))
            return

        metadata = workflow["metadata"]
        name = metadata.name
        description = metadata.description or ""
        category = metadata.category or "Other"
        prompt = description

        self.stdout.write(f"Generating USER_STORY.md for {name} ({workflow_id})...")
        service_task_ids = _get_service_task_ids_for_workflow(workflow_id)
        if service_task_ids:
            self.stdout.write(f"  Steps: {', '.join(service_task_ids)}")

        content = _generate_user_story(
            model,
            name,
            workflow_id,
            category,
            description,
            prompt,
            service_task_ids,
        )

        path = REPO_ROOT / "workflows" / workflow_id / "USER_STORY.md"
        path.write_text(content.strip() + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {path}"))
