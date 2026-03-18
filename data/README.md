# Data Folder Overview

This folder contains all database files and source data for the RealtyIQ application.

## Folder Structure

```
data/
├── source/                          # Original source files (tracked in git)
│   ├── latest_db.sql               # PostgreSQL dump (GRES auction data)
│   ├── SAM_Exclusions_Public_Extract_V2.CSV  # SAM.gov exclusions data
│   └── sdn.csv                     # OFAC SDN list data
│
├── sam_exclusions.db               # Generated SQLite database (gitignored)
├── ofac_sdn.db                     # Generated SQLite database (gitignored)
├── README.md                       # This file
└── DATABASE_SETUP.md               # Complete setup instructions
```

## Quick Reference

| Database | Source File | Size | Records | Import Script |
|----------|-------------|------|---------|---------------|
| **GRES DB** (PostgreSQL) | `source/latest_db.sql` | 5.2 MB | ~50K+ | See docker-compose.yml |
| **SAM Exclusions** (SQLite) | `source/SAM_Exclusions_Public_Extract_V2.CSV` | 69 MB | ~167K | `scripts/import_sam_data.py` |
| **OFAC SDN** (SQLite) | `source/sdn.csv` | 3.0 MB | ~18.7K | `agents/ofac/import_sdn_csv.py` |

## Database Files (Generated)

These files are generated from source data and are **not tracked in git**:

- **`sam_exclusions.db`** (80 MB)
  - Federal contract exclusions database
  - Used by SAM Agent
  - Rebuild: `python scripts/import_sam_data.py`

- **`ofac_sdn.db`** (7.7 MB)
  - OFAC Specially Designated Nationals list
  - Used by OFAC Agent and Bidder Verification Agent
  - Rebuild: `python agents/ofac/import_sdn_csv.py`

## Source Files (Tracked in Git)

These files are the original data sources and **should be tracked in git**:

- **`source/latest_db.sql`** (5.2 MB)
  - PostgreSQL database dump
  - Contains GRES auction and property data
  - Restored automatically by docker-compose on first run

- **`source/SAM_Exclusions_Public_Extract_V2.CSV`** (69 MB)
  - SAM.gov federal contract exclusions export
  - Download from: https://sam.gov/data-services/Exclusions
  - Update frequency: Monthly

- **`source/sdn.csv`** (3.0 MB)
  - OFAC Specially Designated Nationals list
  - Download from: https://sanctionssearch.ofac.treas.gov/
  - Update frequency: Weekly (OFAC updates regularly)

## Quick Commands

### Rebuild All SQLite Databases
```bash
python scripts/rebuild_all_databases.py
```

### Rebuild Individual Databases
```bash
# SAM Exclusions only
python scripts/import_sam_data.py

# OFAC SDN only
python agents/ofac/import_sdn_csv.py
```

### Restore GRES PostgreSQL Database
```bash
# Via Docker Compose (automatic)
make docker-up

# Or manually
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql
```

## Complete Setup Instructions

See [`DATABASE_SETUP.md`](DATABASE_SETUP.md) for comprehensive database setup documentation including:
- Detailed rebuild procedures
- Database schemas
- Verification steps
- Troubleshooting
- Update procedures

## Updating Source Data

### SAM.gov Exclusions
1. Download latest CSV from https://sam.gov/data-services/Exclusions
2. Replace `source/SAM_Exclusions_Public_Extract_V2.CSV`
3. Run import: `python scripts/import_sam_data.py`

### OFAC SDN List
1. Download latest CSV from OFAC website
2. Replace `source/sdn.csv`
3. Run import: `python agents/ofac/import_sdn_csv.py`

### GRES Auction Data
1. Export from production PostgreSQL: `pg_dump gres_db > latest_db.sql`
2. Replace `source/latest_db.sql`
3. Restart Docker containers to reload

## Git Management

Source files in `source/` are tracked in git for disaster recovery.  
Generated `.db` files are gitignored (too large, can be rebuilt).

See `.gitignore` for complete rules.
