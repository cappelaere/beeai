"""
Notification preference tools for Flo – get/set notify on workflow complete and daily digest.
"""

import os

from asgiref.sync import sync_to_async
from beeai_framework.tools import StringToolOutput, tool


def _setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")
    import django

    if not django.apps.apps.ready:
        django.setup()


def _get_user_id():
    return int(os.environ.get("USER_ID", 9))


_DEFAULTS = {"notify_on_workflow_complete": False, "daily_digest": False}


@tool
async def get_notification_preferences(user_id: int | None = None) -> StringToolOutput:
    """
    Get the current user's notification preferences (workflow complete, daily digest).

    Args:
        user_id: User ID (defaults to current user from environment).

    Returns notify_on_workflow_complete and daily_digest (booleans).
    Use when the user asks "what are my notification settings?" or "am I notified when workflows complete?".
    """
    try:
        _setup_django()
        from agent_app.models import UserPreference

        uid = user_id if user_id is not None else _get_user_id()

        def get_prefs():
            pref = UserPreference.objects.filter(user_id=uid).first()
            if not pref or not getattr(pref, "notification_preferences", None):
                return {**_DEFAULTS, "message": "Using defaults (no preferences set)."}
            np = pref.notification_preferences or {}
            return {
                "notify_on_workflow_complete": np.get(
                    "notify_on_workflow_complete", _DEFAULTS["notify_on_workflow_complete"]
                ),
                "daily_digest": np.get("daily_digest", _DEFAULTS["daily_digest"]),
            }

        result = await sync_to_async(get_prefs, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to get notification preferences: {str(e)}"}))


@tool
async def set_notification_preferences(
    notify_on_workflow_complete: bool | None = None,
    daily_digest: bool | None = None,
    user_id: int | None = None,
) -> StringToolOutput:
    """
    Update the current user's notification preferences.

    Args:
        notify_on_workflow_complete: If True, user is notified when a workflow completes or fails.
        daily_digest: If True, user receives a daily digest of pending tasks (if implemented).
        user_id: User ID (defaults to current user from environment).

    Use when the user says "notify me when workflows complete", "turn on daily digest", etc.
    """
    try:
        _setup_django()
        from agent_app.models import UserPreference

        uid = user_id if user_id is not None else _get_user_id()

        def set_prefs():
            pref = UserPreference.objects.filter(user_id=uid).first()
            if not pref:
                pref = UserPreference.objects.create(user_id=uid, session_key="")
            np = dict(getattr(pref, "notification_preferences", None) or _DEFAULTS)
            if notify_on_workflow_complete is not None:
                np["notify_on_workflow_complete"] = bool(notify_on_workflow_complete)
            if daily_digest is not None:
                np["daily_digest"] = bool(daily_digest)
            pref.notification_preferences = np
            pref.save()
            return {"success": True, "notification_preferences": np}

        result = await sync_to_async(set_prefs, thread_sensitive=False)()
        return StringToolOutput(str(result))
    except Exception as e:
        return StringToolOutput(str({"error": f"Failed to set notification preferences: {str(e)}"}))
