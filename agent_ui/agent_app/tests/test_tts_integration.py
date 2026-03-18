"""
Tests for Section 508 TTS integration
"""

import json
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase

from agent_app.models import ChatMessage, ChatSession, UserPreference
from agent_app.tts_client import synthesize_speech_async


class TestTTSIntegration(TestCase):
    """Test Text-to-Speech integration for Section 508 mode"""

    def setUp(self):
        """Set up test client and session"""
        self.client = Client()

        # Create session and set user_id
        self.client.get("/")
        self.session_key = self.client.session.session_key
        session = self.client.session
        session["user_id"] = 9
        session.save()

        # Create chat session with user_id
        self.chat_session = ChatSession.objects.create(
            session_key=self.session_key, title="Test Session", user_id=9
        )

    @patch("agent_app.tts_client.requests.post")
    def test_tts_synthesis_success(self, mock_post):
        """Test successful TTS synthesis"""
        # Mock Piper response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "audio_id": "test123",
            "audio_url": "/v1/audio/test123",
            "content_type": "audio/mpeg",
        }
        mock_post.return_value = mock_response

        # Call synthesis
        result = synthesize_speech_async("Hello world", message_id=1)

        # Verify result
        self.assertTrue(result["success"])
        self.assertIn("audio_url", result)
        self.assertIn("http://localhost:8088", result["audio_url"])

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://localhost:8088/v1/tts/synthesize")

        request_data = call_args[1]["json"]
        self.assertEqual(request_data["text"], "Hello world")
        self.assertEqual(request_data["return_mode"], "url")
        self.assertIn("voice_id", request_data)
        self.assertIn("cache_ttl_seconds", request_data)

    @patch("agent_app.tts_client.requests.post")
    def test_tts_synthesis_failure(self, mock_post):
        """Test TTS synthesis failure handling"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Call synthesis
        result = synthesize_speech_async("Hello world", message_id=1)

        # Verify error handling
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("agent_app.tts_client.requests.post")
    def test_tts_synthesis_timeout(self, mock_post):
        """Test TTS synthesis timeout handling"""
        import requests

        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")

        # Call synthesis
        result = synthesize_speech_async("Hello world", message_id=1)

        # Verify timeout handling
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "TTS service timeout")

    @patch("threading.Thread")
    @patch("agent_runner.run_agent_sync")
    def test_chat_api_with_508_enabled(self, mock_run_agent, mock_thread):
        """Test that chat API triggers TTS when Section 508 is enabled"""
        # Enable Section 508 mode
        UserPreference.objects.create(session_key=self.session_key, section_508_enabled=True)

        # Mock agent response
        mock_run_agent.return_value = (
            "Test response",
            {"trace_id": "test123", "from_cache": False},
        )

        # Mock thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Send chat message
        response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {
                    "prompt": "Test query",
                    "agent": "gres",
                    "model": "claude-3-5-sonnet",
                    "session_id": self.chat_session.id,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response includes Section 508 fields
        self.assertIn("section_508_enabled", data)
        self.assertTrue(data["section_508_enabled"])
        self.assertIn("audio_url", data)

        # Verify TTS thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Verify thread target is synthesize_for_message
        call_args = mock_thread.call_args
        self.assertIn("target", call_args[1])
        self.assertIn("args", call_args[1])

    @patch("threading.Thread")
    @patch("agent_runner.run_agent_sync")
    def test_chat_api_with_508_disabled(self, mock_run_agent, mock_thread):
        """Test that chat API does not trigger TTS when Section 508 is disabled"""
        # Disable Section 508 mode
        UserPreference.objects.create(session_key=self.session_key, section_508_enabled=False)

        # Mock agent response
        mock_run_agent.return_value = (
            "Test response",
            {"trace_id": "test123", "from_cache": False},
        )

        # Send chat message
        response = self.client.post(
            "/api/chat/",
            data=json.dumps(
                {
                    "prompt": "Test query",
                    "agent": "gres",
                    "model": "claude-3-5-sonnet",
                    "session_id": self.chat_session.id,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify Section 508 is disabled
        self.assertFalse(data["section_508_enabled"])

        # Verify TTS thread was NOT started
        mock_thread.assert_not_called()

    def test_message_audio_api(self):
        """Test message audio URL retrieval API"""
        # Create message with audio
        message = ChatMessage.objects.create(
            session=self.chat_session,
            role=ChatMessage.ROLE_ASSISTANT,
            content="Test response",
            audio_url="http://localhost:8088/v1/audio/test123",
        )

        # Get audio URL
        response = self.client.get(f"/api/messages/{message.id}/audio/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["message_id"], message.id)
        self.assertTrue(data["has_audio"])
        self.assertEqual(data["audio_url"], "http://localhost:8088/v1/audio/test123")

    def test_message_audio_api_no_audio(self):
        """Test message audio API when audio is not yet available"""
        # Create message without audio
        message = ChatMessage.objects.create(
            session=self.chat_session,
            role=ChatMessage.ROLE_ASSISTANT,
            content="Test response",
            audio_url=None,
        )

        # Get audio URL
        response = self.client.get(f"/api/messages/{message.id}/audio/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["message_id"], message.id)
        self.assertFalse(data["has_audio"])
        self.assertIsNone(data["audio_url"])

    def test_message_audio_api_not_found(self):
        """Test message audio API with invalid message ID"""
        response = self.client.get("/api/messages/99999/audio/")
        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertIn("error", data)

    def test_chat_history_includes_audio_url(self):
        """Test that chat history API includes audio URLs"""
        # Create message with audio
        ChatMessage.objects.create(
            session=self.chat_session,
            role=ChatMessage.ROLE_ASSISTANT,
            content="Test response",
            audio_url="http://localhost:8088/v1/audio/test123",
        )

        # Get chat history
        response = self.client.get(f"/api/chat/{self.chat_session.id}/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertGreater(len(data["messages"]), 0)

        # Verify audio_url is included
        message_data = data["messages"][0]
        self.assertIn("audio_url", message_data)
        self.assertEqual(message_data["audio_url"], "http://localhost:8088/v1/audio/test123")

    @patch("agent_app.tts_client.requests.post")
    def test_text_truncation(self, mock_post):
        """Test that very long text is truncated to 8000 characters"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "audio_id": "test123",
            "audio_url": "/v1/audio/test123",
            "content_type": "audio/mpeg",
        }
        mock_post.return_value = mock_response

        # Generate very long text (10000 chars)
        long_text = "a" * 10000

        # Call synthesis
        synthesize_speech_async(long_text, message_id=1)

        # Verify text was truncated
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        self.assertEqual(len(request_data["text"]), 8000)

    def test_commands_do_not_trigger_tts(self):
        """Test that command responses don't trigger TTS synthesis"""
        # Enable Section 508 mode
        UserPreference.objects.create(session_key=self.session_key, section_508_enabled=True)

        # Send a command
        response = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "/help", "agent": "gres", "model": "claude-3-5-sonnet"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify it's a command
        self.assertTrue(data.get("is_command"))

        # Verify Section 508 is disabled for commands (no TTS)
        self.assertFalse(data.get("section_508_enabled", True))
