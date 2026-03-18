"""
Agents
3 functions
"""

import logging

from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


def agents_list(request):
    """Display list of all available agents as cards."""

    from agents.registry import load_agents_registry

    registry = load_agents_registry()

    # Convert registry to list of agent objects with metadata

    agents = []

    for agent_id, metadata in registry.items():
        agents.append(
            {
                "id": agent_id,
                "name": metadata["name"],
                "display_name": metadata["display_name"],
                "icon": metadata["icon"],
                "description": metadata["description"],
                "default": metadata.get("default", False),
            }
        )

    # Sort agents: default first, then alphabetically

    agents.sort(key=lambda a: (not a["default"], a["name"]))

    # Get user role from session

    user_role = request.session.get("user_role", "user")

    return render(request, "agents/list.html", {"agents": agents, "user_role": user_role})


def agent_studio(request):
    """Display the agent studio page for creating new agents (admin only)."""

    # Check if user is admin

    user_role = request.session.get("user_role", "user")

    if user_role != "admin":
        return redirect("agents_list")

    return render(request, "agents/studio.html")


def agent_detail(request, agent_id):
    """Display detailed information about a specific agent including skills."""

    import logging

    import markdown

    from agents.registry import get_agent_metadata, get_agent_skills_path

    logger = logging.getLogger(__name__)

    try:
        # Get agent metadata

        metadata = get_agent_metadata(agent_id)

        # Load and convert skills markdown to HTML

        skills_html = None

        skills_path = get_agent_skills_path(agent_id)

        if skills_path and skills_path.exists():
            try:
                with open(skills_path, encoding="utf-8") as f:
                    skills_md = f.read()

                    # Convert markdown to HTML with extensions

                    skills_html = markdown.markdown(
                        skills_md, extensions=["fenced_code", "tables", "toc", "codehilite"]
                    )

            except Exception as e:
                logger.error(f"Error reading skills file for {agent_id}: {e}")

                skills_html = f"<p>Error loading skills documentation: {e}</p>"

        agent = {
            "id": agent_id,
            "name": metadata["name"],
            "display_name": metadata["display_name"],
            "icon": metadata["icon"],
            "description": metadata["description"],
            "config_module": metadata["config_module"],
            "config_name": metadata["config_name"],
            "default": metadata.get("default", False),
            "skills_html": skills_html,
            "has_skills": skills_html is not None,
        }

        return render(request, "agents/detail.html", {"agent": agent})

    except KeyError:
        from django.http import Http404

        raise Http404(f"Agent '{agent_id}' not found")
