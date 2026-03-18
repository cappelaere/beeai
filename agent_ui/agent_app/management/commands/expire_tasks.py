"""
Django management command to expire old human tasks

Usage:
    python manage.py expire_tasks

This command should be run periodically (e.g., via cron) to:
1. Find tasks where expires_at < now() and status is open or in_progress
2. Update task status to 'expired'
3. Update associated workflow runs to 'failed' if appropriate
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from agent_app.models import HumanTask, WorkflowRun


class Command(BaseCommand):
    help = "Expire old human tasks that have passed their expiration date"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be expired without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        # Find expired tasks
        expired_tasks = HumanTask.objects.filter(
            expires_at__lt=now, status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS]
        ).select_related("workflow_run")

        expired_count = expired_tasks.count()

        if expired_count == 0:
            self.stdout.write(self.style.SUCCESS("No expired tasks found"))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[DRY RUN] Would expire {expired_count} task(s):")
            )
            for task in expired_tasks:
                self.stdout.write(
                    f"  - {task.task_id}: {task.title} (expired {now - task.expires_at})"
                )
            return

        # Process each expired task
        workflow_runs_to_fail = set()

        for task in expired_tasks:
            self.stdout.write(f"Expiring task {task.task_id}: {task.title}")

            # Update task status
            task.status = HumanTask.STATUS_EXPIRED
            task.save()

            # Check if workflow should be failed
            workflow_run = task.workflow_run
            if workflow_run.status == WorkflowRun.STATUS_WAITING_FOR_TASK:
                workflow_runs_to_fail.add(workflow_run.run_id)

        # Update workflow runs
        for run_id in workflow_runs_to_fail:
            # Check if all tasks for this workflow are expired/completed/cancelled
            pending_tasks = HumanTask.objects.filter(
                workflow_run_id=run_id,
                status__in=[HumanTask.STATUS_OPEN, HumanTask.STATUS_IN_PROGRESS],
            ).count()

            if pending_tasks == 0:
                # All tasks are done (expired/completed/cancelled), fail the workflow
                WorkflowRun.objects.filter(run_id=run_id).update(
                    status=WorkflowRun.STATUS_FAILED,
                    error_message="Task(s) expired without completion",
                    completed_at=now,
                )
                self.stdout.write(
                    self.style.WARNING(f"  → Failed workflow {run_id} (all tasks expired)")
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully expired {expired_count} task(s)"))
