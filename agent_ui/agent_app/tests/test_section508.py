"""
Tests for Section 508 accessibility settings
"""

import json
import os

from django.test import Client, TestCase

from agent_app.models import UserPreference


class TestSection508Settings(TestCase):
    """Test Section 508 accessibility mode configuration"""

    def setUp(self):
        """Set up test client and session"""
        self.client = Client()

        # Create session
        self.client.get("/")
        self.session_key = self.client.session.session_key

    def test_default_from_environment(self):
        """Test that default Section 508 status comes from environment"""
        # Default should be false (from .env)
        response = self.client.get("/api/section508/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("section_508_enabled", data)
        self.assertIn("default", data)

        # Should match environment default
        env_default = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")
        self.assertEqual(data["default"], env_default)

    def test_toggle_via_api(self):
        """Test toggling Section 508 mode via API"""
        # Enable Section 508
        response = self.client.post(
            "/api/section508/", data=json.dumps({"enabled": True}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["section_508_enabled"])

        # Verify it was saved
        pref = UserPreference.objects.get(session_key=self.session_key)
        self.assertTrue(pref.section_508_enabled)

        # Disable Section 508
        response = self.client.post(
            "/api/section508/", data=json.dumps({"enabled": False}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["section_508_enabled"])

        # Verify it was updated
        pref.refresh_from_db()
        self.assertFalse(pref.section_508_enabled)

    def test_toggle_via_command(self):
        """Test toggling Section 508 mode via /settings command"""
        # Enable via command
        response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {"prompt": "/settings 508 on", "agent": "gres", "model": "claude-3-5-sonnet"}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["is_command"])
        self.assertIn("Section 508 accessibility mode: enabled", data["response"])
        self.assertEqual(data["metadata"]["setting"], "508")
        self.assertTrue(data["metadata"]["value"])
        self.assertTrue(data["metadata"]["reload_ui"])

        # Verify it was saved
        pref = UserPreference.objects.get(session_key=self.session_key)
        self.assertTrue(pref.section_508_enabled)

        # Disable via command
        response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {"prompt": "/settings 508 off", "agent": "gres", "model": "claude-3-5-sonnet"}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Section 508 accessibility mode: disabled", data["response"])
        self.assertFalse(data["metadata"]["value"])

        # Verify it was updated
        pref.refresh_from_db()
        self.assertFalse(pref.section_508_enabled)

    def test_settings_command_shows_508_status(self):
        """Test that /settings command displays Section 508 status"""
        response = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "/settings", "agent": "gres", "model": "claude-3-5-sonnet"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Section 508 Mode:", data["response"])
        self.assertIn("section_508", data["metadata"])

    def test_invalid_508_value(self):
        """Test that invalid values are rejected"""
        response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {"prompt": "/settings 508 maybe", "agent": "gres", "model": "claude-3-5-sonnet"}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Error: Invalid value", data["response"])
        self.assertIn("error", data["metadata"])
        self.assertTrue(data["metadata"]["error"])

    def test_context_processor(self):
        """Test that Section 508 status is available in templates"""
        response = self.client.get("/settings/")
        self.assertEqual(response.status_code, 200)

        # Check that SECTION_508_ENABLED is in context
        self.assertIn("SECTION_508_ENABLED", response.context)
        self.assertIn("SECTION_508_DEFAULT", response.context)

        # Should be boolean
        self.assertIsInstance(response.context["SECTION_508_ENABLED"], bool)
        self.assertIsInstance(response.context["SECTION_508_DEFAULT"], bool)

    def test_null_preference_uses_environment_default(self):
        """Test that null preference falls back to environment default"""
        # Create preference with null section_508_enabled
        UserPreference.objects.create(
            session_key=self.session_key,
            selected_agent="gres",
            selected_model="claude-3-5-sonnet",
            section_508_enabled=None,
        )

        # Should use environment default
        response = self.client.get("/api/section508/")
        data = response.json()

        env_default = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")
        self.assertEqual(data["section_508_enabled"], env_default)
