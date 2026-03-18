"""
Api Sessions
5 functions
"""

import base64
import json
import logging
import re

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import ChatSession

CHART_CACHE_PREFIX = "agent_chart_"

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


@require_GET
def chat_sessions_api(request):
    """List all chat sessions for the current user"""

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    sessions = ChatSession.objects.filter(user_id=user_id).order_by("-created_at")[:50]

    sessions_data = []

    for sess in sessions:
        last_message = sess.messages.order_by("-created_at").first()

        sessions_data.append(
            {
                "id": sess.pk,
                "title": sess.title,
                "created_at": sess.created_at.isoformat(),
                "message_count": sess.messages.count(),
                "last_message_preview": last_message.content[:100] if last_message else None,
            }
        )

    return JsonResponse({"sessions": sessions_data})


@require_POST
@csrf_exempt
@require_POST
@csrf_exempt
def create_session_api(request):
    """Create a new chat session and clear all previous context"""

    try:
        data = json.loads(request.body)

        title = data.get("title", "New Chat")

    except (json.JSONDecodeError, TypeError):
        title = "New Chat"

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Clear Redis cache to ensure fresh context

    cache_cleared = 0

    try:
        from cache import get_cache

        cache = get_cache()

        if cache.enabled:
            cache_cleared = cache.clear_all()

            logger.info(f"🗑️  Cleared {cache_cleared} cached responses from Redis")

    except Exception as e:
        logger.warning(f"Could not clear cache: {e}")

    # Clear all messages from previous sessions for this user

    previous_sessions = ChatSession.objects.filter(user_id=user_id)

    messages_deleted = 0

    for prev_session in previous_sessions:
        count = prev_session.messages.count()

        prev_session.messages.all().delete()

        messages_deleted += count

    logger.info(f"🗑️  Cleared {messages_deleted} messages from previous sessions for user {user_id}")

    # Create new session

    session_obj = ChatSession.objects.create(session_key=session_key, user_id=user_id, title=title)

    return JsonResponse(
        {
            "success": True,
            "session": {
                "id": session_obj.pk,
                "title": session_obj.title,
                "created_at": session_obj.created_at.isoformat(),
            },
            "messages_cleared": messages_deleted,
            "cache_cleared": cache_cleared,
        }
    )


@require_http_methods(["POST", "PATCH"])
@csrf_exempt
@require_http_methods(["POST", "PATCH"])
@csrf_exempt
def rename_session_api(request, session_id):
    """Rename a chat session"""

    try:
        data = json.loads(request.body)

        new_title = data.get("title", "")

    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    session_obj = get_object_or_404(ChatSession, pk=session_id)

    session_obj.title = new_title

    session_obj.save()

    return JsonResponse({"success": True, "title": session_obj.title})


@require_http_methods(["POST", "DELETE"])
@csrf_exempt
@require_http_methods(["POST", "DELETE"])
@csrf_exempt
def delete_session_api(request, session_id):
    """Delete a chat session"""

    session_obj = get_object_or_404(ChatSession, pk=session_id)

    session_obj.delete()

    return JsonResponse({"success": True})


@require_GET
def export_session_api(request, session_id):
    """Export session as Markdown (download), HTML (browser view), or PDF (with charts inlined)."""
    import markdown

    session_obj = get_object_or_404(ChatSession, pk=session_id)
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    if session_obj.user_id != user_id:
        return JsonResponse({"error": "Forbidden"}, status=403)

    # Build Markdown content

    markdown_lines = []

    # Header with session title

    session_title = session_obj.title or f"Chat Session {session_obj.pk}"

    markdown_lines.append(f"# {session_title}\n")

    # Metadata section

    markdown_lines.append("---\n")

    markdown_lines.append(f"**Session ID:** {session_obj.pk}  ")

    markdown_lines.append(f"**Created:** {session_obj.created_at.strftime('%Y-%m-%d %H:%M:%S')}  ")

    markdown_lines.append(f"**Total Messages:** {session_obj.messages.count()}\n")

    markdown_lines.append("---\n\n")

    # Messages

    for msg in session_obj.messages.order_by("created_at"):
        # Role header

        role_header = "## 👤 User" if msg.role == "user" else "## 🤖 Assistant"

        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")

        markdown_lines.append(f"{role_header}\n")

        markdown_lines.append(f"*{timestamp}*\n\n")

        markdown_lines.append(f"{msg.content}\n\n")

        markdown_lines.append("---\n\n")

    # Combine into single string
    markdown_content = "\n".join(markdown_lines)

    view_in_browser = request.GET.get("view") == "browser"
    format_pdf = request.GET.get("format") == "pdf"

    def _markdown_to_html(md):
        return markdown.markdown(md, extensions=["fenced_code", "tables", "nl2br"])

    def _inline_chart_images(html_str):
        """Replace /api/agent-chart/<id>/ img src with data URL from cache so PDF/export can embed charts."""
        pattern = re.compile(r'src="(/api/agent-chart/([^/]+)/)"')

        def repl(m):
            chart_id = m.group(2)
            png_bytes = cache.get(f"{CHART_CACHE_PREFIX}{chart_id}")
            if png_bytes is None:
                return m.group(0)
            b64 = base64.b64encode(png_bytes).decode("ascii")
            return f'src="data:image/png;base64,{b64}"'

        return pattern.sub(repl, html_str)

    export_html_styles = """
        body { max-width: 900px; margin: 2rem auto; padding: 0 2rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6; color: #333; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem; }
        h2 { color: #34495e; margin-top: 2rem; padding: 0.5rem; background: #f8f9fa; border-left: 4px solid #3498db; }
        hr { border: none; border-top: 1px solid #e0e0e0; margin: 2rem 0; }
        code { background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 3px; font-family: 'Monaco', 'Courier New', monospace; }
        pre { background: #f8f9fa; padding: 1rem; border-radius: 5px; overflow-x: auto; border: 1px solid #e0e0e0; }
        pre code { background: none; padding: 0; }
        em { color: #7f8c8d; font-size: 0.9rem; }
        strong { color: #2c3e50; }
        img { max-width: 100%; height: auto; }
        .download-link { position: fixed; top: 1rem; right: 1rem; padding: 0.5rem 1rem; background: #3498db; color: white;
            text-decoration: none; border-radius: 5px; font-size: 0.9rem; }
        .download-link:hover { background: #2980b9; }
        .download-links .download-link { position: static; margin-left: 0.5rem; }
    """

    if format_pdf:
        html_content = _markdown_to_html(markdown_content)
        html_content = _inline_chart_images(html_content)
        full_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><title>{session_title}</title><style>{export_html_styles}</style></head><body>{html_content}</body></html>"""
        try:
            from weasyprint import HTML

            pdf_bytes = HTML(string=full_html).write_pdf()
        except Exception as e:
            logger.warning("PDF export failed: %s", e)
            return JsonResponse({"error": "PDF generation failed"}, status=500)
        safe_title = (
            "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in session_title)
            .strip()
            .replace(" ", "_")[:50]
        )
        filename = f"session_{session_obj.pk}_{safe_title}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    if view_in_browser:
        html_content = _markdown_to_html(markdown_content)
        html_content = _inline_chart_images(html_content)
        full_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/><title>{session_title}</title><style>{export_html_styles}</style></head><body><div class="download-links"><a href="?view=download" class="download-link">Download as Markdown</a><a href="?format=pdf" class="download-link">Download as PDF</a></div>{html_content}</body></html>"""
        return HttpResponse(full_html, content_type="text/html; charset=utf-8")

    # Return as downloadable Markdown file

    safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in session_title)

    safe_title = safe_title.strip().replace(" ", "_")[:50]  # Limit length

    filename = f"session_{session_obj.pk}_{safe_title}.md"

    response = HttpResponse(markdown_content, content_type="text/markdown; charset=utf-8")

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
