# Identity Verification Agent Documentation

## Overview

**Agent Name:** Identity Verification 🔐  
**Purpose:** Verify user identity and manage verification records  
**Type:** Identity verification and audit trail management

The Identity Verification Agent helps verify user identities by collecting required information, maintaining audit trails, and managing verification records. All PII is hashed for privacy - the system stores only cryptographic hashes, not actual personal information.

## When to Use This Agent

Use the Identity Verification Agent when you need to:
- Verify a new user's identity
- Look up an existing verification record
- Search for users by name, city, or state
- List all verification records with filtering
- Extend verification expiration dates
- Check if a verification is still valid

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "🔐 Identity"

### Basic Usage Examples

**Verify a new user:**
```
Verify John Smith from New York, NY at 123 Main St with driver's license ABC123
I need to verify identity for Jane Doe, 456 Oak Ave, Los Angeles, CA, passport P987654
```

**Look up a verification:**
```
Look up the verification for John Smith in New York
Check if Jane Doe from California is verified
```

**Search for users:**
```
Find all verified users in Texas
Search for verifications with the name Smith
Show me all verifications from New York City
```

## Available Tools

### Verification Management

#### verify_new_user
**Purpose:** Create a new identity verification record with full audit trail

**Key Parameters:**
- `name` (str, required): Full name of the person
- `city` (str, required): City of residence
- `state` (str, required): State/province
- `street_address` (str, required): Street address
- `drivers_license` (str, optional): Driver's license number
- `passport_number` (str, optional): Passport number
- `date_of_birth` (str, optional): Date of birth

**Requirements:**
- All required fields must be provided
- At least ONE ID document (driver's license OR passport) is required
- Name, city, state, and street address are mandatory

**Example:**
```
verify_new_user(
    name="John Smith",
    city="New York",
    state="NY",
    street_address="123 Main Street",
    drivers_license="D1234567"
)
```

**Returns:**
- Success/failure status
- Verification hash (unique identifier)
- Verification date
- Expiration date (1 year from verification)
- Fields provided
- Validation result

**Privacy Note:** The system stores only SHA-256 hashes of PII. Original values are never persisted in the database.

#### lookup_user_verification
**Purpose:** Look up a verification by exact match of all identifying information

**Key Parameters:**
- `name` (str, required): Exact name to match
- `city` (str, required): Exact city
- `state` (str, required): Exact state
- `street_address` (str, required): Exact street address
- `drivers_license` (str, optional): Driver's license if provided
- `passport_number` (str, optional): Passport if provided

**Example:**
```
lookup_user_verification(
    name="John Smith",
    city="New York",
    state="NY",
    street_address="123 Main Street",
    drivers_license="D1234567"
)
```

**Returns:**
- Verification found/not found
- Verification details if found:
  - Verification date
  - Expiration date
  - Is valid (not expired)
  - Fields provided
  - Verification details

### Search & Discovery

#### search_user
**Purpose:** Search for verifications using non-sensitive fields (name, city, state)

**Key Parameters:**
- `name` (str, optional): Name to search (partial match)
- `city` (str, optional): City to search (partial match)
- `state` (str, optional): State to search (exact match)

**Example:**
```
search_user(name="Smith")
search_user(city="New York", state="NY")
search_user(state="CA")
```

**Returns:**
- Total matches found
- List of verification records (anonymized):
  - Verification hash
  - Verification date
  - Expiration date
  - Is valid
  - City and state (for context)
  - Fields provided

**Privacy Note:** This tool only searches non-sensitive hashes (name, city, state). Street addresses and ID documents are not searchable.

#### list_all_verifications
**Purpose:** List all verification records with pagination and filtering

**Key Parameters:**
- `limit` (int): Maximum records to return (default: 50, max: 200)
- `offset` (int): Records to skip for pagination (default: 0)
- `valid_only` (bool): Show only non-expired verifications (default: False)

**Example:**
```
list_all_verifications(limit=100, valid_only=True)
list_all_verifications(offset=50, limit=50)
```

**Returns:**
- Total count
- Records returned
- Offset used
- List of verification records with:
  - Verification hash
  - Dates and validity
  - Location (city, state)
  - Fields provided

### Verification Maintenance

#### extend_verification_expiration
**Purpose:** Extend the expiration date of an existing verification

**Key Parameters:**
- `name` (str, required): Name from original verification
- `city` (str, required): City from original verification
- `state` (str, required): State from original verification
- `street_address` (str, required): Address from original verification
- `drivers_license` (str, optional): Driver's license if used
- `passport_number` (str, optional): Passport if used
- `additional_years` (int): Years to add (default: 1)

**Example:**
```
extend_verification_expiration(
    name="John Smith",
    city="New York",
    state="NY",
    street_address="123 Main Street",
    drivers_license="D1234567",
    additional_years=2
)
```

**Returns:**
- Success/failure status
- Original expiration date
- New expiration date
- Years added

## Common Workflows

### New User Verification

1. **Collect required information:**
   - Name, city, state, street address
   - At least one ID (driver's license or passport)

2. **Create verification:**
   ```
   verify_new_user(
       name="Jane Doe",
       city="Los Angeles",
       state="CA",
       street_address="456 Oak Avenue",
       passport_number="P123456789",
       date_of_birth="1990-01-15"
   )
   ```

3. **Confirm verification created:**
   - System returns verification hash
   - Expiration date set to 1 year from now
   - Audit record created

### Verification Lookup

1. **Gather user information:**
   - Exact name, city, state, address
   - ID document used in original verification

2. **Look up verification:**
   ```
   lookup_user_verification(
       name="Jane Doe",
       city="Los Angeles",
       state="CA",
       street_address="456 Oak Avenue",
       passport_number="P123456789"
   )
   ```

3. **Check validity:**
   - Review expiration date
   - Confirm `is_valid` status

### User Search

1. **Search by available criteria:**
   ```
   search_user(name="Doe", state="CA")
   ```

2. **Review results:**
   - Check returned verification hashes
   - Note expiration dates
   - Filter by validity if needed

### Verification Renewal

1. **Locate existing verification:**
   ```
   lookup_user_verification(...)
   ```

2. **Extend expiration:**
   ```
   extend_verification_expiration(
       name="Jane Doe",
       city="Los Angeles",
       state="CA",
       street_address="456 Oak Avenue",
       passport_number="P123456789",
       additional_years=1
   )
   ```

3. **Confirm new expiration date**

## Technical Details

### Privacy & Security

**Hash-Based Storage:**
- All PII is hashed using SHA-256
- Original values are never stored in the database
- Each field is hashed separately for search capability
- Verification hash combines all fields for uniqueness

**Searchable Fields:**
- Name (hash-based partial match)
- City (hash-based partial match)
- State (hash-based exact match)

**Non-Searchable Fields:**
- Street address (privacy protected)
- Driver's license (privacy protected)
- Passport number (privacy protected)
- Date of birth (privacy protected)

### Data Model

**IdentityVerification Model Fields:**
- `verification_hash` - SHA-256 hash of all PII fields
- `name_hash` - SHA-256 hash of name (searchable)
- `city_hash` - SHA-256 hash of city (searchable)
- `state_hash` - SHA-256 hash of state (searchable)
- `verification_date` - When verification was created
- `expiration_date` - When verification expires (1 year default)
- `is_valid` - Calculated: not expired
- `fields_provided` - JSON list of provided fields
- `verification_details` - Audit information
- `requested_by_session` - Session that created verification
- `requested_by_agent` - Agent type (idv)
- `notes` - Optional additional notes

### Verification Lifecycle

1. **Creation:**
   - User provides required information
   - System validates all required fields
   - PII is hashed immediately
   - Verification record created
   - Expiration set to 1 year

2. **Valid Period:**
   - Verification remains valid for 1 year
   - Can be looked up and searched
   - `is_valid` returns True

3. **Expiration:**
   - After 1 year, `is_valid` returns False
   - Record remains in database for audit
   - Can be extended or re-verified

4. **Extension:**
   - Expiration date can be extended
   - Requires all original information
   - Adds specified years to expiration

### Database
- **Type:** Django ORM with PostgreSQL/SQLite
- **Indexes:** Optimized for hash lookups
- **Audit Trail:** Complete history maintained

## Example Use Cases

### For HR/Onboarding
- "Verify new employee John Smith, NYC, with driver's license"
- "Check if Jane Doe's verification is still valid"
- "List all employees with expired verifications"

### For Compliance Officers
- "Search for all verifications in California"
- "How many valid verifications do we have?"
- "Extend verification for John Smith by 2 years"

### For Administrators
- "List all verifications from last month"
- "Find all expired verifications"
- "Search for verifications with passport numbers"

### For Customer Service
- "Look up verification for customer Jane Doe"
- "Is this customer's verification still valid?"
- "When does this verification expire?"

## Validation Rules

### Required Fields
1. **Name** - Must be provided
2. **City** - Must be provided
3. **State** - Must be provided (2-letter code preferred)
4. **Street Address** - Must be provided
5. **ID Document** - At least ONE of:
   - Driver's license number, OR
   - Passport number

### Optional Fields
- Date of birth
- Additional notes

### Field Formats
- **State:** 2-letter codes (e.g., NY, CA, TX)
- **Dates:** ISO format (YYYY-MM-DD) preferred
- **Names:** Any format, normalized to lowercase for hashing
- **Addresses:** Any format, normalized for consistency

## Important Notes

### Privacy Compliance
- **No PII Storage:** Only hashes are stored
- **Audit Trail:** Complete verification history maintained
- **Session Tracking:** Records which session/agent created each verification
- **Search Limitations:** Only non-sensitive fields are searchable

### Expiration Management
- **Default Period:** 1 year from verification date
- **Automatic Calculation:** `is_valid` calculated dynamically
- **Extension:** Can extend multiple times
- **No Auto-Renewal:** Must be manually extended

### Verification Uniqueness
- Each verification has a unique hash combining all PII fields
- Same person can have multiple verifications if any detail changes
- Exact match required for lookups

## Related Agents

- **GRES Agent** - For property auction data
- **SAM.gov Agent** - For federal exclusions verification
- **Library Agent** - For policy and compliance documentation

## Support

For verification issues:
- Ensure all required fields are provided
- Verify at least one ID document is included
- Check state codes are valid (2-letter format)
- Review expiration dates for validity

For database issues:
- Verify Django is properly configured
- Check database connection settings
- Ensure migrations are up to date
- Review database logs for errors
