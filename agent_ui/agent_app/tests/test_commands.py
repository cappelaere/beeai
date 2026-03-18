"""
Tests for slash commands and @Agent mentions system.
"""

import json

from django.test import Client, RequestFactory, TestCase

from agent_app.command_dispatcher import dispatcher
from agent_app.command_parser import Command, parse_command
from agent_app.models import AssistantCard, ChatMessage, ChatSession, UserPreference


class CommandParserTests(TestCase):
    """Test command parsing logic."""

    def test_parse_help_command(self):
        """Test parsing /help command."""
        cmd, remaining = parse_command("/help")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.cmd_type, "slash")
        self.assertEqual(cmd.name, "help")
        self.assertEqual(cmd.args, [])
        self.assertIsNone(remaining)

    def test_parse_agent_list_command(self):
        """Test parsing /agent list command."""
        cmd, remaining = parse_command("/agent list")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "agent")
        self.assertEqual(cmd.args, ["list"])

    def test_parse_card_update_command(self):
        """Test parsing /card update command with multiple args."""
        cmd, remaining = parse_command("/card update 1 name My Card")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "card")
        self.assertEqual(cmd.args, ["update", "1", "name", "My", "Card"])

    def test_parse_quoted_arguments(self):
        """Test parsing command with quoted arguments."""
        cmd, remaining = parse_command('/card update 1 name "My New Card"')
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.args[-1], "My New Card")

    def test_parse_at_mention(self):
        """Test parsing @Agent mention."""
        cmd, remaining = parse_command("@library search for documents")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.cmd_type, "at_mention")
        self.assertEqual(cmd.name, "library")
        self.assertEqual(remaining, "search for documents")

    def test_parse_at_mention_case_insensitive(self):
        """Test @Agent mention is case-insensitive."""
        cmd, remaining = parse_command("@LIBRARY test")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "LIBRARY")

    def test_parse_non_command(self):
        """Test that regular messages are not parsed as commands."""
        cmd, remaining = parse_command("This is a regular message")
        self.assertIsNone(cmd)
        self.assertEqual(remaining, "This is a regular message")

    def test_parse_empty_slash(self):
        """Test that just a slash is not a valid command."""
        cmd, remaining = parse_command("/")
        self.assertIsNone(cmd)

    def test_parse_slash_with_spaces(self):
        """Test slash command with leading/trailing spaces."""
        cmd, remaining = parse_command("  /help  ")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "help")


class CommandDispatcherTests(TestCase):
    """Test command dispatcher logic."""

    def setUp(self):
        """Set up test client and session."""
        self.factory = RequestFactory()
        self.client = Client()
        # Ensure session exists
        session = self.client.session
        session.save()
        self.session_key = session.session_key

    def test_dispatcher_has_handlers(self):
        """Test that dispatcher has registered handlers."""
        handlers = dispatcher.get_available_commands()
        self.assertIn("help", handlers)
        self.assertIn("agent", handlers)
        self.assertIn("model", handlers)
        self.assertIn("card", handlers)

    def test_dispatch_unknown_command(self):
        """Test dispatching unknown command returns error."""
        request = self.factory.post("/api/chat/")
        request.session = self.client.session

        cmd = Command(cmd_type="slash", name="unknown", args=[], raw_text="/unknown")
        result = dispatcher.dispatch(cmd, request, 1)

        self.assertIn("Unknown command", result["content"])
        self.assertTrue(result["metadata"].get("error"))

    def test_dispatch_help_command(self):
        """Test dispatching /help command."""
        request = self.factory.post("/api/chat/")
        request.session = self.client.session

        cmd = Command(cmd_type="slash", name="help", args=[], raw_text="/help")
        result = dispatcher.dispatch(cmd, request, 1)

        self.assertIn("Available Commands", result["content"])
        self.assertEqual(result["metadata"]["command"], "help")


class CommandAPITests(TestCase):
    """Test command API integration."""

    def setUp(self):
        """Set up test client and session."""
        self.client = Client()
        # Force session creation
        session = self.client.session
        session.save()

    def test_help_command_via_api(self):
        """Test /help command through chat API."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/help", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("is_command"))
        self.assertIn("/agent", data["response"])
        self.assertIn("/card", data["response"])

    def test_version_command_via_api(self):
        """Test /version command through chat API."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/version", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("is_command"))
        self.assertIn("BeeAI", data["response"])

    def test_agent_list_command(self):
        """Test /agent list command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/agent list", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Available agents", data["response"])
        self.assertIn("gres", data["response"])

    def test_agent_switch_command(self):
        """Test /agent switch command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/agent library", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Switched to", data["response"])

        # Verify preference was updated
        pref = UserPreference.objects.get(session_key=self.client.session.session_key)
        self.assertEqual(pref.selected_agent, "library")

    def test_card_list_command(self):
        """Test /card list command."""
        # Create a test card
        AssistantCard.objects.create(
            name="Test Card", description="Test", prompt="Test prompt", agent_type="gres"
        )

        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/card list", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Available cards", data["response"])
        self.assertIn("Test Card", data["response"])

    def test_card_create_command(self):
        """Test /card create command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/card create", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Created card", data["response"])

        # Verify card was created
        self.assertTrue(AssistantCard.objects.filter(name="New Card").exists())

    def test_at_mention_invalid_agent(self):
        """Test @Agent mention with invalid agent."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "@invalid search something", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Unknown agent", data["error"])

    def test_context_command(self):
        """Test /context command."""
        # Enable context with 10 messages
        user_id = self.client.session.get("user_id", 9)
        UserPreference.objects.create(
            user_id=user_id,
            session_key=self.client.session.session_key,
            context_message_count=10,
        )

        # Create a session with messages
        session = ChatSession.objects.create(
            session_key=self.client.session.session_key, title="Test", user_id=user_id
        )
        ChatMessage.objects.create(
            session=session, role=ChatMessage.ROLE_USER, content="Test message"
        )

        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/context", "agent": "gres", "session_id": session.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Session context", data["response"])

    def test_metrics_command(self):
        """Test /metrics command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/metrics", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Dashboard Metrics", data["response"])
        self.assertIn("Sessions", data["response"])

    def test_settings_command(self):
        """Test /settings command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/settings", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Current Settings", data["response"])

    def test_model_command(self):
        """Test /model command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/model", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Current model", data["response"])

    def test_workflow_list_command(self):
        """Test /workflow list command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/workflow list", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Available Workflows", data["response"])
        self.assertIn("Bidder Onboarding", data["response"])

    def test_workflow_show_command(self):
        """Test /workflow <number> command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/workflow 1", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Workflow #1", data["response"])
        self.assertIn("Bidder Onboarding", data["response"])

    def test_workflow_execute_command(self):
        """Test /workflow execute <number> command."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/workflow execute 1", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Starting Workflow", data["response"])
        self.assertIn("/workflows/bidder_onboarding/", data["response"])


class CommandMessagesStorageTests(TestCase):
    """Test that commands are stored correctly in chat history."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        session = self.client.session
        session.save()

    def test_command_stored_in_history(self):
        """Test that command and response are both stored."""
        response = self.client.post(
            "/api/chat/",
            json.dumps({"prompt": "/help", "agent": "gres"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        # Check that both messages were stored
        messages = ChatMessage.objects.all()
        self.assertEqual(messages.count(), 2)

        user_msg = messages.filter(role=ChatMessage.ROLE_USER).first()
        self.assertEqual(user_msg.content, "/help")

        assistant_msg = messages.filter(role=ChatMessage.ROLE_ASSISTANT).first()
        self.assertIn("Available Commands", assistant_msg.content)
