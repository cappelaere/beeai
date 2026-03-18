# SAM.gov Exclusions Agent

## Overview

The SAM.gov Exclusions Agent is a specialized AI agent for querying the System for Award Management (SAM) Exclusions database. It provides natural language access to federal contract exclusions data, making it easy to check if individuals or entities are excluded from receiving federal contracts.

**Agent Type:** `sam`  
**Icon:** 🚫  
**Database:** 138,885 exclusion records (as of import)

## Quick Start

### Web UI

1. Navigate to the chat interface
2. Select **"🚫 SAM.gov"** from the Agent dropdown in the top navbar
3. (Optional) Select your preferred model from the Model dropdown
4. Ask questions about exclusions

**Example queries:**
```
- "Search for exclusions by TREAS-OFAC"
- "Is ACME Corporation excluded?"
- "Show me exclusion statistics"
- "List all excluding agencies"
- "Find individuals named John Smith who are excluded"
```

### Command Line

```bash
python run_agent.py --agent sam

# With specific model
python run_agent.py --agent sam --model claude-3-5-opus
```

## Available Tools

The SAM.gov Agent has access to 6 specialized tools:

### 1. search_exclusions

Search the exclusions database with flexible filters.

**Parameters:**
- `name` (string): Individual or entity name (partial match)
- `classification` (string): Individual, Firm, Vessel, or Special Entity Designation
- `excluding_agency` (string): Agency code (e.g., TREAS-OFAC, DOJ, HHS)
- `exclusion_type` (string): Prohibition/Restriction, Ineligible, Voluntary Exclusion
- `country` (string): Country code (USA, CAN, etc.)
- `limit` (int): Maximum results to return (default 20, max 100)

**Example:**
```
"Search for firms excluded by HHS"
"Find all exclusions from Canada"
"Show me the last 50 exclusions"
```

### 2. get_exclusion_detail

Retrieve complete information about a specific exclusion.

**Parameters:**
- `sam_number` (string): SAM Number (e.g., S4MR3R7D6)
- `unique_entity_id` (string): Unique Entity Identifier

**Example:**
```
"Get details for SAM number S4MR3R7D6"
"Show me the full record for UEI XYZ123"
```

### 3. check_entity_status

Quick check if an individual or company is currently excluded.

**Parameters:**
- `entity_name` (string): Full or partial name to check

**Returns:** Active exclusion status and details

**Example:**
```
"Is John Doe excluded?"
"Check if ACME Corporation is excluded"
"Verify exclusion status for ABC Company"
```

### 4. list_excluding_agencies

Get a complete list of federal agencies that have issued exclusions.

**Parameters:** None

**Returns:** List of agencies with exclusion counts, sorted by count descending

**Example:**
```
"Which agencies have issued the most exclusions?"
"List all excluding agencies"
"Show me agency exclusion counts"
```

### 5. exclusion_statistics

Get statistical summary of the exclusions database.

**Parameters:** None

**Returns:**
- Total exclusion count
- Breakdown by classification (Individual, Firm, Vessel, Special Entity Designation)
- Breakdown by exclusion type
- Top 10 excluding agencies
- Termination status (indefinite vs. definite term)

**Example:**
```
"Show me exclusion statistics"
"What's the breakdown by classification?"
"How many exclusions are indefinite?"
```

### 6. ThinkTool

Reasoning and planning tool (available to all agents).

## Database Schema

The SAM.gov exclusions database contains the following key fields:

| Field | Description |
|-------|-------------|
| `classification` | Individual, Firm, Vessel, or Special Entity Designation |
| `name` | Full name of excluded entity |
| `unique_entity_id` | UEI (Unique Entity Identifier) |
| `sam_number` | SAM system identifier |
| `excluding_agency` | Federal agency code |
| `exclusion_type` | Type of exclusion |
| `exclusion_program` | Program under which excluded |
| `active_date` | Date exclusion became active |
| `termination_date` | End date (or "Indefinite") |
| `record_status` | Current status |
| `address_*` | Location information |
| `additional_comments` | Notes about the exclusion |

## Top Excluding Agencies

Based on the current database:

1. **HHS** (Health and Human Services): 66,271 exclusions
2. **TREAS-OFAC** (Treasury - Office of Foreign Assets Control): 40,973 exclusions
3. **OPM** (Office of Personnel Management): 16,209 exclusions
4. **DOJ** (Department of Justice): 2,988 exclusions
5. **EPA** (Environmental Protection Agency): 2,164 exclusions

## Classification Breakdown

- **Individual**: 106,555 records (76.7%)
- **Special Entity Designation**: 24,810 records (17.9%)
- **Firm**: 6,209 records (4.5%)
- **Vessel**: 1,311 records (0.9%)

## Common Use Cases

### 1. Vendor Due Diligence

Before entering into contracts, check if potential vendors are excluded:

```
"Check if ABC Construction Company is excluded"
"Verify exclusion status for vendors: Company A, Company B, Company C"
```

### 2. Compliance Screening

Organizations can use the agent to screen employees, contractors, or business partners:

```
"Search for any individuals named John Smith who are excluded"
"Show me all exclusions in New York state"
```

### 3. Research & Analysis

Analyze exclusion patterns and trends:

```
"Show me exclusion statistics"
"Which agencies exclude the most firms?"
"How many indefinite exclusions are there?"
```

### 4. Investigation Support

Get detailed information for specific cases:

```
"Get full details for SAM number S4MR3R7D6"
"Show me all TREAS-OFAC exclusions from 2023"
```

## Future Enhancements

### Phase 2: Live API Integration

The agent is designed to eventually transition from the local SQLite database to the live SAM.gov API:

- **Phase 1 (Current)**: Local SQLite database for fast queries
- **Phase 2 (Future)**: Hybrid approach - database for common queries, API for validation
- **Phase 3 (Future)**: Full live API integration using the SAM.gov OpenAPI specification

The OpenAPI spec is already available in `sam.gov.openapi.yaml` for future implementation.

### Additional Planned Features

- Exclusion history tracking
- Email notifications for new exclusions
- Advanced analytics and visualization
- Integration with other federal databases (USASpending, FedBizOpps)

## Data Sources

- **Primary Source**: SAM.gov Public Exclusions Extract V2
- **Format**: CSV (imported into SQLite)
- **Last Import**: 138,885 records
- **Update Frequency**: Database should be refreshed periodically from SAM.gov

To update the database:

```bash
# 1. Download latest CSV from SAM.gov
# 2. Replace SAM_Exclusions_Public_Extract_V2.CSV
# 3. Reimport data
python scripts/import_sam_data.py
```

## Technical Architecture

```
SAM.gov Agent
├── Agent Configuration (agents/sam/agent.py)
│   ├── Instructions: "You are SAM.gov Assistant..."
│   ├── Tools: 5 custom + 1 ThinkTool
│   └── Icon: 🚫
├── Tools (agents/sam/tools/)
│   ├── search_exclusions.py
│   ├── get_exclusion_detail.py
│   ├── check_entity_status.py
│   ├── list_excluding_agencies.py
│   └── exclusion_statistics.py
├── Database Layer (agents/sam/database.py)
│   ├── get_db_connection() - Context manager
│   └── dict_from_row() - Row converter
└── Data Storage (data/sam_exclusions.db)
    ├── exclusions table (28 fields)
    └── 8 indexes for performance
```

## Performance

- **Database Size**: ~80 MB (138,885 records)
- **Query Performance**: < 100ms for most searches (with indexes)
- **Index Coverage**: 8 indexes on common search fields
  - name, unique_entity_id, classification
  - excluding_agency, active_date, sam_number, termination_date
  
## Limitations

### Current Implementation (Phase 1)

- **Static Data**: Database is a snapshot and requires manual updates
- **No Real-Time Data**: Not connected to live SAM.gov API
- **CSV Format**: Source data is CSV (not structured API)
- **Limited Fields**: Only includes public extract fields

### Known Issues

- Some records have blank or null fields
- Termination dates may use "Indefinite" string or actual dates
- Address fields are split across 4 columns (Address 1-4)

## Support

For issues or questions about the SAM.gov Agent:

- Review the tool descriptions in the agent
- Check the database using `python test_sam_tools.py`
- Verify data integrity with `SELECT COUNT(*) FROM exclusions`

## Related Documentation

- [Multi-Agent Architecture](MULTI_AGENT_ARCHITECTURE.md)
- [Tools Documentation](tools.md)
- [SAM.gov OpenAPI Spec](../sam.gov.openapi.yaml)
- [Main README](../README.md)

## Agent Comparison

| Feature | GRES Agent (Default) | SAM.gov Agent |
|---------|---------------------|---------------|
| Purpose | Real estate auctions | Contract exclusions |
| Icon | 🏢 | 🚫 |
| Tools | 18 (API + RAG) | 6 (Database) |
| Data Source | API + Documents | SQLite database |
| Default | Yes | No |
| Records | ~Properties | 138,885 exclusions |

Use the **Agent dropdown** in the UI to switch between agents based on your task.
