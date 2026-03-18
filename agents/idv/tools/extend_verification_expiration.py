"""Extend expiration date of existing verification"""

import json
import sys
from datetime import timedelta
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


def _extend_verification_sync(verification_hash: str, extension_days: int) -> str:
    """Synchronous helper function for database queries"""
    IdentityVerification = get_identity_verification_model()
    # Validate extension days (reasonable limits)
    if extension_days < 1 or extension_days > 730:  # Max 2 years
        response = {"success": False, "error": "Extension must be between 1 and 730 days"}
        return json.dumps(response, indent=2)

    # Find verification
    verification = IdentityVerification.objects.filter(verification_hash=verification_hash).first()

    if not verification:
        response = {"success": False, "error": "Verification not found with the provided hash"}
        return json.dumps(response, indent=2)

    # Calculate new expiration date
    old_expiration = verification.expiration_date
    new_expiration = old_expiration + timedelta(days=extension_days)

    # Update the record
    now = timezone.now()
    verification.expiration_date = new_expiration
    if verification.notes:
        verification.notes += f"\n[{now.isoformat()}] Expiration extended by {extension_days} days"
    else:
        verification.notes = f"[{now.isoformat()}] Expiration extended by {extension_days} days"
    verification.save()

    response = {
        "success": True,
        "verification_hash": verification_hash,
        "old_expiration": old_expiration.isoformat(),
        "new_expiration": new_expiration.isoformat(),
        "days_extended": extension_days,
        "is_currently_valid": now < new_expiration,
        "days_until_expiration": (new_expiration - now).days,
    }

    return json.dumps(response, indent=2)


@tool
async def extend_verification_expiration(
    verification_hash: str,
    extension_days: int,
) -> StringToolOutput:
    """
    Extend the expiration date of an existing verification.

    Args:
        verification_hash: The unique hash identifier of the verification
        extension_days: Number of days to extend (e.g., 90, 180, 365)

    Returns:
        Updated verification with new expiration date
    """
    # Run synchronous database operations in a thread (thread_sensitive=False forces thread pool)
    result = await sync_to_async(_extend_verification_sync, thread_sensitive=False)(
        verification_hash, extension_days
    )
    return StringToolOutput(result)
