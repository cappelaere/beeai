from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from agent_app.analytics.middleware import WebsiteAnalyticsMiddleware
from agent_app.models import PageViewEvent, TrackedPage


class AnalyticsMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        TrackedPage.objects.create(key="chat", canonical_path="/chat", enabled=True)

    def test_tracks_tracked_html_page(self):
        middleware = WebsiteAnalyticsMiddleware(lambda request: HttpResponse("ok", content_type="text/html"))
        request = self.factory.get("/chat/")
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageViewEvent.objects.count(), 1)

    def test_does_not_track_non_tracked_page(self):
        middleware = WebsiteAnalyticsMiddleware(lambda request: HttpResponse("ok", content_type="text/html"))
        request = self.factory.get("/untracked/")
        middleware(request)
        self.assertEqual(PageViewEvent.objects.count(), 0)

    def test_does_not_track_api_path(self):
        middleware = WebsiteAnalyticsMiddleware(lambda request: HttpResponse("{}", content_type="application/json"))
        request = self.factory.get("/api/chat/")
        middleware(request)
        self.assertEqual(PageViewEvent.objects.count(), 0)

