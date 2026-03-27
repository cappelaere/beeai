from django.db import migrations


def apply_timescale_setup(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    from agent_app.analytics.timescale import timescale_setup_sql

    with schema_editor.connection.cursor() as cursor:
        for statement in timescale_setup_sql():
            cursor.execute(statement)


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

