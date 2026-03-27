import importlib
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase, override_settings

from agent_app.analytics.timescale import timescale_setup_sql

_migration = importlib.import_module("agent_app.migrations.0032_website_analytics_timescale")
apply_timescale_setup = _migration.apply_timescale_setup


class _CursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class AnalyticsTimescaleTests(SimpleTestCase):
    def test_timescale_sql_contains_expected_constructs(self):
        sql = "\n".join(timescale_setup_sql()).lower()
        self.assertIn("create_hypertable", sql)
        self.assertIn("analytics_pageviews_hourly", sql)
        self.assertIn("analytics_pageviews_daily", sql)
        self.assertIn("analytics_pageviews_weekly", sql)
        self.assertIn("analytics_pageviews_monthly", sql)
        self.assertIn("add_retention_policy", sql)
        self.assertIn("365 days", sql)

    def test_migration_noop_for_non_postgres(self):
        cursor = Mock()
        connection = SimpleNamespace(vendor="sqlite", cursor=Mock(return_value=cursor))
        schema_editor = SimpleNamespace(connection=connection)
        apply_timescale_setup(apps=None, schema_editor=schema_editor)
        connection.cursor.assert_not_called()

    @override_settings(WEBSITE_ANALYTICS_TIMESCALE_ENABLED=False)
    def test_migration_noop_when_timescale_disabled(self):
        cursor = Mock()
        connection = SimpleNamespace(
            vendor="postgresql",
            cursor=Mock(return_value=_CursorContext(cursor)),
        )
        schema_editor = SimpleNamespace(connection=connection)
        apply_timescale_setup(apps=None, schema_editor=schema_editor)
        connection.cursor.assert_not_called()

    def test_migration_skips_when_timescale_extension_unavailable(self):
        cursor = Mock()
        cursor.fetchone.return_value = [False]
        connection = SimpleNamespace(
            vendor="postgresql",
            cursor=Mock(return_value=_CursorContext(cursor)),
        )
        schema_editor = SimpleNamespace(connection=connection)
        apply_timescale_setup(apps=None, schema_editor=schema_editor)

        self.assertEqual(cursor.execute.call_count, 1)
        self.assertIn("pg_available_extensions", cursor.execute.call_args.args[0])

    def test_migration_handles_statement_failures_without_raising(self):
        cursor = Mock()
        cursor.fetchone.return_value = [True]
        calls = {"count": 0}

        def _execute(sql):
            calls["count"] += 1
            # Simulate one statement failure after extension checks.
            if calls["count"] == 3:
                raise RuntimeError("simulated timescale statement failure")

        cursor.execute.side_effect = _execute
        connection = SimpleNamespace(
            vendor="postgresql",
            cursor=Mock(return_value=_CursorContext(cursor)),
        )
        schema_editor = SimpleNamespace(connection=connection)
        apply_timescale_setup(apps=None, schema_editor=schema_editor)

        # Should execute availability check + continue through remaining SQL.
        self.assertGreater(cursor.execute.call_count, 3)

