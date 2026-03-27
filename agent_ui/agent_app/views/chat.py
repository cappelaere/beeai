"""
Chat Views
Main chat interface view.
"""

import json
import logging
import os
from typing import Any

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import AssistantCard, UserPreference

logger = logging.getLogger(__name__)


def _initialize_session_defaults(request) -> None:
    """Set required session defaults once per session."""
    if "user_id" not in request.session:
        env_user_id = os.environ.get("USER_ID")
        request.session["user_id"] = int(env_user_id) if env_user_id else 9
    if "user_role" not in request.session:
        request.session["user_role"] = "admin"


def _load_favorite_cards() -> list[dict[str, Any]]:
    """Load favorite assistant cards for homepage display."""
    return list(
        AssistantCard.objects.filter(is_favorite=True)
        .order_by("agent_type", "name")
        .values("id", "name", "description", "prompt", "is_favorite", "agent_type")
    )


def _build_favorite_workflows(request) -> list[dict[str, Any]]:
    """Build favorite workflow cards based on stored user preferences."""
    from agent_app.workflow_registry import workflow_registry

    session_key = request.session.session_key
    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)
    if not session_key:
        return []

    user_pref = UserPreference.objects.filter(session_key=session_key, user_id=user_id).first()
    if not user_pref or not user_pref.favorite_workflows:
        return []

    favorite_ids = set(json.loads(user_pref.favorite_workflows or "[]"))
    workflows: list[dict[str, Any]] = []
    for workflow_meta in workflow_registry.get_all():
        if workflow_meta.id in favorite_ids:
            workflows.append(
                {
                    "id": workflow_meta.id,
                    "name": workflow_meta.name,
                    "description": workflow_meta.description,
                    "icon": workflow_meta.icon,
                    "category": workflow_meta.category,
                    "estimated_duration": workflow_meta.estimated_duration,
                }
            )
    return workflows


@ensure_csrf_cookie
def chat_view(request):
    """Display chat interface with favorite cards"""
    _initialize_session_defaults(request)

    # Get agent from query parameter, default to 'gres'
    agent_type = request.GET.get("agent", "gres")

    favorite_cards: list[dict[str, Any]] = []
    favorite_cards_json = "[]"
    favorite_workflows: list[dict[str, Any]] = []
    favorite_workflows_json = "[]"

    try:
        # Keep DB reads in a single guarded block so lock errors do not 500 the homepage.
        favorite_cards = _load_favorite_cards()
        favorite_cards_json = json.dumps(favorite_cards)
        favorite_workflows = _build_favorite_workflows(request)
        favorite_workflows_json = json.dumps(favorite_workflows)
    except Exception as e:
        logger.error("Error loading chat favorites (cards/workflows): %s", e, exc_info=True)

    return render(
        request,
        "chat.html",
        {
            "favorite_cards": favorite_cards,
            "favorite_cards_json": favorite_cards_json,
            "favorite_workflows_json": favorite_workflows_json,
            "selected_agent": agent_type,
        },
    )
