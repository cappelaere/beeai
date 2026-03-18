"""
Management command to create initial versions for all existing workflows
"""

from django.core.management.base import BaseCommand

from agent_app.version_manager import version_manager
from agent_app.workflow_registry import workflow_registry


class Command(BaseCommand):
    help = "Create initial version (v1) for all existing workflows that don't have versions yet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--workflow-id",
            type=str,
            help="Only create initial version for specific workflow (optional)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force create initial version even if versions already exist",
        )

    def handle(self, *args, **options):
        workflow_id_filter = options.get("workflow_id")
        force = options.get("force", False)

        # Get all workflows
        all_workflows = workflow_registry.get_all(include_internal=True)

        if workflow_id_filter:
            all_workflows = [w for w in all_workflows if w.id == workflow_id_filter]
            if not all_workflows:
                self.stdout.write(self.style.ERROR(f"Workflow '{workflow_id_filter}' not found"))
                return

        self.stdout.write(f"Found {len(all_workflows)} workflow(s) to process")

        created_count = 0
        skipped_count = 0

        for workflow in all_workflows:
            workflow_id = workflow.id

            # Check if versions already exist
            existing_versions = version_manager.get_version_history(workflow_id)

            if existing_versions.exists() and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping {workflow_id}: Already has {existing_versions.count()} version(s)"
                    )
                )
                skipped_count += 1
                continue

            try:
                from agent_app.constants import ANONYMOUS_USER_ID

                # Create initial version (ANONYMOUS_USER_ID used as system/admin)
                version = version_manager.create_version(
                    workflow_id=workflow_id,
                    user_id=ANONYMOUS_USER_ID,
                    comment="Initial version (auto-created during version control setup)",
                    tag="v1.0",
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created version {version.version_number} for workflow '{workflow_id}'"
                    )
                )
                created_count += 1

                # Generate and save changelog
                changelog_path = version_manager.save_changelog(workflow_id)
                self.stdout.write(
                    self.style.SUCCESS(f"  └─ Saved changelog to {changelog_path.name}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to create version for {workflow_id}: {e}")
                )

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✓ Created {created_count} initial version(s)"))
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f"⊘ Skipped {skipped_count} workflow(s) with existing versions")
            )
        self.stdout.write("=" * 60)
