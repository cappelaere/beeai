"""
API Tests for RealtyIQ Agent UI
Tests all backend API endpoints and functionality
"""

import json
import time

from django.test import Client, TestCase

from agent_app.models import AssistantCard, ChatMessage, ChatSession, Document, PromptSuggestion


class ChatAPITests(TestCase):
    """Test chat API endpoints"""

    def setUp(self):
        self.client = Client()
        self.client.session.create()
        self.client.session.save()

    def test_create_chat_session(self):
        """Test creating a new chat session"""
        response = self.client.post(
            "/api/chat/", data=json.dumps({"prompt": "Hello, AI!"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertIn("response", data)
        self.assertIn("message_id", data)

    def test_chat_with_existing_session(self):
        """Test sending message to existing session"""
        # Create initial session
        response1 = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "First message"}),
            content_type="application/json",
        )
        session_id = response1.json()["session_id"]

        # Send second message to same session
        response2 = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "Second message", "session_id": session_id}),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()["session_id"], session_id)

    def test_chat_history(self):
        """Test retrieving chat history"""
        # Create session with messages (retry once on transient sqlite lock)
        session_id = None
        for attempt in range(2):
            response = self.client.post(
                "/api/chat/",
                data=json.dumps({"prompt": "Test message"}),
                content_type="application/json",
            )
            data = response.json()
            if response.status_code == 200 and "session_id" in data:
                session_id = data["session_id"]
                break
            if (
                "database table is locked" in json.dumps(data).lower()
                and attempt == 0
            ):
                time.sleep(0.1)
                continue
            self.fail(f"Failed to create chat session: status={response.status_code}, body={data}")
        self.assertIsNotNone(session_id)

        # Get history
        history_response = self.client.get(f"/api/chat/{session_id}/")
        self.assertEqual(history_response.status_code, 200)
        data = history_response.json()
        self.assertIn("messages", data)
        self.assertGreaterEqual(len(data["messages"]), 2)  # User + Assistant

    def test_chat_empty_message(self):
        """Test that empty messages are rejected"""
        response = self.client.post(
            "/api/chat/", data=json.dumps({"message": ""}), content_type="application/json"
        )
        data = response.json()
        self.assertIn("error", data)


class SessionAPITests(TestCase):
    """Test session management API endpoints"""

    def setUp(self):
        self.client = Client()
        self.client.session.create()
        self.client.session.save()

    def test_create_session(self):
        """Test creating a new named session"""
        response = self.client.post(
            "/api/sessions/create/",
            data=json.dumps({"title": "Test Session"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["session"]["title"], "Test Session")

    def test_list_sessions(self):
        """Test listing all sessions"""
        # Create a few sessions
        ChatSession.objects.create(session_key=self.client.session.session_key, title="Session 1")
        ChatSession.objects.create(session_key=self.client.session.session_key, title="Session 2")

        response = self.client.get("/api/sessions/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        sessions = data.get("sessions", [])
        self.assertGreaterEqual(len(sessions), 2)

    def test_rename_session(self):
        """Test renaming a session"""
        session = ChatSession.objects.create(
            session_key=self.client.session.session_key, title="Old Title"
        )

        response = self.client.patch(
            f"/api/sessions/{session.pk}/rename/",
            data=json.dumps({"title": "New Title"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        session.refresh_from_db()
        self.assertEqual(session.title, "New Title")

    def test_delete_session(self):
        """Test deleting a session"""
        session = ChatSession.objects.create(
            session_key=self.client.session.session_key, title="To Delete"
        )
        session_id = session.pk

        response = self.client.delete(f"/api/sessions/{session_id}/delete/")
        self.assertEqual(response.status_code, 200)

        self.assertFalse(ChatSession.objects.filter(pk=session_id).exists())


class MessageFeedbackTests(TestCase):
    """Test message feedback API"""

    def setUp(self):
        self.client = Client()
        self.session = ChatSession.objects.create(session_key="test_key", title="Test Session")
        self.message = ChatMessage.objects.create(
            session=self.session, role=ChatMessage.ROLE_ASSISTANT, content="Test response"
        )

    def test_positive_feedback(self):
        """Test submitting positive feedback"""
        response = self.client.post(
            f"/api/messages/{self.message.pk}/feedback/",
            data=json.dumps({"feedback": "positive"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.message.refresh_from_db()
        self.assertEqual(self.message.feedback, ChatMessage.FEEDBACK_POSITIVE)

    def test_negative_feedback(self):
        """Test submitting negative feedback"""
        response = self.client.post(
            f"/api/messages/{self.message.pk}/feedback/",
            data=json.dumps({"feedback": "negative", "comment": "Not helpful"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.message.refresh_from_db()
        self.assertEqual(self.message.feedback, ChatMessage.FEEDBACK_NEGATIVE)
        self.assertEqual(self.message.feedback_comment, "Not helpful")

    def test_change_feedback(self):
        """Test changing feedback from positive to negative"""
        # First set positive
        self.client.post(
            f"/api/messages/{self.message.pk}/feedback/",
            data=json.dumps({"feedback": "positive"}),
            content_type="application/json",
        )

        # Then change to negative
        response = self.client.post(
            f"/api/messages/{self.message.pk}/feedback/",
            data=json.dumps({"feedback": "negative"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.message.refresh_from_db()
        self.assertEqual(self.message.feedback, ChatMessage.FEEDBACK_NEGATIVE)


class PromptSuggestionTests(TestCase):
    """Test prompt suggestion and autocomplete API"""

    def setUp(self):
        self.client = Client()
        # Create test prompts
        PromptSuggestion.objects.create(
            prompt="List all properties in downtown", is_predefined=True, usage_count=10
        )
        PromptSuggestion.objects.create(
            prompt="Show me sales trends", is_predefined=True, usage_count=5
        )
        PromptSuggestion.objects.create(
            prompt="List recent transactions", is_predefined=False, usage_count=2
        )

    def test_autocomplete_suggestions(self):
        """Test getting autocomplete suggestions"""
        response = self.client.get("/api/prompt-suggestions/?q=list&limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)
        self.assertGreater(len(data["suggestions"]), 0)

    def test_autocomplete_ordering(self):
        """Test that suggestions are ordered by usage count"""
        response = self.client.get("/api/prompt-suggestions/?q=list&limit=10")
        data = response.json()
        suggestions = data["suggestions"]

        # First result should have highest usage count
        if len(suggestions) > 1:
            self.assertGreaterEqual(suggestions[0]["usage_count"], suggestions[1]["usage_count"])


class PromptsManagementTests(TestCase):
    """Test prompts management page API"""

    def setUp(self):
        self.client = Client()
        # Create test prompts with varying stats
        self.prompt1 = PromptSuggestion.objects.create(
            prompt="Test prompt 1", is_predefined=True, usage_count=10
        )
        self.prompt2 = PromptSuggestion.objects.create(
            prompt="Test prompt 2", is_predefined=False, usage_count=5
        )

    def test_list_prompts(self):
        """Test listing prompts with pagination"""
        response = self.client.get("/api/prompts/?page=1&page_size=20")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("prompts", data)
        self.assertIn("pagination", data)

    def test_search_prompts(self):
        """Test searching prompts"""
        response = self.client.get("/api/prompts/?search=prompt 1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["prompts"]), 1)
        self.assertIn("prompt 1", data["prompts"][0]["prompt"].lower())

    def test_filter_predefined(self):
        """Test filtering by predefined prompts"""
        response = self.client.get("/api/prompts/?filter=predefined")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for p in data["prompts"]:
            self.assertTrue(p["is_predefined"])

    def test_filter_user_prompts(self):
        """Test filtering by user prompts"""
        response = self.client.get("/api/prompts/?filter=user")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for p in data["prompts"]:
            self.assertFalse(p["is_predefined"])

    def test_create_prompt(self):
        """Test creating a new prompt"""
        response = self.client.post(
            "/api/prompts/create/",
            data=json.dumps({"prompt": "New test prompt"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PromptSuggestion.objects.filter(prompt="New test prompt").exists())

    def test_update_prompt(self):
        """Test updating an existing prompt"""
        response = self.client.post(
            f"/api/prompts/{self.prompt1.pk}/update/",
            data=json.dumps({"prompt": "Updated prompt text"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.prompt1.refresh_from_db()
        self.assertEqual(self.prompt1.prompt, "Updated prompt text")

    def test_delete_prompt(self):
        """Test deleting a prompt"""
        prompt_id = self.prompt2.pk
        response = self.client.delete(f"/api/prompts/{prompt_id}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PromptSuggestion.objects.filter(pk=prompt_id).exists())


class AssistantCardTests(TestCase):
    """Test card API"""

    def setUp(self):
        self.client = Client()
        self.card = AssistantCard.objects.create(
            name="Test Card",
            description="Test description",
            prompt="Test prompt text",
            is_favorite=True,
        )

    def test_list_favorite_cards(self):
        """Test listing favorite cards"""
        response = self.client.get("/api/cards/?favorites=1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        cards = data.get("cards", [])
        self.assertGreater(len(cards), 0)
        for card in cards:
            self.assertTrue(card["is_favorite"])

    def test_update_card(self):
        """Test updating a card"""
        response = self.client.patch(
            f"/api/card/{self.card.pk}/patch/",
            data=json.dumps(
                {
                    "name": "Updated Card",
                    "description": "Updated description",
                    "prompt": "Updated prompt",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.card.refresh_from_db()
        self.assertEqual(self.card.name, "Updated Card")


class DocumentAPITests(TestCase):
    """Test document upload and management API"""

    def setUp(self):
        self.client = Client()

    def test_list_documents(self):
        """Test listing uploaded documents via the documents view"""
        # Create test document
        from django.core.files.base import ContentFile

        Document.objects.create(
            name="test.pdf", file=ContentFile(b"test content", name="test.pdf"), file_size=1024
        )

        # Use the documents view (follows redirect to document_library)
        response = self.client.get("/documents/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test.pdf")

    def test_delete_document(self):
        """Test deleting a document"""
        from django.core.files.base import ContentFile

        doc = Document.objects.create(
            name="to_delete.pdf",
            file=ContentFile(b"test content", name="to_delete.pdf"),
            file_size=1024,
        )
        doc_id = doc.pk

        response = self.client.delete(f"/api/documents/{doc_id}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(pk=doc_id).exists())


class DashboardAPITests(TestCase):
    """Test dashboard statistics"""

    def setUp(self):
        self.client = Client()
        # Ensure session exists and get the session_key
        session = self.client.session
        session.save()
        session_key = session.session_key

        # Create test data with the client's session_key
        chat_session = ChatSession.objects.create(session_key=session_key, title="Test Session")
        ChatMessage.objects.create(session=chat_session, role=ChatMessage.ROLE_USER, content="Test")
        ChatMessage.objects.create(
            session=chat_session,
            role=ChatMessage.ROLE_ASSISTANT,
            content="Response",
            feedback=ChatMessage.FEEDBACK_POSITIVE,
            elapsed_ms=1000,
        )
        from django.core.files.base import ContentFile

        Document.objects.create(
            name="test.pdf", file=ContentFile(b"test content", name="test.pdf"), file_size=2048
        )

    def test_dashboard_view(self):
        """Test dashboard page loads with stats"""
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Sessions")
        self.assertContains(response, "Total Queries")
        self.assertContains(response, "Documents Uploaded")

    def test_dashboard_stats_calculation(self):
        """Test that dashboard calculates stats correctly"""
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

        # Check context data
        stats = response.context["stats"]
        self.assertEqual(stats["total_sessions"], 1)
        self.assertEqual(stats["total_queries"], 1)
        self.assertEqual(stats["total_documents"], 1)
        # total_doc_size might be a formatted string (e.g., "2.0 KB")
        self.assertIsNotNone(stats["total_doc_size"])
        self.assertEqual(stats["positive_feedback"], 1)
        self.assertEqual(stats["negative_feedback"], 0)


class ViewTests(TestCase):
    """Test view rendering"""

    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        """Test home page loads"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RealtyIQ")

    def test_chat_page(self):
        """Test chat page loads"""
        response = self.client.get("/chat/")
        self.assertEqual(response.status_code, 200)

    def test_prompts_page(self):
        """Test prompts management page loads"""
        response = self.client.get("/prompts/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prompts")

    def test_dashboard_page(self):
        """Test dashboard page loads"""
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_documents_page(self):
        """Test documents page loads"""
        response = self.client.get("/documents/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_examples_page(self):
        """Test examples page loads"""
        response = self.client.get("/examples/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Examples")
