"""
Analytics-specific API views.
"""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .constants import MAX_LOCATION_VALUE_LENGTH


def _clean(value: object) -> str:
    return str(value or "").strip()[:MAX_LOCATION_VALUE_LENGTH]


@require_POST
@csrf_protect
def analytics_location_api(request: HttpRequest) -> JsonResponse:
    """
    Store client-provided location fallback in session.
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    if not hasattr(request, "session"):
        return JsonResponse({"ok": False, "error": "session_required"}, status=400)

    request.session["analytics_client_location"] = {
        "city": _clean(payload.get("city")),
        "state": _clean(payload.get("state")),
        "country": _clean(payload.get("country")),
    }
    return JsonResponse({"ok": True})
