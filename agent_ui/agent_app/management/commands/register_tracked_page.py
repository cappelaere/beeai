from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from agent_app.models import TrackedPage, TrackedPageQueryParam


class Command(BaseCommand):
    help = "Create or update a tracked page and selected query parameters."

    def add_arguments(self, parser):
        parser.add_argument("canonical_path", type=str, help="Canonical path, e.g. /chat")
        parser.add_argument("--key", type=str, default="", help="Unique key (slug).")
        parser.add_argument("--name", type=str, default="", help="Display name.")
        parser.add_argument(
            "--param",
            dest="params",
            action="append",
            default=[],
            help="Allowlisted query parameter (repeatable).",
        )
        parser.add_argument(
            "--clear-params",
            action="store_true",
            help="Clear existing selected query params before adding --param values.",
        )
        parser.add_argument(
            "--disable",
            action="store_true",
            help="Disable tracking for this page.",
        )
        parser.add_argument(
            "--enable",
            action="store_true",
            help="Enable tracking for this page.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["disable"] and options["enable"]:
            raise CommandError("Use only one of --disable or --enable.")

        canonical_path = str(options["canonical_path"] or "").strip()
        if not canonical_path:
            raise CommandError("canonical_path is required.")
        if not canonical_path.startswith("/"):
            canonical_path = f"/{canonical_path}"
        if canonical_path != "/" and canonical_path.endswith("/"):
            canonical_path = canonical_path[:-1]

        key = str(options["key"] or "").strip()
        if not key:
            key = slugify(canonical_path.strip("/")) or "root"
        key = slugify(key)
        if not key:
            raise CommandError("Could not derive a valid key.")

        name = str(options["name"] or "").strip()
        enabled = True
        if options["disable"]:
            enabled = False
        elif options["enable"]:
            enabled = True

        tracked_page, created = TrackedPage.objects.update_or_create(
            canonical_path=canonical_path,
            defaults={
                "key": key,
                "name": name,
                "enabled": enabled,
            },
        )

        if options["clear_params"]:
            tracked_page.allowed_query_params.all().delete()

        created_params = 0
        for raw_param in options["params"]:
            param_name = (raw_param or "").strip().lower()
            if not param_name:
                continue
            _, was_created = TrackedPageQueryParam.objects.get_or_create(
                tracked_page=tracked_page, param_name=param_name
            )
            if was_created:
                created_params += 1

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} tracked page {tracked_page.canonical_path} key={tracked_page.key} "
                f"enabled={tracked_page.enabled} new_params={created_params}"
            )
        )

