from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from agent_app.analytics.dashboard_queries import build_dashboard_filters, get_dashboard_data
from agent_app.models import PageViewEvent, TrackedPage


class AnalyticsDashboardQueryTests(TestCase):
    def setUp(self):
        self.page_chat = TrackedPage.objects.create(
            key="chat",
            canonical_path="/chat",
            name="Chat",
            enabled=True,
        )
        self.page_tools = TrackedPage.objects.create(
            key="tools",
            canonical_path="/tools",
            name="Tools",
            enabled=True,
        )

        now = timezone.now()
        PageViewEvent.objects.create(
            tracked_page=self.page_chat,
            canonical_path="/chat",
            event_time=now - timedelta(hours=3),
            visitor_id="v1",
            app_user_id=100,
        )
        PageViewEvent.objects.create(
            tracked_page=self.page_chat,
            canonical_path="/chat",
            event_time=now - timedelta(hours=2),
            visitor_id="v2",
            app_user_id=100,
        )
        PageViewEvent.objects.create(
            tracked_page=self.page_tools,
            canonical_path="/tools",
            event_time=now - timedelta(hours=1),
            visitor_id="v3",
            app_user_id=101,
        )

    def test_build_dashboard_filters_defaults_invalid_range(self):
        filters = build_dashboard_filters("not-a-range")
        self.assertEqual(filters.range_key, "30d")

    def test_get_dashboard_data_from_raw_events(self):
        filters = build_dashboard_filters("24h")
        data = get_dashboard_data(filters)
        self.assertIn(data["source"], {"raw_events", "raw_events_fallback"})
        self.assertEqual(data["summary"]["page_views"], 3)
        self.assertEqual(len(data["top_pages"]), 2)
        self.assertTrue(data["trends"]["hour"])
        self.assertTrue(data["trends"]["day"])
        self.assertTrue(data["trends"]["week"])
        self.assertTrue(data["trends"]["month"])

    def test_get_dashboard_data_filters_selected_page(self):
        filters = build_dashboard_filters("24h", "/chat")
        data = get_dashboard_data(filters)
        self.assertEqual(data["summary"]["page_views"], 2)
        self.assertEqual(len(data["top_pages"]), 1)
        self.assertEqual(data["top_pages"][0]["canonical_path"], "/chat")

    @patch("agent_app.analytics.dashboard_queries._can_use_rollup", return_value=True)
    @patch(
        "agent_app.analytics.dashboard_queries._summary_from_rollup",
        return_value={"page_views": 9, "unique_visitors": 5, "unique_users": 4},
    )
    @patch(
        "agent_app.analytics.dashboard_queries._top_pages_from_rollup",
        return_value=[
            {"canonical_path": "/chat", "page_views": 9, "unique_visitors": 5, "unique_users": 4}
        ],
    )
    @patch(
        "agent_app.analytics.dashboard_queries._trend_from_rollup",
        return_value=[
            {
                "bucket": "2026-03-01T00:00:00+00:00",
                "page_views": 9,
                "unique_visitors": 5,
                "unique_users": 4,
            }
        ],
    )
    def test_rollup_path_preferred_when_available(
        self,
        _trend_mock,
        _top_mock,
        _summary_mock,
        _can_mock,
    ):
        data = get_dashboard_data(build_dashboard_filters("7d"))
        self.assertEqual(data["source"], "rollup_day")
        self.assertEqual(data["summary"]["page_views"], 9)
        self.assertIn("hour", data["trends"])
        self.assertIn("week", data["trends"])
        self.assertIn("month", data["trends"])

    @patch("agent_app.analytics.dashboard_queries._can_use_rollup", return_value=True)
    @patch(
        "agent_app.analytics.dashboard_queries._summary_from_rollup",
        side_effect=RuntimeError("boom"),
    )
    def test_rollup_failure_falls_back_to_raw(self, _summary_mock, _can_mock):
        data = get_dashboard_data(build_dashboard_filters("7d"))
        self.assertEqual(data["source"], "raw_events_fallback")
        self.assertEqual(data["summary"]["page_views"], 3)


class AnalyticsDashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.page = TrackedPage.objects.create(key="chat", canonical_path="/chat", enabled=True)
        self.user_model = get_user_model()
        self.staff_user = self.user_model.objects.create_user(
            username="staff-analytics", password="test-pass", is_staff=True
        )
        self.non_staff_user = self.user_model.objects.create_user(
            username="regular-user", password="test-pass", is_staff=False
        )
        PageViewEvent.objects.create(
            tracked_page=self.page,
            canonical_path="/chat",
            visitor_id="v1",
            app_user_id=9,
        )

    def test_dashboard_requires_staff_auth(self):
        response = self.client.get("/analytics/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_dashboard_denies_non_staff_user(self):
        self.client.force_login(self.non_staff_user)
        response = self.client.get("/analytics/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_dashboard_renders_for_staff_user(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/analytics/dashboard/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn("Website Analytics", body)
        self.assertIn("/static/js/analytics/dashboard_trends.js", body)
        self.assertIn("analytics-trends-data", body)
        self.assertIn("analytics-trend-hour", body)
        self.assertIn("analytics-trend-day", body)
        self.assertIn("analytics-trend-week", body)
        self.assertIn("analytics-trend-month", body)

    def test_dashboard_filter_query_params_applied(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/analytics/dashboard/?range=24h&page=/chat")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_range"], "24h")
        self.assertEqual(response.context["selected_page"], "/chat")
        self.assertEqual(response.context["summary"]["page_views"], 1)
