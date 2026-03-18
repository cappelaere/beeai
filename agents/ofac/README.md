# OFAC Compliance Agent

Screen bidders against the U.S. Treasury Department's Office of Foreign Assets Control (OFAC) Specially Designated Nationals (SDN) list.

## Overview

The OFAC Compliance Agent provides automated screening of individuals and entities against the SDN list to ensure compliance with U.S. sanctions regulations. It uses fuzzy name matching to catch variations, misspellings, and different name formats.

## Database

- **Location**: `data/ofac_sdn.db`
- **Total Records**: 18,708 (as of last import)
- **Individuals**: 9,189
- **Entities**: 9,519

### Top Programs

1. RUSSIA-EO14024: 5,738
2. SDGT (Specially Designated Global Terrorists): 2,114
3. SDNTK (Narcotics): 1,389
4. GLOMAG (Global Magnitsky): 734
5. NPWMD/IFSR (WMD Proliferation): 588

## Tools

### 1. `check_bidder_eligibility`

**Primary screening tool** - Checks if a bidder is eligible to participate in auctions.

**Parameters**:
- `bidder_name` (required): Name of the bidder to check
- `strict_mode` (optional): If True, only flag very close matches (>85% similarity). Default False (>60% threshold)

**Returns**:
- `eligible`: Boolean indicating if bidder can proceed
- `confidence`: Confidence level (0.0 to 1.0)
- `matches`: List of potential SDN matches with similarity scores
- `recommendation`: Clear guidance on next steps
- `requires_review`: Whether manual review is needed

**Example**:
```python
check_bidder_eligibility(bidder_name="John Smith")
# Returns: eligible=True, no matches found

check_bidder_eligibility(bidder_name="Osama Bin Laden")
# Returns: eligible=False, requires_review=True, with match details
```

### 2. `search_sdn_list`

Search the SDN list with fuzzy matching.

**Parameters**:
- `name` (required): Name to search for
- `program` (optional): Filter by OFAC program (e.g., CUBA, SDGT, FTO)
- `entity_type` (optional): Filter by 'individual' or 'entity'
- `min_similarity` (optional): Minimum similarity score (default 0.7)
- `limit` (optional): Max results (default 20, max 100)

**Returns**: List of matching SDN records with similarity scores

### 3. `get_sdn_detail`

Get full details for a specific SDN entry.

**Parameters**:
- `entity_id` (required): The unique entity ID from the SDN list

**Returns**: Complete SDN record with all available information

### 4. `sdn_statistics`

Get statistics about the OFAC SDN database.

**Parameters**: None

**Returns**: Database statistics including total entries, top programs, etc.

## Setup

### 1. Import SDN Data

```bash
python agents/ofac/import_sdn_csv.py
```

This imports the `data/source/sdn.csv` file and creates the SQLite database at `data/ofac_sdn.db`.

For detailed setup instructions, see [`data/DATABASE_SETUP.md`](../../data/DATABASE_SETUP.md).

### 2. Register Agent

The agent is automatically registered when you:

1. Run the import script (creates database)
2. Apply database migration: `python manage.py migrate agent_app`

### 3. Access via UI

The OFAC agent appears in the agent selector dropdown in the web UI.

### 4. Access via CLI

```bash
python run_agent.py --agent ofac
```

## Fuzzy Matching Algorithm

The agent uses a multi-stage fuzzy matching approach:

1. **Name Normalization**: Convert to lowercase, remove punctuation, collapse spaces
2. **Primary Filtering**: SQLite LIKE query on normalized names
3. **Similarity Scoring**: Python's `difflib.SequenceMatcher` for ratio calculation
4. **Threshold Filtering**: Configurable similarity threshold (default 60-85%)
5. **Result Ranking**: Sort by highest similarity score

## Compliance Guidelines

- **Flag any potential match** for manual review, even with low confidence
- **False positives are expected** and acceptable in screening systems
- **Manual review is required** for all flagged matches before final determination
- **Document all decisions** for audit purposes
- **Update the SDN list regularly** as OFAC updates it frequently

## Example Queries

**Screen a bidder**:
```
"Check if John Doe is eligible to bid"
"Is ABC Corporation on the OFAC list?"
"Screen bidder: Mohammed Ahmed"
```

**Search for entities**:
```
"Search for entities related to Cuba"
"Find individuals on the terrorist list"
"Look up entity ID 6365"
```

**Get statistics**:
```
"How many entries are in the OFAC database?"
"What are the most common sanctions programs?"
```

## Data Source

The SDN list is maintained by the U.S. Department of the Treasury's Office of Foreign Assets Control (OFAC):
- **Website**: https://sanctionssearch.ofac.treas.gov/
- **Updates**: OFAC updates the list regularly; re-import periodically (weekly recommended)
- **CSV File**: Located at `data/source/sdn.csv`

For complete database setup and update procedures, see [`data/DATABASE_SETUP.md`](../../data/DATABASE_SETUP.md).

## Limitations

- Fuzzy matching may miss some variations or produce false positives
- Database must be manually updated when OFAC publishes new data
- Does not include consolidated or sectoral sanctions lists
- Manual review is always required for final eligibility determination

## Support

For questions or issues, refer to:
- OFAC Website: https://home.treasury.gov/policy-issues/office-of-foreign-assets-control-sanctions-programs-and-information
- Agent Configuration: `agents/ofac/agent.py`
- Tool Implementations: `agents/ofac/tools/`
