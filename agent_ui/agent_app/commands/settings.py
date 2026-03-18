"""
/settings command handler - Manage user settings
"""


def _handle_settings_show(pref, default_508):
    """Show current settings."""
    current_508 = pref.section_508_enabled if pref.section_508_enabled is not None else default_508
    section_508_status = "enabled" if current_508 else "disabled"
    source = "(from environment)" if pref.section_508_enabled is None else "(custom)"
    return {
        "content": (
            "Current Settings:\n"
            f"  Agent: {pref.selected_agent}\n"
            f"  Model: {pref.selected_model}\n"
            f"  Section 508 Mode: {section_508_status} {source}\n"
            f"  Context Messages: {pref.context_message_count}\n"
            "\n"
            "To update:\n"
            "  /settings agent <value>\n"
            "  /settings model <value>\n"
            "  /settings 508 <on|off>\n"
            "  /settings context <number>"
        ),
        "metadata": {
            "command": "settings",
            "agent": pref.selected_agent,
            "model": pref.selected_model,
            "section_508": pref.section_508_enabled,
            "context_message_count": pref.context_message_count,
        },
    }


def _handle_settings_agent(value, pref):
    """Update default agent setting."""
    import sys
    from pathlib import Path

    _AGENT_UI_DIR = Path(__file__).resolve().parent.parent.parent
    if str(_AGENT_UI_DIR) not in sys.path:
        sys.path.insert(0, str(_AGENT_UI_DIR))

    from agent_runner import AVAILABLE_AGENTS

    if value not in AVAILABLE_AGENTS:
        available = ", ".join(AVAILABLE_AGENTS.keys())
        return {
            "content": f"Error: Unknown agent '{value}'\n\nAvailable: {available}",
            "metadata": {"error": True},
        }

    pref.selected_agent = value
    pref.save()

    return {
        "content": f"Updated default agent to: {value}",
        "metadata": {"command": "settings", "setting": "agent", "value": value},
    }


def _handle_settings_model(value, pref):
    """Update default model setting."""
    from agent_app.models import UserPreference

    available_models = [c[0] for c in UserPreference._meta.get_field("selected_model").choices]

    if value not in available_models:
        available = ", ".join(available_models)
        return {
            "content": f"Error: Unknown model '{value}'\n\nAvailable: {available}",
            "metadata": {"error": True},
        }

    pref.selected_model = value
    pref.save()

    return {
        "content": f"Updated default model to: {value}",
        "metadata": {"command": "settings", "setting": "model", "value": value},
    }


def _handle_settings_508(value, pref):
    """Toggle Section 508 accessibility mode."""
    value_lower = value.lower()

    if value_lower not in ["on", "off", "true", "false", "enabled", "disabled"]:
        return {
            "content": f"Error: Invalid value '{value}'\n\nUse: on, off, true, false, enabled, or disabled",
            "metadata": {"error": True},
        }

    enabled = value_lower in ["on", "true", "enabled"]
    pref.section_508_enabled = enabled
    pref.save()

    status = "enabled" if enabled else "disabled"
    return {
        "content": (
            f"Section 508 accessibility mode: {status}\n\n"
            f"Features {'enabled' if enabled else 'disabled'}:\n"
            f"  - Text-to-speech integration\n"
            f"  - Screen reader optimizations\n"
            f"  - High contrast mode\n"
            f"  - Keyboard navigation enhancements\n"
            f"  - ARIA labels and landmarks"
        ),
        "metadata": {"command": "settings", "setting": "508", "value": enabled, "reload_ui": True},
    }


def _handle_settings_context(value, pref):
    """Set context message count."""
    try:
        count = int(value)
        if count < 0 or count > 50:
            raise ValueError("Out of range")
    except (ValueError, TypeError):
        return {
            "content": f"Error: Invalid value '{value}'\n\nMust be a number between 0 and 50",
            "metadata": {"error": True},
        }

    pref.context_message_count = count
    pref.save()

    if count == 0:
        message = "Context disabled. Each prompt will be independent."
    else:
        message = f"Context set to {count} messages. Previous conversation will be included."

    return {
        "content": (
            f"Context Messages: {count}\n\n"
            f"{message}\n\n"
            f"This controls how many previous messages from the current session\n"
            f"are sent to the agent for context. Higher values provide more memory\n"
            f"but increase token usage and response time.\n\n"
            f"Recommended:\n"
            f"  0 = No context (fastest, lowest cost)\n"
            f"  10-20 = Good balance\n"
            f"  50 = Maximum memory (slower, higher cost)"
        ),
        "metadata": {"command": "settings", "setting": "context", "value": count},
    }


def handle_settings(request, args, session_key):
    """
    Handle settings-related commands.

    Commands:
        /settings - Show current settings
        /settings agent <value> - Update default agent
        /settings model <value> - Update default model
        /settings 508 <on|off> - Toggle Section 508 mode
        /settings context <number> - Set context message count (0-50)

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    import os

    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.models import UserPreference

    default_508 = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    pref, created = UserPreference.objects.get_or_create(
        user_id=user_id,
        defaults={
            "session_key": session_key,
            "selected_agent": "gres",
            "selected_model": "claude-3-5-sonnet",
            "section_508_enabled": None,
        },
    )

    if not args:
        return _handle_settings_show(pref, default_508)

    if len(args) < 2:
        return {
            "content": "Usage: /settings <agent|model|508> <value>",
            "metadata": {"error": True},
        }

    setting = args[0].lower()
    value = args[1]

    if setting == "agent":
        return _handle_settings_agent(value, pref)

    if setting == "model":
        return _handle_settings_model(value, pref)

    if setting == "508":
        return _handle_settings_508(value, pref)

    if setting == "context":
        return _handle_settings_context(value, pref)

    return {
        "content": f"Error: Unknown setting '{setting}'\n\nAvailable: agent, model, 508, context",
        "metadata": {"error": True},
    }
