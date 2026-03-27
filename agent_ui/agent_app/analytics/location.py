"""
Location resolution for analytics capture (no IP storage).
"""

from __future__ import annotations

from django.conf import settings

from .constants import DEFAULT_LOCATION_HEADER_MAP, MAX_LOCATION_VALUE_LENGTH


def _clean_location_value(value: str | None) -> str:
    return (value or "").strip()[:MAX_LOCATION_VALUE_LENGTH]


def _get_header(request, header_name: str) -> str:
    # Django uses HTTP_ prefix in request.META for incoming headers.
    meta_key = "HTTP_" + header_name.upper().replace("-", "_")
    return _clean_location_value(request.META.get(meta_key))


def _resolve_from_proxy_headers(request) -> dict[str, str]:
    header_map = getattr(settings, "WEBSITE_ANALYTICS_LOCATION_HEADER_MAP", DEFAULT_LOCATION_HEADER_MAP)
    country = ""
    state = ""
    city = ""

    for header in header_map.get("country", ()):
        country = _get_header(request, header)
        if country:
            break
    for header in header_map.get("state", ()):
        state = _get_header(request, header)
        if state:
            break
    for header in header_map.get("city", ()):
        city = _get_header(request, header)
        if city:
            break

    return {"city": city, "state": state, "country": country}


def _resolve_from_client_session(request) -> dict[str, str]:
    if not hasattr(request, "session"):
        return {"city": "", "state": "", "country": ""}
    payload = request.session.get("analytics_client_location") or {}
    return {
        "city": _clean_location_value(payload.get("city")),
        "state": _clean_location_value(payload.get("state")),
        "country": _clean_location_value(payload.get("country")),
    }


def resolve_location(request) -> dict[str, str]:
    """
    Resolve location fields using proxy headers first, then client-provided fallback.
    """
    proxy = _resolve_from_proxy_headers(request)
    if any(proxy.values()):
        return {**proxy, "source": "proxy_header"}

    client = _resolve_from_client_session(request)
    if any(client.values()):
        return {**client, "source": "client"}

    return {"city": "", "state": "", "country": "", "source": "unknown"}

