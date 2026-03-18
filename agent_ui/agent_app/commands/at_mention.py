"""
@Agent mention handler - One-shot agent routing
"""

import sys
from pathlib import Path

# Add agent_ui directory to path for imports
_AGENT_UI_DIR = Path(__file__).resolve().parent.parent.parent
if str(_AGENT_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_UI_DIR))


def handle_at_mention(request, agent_name, message_text, session_key):
    """
    Handle @Agent mentions for one-shot routing.

    Routes the message to the specified agent without changing the user's
    default agent preference. After processing, the default agent is restored.

    Args:
        request: Django HTTP request
        agent_name: Name of the agent (e.g., 'library', 'sam')
        message_text: The message text after the @Agent mention
        session_key: User session key

    Returns:
        Dictionary with override_agent and message, or error
    """
    from agent_runner import AVAILABLE_AGENTS

    # Validate agent exists
    agent_key = agent_name.lower()
    if agent_key not in AVAILABLE_AGENTS:
        available = ", ".join(AVAILABLE_AGENTS.keys())
        return {
            "content": f"Error: Unknown agent @{agent_name}\n\nAvailable agents: {available}",
            "metadata": {"error": True, "command": "at_mention"},
        }

    # Return special marker to indicate agent override for this message only
    return {
        "override_agent": agent_key,
        "message": message_text,
        "metadata": {"command": "at_mention", "agent": agent_key},
    }
