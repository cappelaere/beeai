import logging

from django.conf import settings
from django.db import migrations

logger = logging.getLogger(__name__)


def apply_timescale_setup(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    if not getattr(settings, "WEBSITE_ANALYTICS_TIMESCALE_ENABLED", True):
        logger.info("Skipping Timescale setup: WEBSITE_ANALYTICS_TIMESCALE_ENABLED is false.")
        return

    from agent_app.analytics.timescale import timescale_setup_sql

    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb');"
            )
            row = cursor.fetchone() or [False]
            timescale_available = bool(row[0])
        except Exception as exc:
            logger.warning("Skipping Timescale setup: extension availability check failed: %s", exc)
            return

        if not timescale_available:
            logger.warning("Skipping Timescale setup: timescaledb extension not available.")
            return

        for statement in timescale_setup_sql():
            try:
                cursor.execute(statement)
            except Exception as exc:
                logger.warning("Timescale setup statement skipped after error: %s", exc)


def reverse_timescale_setup(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    # Keep raw table data intact. Drop rollups/policies only.
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_pageviews_monthly;")
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_pageviews_weekly;")
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_pageviews_daily;")
        cursor.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_pageviews_hourly;")


class Migration(migrations.Migration):
    dependencies = [
        ("agent_app", "0031_website_analytics_models"),
    ]

    operations = [
        migrations.RunPython(
            apply_timescale_setup,
            reverse_timescale_setup,
        ),
    ]

