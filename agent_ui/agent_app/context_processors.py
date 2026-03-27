"""
Context processors to add variables to all templates
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

from agent_app.constants import ANONYMOUS_USER_ID
from agents.base import get_model_options_for_template
from agents.registry import get_agents_for_template


def observability_settings(request):
    """Add observability settings to all templates."""
    # Get Langfuse dashboard URL from environment
    langfuse_url = os.getenv("OBSERVABILITY_DASHBOARD", "")
    langfuse_enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

    return {
        "OBSERVABILITY_ENABLED": os.getenv("OBSERVABILITY_ENABLED", "false").lower() == "true",
        "LANGSMITH_ENABLED": os.getenv("LANGSMITH_ENABLED", "false").lower() == "true",
        "LANGFUSE_ENABLED": langfuse_enabled,
        "langfuse_dashboard_url": langfuse_url if langfuse_enabled and langfuse_url else None,
    }


def version_info(request):
    """Add version information to all templates."""
    try:
        version_file = Path(__file__).resolve().parent.parent.parent / "VERSION"
        version = version_file.read_text().strip() if version_file.exists() else "1.0.0"
    except Exception:
        version = "1.0.0"

    return {"APP_VERSION": version}


def section_508_settings(request):
    """Add Section 508 accessibility settings to all templates."""
    from agent_app.models import UserPreference

    # Get default from environment
    default_enabled = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")

    # Get user-specific preference if logged in
    section_508_enabled = default_enabled

    user_id = request.session.get("user_id")
    if user_id:
        try:
            pref = UserPreference.objects.filter(user_id=user_id).first()
            if pref and pref.section_508_enabled is not None:
                # Use user preference if explicitly set, otherwise use default
                section_508_enabled = pref.section_508_enabled
        except Exception as e:
            logger.debug("Could not load Section 508 preference for user %s: %s", user_id, e)

    return {"SECTION_508_ENABLED": section_508_enabled, "SECTION_508_DEFAULT": default_enabled}


def model_choices(request):
    """Add available model choices to all templates (single source of truth)."""
    return {"AVAILABLE_MODELS": get_model_options_for_template()}


def agent_choices(request):
    """Add available agent choices to all templates (single source of truth)."""
    return {"AVAILABLE_AGENTS": get_agents_for_template()}


def user_context(request):
    """Add user information to all templates."""
    return {
        "user_role": request.session.get("user_role", "user"),
        "user_id": request.session.get("user_id", ANONYMOUS_USER_ID),
    }
