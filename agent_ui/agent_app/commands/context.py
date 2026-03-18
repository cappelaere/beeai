"""
/context command handler - Manage session context
"""


def handle_context(request, args, session_key):
    """
    Handle context-related commands.

    Commands:
        /context - Show current session context
        /context clear - Clear session context

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.models import ChatMessage, ChatSession, UserPreference

    # Get user_id from session
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    if not args:
        # Get current session for this user
        session = ChatSession.objects.filter(user_id=user_id).order_by("-created_at").first()

        if not session:
            return {
                "content": "No active session. Start a conversation to create one.",
                "metadata": {"command": "context", "count": 0},
            }

        # Get user's context message count setting
        pref = UserPreference.objects.filter(user_id=user_id).first()
        context_count = pref.context_message_count if pref else 0

        if context_count == 0:
            return {
                "content": "Context is disabled (set to 0 messages). Use settings to enable context.",
                "metadata": {"command": "context", "count": 0, "context_setting": 0},
            }

        # Show current context using user's setting
        messages = ChatMessage.objects.filter(session_id=session.id).order_by("-created_at")[
            :context_count
        ]

        if not messages:
            return {
                "content": "Session context is empty.",
                "metadata": {"command": "context", "count": 0, "context_setting": context_count},
            }

        lines = [f"Session context ({messages.count()} of {context_count} messages):"]
        lines.append("")

        # Reverse to show oldest first
        for msg in reversed(list(messages)):
            role_icon = "👤" if msg.role == "user" else "🤖"
            preview = msg.content[:60]
            if len(msg.content) > 60:
                preview += "..."
            timestamp = msg.created_at.strftime("%H:%M")
            lines.append(f"{timestamp} {role_icon} {preview}")

        lines.append("")
        lines.append(f"💡 Context setting: {context_count} messages (change in /settings)")

        return {
            "content": "\n".join(lines),
            "metadata": {
                "command": "context",
                "count": messages.count(),
                "context_setting": context_count,
            },
        }

    if args[0] == "clear":
        # Get current session for this user
        session = ChatSession.objects.filter(user_id=user_id).order_by("-created_at").first()

        if not session:
            return {
                "content": "No active session to clear.",
                "metadata": {"command": "context clear", "count": 0},
            }

        # Clear session context
        count = ChatMessage.objects.filter(session_id=session.id).count()
        ChatMessage.objects.filter(session_id=session.id).delete()

        return {
            "content": f"Cleared {count} messages from session context.",
            "metadata": {"command": "context clear", "count": count},
        }

    return {
        "content": "Usage: /context or /context clear",
        "metadata": {"error": True, "command": "context"},
    }
