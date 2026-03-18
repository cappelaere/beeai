"""
Api System
4 functions
"""

import json
import logging
import os

from django.http import JsonResponse

from agent_app.constants import ANONYMOUS_USER_ID
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

logger = logging.getLogger(__name__)

# Updated: 2026-02-21 - Added agent/workflow folder deletion and integrity validation


@require_GET
def cache_stats_api(request):
    """Get Redis cache statistics"""

    try:
        import logging

        logger = logging.getLogger(__name__)

        # Import cache

        try:
            from cache import get_cache_stats

            stats = get_cache_stats()

            return JsonResponse(stats)

        except ModuleNotFoundError:
            logger.warning("Cache module not available")

            return JsonResponse({"enabled": False, "message": "Cache not configured"})

    except Exception:
        from agent_app.http_utils import json_response_500

        return json_response_500("Error getting cache stats")


@require_POST
@csrf_exempt
@require_POST
@csrf_exempt
def cache_clear_api(request):
    """Clear Redis cache"""

    try:
        import logging

        logger = logging.getLogger(__name__)

        # Import cache

        try:
            from cache import get_cache

            cache = get_cache()

            if not cache.enabled:
                return JsonResponse({"success": False, "message": "Cache is not enabled"})

            # Clear all cached responses

            cache.clear_all()

            # Get updated stats

            stats = cache.get_stats()

            return JsonResponse(
                {"success": True, "message": "Cache cleared successfully", "stats": stats}
            )

        except ModuleNotFoundError:
            logger.warning("Cache module not available")

            return JsonResponse({"success": False, "message": "Cache not configured"})

    except Exception:
        from agent_app.http_utils import json_response_500

        return json_response_500("Error clearing cache")


@require_http_methods(["GET", "POST"])
def section_508_api(request):
    """Get or update Section 508 accessibility mode preference"""

    from agent_app.models import UserPreference

    # Get or create session

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    # Get default from environment

    default_enabled = os.getenv("SECTION_508_MODE", "false").lower() in ("true", "1", "yes")

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    if request.method == "GET":
        # Get current setting

        pref = UserPreference.objects.filter(user_id=user_id).first()

        # Use user preference if explicitly set, otherwise use environment default

        if pref and pref.section_508_enabled is not None:
            enabled = pref.section_508_enabled

        else:
            enabled = default_enabled

        return JsonResponse({"section_508_enabled": enabled, "default": default_enabled})

    if request.method == "POST":
        # Update setting

        try:
            body = json.loads(request.body)

            enabled = body.get("enabled", default_enabled)

            pref, created = UserPreference.objects.get_or_create(
                user_id=user_id,
                defaults={"session_key": session_key, "section_508_enabled": enabled},
            )

            if not created:
                pref.section_508_enabled = enabled

                pref.save()

            return JsonResponse(
                {
                    "success": True,
                    "section_508_enabled": enabled,
                    "message": f"Section 508 mode {'enabled' if enabled else 'disabled'}",
                }
            )

        except Exception as e:
            logger.exception("Section 508 API update failed: %s", e)
            return JsonResponse({"success": False, "error": "Invalid request."}, status=400)
    return None


@require_http_methods(["GET", "POST"])
@csrf_exempt
def context_settings_api(request):
    """Get or update context message count preference"""

    from agent_app.models import UserPreference

    # Get or create session

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    user_id = request.session.get("user_id", ANONYMOUS_USER_ID)

    if request.method == "GET":
        # Get current setting (same row as POST via get_or_create)
        pref, _ = UserPreference.objects.get_or_create(
            user_id=user_id,
            defaults={"session_key": session_key, "context_message_count": 0},
        )
        return JsonResponse({"context_message_count": pref.context_message_count})

    if request.method == "POST":
        # Update setting

        try:
            body = json.loads(request.body)

            raw = body.get("context_message_count", 0)
            try:
                context_count = int(raw) if raw not in (None, "") else 0
            except (TypeError, ValueError):
                context_count = 0

            # Validate
            if context_count < 0:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "context_message_count must be a non-negative integer",
                    },
                    status=400,
                )

            if context_count > 50:
                return JsonResponse(
                    {"success": False, "error": "context_message_count cannot exceed 50"},
                    status=400,
                )

            pref, created = UserPreference.objects.get_or_create(
                user_id=user_id,
                defaults={"session_key": session_key, "context_message_count": context_count},
            )

            if not created:
                pref.context_message_count = context_count

                pref.save()

            return JsonResponse(
                {
                    "success": True,
                    "context_message_count": context_count,
                    "message": f"Context set to {context_count} messages",
                }
            )

        except Exception as e:
            logger.exception("Context settings API update failed: %s", e)
            return JsonResponse({"success": False, "error": "Invalid request."}, status=400)
    return None
