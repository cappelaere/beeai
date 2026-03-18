"""
/agent command handler - Manage agent selection
"""

import sys
from pathlib import Path

# Add agent_ui directory to path for imports
_AGENT_UI_DIR = Path(__file__).resolve().parent.parent.parent
if str(_AGENT_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_UI_DIR))


def handle_agent(request, args, session_key):
    """
    Handle agent-related commands.

    Commands:
        /agent - Show current agent
        /agent list - List all agents
        /agent <name> - Switch to agent
        /agent tools - Show agent's tools

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    from agent_runner import AVAILABLE_AGENTS

    from agent_app.constants import ANONYMOUS_USER_ID
    from agent_app.models import UserPreference

    # Get user_id from session
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    # Get or create user preference
    pref, _ = UserPreference.objects.get_or_create(
        user_id=user_id, defaults={"session_key": session_key, "selected_agent": "gres"}
    )

    if not args:
        # Show current agent
        agent_config = AVAILABLE_AGENTS.get(pref.selected_agent)
        if agent_config:
            return {
                "content": f"Current agent: {agent_config.icon} {agent_config.name}",
                "metadata": {"command": "agent", "current": pref.selected_agent},
            }
        return {
            "content": f"Current agent: {pref.selected_agent} (config not found)",
            "metadata": {"command": "agent", "current": pref.selected_agent},
        }

    if args[0] == "list":
        # List all agents
        lines = ["Available agents:"]
        for key, config in AVAILABLE_AGENTS.items():
            current = "(*)" if key == pref.selected_agent else "   "
            lines.append(f"{current} {config.icon} {key} - {config.description}")
        return {"content": "\n".join(lines), "metadata": {"command": "agent list"}}

    if args[0] == "tools":
        # Show tools for current agent
        from tools.list_tools import get_tools_list

        tools = get_tools_list(pref.selected_agent)
        lines = [f"Tools for {pref.selected_agent}:"]
        for name, desc in tools:
            lines.append(f"  - {name}: {desc[:80]}...")
        return {
            "content": "\n".join(lines),
            "metadata": {"command": "agent tools", "agent": pref.selected_agent},
        }

    # Switch agent
    agent_key = args[0].lower()
    if agent_key not in AVAILABLE_AGENTS:
        available = ", ".join(AVAILABLE_AGENTS.keys())
        return {
            "content": f"Error: Unknown agent '{agent_key}'\n\nAvailable agents: {available}",
            "metadata": {"error": True, "command": "agent switch"},
        }

    pref.selected_agent = agent_key
    pref.save()

    config = AVAILABLE_AGENTS[agent_key]
    return {
        "content": f"Switched to: {config.icon} {config.name}",
        "metadata": {"command": "agent switch", "agent": agent_key},
    }
