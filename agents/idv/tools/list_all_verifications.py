"""List all identity verifications with filters"""

import json
import sys
from pathlib import Path

from asgiref.sync import sync_to_async
from django.utils import timezone

# Add agents directory to path for absolute imports
_AGENTS_DIR = Path(__file__).parent.parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

# Add agent_ui directory for Django models (when tool runs)
_AGENT_UI_DIR = Path(__file__).parent.parent.parent.parent / "agent_ui"
if str(_AGENT_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_UI_DIR))

from beeai_framework.tools import StringToolOutput, tool

from ._django_ready import get_identity_verification_model


def _list_verifications_sync(status: str, limit: int, offset: int) -> str:
    """Synchronous helper function for database queries"""
    identity_verification_model = get_identity_verification_model()
    # Validate and cap limit
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    # Build query
    query = identity_verification_model.objects.all()
    now = timezone.now()

    # Filter by status
    if status == "valid":
        query = query.filter(expiration_date__gt=now, is_valid=True)
    elif status == "expired":
        query = query.filter(expiration_date__lte=now)

    # Apply pagination
    total_count = query.count()
    verifications = list(query.order_by("-verification_date")[offset : offset + limit])

    # Format results with full audit details
    results = []
    for v in verifications:
        is_expired = now > v.expiration_date
        results.append(
            {
                "verification_hash": v.verification_hash,
                "verification_date": v.verification_date.isoformat(),
                "expiration_date": v.expiration_date.isoformat(),
                "is_currently_valid": not is_expired and v.is_valid,
                "days_until_expiration": (v.expiration_date - now).days if not is_expired else 0,
                "fields_provided": v.fields_provided,
                "verification_details": v.verification_details,
                "requested_by_session": v.requested_by_session,
                "requested_by_agent": v.requested_by_agent,
                "notes": v.notes,
                "created_at": v.created_at.isoformat(),
                "updated_at": v.updated_at.isoformat(),
            }
        )

    response = {
        "total_count": total_count,
        "returned_count": len(results),
        "offset": offset,
        "limit": limit,
        "status_filter": status,
        "verifications": results,
    }

    return json.dumps(response, indent=2)


@tool
async def list_all_verifications(
    status: str = "all",
    limit: int = 50,
    offset: int = 0,
) -> StringToolOutput:
    """
    List all identity verifications with full audit details.

    Args:
        status: Filter by status - "valid" (not expired), "expired", or "all"
        limit: Maximum number of records to return (default 50, max 200)
        offset: Number of records to skip for pagination

    Returns:
        List of verifications with complete audit information
    """
    # Run synchronous database operations in a thread (thread_sensitive=False forces thread pool)
    result = await sync_to_async(_list_verifications_sync, thread_sensitive=False)(
        status, limit, offset
    )
    return StringToolOutput(result)
