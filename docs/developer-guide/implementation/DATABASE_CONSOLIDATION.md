# Database and Data Consolidation

## Summary

Reorganized all database source files, created comprehensive documentation, and ensured complete database rebuild procedures are documented and tested.

**Implementation Date:** February 27, 2026  
**Purpose:** Enable disaster recovery and easy database recreation  
**Status:** Complete ✅

## What Was Done

### 1. File Organization

**Before:**
```
beeai/
  latest_db.sql                    # PostgreSQL dump (root)
  SAM_Exclusions_Public_Extract_V2.CSV  # SAM data (root)
  sdn.csv                          # OFAC data (root)
  data/
    sam_exclusions.db              # Generated database
    ofac_sdn.db                    # Generated database
```

**After:**
```
beeai/
  data/
    source/                        # NEW: Source files (tracked in git)
      latest_db.sql                # MOVED: PostgreSQL dump
      SAM_Exclusions_Public_Extract_V2.CSV  # MOVED: SAM data
      sdn.csv                      # MOVED: OFAC data
    sam_exclusions.db              # Generated (gitignored)
    ofac_sdn.db                    # Generated (gitignored)
    README.md                      # NEW: Quick reference
    DATABASE_SETUP.md              # NEW: Complete guide
```

### 2. Documentation Created

#### A. `data/README.md`
Quick reference with:
- Folder structure diagram
- File sizes and record counts
- Quick rebuild commands
- Update procedures

#### B. `data/DATABASE_SETUP.md` (Comprehensive - 600+ lines)
Complete database setup guide with:
- **3 Database Sections**: GRES (PostgreSQL), SAM (SQLite), OFAC (SQLite)
- **Full schemas**: CREATE TABLE statements with indexes
- **Import procedures**: Step-by-step for each database
- **Verification commands**: How to test each database works
- **Troubleshooting**: Common issues and solutions
- **Backup/recovery**: Complete disaster recovery procedures
- **Maintenance schedule**: When and how to update each database
- **Performance specs**: Import times, sizes, query performance

#### C. `agents/sam/README.md`
SAM agent-specific documentation with:
- Tool descriptions
- Example queries
- Database statistics
- Integration with Bidder Verification agent

### 3. Scripts Updated

Updated import scripts to use new `data/source/` paths:

- **`scripts/import_sam_data.py`**: Line 13 updated
  ```python
  csv_path = Path(__file__).parent.parent / "data" / "source" / "SAM_Exclusions_Public_Extract_V2.CSV"
  ```

- **`agents/ofac/import_sdn_csv.py`**: Line 15 updated
  ```python
  CSV_PATH = REPO_ROOT / "data" / "source" / "sdn.csv"
  ```

### 4. Master Rebuild Script Created

**File**: `scripts/rebuild_all_databases.py`

One-command solution to rebuild both SQLite databases:
```bash
python scripts/rebuild_all_databases.py
```

Features:
- Verifies source files exist
- Asks for confirmation before proceeding
- Rebuilds SAM database (2-3 minutes)
- Rebuilds OFAC database (30-60 seconds)
- Shows progress and statistics
- Reports database sizes
- Provides next steps

### 5. Git Management

Updated `.gitignore`:
```gitignore
# Data - Ignore generated databases but keep source files
*.db
*.db-journal
!data/source/*.csv
!data/source/*.CSV
!data/source/*.sql
```

**Result:**
- Generated databases (`.db` files) are gitignored
- Source files in `data/source/` are tracked
- Enables disaster recovery via git

### 6. Main README Updated

Added **Data Management** section with:
- Quick overview of 3 databases
- One-command rebuild instructions
- Link to comprehensive DATABASE_SETUP.md
- Repository structure updated

## Database Overview

### Database 1: GRES (PostgreSQL)
- **Source**: `data/source/latest_db.sql` (5.2 MB)
- **Type**: PostgreSQL dump
- **Purpose**: Auction and property data
- **Restore**: Via Docker or psql command
- **Used by**: GRES Agent

### Database 2: SAM Exclusions (SQLite)
- **Source**: `data/source/SAM_Exclusions_Public_Extract_V2.CSV` (69 MB)
- **Generated**: `data/sam_exclusions.db` (80 MB)
- **Records**: ~167,000 federal contract exclusions
- **Import**: `python scripts/import_sam_data.py`
- **Used by**: SAM Agent, Bidder Verification Agent

### Database 3: OFAC SDN (SQLite)
- **Source**: `data/source/sdn.csv` (3.0 MB)
- **Generated**: `data/ofac_sdn.db` (7.7 MB)
- **Records**: ~18,700 sanctions designations
- **Import**: `python agents/ofac/import_sdn_csv.py`
- **Used by**: OFAC Agent, Bidder Verification Agent

## Quick Reference Commands

### Rebuild All Databases

```bash
# Both SQLite databases (3-4 minutes)
python scripts/rebuild_all_databases.py

# PostgreSQL GRES database
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql
```

### Rebuild Individual Databases

```bash
# SAM only (2-3 minutes)
python scripts/import_sam_data.py

# OFAC only (30-60 seconds)
python agents/ofac/import_sdn_csv.py
```

### Verify Databases

```bash
# Check files exist
ls -lh data/*.db

# Check record counts
python -c "import sqlite3; conn = sqlite3.connect('data/sam_exclusions.db'); print(f'SAM: {conn.execute(\"SELECT COUNT(*) FROM exclusions\").fetchone()[0]:,}'); conn.close()"
python -c "import sqlite3; conn = sqlite3.connect('data/ofac_sdn.db'); print(f'OFAC: {conn.execute(\"SELECT COUNT(*) FROM sdn_list\").fetchone()[0]:,}'); conn.close()"

# Test agents
python run_agent.py --agent sam    # SAM database
python run_agent.py --agent ofac   # OFAC database
```

## Disaster Recovery Procedure

If databases are lost but git repository is intact:

```bash
# 1. Source files are in git
cd beeai
ls -lh data/source/  # Verify files exist

# 2. Rebuild SQLite databases
python scripts/rebuild_all_databases.py

# 3. Restore PostgreSQL
docker-compose up -d db
sleep 15
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql

# 4. Verify
python run_agent.py --agent sam
python run_agent.py --agent ofac
./start-server.sh  # Test GRES agent in UI
```

**Recovery Time**: ~5 minutes total

## Files Created/Modified

### New Files (5)
1. `data/README.md` - Quick reference and folder overview
2. `data/DATABASE_SETUP.md` - Comprehensive 600+ line setup guide
3. `agents/sam/README.md` - SAM agent documentation
4. `scripts/rebuild_all_databases.py` - Master rebuild script
5. `DATABASE_CONSOLIDATION.md` - This file

### Modified Files (5)
1. `scripts/import_sam_data.py` - Updated CSV path to data/source/
2. `agents/ofac/import_sdn_csv.py` - Updated CSV path to data/source/
3. `README.md` - Added Data Management section
4. `.gitignore` - Added data file rules
5. Repository structure - Moved 3 files to data/source/

### Files Moved (3)
1. `latest_db.sql` → `data/source/latest_db.sql`
2. `SAM_Exclusions_Public_Extract_V2.CSV` → `data/source/SAM_Exclusions_Public_Extract_V2.CSV`
3. `sdn.csv` → `data/source/sdn.csv`

## Benefits Achieved

### 1. Organization
- All data files in one logical location (`data/`)
- Source files separated from generated databases
- Clear folder structure

### 2. Disaster Recovery
- Complete rebuild procedures documented
- Source files tracked in git
- One-command rebuild option available

### 3. Onboarding
- New developers can set up databases easily
- Clear documentation for each database
- Automated scripts reduce errors

### 4. Maintenance
- Update procedures documented
- Source URLs provided for data downloads
- Backup strategies included

### 5. Git-Friendly
- Large generated databases gitignored
- Essential source files tracked
- Reduces repository bloat

## Testing Results

✅ Source files moved successfully  
✅ Import scripts updated to new paths  
✅ All paths verified in scripts  
✅ Master rebuild script created and tested  
✅ Documentation complete and comprehensive  
✅ Git ignore rules configured correctly  

## Documentation Hierarchy

```
README.md
  └─→ Data Management section
       └─→ Links to: data/DATABASE_SETUP.md

data/DATABASE_SETUP.md (Master guide)
  ├─→ GRES PostgreSQL setup
  ├─→ SAM SQLite setup
  │    └─→ References: agents/sam/README.md
  └─→ OFAC SQLite setup
       └─→ References: agents/ofac/README.md

data/README.md (Quick reference)
  └─→ Links to: DATABASE_SETUP.md for details
```

## Validation Checklist

- [x] Source files in `data/source/` ✅
- [x] Databases in `data/` root ✅
- [x] Import scripts updated ✅
- [x] Scripts point to correct paths ✅
- [x] Documentation complete ✅
- [x] Git rules configured ✅
- [x] README updated ✅
- [x] Master rebuild script created ✅
- [x] All agents still work ✅

## Next Steps for New Setup

If starting from scratch:

```bash
# 1. Clone repo (source files come with it)
git clone <repo>
cd beeai

# 2. Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Build all databases
python scripts/rebuild_all_databases.py

# 4. Start services
docker-compose up -d

# 5. Restore GRES data
sleep 15
docker exec -i beeai-postgres psql -U postgres -d gres_db < data/source/latest_db.sql

# 6. Start UI
./start-server.sh
```

**Total Setup Time**: ~10 minutes

## Conclusion

All database source files are now:
- ✅ Organized in `data/source/` folder
- ✅ Tracked in git for disaster recovery
- ✅ Documented with complete rebuild procedures
- ✅ Accessible via automated rebuild scripts
- ✅ Properly separated from generated databases

**Result**: Complete database recreation is now fully documented and automated.
