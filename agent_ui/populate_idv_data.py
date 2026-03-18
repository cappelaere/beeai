"""
Populate Identity Verification database with sample data
Run with: python populate_idv_data.py
"""

import hashlib
import os
import sys
from datetime import timedelta
from pathlib import Path

import django

# Setup Django environment
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ui.settings")
django.setup()

from django.utils import timezone

from agent_app.models import IdentityVerification

# Sample data with diverse information
SAMPLE_USERS = [
    {
        "name": "John Smith",
        "street": "123 Main Street",
        "city": "San Francisco",
        "state": "CA",
        "drivers_license": "D1234567",
        "passport": "",
        "dob": "1985-03-15",
        "exp_offset_days": 300,  # Expires in 300 days
    },
    {
        "name": "Jane Doe",
        "street": "456 Oak Avenue",
        "city": "Los Angeles",
        "state": "CA",
        "drivers_license": "",
        "passport": "P9876543",
        "dob": "1990-07-22",
        "exp_offset_days": 180,  # Expires in 180 days
    },
    {
        "name": "Robert Johnson",
        "street": "789 Pine Road",
        "city": "New York",
        "state": "NY",
        "drivers_license": "D2345678",
        "passport": "P1234567",
        "dob": "1978-11-03",
        "exp_offset_days": 400,  # Expires in 400 days
    },
    {
        "name": "Maria Garcia",
        "street": "321 Elm Street",
        "city": "Miami",
        "state": "FL",
        "drivers_license": "D3456789",
        "passport": "",
        "dob": "1992-05-18",
        "exp_offset_days": -30,  # Expired 30 days ago
    },
    {
        "name": "David Chen",
        "street": "654 Maple Drive",
        "city": "Seattle",
        "state": "WA",
        "drivers_license": "D4567890",
        "passport": "",
        "dob": "1988-09-12",
        "exp_offset_days": 90,  # Expires in 90 days
    },
    {
        "name": "Sarah Williams",
        "street": "987 Cedar Lane",
        "city": "Boston",
        "state": "MA",
        "drivers_license": "",
        "passport": "P2345678",
        "dob": "1995-01-25",
        "exp_offset_days": 500,  # Expires in 500 days
    },
    {
        "name": "Michael Brown",
        "street": "147 Birch Court",
        "city": "Chicago",
        "state": "IL",
        "drivers_license": "D5678901",
        "passport": "",
        "dob": "1982-12-08",
        "exp_offset_days": -60,  # Expired 60 days ago
    },
    {
        "name": "Emily Davis",
        "street": "258 Spruce Way",
        "city": "Austin",
        "state": "TX",
        "drivers_license": "D6789012",
        "passport": "P3456789",
        "dob": "1991-04-30",
        "exp_offset_days": 200,  # Expires in 200 days
    },
    {
        "name": "James Wilson",
        "street": "369 Willow Street",
        "city": "Denver",
        "state": "CO",
        "drivers_license": "D7890123",
        "passport": "",
        "dob": "1987-08-14",
        "exp_offset_days": 365,  # Expires in exactly 1 year
    },
    {
        "name": "Lisa Anderson",
        "street": "741 Redwood Boulevard",
        "city": "Portland",
        "state": "OR",
        "drivers_license": "",
        "passport": "P4567890",
        "dob": "1993-02-19",
        "exp_offset_days": 45,  # Expires in 45 days
    },
    {
        "name": "Thomas Martinez",
        "street": "852 Cypress Street",
        "city": "Phoenix",
        "state": "AZ",
        "drivers_license": "D8901234",
        "passport": "",
        "dob": "1980-06-27",
        "exp_offset_days": -90,  # Expired 90 days ago
    },
    {
        "name": "Jennifer Taylor",
        "street": "963 Aspen Avenue",
        "city": "San Diego",
        "state": "CA",
        "drivers_license": "D9012345",
        "passport": "P5678901",
        "dob": "1989-10-05",
        "exp_offset_days": 275,  # Expires in 275 days
    },
    {
        "name": "Christopher Lee",
        "street": "159 Hickory Drive",
        "city": "Atlanta",
        "state": "GA",
        "drivers_license": "D0123456",
        "passport": "",
        "dob": "1984-03-11",
        "exp_offset_days": 150,  # Expires in 150 days
    },
    {
        "name": "Amanda White",
        "street": "357 Magnolia Lane",
        "city": "Nashville",
        "state": "TN",
        "drivers_license": "",
        "passport": "P6789012",
        "dob": "1996-07-08",
        "exp_offset_days": -10,  # Expired 10 days ago
    },
    {
        "name": "Daniel Harris",
        "street": "486 Dogwood Court",
        "city": "San Francisco",
        "state": "CA",
        "drivers_license": "D1357924",
        "passport": "",
        "dob": "1986-11-23",
        "exp_offset_days": 420,  # Expires in 420 days
    },
    {
        "name": "Jessica Clark",
        "street": "753 Poplar Street",
        "city": "Charlotte",
        "state": "NC",
        "drivers_license": "D2468135",
        "passport": "P7890123",
        "dob": "1994-09-16",
        "exp_offset_days": 120,  # Expires in 120 days
    },
    {
        "name": "Matthew Lewis",
        "street": "951 Sycamore Road",
        "city": "Las Vegas",
        "state": "NV",
        "drivers_license": "D3579246",
        "passport": "",
        "dob": "1981-05-29",
        "exp_offset_days": -120,  # Expired 120 days ago
    },
    {
        "name": "Ashley Robinson",
        "street": "147 Beech Avenue",
        "city": "Seattle",
        "state": "WA",
        "drivers_license": "",
        "passport": "P8901234",
        "dob": "1997-12-31",
        "exp_offset_days": 600,  # Expires in 600 days
    },
    {
        "name": "Joshua Walker",
        "street": "258 Walnut Drive",
        "city": "Minneapolis",
        "state": "MN",
        "drivers_license": "D4680357",
        "passport": "",
        "dob": "1983-04-07",
        "exp_offset_days": 240,  # Expires in 240 days
    },
    {
        "name": "Michelle Hall",
        "street": "369 Cherry Lane",
        "city": "Tampa",
        "state": "FL",
        "drivers_license": "D5791468",
        "passport": "P9012345",
        "dob": "1998-08-20",
        "exp_offset_days": 15,  # Expires in 15 days (soon!)
    },
]


def create_verification_hash(user_data):
    """Create verification hash from user data"""
    name_norm = user_data["name"].strip().lower()
    city_norm = user_data["city"].strip().lower()
    state_norm = user_data["state"].strip().upper()
    street_norm = user_data["street"].strip().lower()
    dl_norm = user_data["drivers_license"].strip()
    passport_norm = user_data["passport"].strip()
    dob_norm = user_data["dob"].strip()

    hash_input = (
        f"{name_norm}|{street_norm}|{city_norm}|{state_norm}|{dl_norm}|{passport_norm}|{dob_norm}"
    )
    return hashlib.sha256(hash_input.encode()).hexdigest()


def create_field_hashes(user_data):
    """Create searchable field hashes"""
    name_norm = user_data["name"].strip().lower()
    city_norm = user_data["city"].strip().lower()
    state_norm = user_data["state"].strip().upper()

    return {
        "name_hash": hashlib.sha256(name_norm.encode()).hexdigest(),
        "city_hash": hashlib.sha256(city_norm.encode()).hexdigest(),
        "state_hash": hashlib.sha256(state_norm.encode()).hexdigest(),
    }


def populate_data():
    """Populate database with sample verification data"""
    now = timezone.now()
    created_count = 0
    skipped_count = 0

    print("Populating Identity Verification database...")
    print()

    for user_data in SAMPLE_USERS:
        # Create verification hash
        verification_hash = create_verification_hash(user_data)

        # Check if already exists
        if IdentityVerification.objects.filter(verification_hash=verification_hash).exists():
            print(f"⏭️  Skipped: {user_data['name']} (already exists)")
            skipped_count += 1
            continue

        # Create field hashes
        field_hashes = create_field_hashes(user_data)

        # Calculate verification and expiration dates
        # Simulate different verification dates in the past
        verification_date = now - timedelta(days=30)  # All verified 30 days ago
        expiration_date = verification_date + timedelta(days=user_data["exp_offset_days"])

        # Build fields_provided list
        fields_provided = ["name", "city", "state", "street_address"]
        if user_data["drivers_license"]:
            fields_provided.append("drivers_license")
        if user_data["passport"]:
            fields_provided.append("passport_number")
        if user_data["dob"]:
            fields_provided.append("date_of_birth")

        # Determine if currently valid
        is_valid = expiration_date > now
        status_text = "Valid" if is_valid else "Expired"

        # Create verification record
        IdentityVerification.objects.create(
            verification_hash=verification_hash,
            name_hash=field_hashes["name_hash"],
            city_hash=field_hashes["city_hash"],
            state_hash=field_hashes["state_hash"],
            verification_date=verification_date,
            expiration_date=expiration_date,
            is_valid=is_valid,
            fields_provided=fields_provided,
            verification_details=f"Sample verification data - {status_text}",
            requested_by_session="data_generator",
            requested_by_agent="system",
            notes=f"Generated test data for {user_data['name']}",
        )

        days_diff = (expiration_date - now).days
        exp_status = (
            f"expires in {days_diff} days"
            if days_diff > 0
            else f"expired {abs(days_diff)} days ago"
        )
        print(
            f"✅ Created: {user_data['name']:20} | {user_data['city']:15}, {user_data['state']} | {exp_status}"
        )
        created_count += 1

    print()
    print("📊 Summary:")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total in DB: {IdentityVerification.objects.count()}")
    print()

    # Show some statistics
    valid_count = IdentityVerification.objects.filter(
        expiration_date__gt=now, is_valid=True
    ).count()
    expired_count = IdentityVerification.objects.filter(expiration_date__lte=now).count()
    print(f"   Valid verifications: {valid_count}")
    print(f"   Expired verifications: {expired_count}")


if __name__ == "__main__":
    populate_data()
