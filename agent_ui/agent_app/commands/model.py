"""
/model command handler - Manage model selection
"""


def handle_model(request, args, session_key):
    """
    Handle model-related commands.

    Commands:
        /model - Show current model
        /model <name> - Switch to model

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.models import UserPreference

    # Get user_id from session
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Get or create user preference
    pref, _ = UserPreference.objects.get_or_create(
        user_id=user_id,
        defaults={"session_key": session_key, "selected_model": "claude-3-5-sonnet"},
    )

    if not args:
        # Show current model
        return {
            "content": f"Current model: {pref.selected_model}",
            "metadata": {"command": "model", "current": pref.selected_model},
        }

    # Switch model
    model_key = args[0]

    # Get available model choices from the model field
    available_models = [
        choice[0] for choice in UserPreference._meta.get_field("selected_model").choices
    ]

    if model_key not in available_models:
        available = ", ".join(available_models)
        return {
            "content": f"Error: Unknown model '{model_key}'\n\nAvailable models: {available}",
            "metadata": {"error": True, "command": "model switch"},
        }

    pref.selected_model = model_key
    pref.save()

    return {
        "content": f"Switched to model: {model_key}",
        "metadata": {"command": "model switch", "model": model_key},
    }
