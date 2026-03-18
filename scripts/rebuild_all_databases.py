#!/usr/bin/env python3
"""
Master Database Rebuild Script
Rebuilds all SQLite databases from source files in data/source/

This script rebuilds:
1. SAM.gov Exclusions Database (sam_exclusions.db)
2. OFAC SDN Database (ofac_sdn.db)

Note: GRES PostgreSQL database must be restored separately via Docker.
"""
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

def rebuild_all():
    """Rebuild all SQLite databases from source files"""
    print("=" * 80)
    print("RealtyIQ Database Rebuild - All SQLite Databases")
    print("=" * 80)
    print()
    print("This will rebuild:")
    print("  1. SAM.gov Exclusions Database (~167K records, 2-3 minutes)")
    print("  2. OFAC SDN Database (~18.7K records, 30-60 seconds)")
    print()
    print("Source files location: data/source/")
    print("Target databases: data/")
    print()
    
    # Verify source files exist
    sam_csv = REPO_ROOT / "data" / "source" / "SAM_Exclusions_Public_Extract_V2.CSV"
    ofac_csv = REPO_ROOT / "data" / "source" / "sdn.csv"
    
    missing_files = []
    if not sam_csv.exists():
        missing_files.append(f"  - {sam_csv}")
    if not ofac_csv.exists():
        missing_files.append(f"  - {ofac_csv}")
    
    if missing_files:
        print("ERROR: Missing source files:")
        for f in missing_files:
            print(f)
        print()
        print("Please ensure source CSV files are in data/source/ directory.")
        print("See data/DATABASE_SETUP.md for download instructions.")
        sys.exit(1)
    
    print("✓ All source files found")
    print()
    
    # Confirm before proceeding
    try:
        response = input("Proceed with rebuild? This will take 3-4 minutes (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled by user")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled by user")
        sys.exit(0)
    
    print()
    success_count = 0
    total_records = 0
    
    # ===== 1. SAM.gov Exclusions =====
    try:
        print("=" * 80)
        print("STEP 1/2: Building SAM.gov Exclusions Database")
        print("=" * 80)
        print()
        
        # Import and run SAM import
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from import_sam_data import import_sam_exclusions
        
        import_sam_exclusions()
        success_count += 1
        
        # Get record count
        import sqlite3
        conn = sqlite3.connect(REPO_ROOT / "data" / "sam_exclusions.db")
        cursor = conn.execute("SELECT COUNT(*) FROM exclusions")
        sam_records = cursor.fetchone()[0]
        total_records += sam_records
        conn.close()
        
        print()
    except Exception as e:
        print(f"ERROR: Failed to build SAM database: {e}")
        print()
    
    # ===== 2. OFAC SDN =====
    try:
        print("=" * 80)
        print("STEP 2/2: Building OFAC SDN Database")
        print("=" * 80)
        print()
        
        # Import and run OFAC import
        sys.path.insert(0, str(REPO_ROOT / "agents" / "ofac"))
        from import_sdn_csv import import_sdn_data
        
        import_sdn_data()
        success_count += 1
        
        # Get record count
        import sqlite3
        conn = sqlite3.connect(REPO_ROOT / "data" / "ofac_sdn.db")
        cursor = conn.execute("SELECT COUNT(*) FROM sdn_list")
        ofac_records = cursor.fetchone()[0]
        total_records += ofac_records
        conn.close()
        
        print()
    except Exception as e:
        print(f"ERROR: Failed to build OFAC database: {e}")
        print()
    
    # ===== Summary =====
    print("=" * 80)
    print("DATABASE REBUILD SUMMARY")
    print("=" * 80)
    if success_count == 2:
        print(f"✅ SUCCESS: All {success_count} databases rebuilt successfully!")
    else:
        print(f"⚠️  WARNING: Only {success_count}/2 databases built successfully")
    print()
    print(f"Total records imported: {total_records:,}")
    print()
    
    # Show database sizes
    sam_db = REPO_ROOT / "data" / "sam_exclusions.db"
    ofac_db = REPO_ROOT / "data" / "ofac_sdn.db"
    
    if sam_db.exists():
        sam_size = sam_db.stat().st_size / (1024 * 1024)
        print(f"  - sam_exclusions.db: {sam_size:.1f} MB ({sam_records:,} records)")
    
    if ofac_db.exists():
        ofac_size = ofac_db.stat().st_size / (1024 * 1024)
        print(f"  - ofac_sdn.db: {ofac_size:.1f} MB ({ofac_records:,} records)")
    
    print()
    print("Databases are ready to use!")
    print()
    print("Next steps:")
    print("  - Test SAM agent: python run_agent.py --agent sam")
    print("  - Test OFAC agent: python run_agent.py --agent ofac")
    print("  - Test Bidder Verification: python run_agent.py --agent bidder_verification")
    print()
    print("For GRES PostgreSQL database setup, see data/DATABASE_SETUP.md")
    print("=" * 80)

if __name__ == "__main__":
    rebuild_all()
