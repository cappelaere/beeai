"""Template filter to render markdown as HTML."""

import markdown
from django import template
from django.utils.safestring import SafeString

register = template.Library()


@register.filter
def markdown_to_html(value):
    """Convert markdown string to HTML. Returns empty string for non-string/empty input."""
    if not value or not isinstance(value, str):
        return ""
    html = markdown.markdown(value, extensions=["fenced_code", "tables", "nl2br", "sane_lists"])
    return SafeString(html)


@register.filter
def is_markdown_key(key):
    """Return True if key suggests markdown content (e.g. executive_brief_markdown)."""
    return isinstance(key, str) and "markdown" in key.lower()
