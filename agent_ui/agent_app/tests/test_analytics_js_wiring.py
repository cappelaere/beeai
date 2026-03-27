from django.test import Client, TestCase


class AnalyticsJsWiringTests(TestCase):
    def test_base_template_loads_website_analytics_js(self):
        client = Client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8", errors="replace")
        self.assertIn("/static/js/analytics/website_analytics.js", body)
