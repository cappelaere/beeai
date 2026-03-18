"""
Django management command to run scheduled workflows.

Usage:
    python manage.py run_scheduled_workflows

Run every 1-5 minutes via cron or systemd timer. Finds ScheduledWorkflow
rows where is_active=True and next_run_at <= now, creates a WorkflowRun,
executes it via the shared workflow runner, then updates or removes the schedule.
"""

import asyncio
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from agent_app.models import ScheduledWorkflow, WorkflowRun
from agent_app.utils import generate_short_run_id
from agent_app.workflow_registry import workflow_registry
from agent_app.workflow_runner import execute_workflow_run

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run scheduled workflows that are due (is_active=True, next_run_at <= now)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List due schedules without executing",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        due = list(
            ScheduledWorkflow.objects.filter(is_active=True, next_run_at__lte=now).order_by(
                "next_run_at"
            )
        )

        if not due:
            if not dry_run:
                logger.debug("No scheduled workflows due")
            return

        self.stdout.write(f"Found {len(due)} scheduled workflow(s) due")

        for schedule in due:
            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would run: id={schedule.id} workflow={schedule.workflow_id} "
                    f"next_run_at={schedule.next_run_at}"
                )
                continue

            workflow = workflow_registry.get(schedule.workflow_id)
            if not workflow:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Schedule id={schedule.id}: workflow {schedule.workflow_id} not in registry, skipping"
                    )
                )
                continue

            run_id = generate_short_run_id()
            workflow_name = workflow["metadata"].name
            WorkflowRun.objects.create(
                run_id=run_id,
                workflow_id=schedule.workflow_id,
                workflow_name=workflow_name,
                status=WorkflowRun.STATUS_PENDING,
                user_id=schedule.user_id,
                input_data=schedule.input_data or {},
            )

            try:
                asyncio.run(execute_workflow_run(run_id, send_message=None))
            except Exception as e:
                logger.exception("Scheduled workflow run %s failed: %s", run_id, e)
                self.stdout.write(self.style.ERROR(f"  Run {run_id} failed: {e}"))
                continue

            if schedule.schedule_type == ScheduledWorkflow.TYPE_ONCE:
                schedule.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Schedule id={schedule.id} ran once (run_id={run_id}), schedule removed"
                    )
                )
            else:
                schedule.next_run_at = timezone.now() + timedelta(minutes=schedule.interval_minutes)
                schedule.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Schedule id={schedule.id} ran (run_id={run_id}), next at {schedule.next_run_at}"
                    )
                )
