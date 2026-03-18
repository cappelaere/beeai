"""
Shared HTTP response helpers for consistent API error handling.
"""

import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "An error occurred. See server logs."


def json_response_500(log_msg: str, **log_extra) -> JsonResponse:
    """
    Log an exception with full traceback and return a generic 500 JSON response.
    Call this from except blocks instead of returning str(e) to avoid leaking
    internal details to clients.
    """
    logger.exception(log_msg, **log_extra)
    return JsonResponse(
        {"success": False, "error": GENERIC_ERROR_MESSAGE},
        status=500,
    )
