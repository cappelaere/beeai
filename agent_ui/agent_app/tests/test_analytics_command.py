from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from agent_app.models import TrackedPage, TrackedPageQueryParam


class AnalyticsCommandTests(TestCase):
    def test_register_tracked_page_creates_page_and_params(self):
        stdout = StringIO()
        call_command(
            "register_tracked_page",
            "/chat",
            "--key",
            "chat",
            "--param",
            "utm_source",
            "--param",
            "campaign",
            stdout=stdout,
        )
        page = TrackedPage.objects.get(canonical_path="/chat")
        self.assertEqual(page.key, "chat")
        self.assertTrue(page.enabled)
        params = set(
            TrackedPageQueryParam.objects.filter(tracked_page=page).values_list("param_name", flat=True)
        )
        self.assertEqual(params, {"utm_source", "campaign"})

    def test_register_tracked_page_can_disable(self):
        call_command("register_tracked_page", "/tools", "--disable")
        page = TrackedPage.objects.get(canonical_path="/tools")
        self.assertFalse(page.enabled)

