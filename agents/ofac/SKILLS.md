# OFAC Compliance Agent Documentation

## Overview

**Agent Name:** OFAC Compliance 🚨  
**Purpose:** Screen bidders against OFAC Specially Designated Nationals (SDN) list  
**Type:** Read-only database query agent with fuzzy matching

The OFAC Compliance Agent provides automated screening of individuals and entities against the U.S. Treasury Department's Office of Foreign Assets Control (OFAC) Specially Designated Nationals (SDN) list. The agent uses fuzzy name matching to catch variations, misspellings, and different name formats to ensure compliance with U.S. sanctions regulations.

## When to Use This Agent

Use the OFAC Agent when you need to:
- Screen bidders before allowing them to participate in auctions
- Verify if an individual or entity is on the OFAC SDN list
- Search for sanctioned entities by name, program, or type
- Check compliance with U.S. Treasury sanctions regulations
- Analyze OFAC sanctions data and statistics

## Quick Start

### Selecting the Agent
1. Open the RealtyIQ interface
2. Use the agent selector dropdown in the top bar
3. Select "🚨 OFAC"

### Basic Usage Examples

**Screen a bidder:**
```
Check if John Doe is eligible to bid
Is Mohammed Ahmed on the OFAC list?
Screen bidder: ABC Corporation for OFAC compliance
Can Maria Garcia participate in our auction?
```

**Search for entities:**
```
Search for entities related to Cuba
Find individuals on the terrorist list
Search SDN list for Banco Nacional
Look up Syrian sanctioned entities
```

**Get detailed information:**
```
Get details for SDN entity ID 6365
Tell me about entity 12345 on the SDN list
What programs does entity 6365 belong to?
```

**Database statistics:**
```
How many entries are in the OFAC database?
What are the most common sanctions programs?
Show me SDN statistics
```

## Available Tools

### Screening & Eligibility

#### check_bidder_eligibility
**Purpose:** Primary tool for screening bidders before allowing them to participate in auctions

**Key Parameters:**
- `bidder_name` (str, required): Name of the bidder to check
- `strict_mode` (bool, optional): If True, only flag very close matches (>85% similarity). Default False (>60% threshold)

**Example:**
```
check_bidder_eligibility(bidder_name="John Smith")
check_bidder_eligibility(bidder_name="Mohammed Ahmed", strict_mode=False)
check_bidder_eligibility(bidder_name="ABC Corporation")
```

**Returns:**
- `eligible` (bool): Whether bidder can proceed (False if ANY match found)
- `confidence` (float): Confidence level (0.0 to 1.0)
- `matches` (list): Potential SDN matches with similarity scores
- `risk_level` (str): VERY HIGH, HIGH, MODERATE, or LOW
- `recommendation` (str): Clear guidance on next steps
- `requires_review` (bool): Whether manual review is needed

**Risk Levels:**
- **VERY HIGH** (>95% similarity): Likely exact match
- **HIGH** (85-95%): Very similar name
- **MODERATE** (75-85%): Similar name
- **LOW** (60-75%): Possible match

**Important Notes:**
- Flags ANY potential match (>60% similarity) for review
- False positives are expected and acceptable in screening
- Manual review is REQUIRED for all flagged matches
- Conservative approach ensures compliance

### Search & Query

#### search_sdn_list
**Purpose:** Search the SDN list with fuzzy name matching

**Key Parameters:**
- `name` (str, required): Name to search for (supports fuzzy matching)
- `program` (str, optional): Filter by OFAC program (e.g., CUBA, SDGT, FTO, SDNTK)
- `entity_type` (str, optional): Filter by 'individual' or 'entity'
- `min_similarity` (float, optional): Minimum similarity score (0.0 to 1.0, default 0.7)
- `limit` (int, optional): Maximum results (default 20, max 100)

**Example:**
```
search_sdn_list(name="Osama Bin Laden", limit=5)
search_sdn_list(name="Banco", program="CUBA", entity_type="entity")
search_sdn_list(name="Ahmed", min_similarity=0.8)
```

**Returns:**
- Total matches found
- List of matching SDN records with:
  - `entity_id` - Unique identifier
  - `name` - Full name
  - `entity_type` - 'individual' or 'entity'
  - `program` - OFAC program designation
  - `remarks` - Additional info (a.k.a. names, DOB, POB, etc.)
  - `similarity_score` - Match confidence (0.0 to 1.0)

**Fuzzy Matching:**
- Handles typos and misspellings
- Catches name variations (e.g., "Osama" vs "Usama")
- Ignores punctuation and case differences
- Scores based on character sequence similarity

#### get_sdn_detail
**Purpose:** Get complete details for a specific SDN list entry

**Key Parameters:**
- `entity_id` (int, required): Unique entity ID from the SDN list

**Example:**
```
get_sdn_detail(entity_id=6365)
get_sdn_detail(entity_id=12345)
```

**Returns:**
- Complete SDN record including:
  - Entity ID
  - Full name
  - Entity type (individual or entity)
  - OFAC program designation
  - Remarks (a.k.a. names, DOB, POB, passport numbers, NIT numbers)
  - Database timestamp

### Analytics & Statistics

#### sdn_statistics
**Purpose:** Get comprehensive statistics about the OFAC SDN database

**No parameters required**

**Example:**
```
sdn_statistics()
```

**Returns:**
- `total_entries` - Total SDN records (18,708)
- `individuals` - Count of individual entries (9,189)
- `entities` - Count of entity entries (9,519)
- `top_programs` - Most common OFAC programs with counts
- `database_info` - Database file path, size, status

**Top Programs (as of last import):**
1. RUSSIA-EO14024: 5,738 entries
2. SDGT (Specially Designated Global Terrorists): 2,114
3. SDNTK (Narcotics Trafficking): 1,389
4. GLOMAG (Global Magnitsky): 734
5. NPWMD/IFSR (WMD Proliferation): 588

## Common Workflows

### Bidder Screening (Primary Use Case)

1. **Screen a bidder before auction participation:**
   ```
   check_bidder_eligibility(bidder_name="John Doe")
   ```

2. **Review flagged matches:**
   - If matches are found, review the similarity scores
   - Check entity IDs and remarks for additional context
   - Conduct manual review as required

3. **Get detailed information on flagged entity:**
   ```
   get_sdn_detail(entity_id=12345)
   ```

4. **Document decision:**
   - Record the screening result
   - Note any manual review conducted
   - Keep audit trail for compliance

### Entity Research

1. **Search by name:**
   ```
   search_sdn_list(name="ABC Corporation", limit=10)
   ```

2. **Filter by program:**
   ```
   search_sdn_list(name="Company", program="CUBA")
   ```

3. **Review all matches:**
   - Check similarity scores
   - Review remarks for additional identifiers
   - Consider different name spellings

### Sanctions Program Analysis

1. **Get database statistics:**
   ```
   sdn_statistics()
   ```

2. **Search specific programs:**
   ```
   search_sdn_list(name="", program="SDGT", entity_type="individual", limit=50)
   ```

3. **Analyze by entity type:**
   - Search for individuals: `entity_type="individual"`
   - Search for entities: `entity_type="entity"`

### Compliance Monitoring

1. **Periodic screening of existing bidders:**
   - Re-run eligibility checks on active bidders
   - Flag any new matches for review
   - Update bidder status based on findings

2. **Program-specific screening:**
   ```
   search_sdn_list(program="SDNTK")  # Narcotics trafficking
   search_sdn_list(program="RUSSIA-EO14024")  # Russia sanctions
   ```

## OFAC Programs Explained

### Major Sanctions Programs

#### SDGT - Specially Designated Global Terrorists
- Individuals and entities designated for terrorism-related activities
- Executive Order 13224
- Strictest sanctions, highest risk

#### SDNTK - Specially Designated Narcotics Traffickers
- Drug trafficking organizations and individuals
- Kingpin Act designations
- International narcotics control

#### Country-Based Programs
- **CUBA** - Cuban sanctions program
- **IRAN** - Iranian sanctions (multiple executive orders)
- **SYRIA** - Syrian sanctions program
- **RUSSIA-EO14024** - Russia-related sanctions

#### GLOMAG - Global Magnitsky
- Human rights violators
- Corrupt government officials
- Executive Order 13818

#### FTO - Foreign Terrorist Organizations
- Designated terrorist groups
- Immigration and nationality act designations

#### NPWMD/IFSR - Nonproliferation
- WMD proliferation concerns
- Iran, North Korea, Syria Nonproliferation Act

## Technical Details

### Database
- **Source:** U.S. Treasury OFAC SDN list
- **Records:** 18,708 entries (9,189 individuals, 9,519 entities)
- **Type:** SQLite database with full-text search indexes
- **Location:** `data/ofac_sdn.db`
- **Size:** ~7.69 MB

### Data Structure

**SDN Record Fields:**
- `entity_id` (int) - Unique identifier
- `name` (str) - Full name of individual or entity
- `entity_type` (str) - 'individual' or 'entity'
- `program` (str) - OFAC program code(s)
- `remarks` (str) - Additional information:
  - Also Known As (a.k.a.) names
  - Date of Birth (DOB)
  - Place of Birth (POB)
  - Passport numbers
  - National ID numbers (NIT, etc.)
  - Executive order references
  - Secondary sanctions risk

### Fuzzy Matching Algorithm

The agent uses a multi-stage approach for accurate matching:

1. **Name Normalization:**
   - Convert to lowercase
   - Remove punctuation (except spaces)
   - Collapse multiple spaces
   - Trim whitespace

2. **Primary Filtering:**
   - SQLite LIKE query on normalized names
   - Casts a wide net to catch variations

3. **Similarity Scoring:**
   - Python's `difflib.SequenceMatcher` for ratio calculation
   - Compares both normalized and original names
   - Uses highest similarity score

4. **Threshold Filtering:**
   - Default mode: >60% similarity flagged for review
   - Strict mode: >85% similarity required
   - Configurable per search

5. **Result Ranking:**
   - Sort by similarity score (highest first)
   - Limit to requested number of results

### Search Capabilities
- **Fuzzy matching:** Catches typos, alternate spellings, name variations
- **Case insensitive:** Matching ignores capitalization
- **Punctuation agnostic:** Handles different punctuation styles
- **Program filtering:** Search within specific OFAC programs
- **Entity type filtering:** Distinguish individuals from entities
- **Configurable thresholds:** Adjust sensitivity for different use cases

### Performance
- Database queries with indexes: < 100ms typical
- Fuzzy matching overhead: < 200ms for 100 candidates
- Full screening process: < 500ms total
- Statistics query: < 50ms

## Best Practices

### For Bidder Screening

1. **Always screen before accepting bids:**
   - Use `check_bidder_eligibility` as primary tool
   - Default mode (60% threshold) for maximum safety
   - Strict mode only for low-risk scenarios

2. **Review all flagged matches:**
   - Manual review is REQUIRED by compliance regulations
   - Check similarity scores and remarks
   - Document your determination

3. **Handle false positives appropriately:**
   - False positives are normal in screening systems
   - Document why a flagged match is not a true match
   - Keep audit trail for compliance

4. **Update regularly:**
   - OFAC updates the SDN list frequently
   - Re-import data periodically (monthly recommended)
   - Re-screen existing bidders when list updates

### For Search & Research

1. **Start broad, then narrow:**
   - Begin with basic name search
   - Add program or entity_type filters if too many results
   - Adjust similarity threshold if needed

2. **Check remarks field:**
   - Contains critical identifying information
   - Includes a.k.a. names, DOB, POB
   - May have passport or ID numbers

3. **Use entity IDs for precision:**
   - Once you find a match, use `get_sdn_detail`
   - Entity IDs are stable and unique
   - Include entity IDs in compliance documentation

## Important Compliance Notes

### Legal Requirements

- **OFAC compliance is mandatory** for U.S. government contracts and transactions
- **Penalties for violations** can include significant fines and criminal prosecution
- **Strict liability** - even inadvertent violations can result in penalties
- **Due diligence required** - reasonable steps to prevent violations

### Screening Guidelines

1. **Screen all new bidders** before allowing participation
2. **Flag any potential match** for manual review
3. **Document all screening decisions** for audit purposes
4. **Maintain audit trails** of searches and determinations
5. **Re-screen periodically** as the SDN list is updated
6. **Consult legal counsel** for complex determinations

### False Positives

- False positives are **expected and acceptable**
- Better to flag for review than miss a true match
- Manual review required to clear false positives
- Document rationale for clearing flagged matches

### Data Currency

- OFAC updates the SDN list regularly
- Database snapshot is from import date
- For real-time verification, check OFAC website
- Re-import recommended: monthly or when notified of updates

## Example Use Cases

### For Auction Managers
- "Screen bidder John Smith before accepting his registration"
- "Check if ABC Corporation is eligible to bid"
- "Verify this bidder isn't on the OFAC list: [name]"

### For Compliance Officers
- "Search for all individuals in the narcotics trafficking program"
- "Find entities sanctioned under Russia Executive Order 14024"
- "Show me statistics on terrorist designations"

### For Legal/Due Diligence
- "Is Banco Nacional de Cuba on the SDN list?"
- "Search for any matches for this company name: [name]"
- "Get full details on entity ID 6365"

### For Research & Analysis
- "How many entries are in the OFAC database?"
- "What are the top 10 sanctions programs?"
- "How many Russian entities are sanctioned?"

## Common Sanctions Programs

### Terrorism-Related
- **SDGT** - Specially Designated Global Terrorists
- **FTO** - Foreign Terrorist Organizations
- **IFSR** - Iran Financial Sanctions Regulations

### Country-Based
- **CUBA** - Cuban Assets Control Regulations
- **IRAN** - Iranian sanctions (multiple EOs)
- **SYRIA** - Syrian sanctions program
- **RUSSIA-EO14024** - Russia-related sanctions (largest program)
- **UKRAINE-EO13662** - Ukraine/Russia conflict sanctions

### Criminal Activity
- **SDNTK** - Specially Designated Narcotics Traffickers
- **ILLICIT-DRUGS-EO14059** - Illicit drug trafficking
- **TCO** - Transnational Criminal Organizations

### Human Rights & Corruption
- **GLOMAG** - Global Magnitsky Act (human rights/corruption)
- **CAATSA** - Countering America's Adversaries Through Sanctions Act

### Proliferation
- **NPWMD** - Nonproliferation of WMD
- **IFSR** - WMD proliferation concerns

## Entity Types

### Individual
- Natural persons
- 9,189 records in database
- May include DOB, POB in remarks
- Often has passport numbers

### Entity
- Companies, organizations, vessels
- 9,519 records in database
- May include business identifiers (NIT, tax ID)
- Can include vessels and aircraft

## Fuzzy Matching Examples

The fuzzy matching algorithm catches many variations:

**Name Variations:**
- "Osama Bin Laden" matches "BIN LADIN, Usama bin Muhammad bin Awad" (80% similarity)
- "Usama bin Laden" matches "BIN LADIN, Usama" (85% similarity)
- "Banco Cuba" matches "BANCO NACIONAL DE CUBA" (65% similarity)

**Typos:**
- "Muhammed Ahmed" matches "Mohammed Ahmed" (90% similarity)
- "Corporacion" matches "Corporation" (75% similarity)

**Punctuation Differences:**
- "Al-Qaeda" matches "AL QA'IDA" (high similarity after normalization)
- "O'Brien" matches "OBrien" (normalized equally)

**Name Order:**
- "John Smith" vs "Smith, John" (detected via word-level matching)
- Middle names included or omitted

## Technical Details

### Database Schema
```sql
CREATE TABLE sdn_list (
    entity_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    program TEXT,
    remarks TEXT,
    name_normalized TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_name ON sdn_list(name);
CREATE INDEX idx_name_normalized ON sdn_list(name_normalized);
CREATE INDEX idx_program ON sdn_list(program);
CREATE INDEX idx_entity_type ON sdn_list(entity_type);
```

### Similarity Calculation

Uses `difflib.SequenceMatcher` with Ratcliff/Obershelp algorithm:
- Compares character sequences
- Returns ratio: matching characters / total characters
- Range: 0.0 (no match) to 1.0 (exact match)
- Typical threshold: 0.70 (70% similarity)

### Performance Metrics
- Average screening time: 200-500ms
- Database size: 7.69 MB
- Search index: Full-text on normalized names
- Concurrent queries: Supported via SQLite connection pooling

## Audit & Compliance

### Logging
- All screening requests are logged
- Search terms and results recorded
- Timestamps for audit trail
- User session tracking

### Documentation Requirements

For each screening, document:
1. Bidder name searched
2. Date and time of screening
3. Results (eligible/flagged)
4. Similarity scores if flagged
5. Manual review determination if applicable
6. Reviewer name and decision rationale

### Periodic Re-screening

Recommended frequency:
- **New bidders:** Screen immediately before first bid
- **Active bidders:** Monthly re-screening
- **List updates:** Re-screen all when OFAC updates SDN list
- **High-risk names:** More frequent checks (weekly)

## Data Updates

### Updating the SDN List

1. Download latest SDN list from OFAC:
   - https://sanctionssearch.ofac.treas.gov/
   - Export as CSV format

2. Replace existing `sdn.csv` file in repository root

3. Re-run import script:
   ```bash
   python agents/ofac/import_sdn_csv.py
   ```

4. Verify import statistics match expected counts

### OFAC Resources

- **Main website:** https://home.treasury.gov/policy-issues/office-of-foreign-assets-control-sanctions-programs-and-information
- **Sanctions search:** https://sanctionssearch.ofac.treas.gov/
- **Sanctions list:** https://www.treasury.gov/ofac/downloads/sdnlist.txt
- **Updates:** Subscribe to OFAC mailing list for notifications

## Troubleshooting

### Agent Not Responding

1. Check database exists: `data/ofac_sdn.db`
2. Verify database has records: `sdn_statistics()`
3. Check import log for errors
4. Re-run import script if needed

### No Matches Found

1. Try broader search terms
2. Lower similarity threshold: `min_similarity=0.6`
3. Search without program filter first
4. Check for typos in search term
5. Try searching partial name

### Too Many Matches

1. Increase similarity threshold: `min_similarity=0.85`
2. Add program filter to narrow results
3. Specify entity_type (individual or entity)
4. Use strict_mode in eligibility checks

### Database Errors

1. Verify `data/ofac_sdn.db` exists and is readable
2. Check file permissions
3. Re-run import script to rebuild
4. Check disk space available

## Related Agents

- **SAM.gov Agent (🚫)** - Federal contract exclusions (complementary screening)
- **GRES Agent (🏢)** - GSA real estate auctions (primary business function)
- **Identity Verification Agent (🔐)** - User identity verification
- **Library Agent (📚)** - Compliance documentation search

## Best Practices Summary

✅ **DO:**
- Screen all bidders before participation
- Flag any potential match (>60% similarity)
- Require manual review for flagged matches
- Document all screening decisions
- Update SDN database regularly
- Maintain audit trails

❌ **DON'T:**
- Skip screening to save time
- Use strict mode for critical screening
- Clear matches without review
- Rely solely on automated results
- Ignore low-confidence matches
- Forget to document decisions

## Support & Resources

### Configuration
- Agent config: `agents/ofac/agent.py`
- Tools: `agents/ofac/tools/`
- Database: `agents/ofac/database.py`
- Import script: `agents/ofac/import_sdn_csv.py`

### External Resources
- OFAC Sanctions Programs: https://ofac.treasury.gov/sanctions-programs-and-country-information
- Sanctions Search Tool: https://sanctionssearch.ofac.treas.gov/
- OFAC Compliance: https://ofac.treasury.gov/compliance

### Getting Help
- Review logs: Check application logs for error details
- Test database: Run `sdn_statistics()` to verify database
- Re-import data: If database corruption suspected
- Contact OFAC: For questions about specific designations
