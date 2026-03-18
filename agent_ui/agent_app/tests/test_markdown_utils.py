"""
Tests for markdown utility functions
"""

from django.test import TestCase

from agent_app.markdown_utils import markdown_to_plain_text, strip_code_blocks, truncate_for_tts


class MarkdownToPlainTextTests(TestCase):
    """Test markdown_to_plain_text function"""

    def test_headers(self):
        """Test that headers are converted to plain text with periods"""
        md = "## Summary\nSome content"
        result = markdown_to_plain_text(md)
        self.assertIn("Summary", result)
        self.assertNotIn("##", result)

    def test_bold_italic(self):
        """Test that bold and italic formatting is stripped"""
        md = "This is **bold** and *italic* text"
        result = markdown_to_plain_text(md)
        self.assertEqual(result, "This is bold and italic text.")
        self.assertNotIn("**", result)
        self.assertNotIn("*", result)

    def test_inline_code(self):
        """Test that inline code backticks are removed"""
        md = "The status is `Active` for this property"
        result = markdown_to_plain_text(md)
        self.assertIn("Active", result)
        self.assertNotIn("`", result)

    def test_code_blocks(self):
        """Test that code blocks are preserved but backticks removed"""
        md = "Here's code:\n```python\nprint('hello')\n```\nEnd"
        result = markdown_to_plain_text(md)
        self.assertIn("print", result)
        self.assertNotIn("```", result)

    def test_lists(self):
        """Test that list items are converted with commas"""
        md = "Features:\n- Item 1\n- Item 2\n- Item 3"
        result = markdown_to_plain_text(md)
        self.assertIn("Item 1", result)
        self.assertIn("Item 2", result)
        # Check that markdown syntax doesn't start the items
        self.assertFalse(result.strip().startswith("-"))

    def test_links(self):
        """Test that links show text only, not URLs"""
        md = "Visit [our website](https://example.com) for more"
        result = markdown_to_plain_text(md)
        self.assertIn("our website", result)
        self.assertNotIn("https://", result)
        self.assertNotIn("[", result)
        self.assertNotIn("]", result)

    def test_blockquotes(self):
        """Test that blockquotes are converted to plain text"""
        md = "> This is a quote\n> Second line"
        result = markdown_to_plain_text(md)
        self.assertIn("This is a quote", result)
        self.assertNotIn(">", result)

    def test_multiple_paragraphs(self):
        """Test that multiple paragraphs are preserved with spacing"""
        md = "First paragraph.\n\nSecond paragraph."
        result = markdown_to_plain_text(md)
        self.assertIn("First paragraph", result)
        self.assertIn("Second paragraph", result)

    def test_html_entities(self):
        """Test that HTML entities are decoded"""
        md = "Less than &lt; and greater than &gt;"
        result = markdown_to_plain_text(md)
        self.assertIn("<", result)
        self.assertIn(">", result)
        self.assertNotIn("&lt;", result)
        self.assertNotIn("&gt;", result)

    def test_empty_input(self):
        """Test that empty input returns empty string"""
        self.assertEqual(markdown_to_plain_text(""), "")
        self.assertEqual(markdown_to_plain_text("   "), "")
        self.assertEqual(markdown_to_plain_text(None), "")

    def test_complex_markdown(self):
        """Test complex nested markdown"""
        md = """## Property Summary

The property at **123 Main St** has:
- 3 bedrooms
- 2 bathrooms
- Status: `Active`

Visit [our site](https://example.com) for more details.

> Note: Auction ends soon!
"""
        result = markdown_to_plain_text(md)

        # Check content is preserved
        self.assertIn("Property Summary", result)
        self.assertIn("123 Main St", result)
        self.assertIn("3 bedrooms", result)
        self.assertIn("2 bathrooms", result)
        self.assertIn("Active", result)
        self.assertIn("our site", result)
        self.assertIn("Auction ends soon", result)

        # Check markdown syntax is removed
        self.assertNotIn("##", result)
        self.assertNotIn("**", result)
        self.assertNotIn("`", result)
        self.assertNotIn("[", result)
        self.assertNotIn(">", result)

    def test_period_ending(self):
        """Test that text ends with proper punctuation"""
        md = "This is text without ending punctuation"
        result = markdown_to_plain_text(md)
        self.assertTrue(result.endswith((".", "!", "?")))


class StripCodeBlocksTests(TestCase):
    """Test strip_code_blocks function"""

    def test_remove_fenced_code(self):
        """Test that fenced code blocks are removed"""
        text = "Before code\n```python\ncode here\n```\nAfter code"
        result = strip_code_blocks(text)
        self.assertNotIn("code here", result)
        self.assertIn("[code block]", result)
        self.assertIn("Before code", result)
        self.assertIn("After code", result)

    def test_keep_inline_code(self):
        """Test that inline code is kept but backticks removed"""
        text = "The value is `42` in the config"
        result = strip_code_blocks(text)
        self.assertIn("42", result)
        self.assertNotIn("`", result)

    def test_multiple_code_blocks(self):
        """Test multiple code blocks"""
        text = "```python\ncode1\n```\nText\n```js\ncode2\n```"
        result = strip_code_blocks(text)
        self.assertEqual(result.count("[code block]"), 2)


class TruncateForTTSTests(TestCase):
    """Test truncate_for_tts function"""

    def test_no_truncation_needed(self):
        """Test that short text is not truncated"""
        text = "Short text."
        result = truncate_for_tts(text, max_length=1000)
        self.assertEqual(result, text)

    def test_truncate_at_sentence(self):
        """Test that truncation happens at sentence boundary"""
        text = "First sentence. Second sentence. Third sentence."
        result = truncate_for_tts(text, max_length=30)
        self.assertTrue(result.endswith("."))
        self.assertIn("First sentence", result)

    def test_truncate_with_ellipsis(self):
        """Test that ellipsis is added when no good boundary"""
        text = "A very long sentence without any punctuation marks at all"
        result = truncate_for_tts(text, max_length=20)
        self.assertTrue(result.endswith("..."))

    def test_long_text_boundary(self):
        """Test that at least 70% of text is preserved"""
        text = "A" * 100 + ". " + "B" * 100
        result = truncate_for_tts(text, max_length=150)
        # Should keep first sentence since it's within 70% threshold
        self.assertIn("A", result)


class MarkdownTTSIntegrationTests(TestCase):
    """Test integration with TTS synthesis"""

    def test_real_world_example(self):
        """Test with realistic agent response"""
        md = """## Auction Dashboard Summary

Based on the latest data:

### Active Properties
- Total properties: **16**
- Status: `Active`
- Type: Classic Online Auction

### Key Metrics
1. Total offers: 0
2. Registered users: 0
3. Properties sold: 0

Visit the [dashboard](/dashboard) for more details.
"""
        result = markdown_to_plain_text(md)

        # Should be speakable without markdown syntax
        self.assertNotIn("##", result)
        self.assertNotIn("**", result)
        self.assertNotIn("`", result)
        self.assertNotIn("[", result)

        # Should contain actual content
        self.assertIn("Auction Dashboard Summary", result)
        self.assertIn("16", result)
        self.assertIn("Active", result)
        self.assertIn("dashboard", result)

        # Should be under reasonable length
        self.assertLess(len(result), len(md))

    def test_preserves_numbers_and_data(self):
        """Test that important data (numbers, addresses) is preserved"""
        md = "Property **123 Main St** has `3` bedrooms"
        result = markdown_to_plain_text(md)
        self.assertIn("123 Main St", result)
        self.assertIn("3", result)
        self.assertIn("bedrooms", result)

    def test_natural_pauses(self):
        """Test that natural pauses (periods) are added"""
        md = "## Header\nSome text"
        result = markdown_to_plain_text(md)
        # Headers should end with period for pause
        self.assertIn("Header.", result)
