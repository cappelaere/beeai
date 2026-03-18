"""
Markdown utilities for converting markdown to plain text
Used for TTS synthesis to avoid speaking markdown syntax
"""

import html
import re

import markdown


def markdown_to_plain_text(md_text: str) -> str:
    """
    Convert markdown text to plain text suitable for TTS.

    This function:
    1. Converts markdown to HTML using the markdown library
    2. Strips HTML tags to get plain text
    3. Cleans up whitespace and formatting
    4. Adds natural pauses (periods) for better speech

    Args:
        md_text: Markdown formatted text

    Returns:
        Plain text without markdown syntax

    Examples:
        >>> markdown_to_plain_text("## Summary\\nThis is **bold** text")
        'Summary. This is bold text'

        >>> markdown_to_plain_text("- Item 1\\n- Item 2")
        'Item 1, Item 2'
    """
    if not md_text or not md_text.strip():
        return ""

    # Convert markdown to HTML
    html_text = markdown.markdown(
        md_text,
        extensions=["extra", "nl2br"],  # Support tables, fenced code, etc.
    )

    # Strip HTML tags but preserve some structure
    # Replace common block elements with appropriate spacing
    html_text = re.sub(r"</p>", ". ", html_text)  # Paragraphs end with period
    html_text = re.sub(r"</h[1-6]>", ". ", html_text)  # Headers end with period
    html_text = re.sub(r"</li>", ", ", html_text)  # List items separated by comma
    html_text = re.sub(r"<br\s*/?>", " ", html_text)  # Line breaks become spaces
    html_text = re.sub(r"</div>", " ", html_text)  # Divs add space
    html_text = re.sub(r"</blockquote>", ". ", html_text)  # Quotes end with period

    # Remove all remaining HTML tags
    plain_text = re.sub(r"<[^>]+>", "", html_text)

    # Decode HTML entities (e.g., &amp; → &, &lt; → <)
    plain_text = html.unescape(plain_text)

    # Clean up whitespace
    # Multiple spaces → single space
    plain_text = re.sub(r" +", " ", plain_text)

    # Multiple periods/commas
    plain_text = re.sub(r"\.\.+", ".", plain_text)
    plain_text = re.sub(r",,+", ",", plain_text)

    # Fix spacing around punctuation
    plain_text = re.sub(r"\s+([.,;:!?])", r"\1", plain_text)  # Remove space before punctuation
    plain_text = re.sub(
        r"([.,;:!?])([A-Za-z])", r"\1 \2", plain_text
    )  # Add space after punctuation

    # Clean up commas followed by periods
    plain_text = re.sub(r",\s*\.", ".", plain_text)

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in plain_text.split("\n")]

    # Remove empty lines and join with spaces
    lines = [line for line in lines if line]
    plain_text = " ".join(lines)

    # Final cleanup
    plain_text = plain_text.strip()

    # Ensure proper sentence ending
    if plain_text and plain_text[-1] not in ".!?":
        plain_text += "."

    return plain_text


def strip_code_blocks(text: str) -> str:
    """
    Remove code blocks from text but keep inline code.
    Useful for TTS when you want to skip code snippets.

    Args:
        text: Text that may contain code blocks

    Returns:
        Text with code blocks removed
    """
    # Remove fenced code blocks (```...```)
    text = re.sub(r"```[\s\S]*?```", "[code block]", text)

    # Keep inline code but remove backticks
    text = re.sub(r"`([^`]+)`", r"\1", text)

    return text


def truncate_for_tts(text: str, max_length: int = 8000) -> str:
    """
    Truncate text to maximum length for TTS, breaking at sentence boundaries.

    Args:
        text: Text to truncate
        max_length: Maximum length in characters

    Returns:
        Truncated text at sentence boundary
    """
    if len(text) <= max_length:
        return text

    # Find last sentence boundary before max_length
    truncated = text[:max_length]

    # Look for last period, exclamation, or question mark
    for punct in [". ", "! ", "? "]:
        last_idx = truncated.rfind(punct)
        if last_idx > 0 and last_idx > (max_length * 0.7):  # At least 70% of max
            return truncated[: last_idx + 1]

    # No good boundary found, truncate at max and add ellipsis
    return truncated.rstrip() + "..."
