from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from agent_app.analytics.services import create_page_view_event
from agent_app.models import PageViewEvent, TrackedPage, TrackedPageQueryParam


def _with_session(request):
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.create()
    request.session["user_id"] = 9
    request.session.save()
    return request


class AnalyticsModelTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.page = TrackedPage.objects.create(key="chat", canonical_path="/chat", enabled=True)
        TrackedPageQueryParam.objects.create(tracked_page=self.page, param_name="utm_source")
        TrackedPageQueryParam.objects.create(tracked_page=self.page, param_name="token")

    def test_create_page_view_event_filters_selected_params_and_saves_path(self):
        request = _with_session(
            self.factory.get(
                "/chat/?utm_source=google&token=secret-token&ignored=1",
                HTTP_CF_IPCOUNTRY="US",
                HTTP_X_REGION="VA",
                HTTP_X_CITY="Arlington",
                HTTP_USER_AGENT="Mozilla/5.0",
            )
        )
        event = create_page_view_event(request)
        self.assertIsNotNone(event)
        self.assertEqual(event.canonical_path, "/chat")
        self.assertEqual(event.query_params_filtered, {"utm_source": "google"})
        self.assertEqual(event.location_country, "US")
        self.assertEqual(event.location_source, "proxy_header")
        self.assertEqual(event.app_user_id, 9)
        self.assertTrue(event.session_key_hash)
        self.assertTrue(event.visitor_id)
        self.assertNotEqual(event.visitor_id, event.session_key_hash[:20])

    def test_page_view_model_has_no_ip_field(self):
        field_names = {field.name for field in PageViewEvent._meta.get_fields()}
        self.assertNotIn("ip_address", field_names)
        self.assertNotIn("raw_querystring", field_names)
        self.assertNotIn("querystring", field_names)

