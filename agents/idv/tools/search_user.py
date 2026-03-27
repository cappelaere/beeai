"""Search for identity verifications by name, city, or state"""

import hashlib
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


def _search_user_sync(name: str, city: str, state: str) -> str:
    """Synchronous helper function for database queries"""
    identity_verification_model = get_identity_verification_model()
    # Require at least one search field
    if not any([name, city, state]):
        return json.dumps(
            {
                "success": False,
                "error": "Must provide at least one search field (name, city, or state)",
            },
            indent=2,
        )

    # Normalize search inputs
    name_norm = name.strip().lower() if name else None
    city_norm = city.strip().lower() if city else None
    state_norm = state.strip().upper() if state else None

    # Build query using field hashes
    query = identity_verification_model.objects.all()

    if name_norm:
        name_hash = hashlib.sha256(name_norm.encode()).hexdigest()
        query = query.filter(name_hash=name_hash)

    if city_norm:
        city_hash = hashlib.sha256(city_norm.encode()).hexdigest()
        query = query.filter(city_hash=city_hash)

    if state_norm:
        state_hash = hashlib.sha256(state_norm.encode()).hexdigest()
        query = query.filter(state_hash=state_hash)

    # Execute query
    verifications = list(query.order_by("-verification_date")[:100])  # Limit to 100 results

    if not verifications:
        response = {
            "found": False,
            "count": 0,
            "message": "No verifications found matching the search criteria",
        }
        return json.dumps(response, indent=2)

    # Format results
    now = timezone.now()
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
                "fields_verified": v.fields_provided,
            }
        )

    response = {
        "found": True,
        "count": len(results),
        "search_criteria": {
            "name": "provided" if name else "not provided",
            "city": "provided" if city else "not provided",
            "state": "provided" if state else "not provided",
        },
        "verifications": results,
    }

    return json.dumps(response, indent=2)


@tool
async def search_user(
    name: str = "",
    city: str = "",
    state: str = "",
) -> StringToolOutput:
    """
    Search for identity verifications by name, city, and/or state.
    Provide at least one search field. Only non-sensitive fields are searchable.

    Args:
        name: Full legal name (exact match)
        city: City name (exact match)
        state: State/province 2-letter code (exact match)

    Returns:
        List of matching verifications with status and expiration details
    """
    # Run synchronous database operations in a thread (thread_sensitive=False forces thread pool)
    result = await sync_to_async(_search_user_sync, thread_sensitive=False)(name, city, state)
    return StringToolOutput(result)
