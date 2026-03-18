"""Lookup existing identity verification"""

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


def _lookup_user_sync(
    name: str,
    city: str,
    state: str,
    street_address: str,
    drivers_license: str,
    passport_number: str,
    date_of_birth: str,
) -> str:
    """Synchronous helper function for database queries"""
    IdentityVerification = get_identity_verification_model()
    # Normalize inputs (same as verify_new_user)
    name_norm = name.strip().lower()
    city_norm = city.strip().lower()
    state_norm = state.strip().upper()
    street_norm = street_address.strip().lower()
    dl_norm = drivers_license.strip() if drivers_license else ""
    passport_norm = passport_number.strip() if passport_number else ""
    dob_norm = date_of_birth.strip() if date_of_birth else ""

    # Create same hash from provided PII
    hash_input = (
        f"{name_norm}|{street_norm}|{city_norm}|{state_norm}|{dl_norm}|{passport_norm}|{dob_norm}"
    )
    verification_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    # Lookup by hash
    verification = IdentityVerification.objects.filter(verification_hash=verification_hash).first()

    if not verification:
        response = {
            "verification_found": False,
            "message": "No verification found for this user with the provided information",
        }
        return json.dumps(response, indent=2)

    # Check expiration
    now = timezone.now()
    is_expired = now > verification.expiration_date
    days_until_expiration = (verification.expiration_date - now).days if not is_expired else 0

    response = {
        "verification_found": True,
        "verification_hash": verification.verification_hash,
        "verification_date": verification.verification_date.isoformat(),
        "expiration_date": verification.expiration_date.isoformat(),
        "is_currently_valid": not is_expired and verification.is_valid,
        "days_until_expiration": days_until_expiration,
        "fields_verified": verification.fields_provided,
        "verification_details": verification.verification_details,
        "created_at": verification.created_at.isoformat(),
        "notes": verification.notes,
    }

    return json.dumps(response, indent=2)


@tool
async def lookup_user_verification(
    name: str,
    city: str,
    state: str,
    street_address: str,
    drivers_license: str = "",
    passport_number: str = "",
    date_of_birth: str = "",
) -> StringToolOutput:
    """
    Lookup an existing identity verification by complete user information.
    All fields used in original verification must match exactly.

    Args:
        name: Full legal name
        city: City of residence
        state: State/province (2-letter code)
        street_address: Street address
        drivers_license: Driver's license number (optional)
        passport_number: Passport number (optional)
        date_of_birth: Date of birth (optional)

    Returns:
        Verification status, expiration date, and whether still valid
    """
    # Run synchronous database operations in a thread (thread_sensitive=False forces thread pool)
    result = await sync_to_async(_lookup_user_sync, thread_sensitive=False)(
        name, city, state, street_address, drivers_license, passport_number, date_of_birth
    )
    return StringToolOutput(result)
