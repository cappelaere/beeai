"""
Management command: validate agents.yaml and workflow metadata.yaml schemas.
Run: python manage.py validate_metadata
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from agent_app.schema_validation import validate_all_metadata


class Command(BaseCommand):
    help = "Validate agents.yaml and all workflow metadata.yaml schemas; print a report."

    def add_arguments(self, parser):
        parser.add_argument(
            "--repo",
            type=Path,
            default=None,
            help="Repo root path (default: derived from agents registry)",
        )

    def handle(self, *args, **options):
        repo_root = options.get("repo")
        errors, warnings = validate_all_metadata(repo_root)
        if errors:
            self.stdout.write(self.style.ERROR(f"Validation errors ({len(errors)}):"))
            for e in errors:
                self.stdout.write(self.style.ERROR(f"  - {e}"))
        if warnings:
            self.stdout.write(self.style.WARNING(f"Warnings ({len(warnings)}):"))
            for w in warnings:
                self.stdout.write(self.style.WARNING(f"  - {w}"))
        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS("All metadata schemas validated successfully."))
        elif not errors:
            self.stdout.write(self.style.SUCCESS("Validation passed with warnings (see above)."))
        else:
            self.exit(1)
