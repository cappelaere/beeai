# Database Setup Guide

Complete instructions for setting up and rebuilding all RealtyIQ databases from source files.

## Overview

RealtyIQ uses three databases:

| Database | Type | Size | Purpose | Agent(s) |
|----------|------|------|---------|----------|
| **GRES Database** | PostgreSQL | 5.2 MB SQL | Auction/property data | GRES Agent |
| **SAM Exclusions** | SQLite | 80 MB | Federal contract exclusions | SAM Agent, Bidder Verification |
| **OFAC SDN** | SQLite | 7.7 MB | Sanctions screening | OFAC Agent, Bidder Verification |

## Quick Start - Rebuild Everything

### Option 1: Automated (Recommended)

```bash
cd /path/to/beeai

# Rebuild both SQLite databases
python scripts/rebuild_all_databases.py

# Restore PostgreSQL (via Docker)
make restore-db
```

### Option 2: Manual Step-by-Step

```bash
# 1. SAM Exclusions
python scripts/import_sam_data.py

# 2. OFAC SDN
python agents/ofac/import_sdn_csv.py

# 3. GRES PostgreSQL (via Docker)
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql
```

---

## Database 1: GRES Auction Database (PostgreSQL)

### Purpose
Stores GSA Real Estate Sales auction and property data including:
- Properties (descriptions, locations, valuations)
- Auctions (dates, status, reserve prices)
- Bids and bidder information
- Agents and performance metrics
- Network domains and sites

### Source File
- **Location**: `data/source/latest_db.sql`
- **Format**: PostgreSQL dump
- **Size**: 5.2 MB
- **Records**: ~50,000+ across multiple tables

### Setup via Docker Compose

#### Method 1: Automatic Restore (Docker Compose)

Add init volume to `docker-compose.yml` under the `db` service:

```yaml
db:
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./data/source/latest_db.sql:/docker-entrypoint-initdb.d/init.sql  # Add this
```

Then run:
```bash
docker-compose down -v  # Remove existing volumes
docker-compose up -d db  # Recreate with init script
```

#### Method 2: Manual Restore (Running Container)

```bash
# Start PostgreSQL container
docker-compose up -d db

# Wait for database to be ready (10-15 seconds)
sleep 15

# Restore database
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql
```

### Verification

```bash
# Connect to database
docker exec -it beeai-postgres psql -U postgres -d gres_db

# Check tables
\dt

# Count properties
SELECT COUNT(*) FROM auction_property;

# Exit
\q
```

### Expected Tables

The database should contain these key tables:
- `auction_property` - Property listings
- `auction_auction` - Auction events
- `auction_bid` - Bid history
- `auction_agent` - Agent information
- `auction_networkdomain` - Network domains
- Many more Django models...

### Connection Details

From `.env` and `Api/.env`:
- **Host**: localhost
- **Port**: 8080 (mapped from container's 5432)
- **Database**: gres_db
- **Username**: postgres
- **Password**: (see Api/.env)

### Updating Data

To create a new PostgreSQL dump:

```bash
# Export from running container
docker exec -t beeai-postgres pg_dump -U postgres gres_db > data/source/latest_db.sql

# Or from remote database
pg_dump -h remote-host -U postgres gres_db > data/source/latest_db.sql
```

---

## Database 2: SAM Exclusions (SQLite)

### Purpose
Federal contract exclusions database from SAM.gov. Used to verify if bidders are excluded from federal contracting.

### Source File
- **Location**: `data/source/SAM_Exclusions_Public_Extract_V2.CSV`
- **Format**: CSV export from SAM.gov
- **Size**: 69 MB
- **Records**: ~167,000 exclusions
- **Download**: https://sam.gov/data-services/Exclusions

### Database File
- **Location**: `data/sam_exclusions.db`
- **Size**: 80 MB (includes indexes)
- **Format**: SQLite 3

### Database Schema

```sql
CREATE TABLE exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classification TEXT,              -- Individual, Firm, Vessel, etc.
    name TEXT,                        -- Full name
    prefix TEXT, first TEXT, middle TEXT, last TEXT, suffix TEXT,
    address_1 TEXT, address_2 TEXT, address_3 TEXT, address_4 TEXT,
    city TEXT, state_province TEXT, country TEXT, zip_code TEXT,
    unique_entity_id TEXT,            -- UEI
    exclusion_program TEXT,
    excluding_agency TEXT,            -- Agency that issued exclusion
    ct_code TEXT,
    exclusion_type TEXT,              -- Type of exclusion
    additional_comments TEXT,
    active_date TEXT,                 -- When exclusion started
    termination_date TEXT,            -- When exclusion ends (or 'Indefinite')
    record_status TEXT,
    cross_reference TEXT,
    sam_number TEXT,                  -- Unique SAM identifier
    cage TEXT, npi TEXT,
    creation_date TEXT,
    UNIQUE(sam_number, name, unique_entity_id)
);

-- Indexes for performance
CREATE INDEX idx_name ON exclusions(name);
CREATE INDEX idx_uei ON exclusions(unique_entity_id);
CREATE INDEX idx_classification ON exclusions(classification);
CREATE INDEX idx_excluding_agency ON exclusions(excluding_agency);
CREATE INDEX idx_active_date ON exclusions(active_date);
CREATE INDEX idx_sam_number ON exclusions(sam_number);
CREATE INDEX idx_termination_date ON exclusions(termination_date);
```

### Import Process

```bash
# Run import script
python scripts/import_sam_data.py
```

**What it does:**
1. Creates database if it doesn't exist
2. Creates table schema with indexes
3. Imports all CSV rows (takes 2-3 minutes)
4. Commits in batches of 10,000 for performance
5. Shows statistics and verification

**Expected output:**
```
SAM.gov Exclusions Database Import
Source: SAM_Exclusions_Public_Extract_V2.CSV
Target: data/sam_exclusions.db

Creating table schema...
Creating indexes...
Importing CSV data...
  Progress: 10,000 records imported...
  Progress: 20,000 records imported...
  ...
  Progress: 160,000 records imported...

Import complete: 167,XXX records processed
Database contains 167,XXX exclusion records

Breakdown by classification:
  - Firm: 120,000+
  - Individual: 45,000+
  - Vessel: 1,000+
  ...

Database file size: 80.0 MB
Import successful! Database ready for use.
```

### Verification

```bash
# Check database exists
ls -lh data/sam_exclusions.db

# Query via Python
python -c "
import sqlite3
conn = sqlite3.connect('data/sam_exclusions.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM exclusions')
print(f'Total exclusions: {cursor.fetchone()[0]:,}')
conn.close()
"
```

### Updating Data

SAM.gov updates exclusions regularly:

1. Download latest CSV:
   - Go to https://sam.gov/data-services/Exclusions
   - Click "Download" for Public Extract V2
   - Save as `data/source/SAM_Exclusions_Public_Extract_V2.CSV`

2. Rebuild database:
   ```bash
   # Backup existing
   cp data/sam_exclusions.db data/sam_exclusions.db.backup
   
   # Rebuild
   python scripts/import_sam_data.py
   ```

3. Verify new data:
   ```bash
   python run_agent.py --agent sam
   # Ask: "How many exclusions are in the database?"
   ```

---

## Database 3: OFAC SDN List (SQLite)

### Purpose
Office of Foreign Assets Control (OFAC) Specially Designated Nationals (SDN) list. Used to screen bidders against U.S. sanctions.

### Source File
- **Location**: `data/source/sdn.csv`
- **Format**: CSV from OFAC
- **Size**: 3.0 MB
- **Records**: ~18,700 individuals and entities
- **Download**: https://sanctionssearch.ofac.treas.gov/

### Database File
- **Location**: `data/ofac_sdn.db`
- **Size**: 7.7 MB (includes indexes and normalized names)
- **Format**: SQLite 3

### Database Schema

```sql
CREATE TABLE sdn_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE NOT NULL,   -- OFAC entity ID (e.g., "6365")
    name TEXT NOT NULL,               -- Full name as published
    entity_type TEXT,                 -- 'individual' or 'entity'
    program TEXT,                     -- Sanctions program (CUBA, SDGT, etc.)
    remarks TEXT,                     -- Additional identifying information
    name_normalized TEXT,             -- Lowercase, no punctuation (for fuzzy matching)
    import_date TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fuzzy search performance
CREATE INDEX idx_sdn_entity_id ON sdn_list(entity_id);
CREATE INDEX idx_sdn_name ON sdn_list(name);
CREATE INDEX idx_sdn_name_normalized ON sdn_list(name_normalized);
CREATE INDEX idx_sdn_entity_type ON sdn_list(entity_type);
CREATE INDEX idx_sdn_program ON sdn_list(program);
```

### Import Process

```bash
# Run import script
python agents/ofac/import_sdn_csv.py
```

**What it does:**
1. Creates database if it doesn't exist
2. Creates table schema with indexes
3. Parses CSV (handles varying column counts)
4. Normalizes names for fuzzy matching
5. Imports all rows (takes 30-60 seconds)
6. Shows statistics by program and entity type

**Expected output:**
```
OFAC SDN List Database Import
Source: data/source/sdn.csv
Target: data/ofac_sdn.db

Creating database schema...
Parsing CSV file...
Importing SDN records...
  Progress: 5,000 records imported...
  Progress: 10,000 records imported...
  Progress: 15,000 records imported...

Import complete: 18,708 records processed

Verification:
  Database contains 18,708 SDN entries
  
Breakdown by entity type:
  - entity: 9,519
  - individual: 9,189

Top sanctions programs:
  - RUSSIA-EO14024: 5,738
  - SDGT: 2,114
  - SDNTK: 1,389
  - GLOMAG: 734
  - NPWMD: 588

Database file size: 7.7 MB
Import successful!
```

### Verification

```bash
# Check database
ls -lh data/ofac_sdn.db

# Query via Python
python -c "
import sqlite3
conn = sqlite3.connect('data/ofac_sdn.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM sdn_list')
print(f'Total SDN entries: {cursor.fetchone()[0]:,}')
conn.close()
"

# Test via agent
python run_agent.py --agent ofac
# Ask: "How many entries are in the database?"
```

### Updating Data

OFAC updates the SDN list frequently (sometimes weekly):

1. Download latest CSV:
   - Go to https://sanctionssearch.ofac.treas.gov/
   - Export consolidated SDN list as CSV
   - Save as `data/source/sdn.csv`

2. Rebuild database:
   ```bash
   # Backup existing
   cp data/ofac_sdn.db data/ofac_sdn.db.backup
   
   # Rebuild
   python agents/ofac/import_sdn_csv.py
   ```

3. Verify:
   ```bash
   python run_agent.py --agent ofac
   # Ask: "Show me SDN statistics"
   ```

---

## Automated Rebuild Script

### Master Rebuild Script

**File**: `scripts/rebuild_all_databases.py`

Rebuilds both SQLite databases with one command:

```bash
python scripts/rebuild_all_databases.py
```

This script:
1. Calls `import_sam_data.import_sam_exclusions()`
2. Calls `import_sdn_csv.import_sdn_data()`
3. Shows combined statistics
4. Verifies both databases

**Runtime**: 3-4 minutes total

### Individual Scripts

```bash
# SAM only (2-3 minutes)
python scripts/import_sam_data.py

# OFAC only (30-60 seconds)
python agents/ofac/import_sdn_csv.py
```

---

## Database Sizes and Performance

### Disk Space Requirements

| Database | Source | Generated | Total |
|----------|--------|-----------|-------|
| GRES | 5.2 MB | Varies | ~500 MB (PostgreSQL) |
| SAM | 69 MB | 80 MB | 149 MB |
| OFAC | 3.0 MB | 7.7 MB | 10.7 MB |
| **Total** | **77 MB** | **~590 MB** | **~667 MB** |

### Import Times

| Database | Import Time | Notes |
|----------|-------------|-------|
| SAM Exclusions | 2-3 minutes | 167K records with indexes |
| OFAC SDN | 30-60 seconds | 18.7K records with normalization |
| GRES PostgreSQL | 30-60 seconds | Docker restore from SQL dump |

### Query Performance

All databases have appropriate indexes for fast queries:
- Name lookups: <10ms
- Fuzzy searches: <100ms
- Statistics: <50ms
- Full-text search: <200ms

---

## Troubleshooting

### Issue: CSV File Not Found

**Error**: `Error: CSV file not found at data/source/...`

**Solution**:
```bash
# Verify files exist
ls -lh data/source/

# Expected files:
# - SAM_Exclusions_Public_Extract_V2.CSV (69M)
# - sdn.csv (3.0M)
# - latest_db.sql (5.2M)
```

If missing, download from sources listed above.

### Issue: Database Already Exists

**Error**: Database creation fails due to existing file

**Solution**:
```bash
# Backup and remove old database
cp data/sam_exclusions.db data/sam_exclusions.db.backup
rm data/sam_exclusions.db

# Re-run import
python scripts/import_sam_data.py
```

### Issue: PostgreSQL Connection Refused

**Error**: Cannot connect to PostgreSQL for restoration

**Solution**:
```bash
# Ensure Docker container is running
docker ps | grep postgres

# If not running, start it
docker-compose up -d db

# Wait for database to initialize
sleep 15

# Then restore
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql
```

### Issue: Import Takes Too Long

**Solution**: This is normal for large datasets
- SAM import (167K records): Expected 2-3 minutes
- Progress shown every 10,000 records
- Commits done in batches for performance

### Issue: Database Size Unexpectedly Large

**Normal sizes:**
- `sam_exclusions.db`: 75-85 MB (includes 7 indexes)
- `ofac_sdn.db`: 7-10 MB (includes 5 indexes and normalized names)

If much larger, database may contain duplicates. Delete and reimport.

---

## Database Schemas and Statistics

### GRES Database (PostgreSQL)

**Key Tables:**
- `auction_property` - ~30K properties
- `auction_auction` - ~15K auctions
- `auction_bid` - ~100K+ bids
- `auction_agent` - ~500 agents
- `auction_user` - ~5K users

**Access:**
```python
# From tools (with API_URL env var)
from list_properties import list_properties
properties = list_properties(limit=10)

# Direct PostgreSQL
docker exec -it beeai-postgres psql -U postgres gres_db -c "SELECT COUNT(*) FROM auction_property;"
```

### SAM Exclusions Database (SQLite)

**Table**: `exclusions`

**Statistics:**
- Total records: ~167,000
- Firms: ~120,000
- Individuals: ~45,000
- Vessels: ~1,000
- Special Entity Designations: ~500

**Top Excluding Agencies:**
1. GSA (General Services Administration)
2. USAF (U.S. Air Force)
3. HHS (Health & Human Services)
4. DOJ (Department of Justice)
5. ARMY (U.S. Army)

**Access:**
```python
# Via SAM Agent tool
from agents.sam.tools.check_entity_status import check_entity_status
result = check_entity_status("John Smith")

# Direct SQLite
import sqlite3
conn = sqlite3.connect('data/sam_exclusions.db')
cursor = conn.execute("SELECT COUNT(*) FROM exclusions")
print(cursor.fetchone()[0])
```

### OFAC SDN Database (SQLite)

**Table**: `sdn_list`

**Statistics:**
- Total entries: ~18,700
- Individuals: ~9,200
- Entities: ~9,500

**Top Sanctions Programs:**
1. RUSSIA-EO14024: ~5,700
2. SDGT (Terrorists): ~2,100
3. SDNTK (Narcotics): ~1,400
4. GLOMAG (Magnitsky): ~730
5. NPWMD (WMD): ~590

**Access:**
```python
# Via OFAC Agent tool
from agents.ofac.tools.check_bidder_eligibility import check_bidder_eligibility
result = check_bidder_eligibility("John Smith")

# Direct SQLite
import sqlite3
conn = sqlite3.connect('data/ofac_sdn.db')
cursor = conn.execute("SELECT COUNT(*) FROM sdn_list")
print(cursor.fetchone()[0])
```

---

## Backup and Recovery

### Backing Up Databases

```bash
# Create backups directory
mkdir -p backups/$(date +%Y%m%d)

# Backup PostgreSQL
docker exec -t beeai-postgres pg_dump -U postgres gres_db > backups/$(date +%Y%m%d)/gres_db.sql

# Backup SQLite databases
cp data/sam_exclusions.db backups/$(date +%Y%m%d)/
cp data/ofac_sdn.db backups/$(date +%Y%m%d)/

# Backup source files
cp -r data/source/ backups/$(date +%Y%m%d)/source/
```

### Restoring from Backup

```bash
# Restore PostgreSQL
docker exec -i beeai-postgres psql -U postgres -d gres_db < backups/20260227/gres_db.sql

# Restore SQLite
cp backups/20260227/sam_exclusions.db data/
cp backups/20260227/ofac_sdn.db data/
```

### Disaster Recovery

If all databases are lost but source files remain:

```bash
# 1. Ensure source files exist
ls -lh data/source/

# 2. Rebuild all SQLite databases
python scripts/rebuild_all_databases.py

# 3. Restore PostgreSQL
docker-compose up -d db
sleep 15
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql

# 4. Verify all agents work
python run_agent.py --agent sam    # Test SAM
python run_agent.py --agent ofac   # Test OFAC
# Start UI and test GRES agent
```

---

## Maintenance Schedule

### Recommended Update Frequency

| Database | Update Frequency | Reason |
|----------|-----------------|--------|
| **GRES** | As needed | Internal data, updated when new auctions added |
| **SAM** | Monthly | SAM.gov publishes monthly extracts |
| **OFAC** | Weekly | OFAC updates list frequently during sanctions activity |

### Update Checklist

Weekly:
- [ ] Download latest `sdn.csv` from OFAC
- [ ] Run `python agents/ofac/import_sdn_csv.py`
- [ ] Verify OFAC agent works

Monthly:
- [ ] Download latest SAM Exclusions CSV
- [ ] Run `python scripts/import_sam_data.py`
- [ ] Verify SAM agent works

As Needed:
- [ ] Export GRES database: `pg_dump > data/source/latest_db.sql`
- [ ] Commit updated source files to git

---

## Development Workflow

### Initial Setup (New Developer)

```bash
# 1. Clone repository
git clone <repo-url>
cd beeai

# 2. Source files are in git, databases are not
ls -lh data/source/  # Should see 3 files

# 3. Build databases
python scripts/rebuild_all_databases.py

# 4. Start Docker services (includes PostgreSQL restore)
make docker-up

# 5. Verify
python run_agent.py --agent sam    # Should work
python run_agent.py --agent ofac   # Should work
./start-server.sh                  # Web UI should work
```

### Daily Development

Databases persist between restarts. Only rebuild if:
- Source data updates
- Database corruption
- Schema changes
- Testing import scripts

### Testing Changes

```bash
# Create test databases
cp data/sam_exclusions.db data/sam_exclusions_test.db
cp data/ofac_sdn.db data/ofac_sdn_test.db

# Modify import scripts and test
python scripts/import_sam_data.py  # Rebuilds from scratch

# If successful, commit changes
git add scripts/import_sam_data.py
git commit -m "Update SAM import script"
```

---

## References

### Data Sources

- **SAM.gov**: https://sam.gov/data-services/Exclusions
- **OFAC SDN**: https://sanctionssearch.ofac.treas.gov/
- **GRES API**: Internal GSA system

### Documentation

- SAM Agent: [`agents/sam/SKILLS.md`](../agents/sam/SKILLS.md)
- OFAC Agent: [`agents/ofac/SKILLS.md`](../agents/ofac/SKILLS.md)
- Bidder Verification: [`agents/bidder_verification/SKILLS.md`](../agents/bidder_verification/SKILLS.md)
- Data Folder: [`data/README.md`](README.md)

### Import Scripts

- SAM Import: [`scripts/import_sam_data.py`](../scripts/import_sam_data.py)
- OFAC Import: [`agents/ofac/import_sdn_csv.py`](../agents/ofac/import_sdn_csv.py)
- Master Rebuild: [`scripts/rebuild_all_databases.py`](../scripts/rebuild_all_databases.py)

---

## Summary

All databases can be completely rebuilt from source files in `data/source/`:
- ✅ **GRES**: Restore `latest_db.sql` to PostgreSQL
- ✅ **SAM**: Import `SAM_Exclusions_Public_Extract_V2.CSV` via Python script
- ✅ **OFAC**: Import `sdn.csv` via Python script

**One-command rebuild**: `python scripts/rebuild_all_databases.py`

For questions or issues, see the troubleshooting section above or check individual agent documentation.
