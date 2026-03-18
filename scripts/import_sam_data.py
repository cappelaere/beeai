#!/usr/bin/env python3
"""
Import SAM.gov Exclusions CSV into SQLite database
"""
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

def import_sam_exclusions():
    """Import SAM Exclusions CSV into SQLite database"""
    
    csv_path = Path(__file__).parent.parent / "data" / "source" / "SAM_Exclusions_Public_Extract_V2.CSV"
    db_path = Path(__file__).parent.parent / "data" / "sam_exclusions.db"
    db_path.parent.mkdir(exist_ok=True)
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    print("=" * 80)
    print("SAM.gov Exclusions Database Import")
    print("=" * 80)
    print(f"Source: {csv_path.name}")
    print(f"Target: {db_path}")
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table matching CSV structure
    print("Creating table schema...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exclusions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification TEXT,
            name TEXT,
            prefix TEXT,
            first TEXT,
            middle TEXT,
            last TEXT,
            suffix TEXT,
            address_1 TEXT,
            address_2 TEXT,
            address_3 TEXT,
            address_4 TEXT,
            city TEXT,
            state_province TEXT,
            country TEXT,
            zip_code TEXT,
            unique_entity_id TEXT,
            exclusion_program TEXT,
            excluding_agency TEXT,
            ct_code TEXT,
            exclusion_type TEXT,
            additional_comments TEXT,
            active_date TEXT,
            termination_date TEXT,
            record_status TEXT,
            cross_reference TEXT,
            sam_number TEXT,
            cage TEXT,
            npi TEXT,
            creation_date TEXT,
            UNIQUE(sam_number, name, unique_entity_id)
        )
    ''')
    
    # Create indexes for common searches
    print("Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON exclusions(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_uei ON exclusions(unique_entity_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_classification ON exclusions(classification)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_excluding_agency ON exclusions(excluding_agency)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_active_date ON exclusions(active_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sam_number ON exclusions(sam_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_termination_date ON exclusions(termination_date)')
    
    # Import CSV data
    print("Importing CSV data...")
    print("(This may take 2-3 minutes for 167K records)")
    print()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        
        for row in reader:
            cursor.execute('''
                INSERT OR IGNORE INTO exclusions (
                    classification, name, prefix, first, middle, last, suffix,
                    address_1, address_2, address_3, address_4, city, state_province,
                    country, zip_code, unique_entity_id, exclusion_program,
                    excluding_agency, ct_code, exclusion_type, additional_comments,
                    active_date, termination_date, record_status, cross_reference,
                    sam_number, cage, npi, creation_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Classification'], row['Name'], row['Prefix'], row['First'],
                row['Middle'], row['Last'], row['Suffix'], row['Address 1'],
                row['Address 2'], row['Address 3'], row['Address 4'], row['City'],
                row['State / Province'], row['Country'], row['Zip Code'],
                row['Unique Entity ID'], row['Exclusion Program'],
                row['Excluding Agency'], row['CT Code'], row['Exclusion Type'],
                row['Additional Comments'], row['Active Date'],
                row['Termination Date'], row['Record Status'],
                row['Cross-Reference'], row['SAM Number'], row['CAGE'],
                row['NPI'], row['Creation_Date']
            ))
            
            count += 1
            if count % 10000 == 0:
                print(f"  Progress: {count:,} records imported...")
                conn.commit()
    
    conn.commit()
    print()
    print(f"✓ Import complete: {count:,} records processed")
    print()
    
    # Verify and show statistics
    print("Verifying database...")
    cursor.execute("SELECT COUNT(*) FROM exclusions")
    total = cursor.fetchone()[0]
    print(f"✓ Database contains {total:,} exclusion records")
    print()
    
    # Show breakdown by classification
    cursor.execute("""
        SELECT classification, COUNT(*) as count
        FROM exclusions
        GROUP BY classification
        ORDER BY count DESC
    """)
    print("Breakdown by classification:")
    for row in cursor.fetchall():
        print(f"  - {row[0] or '(blank)'}: {row[1]:,}")
    print()
    
    # Show top excluding agencies
    cursor.execute("""
        SELECT excluding_agency, COUNT(*) as count
        FROM exclusions
        WHERE excluding_agency IS NOT NULL AND excluding_agency != ''
        GROUP BY excluding_agency
        ORDER BY count DESC
        LIMIT 5
    """)
    print("Top 5 excluding agencies:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]:,}")
    print()
    
    # Database size
    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"Database file size: {db_size_mb:.1f} MB")
    print()
    print("=" * 80)
    print("✓ Import successful! Database ready for use.")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    import_sam_exclusions()
