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

    def _validate_toggle_flags(self, options: dict) -> None:
        if options["disable"] and options["enable"]:
            raise CommandError("Use only one of --disable or --enable.")

    def _normalize_canonical_path(self, raw_path: str) -> str:
        canonical_path = str(raw_path or "").strip()
        if not canonical_path:
            raise CommandError("canonical_path is required.")
        if not canonical_path.startswith("/"):
            canonical_path = f"/{canonical_path}"
        if canonical_path != "/" and canonical_path.endswith("/"):
            canonical_path = canonical_path[:-1]
        return canonical_path

    def _resolve_key(self, raw_key: str, canonical_path: str) -> str:
        key = str(raw_key or "").strip()
        if not key:
            key = slugify(canonical_path.strip("/")) or "root"
        key = slugify(key)
        if not key:
            raise CommandError("Could not derive a valid key.")
        return key

    def _resolve_enabled(self, options: dict) -> bool:
        return not options["disable"]

    def _save_selected_params(self, tracked_page: TrackedPage, raw_params: list[str]) -> int:
        created_params = 0
        for raw_param in raw_params:
            param_name = (raw_param or "").strip().lower()
            if not param_name:
                continue
            _, was_created = TrackedPageQueryParam.objects.get_or_create(
                tracked_page=tracked_page, param_name=param_name
            )
            if was_created:
                created_params += 1
        return created_params

    @transaction.atomic
    def handle(self, *args, **options):
        self._validate_toggle_flags(options)
        canonical_path = self._normalize_canonical_path(options["canonical_path"])
        key = self._resolve_key(options["key"], canonical_path)

        name = str(options["name"] or "").strip()
        enabled = self._resolve_enabled(options)

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

        created_params = self._save_selected_params(tracked_page, options["params"])

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} tracked page {tracked_page.canonical_path} key={tracked_page.key} "
                f"enabled={tracked_page.enabled} new_params={created_params}"
            )
        )
