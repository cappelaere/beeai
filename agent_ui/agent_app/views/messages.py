"""
Messages
2 functions
"""

import json
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods

from agent_app.models import ChatMessage

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


@require_http_methods(["POST"])
def message_feedback_api(request, message_id):
    """Store feedback for a message"""

    from django.utils import timezone

    message = get_object_or_404(ChatMessage, pk=message_id)

    # Only allow feedback on assistant messages

    if message.role != ChatMessage.ROLE_ASSISTANT:
        return JsonResponse({"error": "Feedback only allowed on assistant messages"}, status=400)

    try:
        body = json.loads(request.body)

        feedback_type = body.get("feedback")

        comment = body.get("comment", "")

        trace_id = body.get("trace_id")  # Optional Langfuse trace ID

    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if feedback_type not in [ChatMessage.FEEDBACK_POSITIVE, ChatMessage.FEEDBACK_NEGATIVE]:
        return JsonResponse({"error": "Invalid feedback type"}, status=400)

    # Store feedback

    message.feedback = feedback_type

    message.feedback_comment = comment

    message.feedback_at = timezone.now()

    message.save()

    # Log feedback to Langfuse if trace_id is provided

    if trace_id:
        try:
            import sys
            from pathlib import Path

            repo_root = Path(__file__).resolve().parent.parent.parent

            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))

            from observability import log_feedback

            score = 1.0 if feedback_type == ChatMessage.FEEDBACK_POSITIVE else 0.0

            log_feedback(trace_id, score, comment)

        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Failed to log feedback to Langfuse: {e}")

    return JsonResponse({"success": True})


@require_GET
def message_audio_api(request, message_id):
    """

    Get audio URL for a message (Section 508 TTS).

    Allows frontend to poll for audio once TTS synthesis is complete.

    """

    from agent_app.models import ChatMessage

    try:
        message = ChatMessage.objects.get(pk=message_id)

        return JsonResponse(
            {
                "message_id": message_id,
                "audio_url": message.audio_url,
                "has_audio": bool(message.audio_url),
                "content_preview": message.content[:100] if message.content else "",
            }
        )

    except ChatMessage.DoesNotExist:
        return JsonResponse({"error": "Message not found"}, status=404)
