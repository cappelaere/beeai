"""
Chat Views
Main chat interface view.
"""

import json
import os

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from agent_app.constants import ANONYMOUS_USER_ID
from agent_app.models import AssistantCard, UserPreference


@ensure_csrf_cookie
def chat_view(request):
    """Display chat interface with favorite cards"""
    # Initialize user_id from environment variable on first visit
    if "user_id" not in request.session:
        env_user_id = os.environ.get("USER_ID")
        if env_user_id:
            request.session["user_id"] = int(env_user_id)
        else:
            # Fallback to 9 if not set
            request.session["user_id"] = 9

    if "user_role" not in request.session:
        # Default role based on user_id (can be made configurable later)
        request.session["user_role"] = "admin"  # Default to admin for testing

    # Get agent from query parameter, default to 'gres'
    agent_type = request.GET.get("agent", "gres")

    # Show ALL favorite cards on homepage, regardless of agent selection
    # Users can use any card with any agent
    favorite_cards = list(
        AssistantCard.objects.filter(is_favorite=True)
        .order_by("agent_type", "name")
        .values("id", "name", "description", "prompt", "is_favorite", "agent_type")
    )
    favorite_cards_json = json.dumps(favorite_cards)

    # Get favorite workflows
    from agent_app.workflow_registry import workflow_registry

    favorite_workflows = []
    try:
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key
        user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

        user_pref = UserPreference.objects.filter(session_key=session_key, user_id=user_id).first()

        if user_pref and user_pref.favorite_workflows:
            favorite_workflow_ids = json.loads(user_pref.favorite_workflows or "[]")
            all_workflows = workflow_registry.get_all()

            for workflow_meta in all_workflows:
                if workflow_meta.id in favorite_workflow_ids:
                    favorite_workflows.append(
                        {
                            "id": workflow_meta.id,
                            "name": workflow_meta.name,
                            "description": workflow_meta.description,
                            "icon": workflow_meta.icon,
                            "category": workflow_meta.category,
                            "estimated_duration": workflow_meta.estimated_duration,
                        }
                    )
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error loading favorite workflows: {e}")

    favorite_workflows_json = json.dumps(favorite_workflows)

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
