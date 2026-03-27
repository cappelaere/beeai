"""
Service helpers for analytics event capture.
"""

from __future__ import annotations

import hashlib
import logging
from urllib.parse import urlsplit

from django.conf import settings

from .constants import DEFAULT_ANALYTICS_EXCLUDED_PATH_PREFIXES, SENSITIVE_QUERY_PARAM_DENYLIST
from .location import resolve_location
from .models import PageViewEvent, TrackedPage
from .query_filter import build_filtered_query_params

logger = logging.getLogger(__name__)


def canonicalize_path(path: str) -> str:
    cleaned = (path or "").strip() or "/"
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    if cleaned != "/" and cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned


def should_consider_request_for_pageview(request, response) -> bool:
    if not getattr(settings, "WEBSITE_ANALYTICS_ENABLED", True):
        return False
    if request.method != "GET":
        return False

    status_code = getattr(response, "status_code", 500)
    if status_code >= 400:
        return False

    path = canonicalize_path(request.path)
    excluded_prefixes = getattr(
        settings, "WEBSITE_ANALYTICS_EXCLUDED_PATH_PREFIXES", DEFAULT_ANALYTICS_EXCLUDED_PATH_PREFIXES
    )
    if any(path.startswith(prefix) for prefix in excluded_prefixes):
        return False

    content_type = str(response.get("Content-Type", ""))
    return content_type.startswith("text/html")


def _session_key_hash(request) -> str:
    session_key = ""
    if hasattr(request, "session"):
        session_key = request.session.session_key or ""
    if not session_key:
        return ""
    return hashlib.sha256(session_key.encode("utf-8")).hexdigest()


def _visitor_id(request, session_key_hash: str) -> str:
    if hasattr(request, "session"):
        existing = request.session.get("analytics_visitor_id", "")
        if existing:
            return str(existing)
        if session_key_hash:
            # Keep deterministic visitor id for the session (no raw session key storage).
            visitor_id = session_key_hash[:20]
            request.session["analytics_visitor_id"] = visitor_id
            return visitor_id
    return ""


def _auth_and_app_user_id(request) -> tuple[object | None, int | None]:
    auth_user = None
    if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
        auth_user = request.user

    app_user_id = None
    if hasattr(request, "session"):
        user_id = request.session.get("user_id")
        if user_id is not None:
            try:
                app_user_id = int(user_id)
            except (TypeError, ValueError):
                app_user_id = None
    return auth_user, app_user_id


def _get_tracked_page(path: str) -> TrackedPage | None:
    return (
        TrackedPage.objects.filter(canonical_path=path, enabled=True)
        .prefetch_related("allowed_query_params")
        .first()
    )


def _filtered_referrer(request) -> str:
    referrer = str(request.META.get("HTTP_REFERER", "") or "")
    if not referrer:
        return ""
    parsed = urlsplit(referrer)
    # Drop query and fragment from referrer for privacy.
    sanitized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return sanitized[:512]


def create_page_view_event(request) -> PageViewEvent | None:
    canonical_path = canonicalize_path(request.path)
    tracked_page = _get_tracked_page(canonical_path)
    if tracked_page is None:
        return None

    allowlist = [item.param_name for item in tracked_page.allowed_query_params.all()]
    denylist = getattr(settings, "WEBSITE_ANALYTICS_SENSITIVE_QUERY_PARAM_DENYLIST", None)
    if denylist is None:
        denylist = SENSITIVE_QUERY_PARAM_DENYLIST
    filtered_query_params = build_filtered_query_params(
        request.GET, allowlist=allowlist, denylist=denylist
    )

    location = resolve_location(request)
    session_key_hash = _session_key_hash(request)
    visitor_id = _visitor_id(request, session_key_hash)
    auth_user, app_user_id = _auth_and_app_user_id(request)

    return PageViewEvent.objects.create(
        tracked_page=tracked_page,
        canonical_path=canonical_path,
        session_key_hash=session_key_hash,
        visitor_id=visitor_id,
        app_user_id=app_user_id,
        auth_user=auth_user,
        referrer=_filtered_referrer(request),
        user_agent=str(request.META.get("HTTP_USER_AGENT", "") or "")[:512],
        query_params_filtered=filtered_query_params,
        location_city=location["city"],
        location_state=location["state"],
        location_country=location["country"],
        location_source=location["source"],
    )


def try_create_page_view_event(request) -> None:
    try:
        create_page_view_event(request)
    except Exception:
        logger.exception("website analytics capture failed")

