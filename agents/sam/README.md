# SAM.gov Exclusions Agent

Query the federal contract exclusions database from SAM.gov (System for Award Management).

## Overview

The SAM.gov Exclusions Agent provides access to over 167,000 federal contract exclusion records. It helps verify if individuals or companies are excluded from receiving federal contracts due to fraud, performance issues, legal violations, or other reasons.

## Database

- **Location**: `data/sam_exclusions.db`
- **Total Records**: ~167,000 exclusions
- **Firms**: ~120,000
- **Individuals**: ~45,000
- **Vessels**: ~1,000

### Top Excluding Agencies

1. GSA (General Services Administration)
2. USAF (U.S. Air Force)
3. HHS (Health & Human Services)
4. DOJ (Department of Justice)
5. ARMY (U.S. Army)

## Tools

### 1. `search_exclusions`

Search the exclusions database with flexible filters.

**Parameters**:
- `name` (optional): Individual or entity name (partial match)
- `classification` (optional): Individual, Firm, Vessel, or Special Entity Designation
- `excluding_agency` (optional): Agency code (e.g., GSA, DOJ, HHS)
- `exclusion_type` (optional): Prohibition/Restriction, Ineligible, Voluntary Exclusion
- `country` (optional): Country code (USA, CAN, etc.)
- `limit` (optional): Max results (default 20, max 100)

**Returns**: List of matching exclusion records with key fields

**Example**:
```python
search_exclusions(name="Smith", classification="Individual", limit=10)
search_exclusions(excluding_agency="GSA", exclusion_type="Prohibition")
```

### 2. `check_entity_status`

Check if an individual or company is currently excluded from federal contracts.

**Parameters**:
- `entity_name` (required): Full or partial name to check

**Returns**: 
- `is_excluded`: Boolean
- `active_exclusions`: Count of active exclusions
- `details`: Full exclusion records if found

**Example**:
```python
check_entity_status("John Smith")
# Returns: is_excluded=False, message="No active exclusions found"

check_entity_status("ABC Corporation")
# If excluded, returns: is_excluded=True, active_exclusions=1, details=[...]
```

**Important**: Only checks **active** exclusions (not expired or terminated).

### 3. `get_exclusion_detail`

Get detailed information about a specific exclusion record.

**Parameters**:
- `sam_number` (required): The unique SAM identifier for the exclusion

**Returns**: Complete exclusion record with all fields

**Example**:
```python
get_exclusion_detail(sam_number="1234567890ABC")
```

### 4. `list_excluding_agencies`

List all federal agencies that have issued exclusions in the database.

**Parameters**: None

**Returns**: 
- List of agencies with exclusion counts
- Sorted by count (most active first)

**Example**:
```python
list_excluding_agencies()
# Returns: [("GSA", 45000), ("USAF", 12000), ...]
```

### 5. `exclusion_statistics`

Get comprehensive statistics about the exclusions database.

**Parameters**: None

**Returns**:
- Total exclusions
- Breakdown by classification
- Breakdown by exclusion type
- Top excluding agencies
- Active vs terminated counts

**Example**:
```python
exclusion_statistics()
```

## Setup

### 1. Obtain Source Data

Download the SAM Exclusions Public Extract:
1. Go to https://sam.gov/data-services/Exclusions
2. Download "Public Extract V2" CSV file
3. Save as `data/source/SAM_Exclusions_Public_Extract_V2.CSV`

**Or** use the existing file already in the repository.

### 2. Import Data

```bash
python scripts/import_sam_data.py
```

This creates `data/sam_exclusions.db` from the CSV file.

**Import time**: 2-3 minutes for 167K records

**Output**: Progress updates every 10,000 records

### 3. Verify Database

```bash
# Via Python
python -c "import sqlite3; conn = sqlite3.connect('data/sam_exclusions.db'); print(f'{conn.execute(\"SELECT COUNT(*) FROM exclusions\").fetchone()[0]:,} exclusions')"

# Via Agent CLI
python run_agent.py --agent sam
# Ask: "How many exclusions are in the database?"

# Via Web UI
# Select SAM Agent from dropdown
# Ask: "Show me exclusion statistics"
```

### 4. Access via UI

The SAM agent appears in the agent selector dropdown as "🚫 SAM.gov".

### 5. Access via CLI

```bash
python run_agent.py --agent sam
```

## Example Queries

**Check if someone is excluded**:
```
"Check if John Smith is excluded from federal contracts"
"Is ABC Corporation currently excluded?"
"Search for exclusions for Jane Doe"
```

**Search by agency**:
```
"Show me GSA exclusions"
"List exclusions by the Department of Justice"
"Find USAF exclusions from 2023"
```

**Get statistics**:
```
"How many exclusions are in the database?"
"Show me exclusion statistics"
"Which agencies have issued the most exclusions?"
```

**Look up details**:
```
"Get details for SAM number 1234567890ABC"
"Tell me about exclusion record XYZ"
```

## Database Schema

### Table: `exclusions`

**Identification Fields**:
- `id` - Auto-increment primary key
- `sam_number` - Unique SAM identifier (TEXT)
- `unique_entity_id` - UEI identifier (TEXT)
- `cage` - CAGE code (TEXT)
- `npi` - NPI number (TEXT)

**Name Fields**:
- `classification` - Individual, Firm, Vessel, Special Entity
- `name` - Full name (TEXT)
- `prefix`, `first`, `middle`, `last`, `suffix` - Name components

**Address Fields**:
- `address_1`, `address_2`, `address_3`, `address_4`
- `city`, `state_province`, `country`, `zip_code`

**Exclusion Details**:
- `exclusion_program` - Program name
- `excluding_agency` - Agency that issued exclusion
- `exclusion_type` - Type of exclusion
- `ct_code` - Cause/treatment code
- `additional_comments` - Extra details
- `cross_reference` - Related exclusions

**Date Fields**:
- `active_date` - When exclusion became active
- `termination_date` - When exclusion ends (or "Indefinite")
- `record_status` - Current status
- `creation_date` - When record was created

### Indexes

For query performance:
- `idx_name` - Name lookups
- `idx_uei` - UEI lookups
- `idx_classification` - Filter by type
- `idx_excluding_agency` - Filter by agency
- `idx_active_date` - Date range queries
- `idx_sam_number` - Direct lookups
- `idx_termination_date` - Active exclusion queries

## Data Source

**Source**: SAM.gov (System for Award Management)  
**Website**: https://sam.gov/  
**Data Services**: https://sam.gov/data-services/Exclusions  
**Format**: CSV export (Public Extract V2)  
**Update Frequency**: Monthly  
**Authority**: U.S. General Services Administration  

## Use Cases

### 1. Bidder Screening
Verify bidders are not excluded before allowing auction participation.

### 2. Contractor Verification
Check if a contractor can receive federal contracts.

### 3. Due Diligence
Research potential business partners for federal compliance.

### 4. Compliance Reporting
Generate reports on exclusion trends and agency activity.

### 5. Risk Assessment
Identify exclusion patterns for risk management.

## Integration with Other Agents

### Bidder Verification Agent (Orchestration)

The Bidder Verification Agent automatically calls SAM tools:

```python
# User asks Bidder Verification agent: "Can John Smith bid?"
# Agent automatically:
1. Calls check_entity_status("John Smith") from SAM agent
2. Calls check_bidder_eligibility("John Smith") from OFAC agent
3. Combines both results
4. Returns unified eligibility determination
```

This demonstrates **agent orchestration** - one agent coordinating multiple specialized agents.

## Limitations

- Database must be manually updated when SAM.gov publishes new data
- Name matching is case-insensitive substring match (not fuzzy)
- Historical exclusions (terminated) are included but marked
- Some fields may be empty depending on exclusion type
- Does not include state or local contract exclusions

## Support

For questions or issues:
- **SAM.gov Help**: https://www.fsd.gov/gsafsd_sp
- **Agent Configuration**: `agents/sam/agent.py`
- **Tool Implementations**: `agents/sam/tools/`
- **Database Setup**: `data/DATABASE_SETUP.md`
- **Import Script**: `scripts/import_sam_data.py`
