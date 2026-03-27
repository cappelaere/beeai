"""Verify new user identity and create audit record"""

import hashlib
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


def _verify_new_user_sync(
    name: str,
    city: str,
    state: str,
    street_address: str,
    drivers_license: str,
    passport_number: str,
    date_of_birth: str,
) -> str:
    """Synchronous helper function for database queries"""
    identity_verification_model = get_identity_verification_model()
    # Validation: Check required fields
    if not name or not city or not state or not street_address:
        response = {
            "success": False,
            "error": "Missing required fields. Name, city, state, and street_address are required.",
            "fields_missing": [
                f
                for f, v in [
                    ("name", name),
                    ("city", city),
                    ("state", state),
                    ("street_address", street_address),
                ]
                if not v
            ],
        }
        return json.dumps(response, indent=2)

    # Check at least one ID document
    if not drivers_license and not passport_number:
        response = {
            "success": False,
            "error": "At least one ID document is required (drivers_license or passport_number).",
        }
        return json.dumps(response, indent=2)

    # Normalize inputs for hashing (lowercase, strip whitespace)
    name_norm = name.strip().lower()
    city_norm = city.strip().lower()
    state_norm = state.strip().upper()  # States as uppercase
    street_norm = street_address.strip().lower()
    dl_norm = drivers_license.strip() if drivers_license else ""
    passport_norm = passport_number.strip() if passport_number else ""
    dob_norm = date_of_birth.strip() if date_of_birth else ""

    # Create primary verification hash from ALL fields
    hash_input = (
        f"{name_norm}|{street_norm}|{city_norm}|{state_norm}|{dl_norm}|{passport_norm}|{dob_norm}"
    )
    verification_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    # Create searchable field hashes
    name_hash = hashlib.sha256(name_norm.encode()).hexdigest()
    city_hash = hashlib.sha256(city_norm.encode()).hexdigest()
    state_hash = hashlib.sha256(state_norm.encode()).hexdigest()

    # Check if already exists
    existing = identity_verification_model.objects.filter(
        verification_hash=verification_hash
    ).first()
    if existing:
        now = timezone.now()
        is_expired = now > existing.expiration_date
        response = {
            "success": False,
            "already_verified": True,
            "verification_hash": existing.verification_hash,
            "verification_date": existing.verification_date.isoformat(),
            "expiration_date": existing.expiration_date.isoformat(),
            "is_currently_valid": not is_expired and existing.is_valid,
            "message": "User already has an existing verification",
        }
        return json.dumps(response, indent=2)

    # Placeholder until request context wiring is added.
    session_key = "system"

    # Calculate expiration (1 year from now)
    now = timezone.now()
    expiration_date = now + timedelta(days=365)

    # Build fields_provided list
    fields_provided = ["name", "city", "state", "street_address"]
    if drivers_license:
        fields_provided.append("drivers_license")
    if passport_number:
        fields_provided.append("passport_number")
    if date_of_birth:
        fields_provided.append("date_of_birth")

    # Create audit record
    verification = identity_verification_model.objects.create(
        verification_hash=verification_hash,
        name_hash=name_hash,
        city_hash=city_hash,
        state_hash=state_hash,
        expiration_date=expiration_date,
        is_valid=True,
        fields_provided=fields_provided,
        verification_details="All required fields provided and validated",
        requested_by_session=session_key,
    )

    response = {
        "success": True,
        "verification_hash": verification.verification_hash,
        "verification_date": verification.verification_date.isoformat(),
        "expiration_date": verification.expiration_date.isoformat(),
        "days_until_expiration": 365,
        "is_valid": True,
        "fields_verified": fields_provided,
        "message": "Identity verification successful",
    }

    return json.dumps(response, indent=2)


@tool
async def verify_new_user(
    name: str,
    city: str,
    state: str,
    street_address: str,
    drivers_license: str = "",
    passport_number: str = "",
    date_of_birth: str = "",
) -> StringToolOutput:
    """
    Verify a new user's identity and create an audit record.

    Args:
        name: Full legal name
        city: City of residence
        state: State/province (2-letter code recommended, e.g., CA, NY)
        street_address: Street address (not searchable, only for verification)
        drivers_license: Driver's license number (optional)
        passport_number: Passport number (optional)
        date_of_birth: Date of birth (optional)

    Returns:
        Verification result with hash ID and expiration date
    """
    # Run synchronous database operations in a thread (thread_sensitive=False forces thread pool)
    result = await sync_to_async(_verify_new_user_sync, thread_sensitive=False)(
        name, city, state, street_address, drivers_license, passport_number, date_of_birth
    )
    return StringToolOutput(result)
