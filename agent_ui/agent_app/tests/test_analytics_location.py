from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from agent_app.analytics.location import resolve_location


def _with_session(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


class AnalyticsLocationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_proxy_headers_have_priority(self):
        request = _with_session(
            self.factory.get(
                "/chat/",
                HTTP_CF_IPCOUNTRY="US",
                HTTP_X_REGION="VA",
                HTTP_X_CITY="Arlington",
            )
        )
        request.session["analytics_client_location"] = {
            "city": "Fallback City",
            "state": "FS",
            "country": "FC",
        }
        resolved = resolve_location(request)
        self.assertEqual(resolved["source"], "proxy_header")
        self.assertEqual(resolved["city"], "Arlington")
        self.assertEqual(resolved["state"], "VA")
        self.assertEqual(resolved["country"], "US")

    def test_client_fallback_when_no_proxy_headers(self):
        request = _with_session(self.factory.get("/chat/"))
        request.session["analytics_client_location"] = {
            "city": "Austin",
            "state": "TX",
            "country": "US",
        }
        resolved = resolve_location(request)
        self.assertEqual(resolved["source"], "client")
        self.assertEqual(resolved["city"], "Austin")
