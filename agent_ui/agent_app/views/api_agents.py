"""
Api Agents
4 functions — delegate to agent_registry_service; map domain exceptions to HTTP.
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from agent_app.exceptions import AgentNotFoundError, ConflictError, ValidationError
from agent_app.http_utils import json_response_500

logger = logging.getLogger(__name__)


def _require_admin(request):
    """Return 403 JsonResponse if not admin; else None."""
    if request.session.get("user_role", "user") != "admin":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)
    return None


@require_POST
def agent_set_default(request, agent_id):
    """Set an agent as the default agent (admin only)."""
    if resp := _require_admin(request):
        return resp
    try:
        from agent_app.services.agent_registry_service import set_default_agent

        set_default_agent(agent_id)
        return JsonResponse({"success": True})
    except AgentNotFoundError:
        return JsonResponse({"success": False, "error": "Agent not found"}, status=404)
    except (FileNotFoundError, OSError):
        return json_response_500("Agent set default failed", agent_id=agent_id)
    except Exception:
        return json_response_500("Agent set default failed", agent_id=agent_id)


@require_POST
def agent_update(request, agent_id):
    """Update agent metadata (admin only)."""
    if resp := _require_admin(request):
        return resp
    try:
        data = json.loads(request.body)
        name = data.get("name")
        description = data.get("description")
        from agent_app.services.agent_registry_service import update_agent_metadata

        update_agent_metadata(agent_id, name, description)
        return JsonResponse({"success": True})
    except ValidationError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except AgentNotFoundError:
        return JsonResponse({"success": False, "error": "Agent not found"}, status=404)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return json_response_500("Agent update failed", agent_id=agent_id)


@require_POST
def agent_create(request):
    """Create a new agent with AI-generated SKILLS.md (admin only)."""
    if resp := _require_admin(request):
        return resp
    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        agent_id = data.get("agent_id", "").strip()
        icon = data.get("icon", "").strip()
        description = data.get("description", "").strip()
        prompt = data.get("prompt", "").strip()

        skills_content = None
        try:
            from agents.base import get_llm_client

            client = get_llm_client()
            skills_generation_prompt = f"""Generate a comprehensive SKILLS.md file for a new AI agent with the following specifications:

Agent Name: {name}
Agent ID: {agent_id}
Description: {description}

User Requirements:
{prompt}

Create a detailed SKILLS.md file that includes:
1. Agent overview and purpose
2. Core capabilities and expertise areas
3. Available tools and how to use them
4. Best practices and guidelines
5. Example usage scenarios
6. Limitations and constraints

Format the output as a professional markdown document suitable for technical documentation.
Start with a # heading with the agent name, followed by well-structured sections."""
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": skills_generation_prompt}],
            )
            skills_content = response.content[0].text
        except Exception as e:
            logger.exception("Failed to generate SKILLS.md: %s", e)
            skills_content = None

        from agent_app.services.agent_registry_service import create_agent

        create_agent(
            agent_id=agent_id,
            name=name,
            description=description,
            icon=icon,
            prompt=prompt,
            skills_content=skills_content,
        )
        return JsonResponse({"success": True, "agent_id": agent_id})
    except ValidationError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return json_response_500("Error creating agent")
    except Exception:
        return json_response_500("Error creating agent")


@require_POST
def agent_remove(request, agent_id):
    """Remove an agent from the registry and delete its folder (admin only)."""
    if resp := _require_admin(request):
        return resp
    try:
        from agent_app.services.agent_registry_service import remove_agent

        remove_agent(agent_id)
        return JsonResponse({"success": True})
    except AgentNotFoundError:
        return JsonResponse({"success": False, "error": "Agent not found"}, status=404)
    except ConflictError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except (FileNotFoundError, OSError):
        return json_response_500("Agent remove failed", agent_id=agent_id)
    except Exception:
        return json_response_500("Agent remove failed", agent_id=agent_id)
