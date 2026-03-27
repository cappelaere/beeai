import json

from django.middleware.csrf import _get_new_csrf_string
from django.test import Client, TestCase


class AnalyticsViewsTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_location_api_requires_csrf(self):
        response = self.client.post(
            "/api/analytics/location/",
            data=json.dumps({"city": "Austin", "state": "TX", "country": "US"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_location_api_accepts_valid_csrf_and_stores_session_location(self):
        csrf_token = _get_new_csrf_string()
        self.client.cookies["csrftoken"] = csrf_token
        response = self.client.post(
            "/api/analytics/location/",
            data=json.dumps({"city": "Austin", "state": "TX", "country": "US"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        session = self.client.session
        self.assertEqual(
            session.get("analytics_client_location"),
            {"city": "Austin", "state": "TX", "country": "US"},
        )
