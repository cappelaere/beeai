# SAM.gov Exclusions Agent Documentation

## Overview

**Agent Name:** SAM.gov Exclusions 🚫  
**Purpose:** Query federal contract exclusions from SAM.gov database  
**Type:** Read-only database query agent

The SAM.gov Exclusions Agent provides access to the System for Award Management (SAM) Exclusions database, containing 138,885 exclusion records from various federal agencies. Use this agent to check if individuals or entities are excluded from receiving federal contracts.

## When to Use This Agent

Use the SAM.gov Agent when you need to:
- Verify if an individual or entity is excluded from federal contracts
- Search for exclusions by name, agency, or type
- Get detailed exclusion information including dates and reasons
- List all agencies that issue exclusions
- Analyze exclusion statistics across agencies

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "🚫 SAM.gov"

### Basic Usage Examples

**Check if someone is excluded:**
```
Is John Smith excluded from federal contracts?
Check the exclusion status of ABC Corporation
```

**Search for exclusions:**
```
Find all exclusions from the Department of Justice
Show me all Treasury Department exclusions
List exclusions from 2024
```

**Get detailed information:**
```
Tell me more about exclusion SAM-12345
What agencies issue the most exclusions?
```

## Available Tools

### Search & Query

#### search_exclusions
**Purpose:** Search the SAM.gov exclusions database with flexible criteria

**Key Parameters:**
- `name` (str): Individual or entity name (partial match)
- `classification` (str): Individual, Firm, Vessel, or Special Entity Designation
- `excluding_agency` (str): Agency code (e.g., TREAS-OFAC, DOJ, HHS, OPM)
- `exclusion_type` (str): Prohibition/Restriction, Ineligible, Voluntary Exclusion
- `country` (str): Country code (USA, CAN, etc.)
- `limit` (int): Maximum results (default: 20, max: 100)

**Example:**
```
search_exclusions(name="Smith", classification="Individual", limit=50)
search_exclusions(excluding_agency="DOJ", exclusion_type="Prohibition")
```

**Returns:**
- Total count found
- List of matching records with:
  - Name
  - Classification
  - Excluding agency
  - Exclusion type
  - Active and termination dates
  - SAM number
  - Unique entity ID
  - Location (city, state, country)

#### check_entity_status
**Purpose:** Check if a specific individual or entity is currently excluded

**Key Parameters:**
- `name` (str): Exact or partial name to check

**Example:**
```
check_entity_status(name="ABC Corporation")
check_entity_status(name="John Doe")
```

**Returns:**
- Exclusion status (excluded or not excluded)
- Current active exclusions if any
- Relevant exclusion details

#### get_exclusion_detail
**Purpose:** Get comprehensive details for a specific exclusion record

**Key Parameters:**
- `sam_number` (str): SAM unique identifier for the exclusion

**Example:**
```
get_exclusion_detail(sam_number="SAM-12345-ABCDE")
```

**Returns:**
- Complete exclusion record including:
  - Entity information
  - Exclusion dates
  - Agency details
  - Exclusion type and reason
  - Cross-reference information
  - Additional details

### Analytics & Statistics

#### list_excluding_agencies
**Purpose:** List all federal agencies that issue exclusions

**Example:**
```
list_excluding_agencies()
```

**Returns:**
- Complete list of agency codes
- Agency names
- Count of exclusions per agency

**Common Agencies:**
- **TREAS-OFAC** - Treasury Department, Office of Foreign Assets Control
- **DOJ** - Department of Justice
- **HHS** - Health and Human Services
- **OPM** - Office of Personnel Management
- **EPA** - Environmental Protection Agency

#### exclusion_statistics
**Purpose:** Get comprehensive statistics about exclusions

**Example:**
```
exclusion_statistics()
```

**Returns:**
- Total exclusion count (138,885 records)
- Breakdown by:
  - Classification (Individual, Firm, Vessel, Special Entity)
  - Exclusion type
  - Excluding agency
  - Active vs. terminated exclusions

## Common Workflows

### Vendor Due Diligence

1. **Check vendor status:**
   ```
   check_entity_status(name="Vendor Company Name")
   ```

2. **Search for similar names:**
   ```
   search_exclusions(name="Vendor", limit=50)
   ```

3. **Review details if excluded:**
   ```
   get_exclusion_detail(sam_number="SAM-XXXXX-XXXXX")
   ```

### Agency Analysis

1. **List all agencies:**
   ```
   list_excluding_agencies()
   ```

2. **Search agency exclusions:**
   ```
   search_exclusions(excluding_agency="DOJ", limit=100)
   ```

3. **Get statistics:**
   ```
   exclusion_statistics()
   ```

### Compliance Monitoring

1. **Search by exclusion type:**
   ```
   search_exclusions(exclusion_type="Prohibition", limit=100)
   ```

2. **Filter by country:**
   ```
   search_exclusions(country="USA", excluding_agency="TREAS-OFAC")
   ```

3. **Check multiple classifications:**
   ```
   search_exclusions(classification="Firm", limit=50)
   search_exclusions(classification="Individual", limit=50)
   ```

## Technical Details

### Database
- **Source:** System for Award Management (SAM.gov)
- **Records:** 138,885 exclusion records
- **Type:** SQLite database
- **Location:** Local database file

### Data Structure

**Exclusion Record Fields:**
- `name` - Individual or entity name
- `classification` - Individual, Firm, Vessel, Special Entity Designation
- `excluding_agency` - Federal agency code
- `exclusion_type` - Prohibition/Restriction, Ineligible, Voluntary Exclusion
- `active_date` - When exclusion became effective
- `termination_date` - When exclusion ends (if applicable)
- `sam_number` - Unique SAM identifier
- `unique_entity_id` - UEI identifier
- `city`, `state_province`, `country` - Location information
- `cross_reference` - Related records
- `additional_comments` - Exclusion details

### Search Capabilities
- **Name matching:** Partial, case-insensitive
- **Agency matching:** Exact code or partial match
- **Classification filter:** Exact match
- **Exclusion type:** Partial match
- **Country filter:** Exact code
- **Result limits:** 1-100 records per query

### Performance
- Database queries are optimized with indexes
- Typical search response: < 1 second
- Full database scan available for statistics

## Example Use Cases

### For Contracting Officers
- "Check if contractor XYZ is excluded from federal contracts"
- "Show me all active exclusions from last month"
- "Is this vendor on the exclusion list?"

### For Compliance Teams
- "Search all Treasury Department exclusions"
- "Find exclusions related to fraud"
- "Show statistics for voluntary exclusions"

### For Due Diligence
- "Check the exclusion status of potential vendor ABC Corp"
- "Search for any exclusions in California"
- "List all vessel exclusions"

### For Research & Analysis
- "What agencies issue the most exclusions?"
- "Show me exclusion statistics by classification"
- "How many exclusions are currently active?"

## Classification Types

The database tracks four classification types:

1. **Individual** - Natural persons
2. **Firm** - Companies, partnerships, corporations
3. **Vessel** - Ships and maritime vessels
4. **Special Entity Designation** - Special categories (e.g., foreign government entities)

## Exclusion Types

Common exclusion types in the database:

1. **Prohibition/Restriction** - Most common, prevents contract awards
2. **Ineligible** - Entity/individual ineligible for federal contracts
3. **Voluntary Exclusion** - Self-imposed exclusion

## Important Notes

### Data Currency
- The database is a snapshot of SAM.gov exclusions
- For real-time verification, check SAM.gov directly
- Database may require periodic updates

### Legal Disclaimer
- This agent provides informational data only
- Not a substitute for official SAM.gov verification
- Consult legal counsel for compliance decisions
- Exclusion status can change rapidly

### Privacy
- Data is from public records
- No additional PII is collected or stored
- Queries are logged for audit purposes

## Related Agents

- **GRES Agent** - For GSA real estate auction data
- **Identity Verification Agent** - For user verification workflows
- **Library Agent** - For searching compliance documentation

## Support

For database issues:
- Verify the SAM.gov exclusions database file is accessible
- Check database file path configuration
- Ensure SQLite is properly installed
- Review database schema if queries fail

For SAM.gov official data:
- Visit https://sam.gov/
- Use the official SAM.gov Exclusions portal
- Contact GSA for data updates
