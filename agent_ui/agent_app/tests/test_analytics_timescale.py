import importlib
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from agent_app.analytics.timescale import timescale_setup_sql

_migration = importlib.import_module("agent_app.migrations.0032_website_analytics_timescale")
apply_timescale_setup = _migration.apply_timescale_setup


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

