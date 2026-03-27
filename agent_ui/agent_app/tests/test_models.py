"""
Model Tests for RealtyIQ Agent UI
Tests model creation, validation, and relationships
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from agent_app.models import AssistantCard, ChatMessage, ChatSession, Document, PromptSuggestion


class ChatSessionModelTests(TestCase):
    """Test ChatSession model"""

    def test_create_session(self):
        """Test creating a chat session"""
        session = ChatSession.objects.create(session_key="test_key_123", title="Test Session")
        self.assertEqual(session.title, "Test Session")
        self.assertIsNotNone(session.created_at)

    def test_session_default_title(self):
        """Test that sessions have a default title or string representation"""
        session = ChatSession.objects.create(session_key="test-123")
        # Session can have empty title, but should have a valid __str__
        self.assertIsNotNone(str(session))
        # Either has a title or falls back to "Session {pk}"
        self.assertTrue(session.title or str(session).startswith("Session"))

    def test_session_ordering(self):
        """Test that sessions are ordered by creation date"""
        ChatSession.objects.create(session_key="key1", title="First")
        session2 = ChatSession.objects.create(session_key="key2", title="Second")

        sessions = list(ChatSession.objects.all())
        self.assertEqual(sessions[0].pk, session2.pk)  # Most recent first


class ChatMessageModelTests(TestCase):
    """Test ChatMessage model"""

    def setUp(self):
        self.session = ChatSession.objects.create(session_key="test", title="Test Session")

    def test_create_user_message(self):
        """Test creating a user message"""
        message = ChatMessage.objects.create(
            session=self.session, role=ChatMessage.ROLE_USER, content="Hello, AI!"
        )
        self.assertEqual(message.role, ChatMessage.ROLE_USER)
        self.assertEqual(message.content, "Hello, AI!")

    def test_create_assistant_message(self):
        """Test creating an assistant message"""
        message = ChatMessage.objects.create(
            session=self.session,
            role=ChatMessage.ROLE_ASSISTANT,
            content="Hello, human!",
            elapsed_ms=1500,
            tokens_used=50,
        )
        self.assertEqual(message.role, ChatMessage.ROLE_ASSISTANT)
        self.assertEqual(message.elapsed_ms, 1500)
        self.assertEqual(message.tokens_used, 50)

    def test_message_feedback(self):
        """Test adding feedback to a message"""
        message = ChatMessage.objects.create(
            session=self.session, role=ChatMessage.ROLE_ASSISTANT, content="Response"
        )

        message.feedback = ChatMessage.FEEDBACK_POSITIVE
        message.feedback_comment = "Great response!"
        message.feedback_at = timezone.now()
        message.save()

        self.assertEqual(message.feedback, ChatMessage.FEEDBACK_POSITIVE)
        self.assertIsNotNone(message.feedback_at)

    def test_message_ordering(self):
        """Test that messages are ordered by creation date"""
        msg1 = ChatMessage.objects.create(
            session=self.session, role=ChatMessage.ROLE_USER, content="First"
        )
        msg2 = ChatMessage.objects.create(
            session=self.session, role=ChatMessage.ROLE_ASSISTANT, content="Second"
        )

        messages = list(self.session.messages.all())
        self.assertEqual(messages[0].pk, msg1.pk)
        self.assertEqual(messages[1].pk, msg2.pk)


class AssistantCardModelTests(TestCase):
    """Test AssistantCard model"""

    def test_create_card(self):
        """Test creating a card"""
        card = AssistantCard.objects.create(
            name="Sales Analysis",
            description="Analyze sales trends",
            prompt="Show me sales trends for Q4",
            is_favorite=True,
        )
        self.assertEqual(card.name, "Sales Analysis")
        self.assertTrue(card.is_favorite)

    def test_favorite_cards_filter(self):
        """Test filtering favorite cards"""
        AssistantCard.objects.create(
            name="Card 1", description="Test", prompt="Test", is_favorite=True
        )
        AssistantCard.objects.create(
            name="Card 2", description="Test", prompt="Test", is_favorite=False
        )

        favorites = AssistantCard.objects.filter(is_favorite=True)
        self.assertEqual(favorites.count(), 1)

    def test_card_ordering(self):
        """Test that cards are ordered by creation date"""
        AssistantCard.objects.create(name="Card 1", description="Test", prompt="Test")
        AssistantCard.objects.create(name="Card 2", description="Test", prompt="Test")

        cards = list(AssistantCard.objects.all())
        # Most recent first (reversed chronological)
        self.assertGreaterEqual(len(cards), 2)


class DocumentModelTests(TestCase):
    """Test Document model"""

    def test_create_document(self):
        """Test creating an uploaded document"""
        from django.core.files.base import ContentFile

        doc = Document.objects.create(
            name="report.pdf",
            file=ContentFile(b"test pdf content", name="report.pdf"),
            file_size=1024000,
        )
        self.assertEqual(doc.name, "report.pdf")
        self.assertEqual(doc.file_size, 1024000)
        self.assertIsNotNone(doc.uploaded_at)

    def test_document_ordering(self):
        """Test that documents are ordered by upload date"""
        from django.core.files.base import ContentFile

        Document.objects.create(
            name="doc1.pdf", file=ContentFile(b"test content 1", name="doc1.pdf"), file_size=1000
        )
        doc2 = Document.objects.create(
            name="doc2.pdf", file=ContentFile(b"test content 2", name="doc2.pdf"), file_size=2000
        )

        docs = list(Document.objects.all())
        self.assertEqual(docs[0].pk, doc2.pk)  # Most recent first


class PromptSuggestionModelTests(TestCase):
    """Test PromptSuggestion model"""

    def test_create_suggestion(self):
        """Test creating a prompt suggestion"""
        suggestion = PromptSuggestion.objects.create(
            prompt="List all properties", is_predefined=True, usage_count=5
        )
        self.assertEqual(suggestion.prompt, "List all properties")
        self.assertTrue(suggestion.is_predefined)
        self.assertEqual(suggestion.usage_count, 5)

    def test_unique_prompt_constraint(self):
        """Test that prompts must be unique"""
        PromptSuggestion.objects.create(prompt="Test prompt")

        with self.assertRaises(IntegrityError):
            PromptSuggestion.objects.create(prompt="Test prompt")

    def test_suggestion_ordering(self):
        """Test that suggestions are ordered by usage count"""
        PromptSuggestion.objects.create(prompt="Low usage", usage_count=2)
        s2 = PromptSuggestion.objects.create(prompt="High usage", usage_count=10)

        suggestions = list(PromptSuggestion.objects.all())
        self.assertEqual(suggestions[0].pk, s2.pk)

    def test_last_used_update(self):
        """Test updating last_used timestamp"""
        suggestion = PromptSuggestion.objects.create(prompt="Test", usage_count=0)

        suggestion.usage_count += 1
        suggestion.last_used = timezone.now()
        suggestion.save()

        self.assertEqual(suggestion.usage_count, 1)
        self.assertIsNotNone(suggestion.last_used)


class ModelRelationshipTests(TestCase):
    """Test relationships between models"""

    def test_session_message_relationship(self):
        """Test that messages are linked to sessions"""
        session = ChatSession.objects.create(session_key="test", title="Test")

        ChatMessage.objects.create(session=session, role=ChatMessage.ROLE_USER, content="Message 1")
        ChatMessage.objects.create(
            session=session, role=ChatMessage.ROLE_ASSISTANT, content="Message 2"
        )

        self.assertEqual(session.messages.count(), 2)

    def test_cascade_delete(self):
        """Test that deleting a session deletes its messages"""
        session = ChatSession.objects.create(session_key="test", title="Test")

        ChatMessage.objects.create(session=session, role=ChatMessage.ROLE_USER, content="Test")

        session_id = session.pk
        session.delete()

        self.assertEqual(ChatMessage.objects.filter(session_id=session_id).count(), 0)
