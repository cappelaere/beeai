"""
Import OFAC SDN List from CSV to SQLite Database

This script parses the sdn.csv file and creates a searchable SQLite database
with fuzzy matching capabilities.
"""

import csv
import re
import sqlite3
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
CSV_PATH = REPO_ROOT / "data" / "source" / "sdn.csv"
DB_PATH = REPO_ROOT / "data" / "ofac_sdn.db"


def normalize_name(name: str) -> str:
    """
    Normalize name for fuzzy matching.
    - Convert to lowercase
    - Remove punctuation except spaces
    - Collapse multiple spaces
    - Strip whitespace
    """
    if not name:
        return ""
    # Convert to lowercase
    name = name.lower()
    # Remove punctuation except spaces
    name = re.sub(r"[^\w\s]", " ", name)
    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)
    # Strip
    return name.strip()


def parse_csv_row(row):
    """Parse a CSV row and extract relevant fields."""
    # Handle rows with varying column counts
    if len(row) < 4:
        return None

    entity_id = row[0].strip()
    name = row[1].strip() if len(row) > 1 else ""
    entity_type = row[2].strip() if len(row) > 2 else ""
    program = row[3].strip() if len(row) > 3 else ""
    remarks = row[11].strip() if len(row) > 11 else ""

    # Skip empty rows or invalid data
    if not entity_id or not name or entity_id == "-0-" or name == "-0-":
        return None

    # Clean up entity_type
    entity_type = "entity" if entity_type == "-0-" or entity_type == "" else "individual"

    # Clean up program
    if program == "-0-":
        program = ""

    # Clean up remarks
    if remarks == "-0-":
        remarks = ""

    return {
        "entity_id": int(entity_id),
        "name": name,
        "entity_type": entity_type,
        "program": program,
        "remarks": remarks,
        "name_normalized": normalize_name(name),
    }


def create_database():
    """Create the SQLite database and schema."""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database: {DB_PATH}")

    # Create new database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE sdn_list (
            entity_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            program TEXT,
            remarks TEXT,
            name_normalized TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for fast searching
    cursor.execute("CREATE INDEX idx_name ON sdn_list(name)")
    cursor.execute("CREATE INDEX idx_name_normalized ON sdn_list(name_normalized)")
    cursor.execute("CREATE INDEX idx_program ON sdn_list(program)")
    cursor.execute("CREATE INDEX idx_entity_type ON sdn_list(entity_type)")

    conn.commit()
    conn.close()

    print(f"Created database: {DB_PATH}")


def import_csv():
    """Import CSV data into the database."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    imported_count = 0
    skipped_count = 0

    print(f"Importing from: {CSV_PATH}")

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)

        for row_num, row in enumerate(reader, 1):
            parsed = parse_csv_row(row)

            if parsed is None:
                skipped_count += 1
                continue

            try:
                cursor.execute(
                    """
                    INSERT INTO sdn_list
                    (entity_id, name, entity_type, program, remarks, name_normalized)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        parsed["entity_id"],
                        parsed["name"],
                        parsed["entity_type"],
                        parsed["program"],
                        parsed["remarks"],
                        parsed["name_normalized"],
                    ),
                )
                imported_count += 1

                if imported_count % 1000 == 0:
                    print(f"Imported {imported_count} records...")

            except sqlite3.IntegrityError as e:
                print(f"Row {row_num}: Duplicate entity_id {parsed['entity_id']} - {e}")
                skipped_count += 1

    conn.commit()

    # Get statistics
    cursor.execute("SELECT COUNT(*) FROM sdn_list")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sdn_list WHERE entity_type = 'individual'")
    individuals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sdn_list WHERE entity_type = 'entity'")
    entities = cursor.fetchone()[0]

    cursor.execute(
        "SELECT program, COUNT(*) as count FROM sdn_list WHERE program != '' GROUP BY program ORDER BY count DESC LIMIT 10"
    )
    top_programs = cursor.fetchall()

    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"Total records imported: {imported_count}")
    print(f"Records skipped: {skipped_count}")
    print(f"Total in database: {total}")
    print(f"Individuals: {individuals}")
    print(f"Entities: {entities}")
    print("\nTop 10 Programs:")
    for program, count in top_programs:
        print(f"  {program}: {count}")
    print("=" * 60)


def main():
    """Main import process."""
    print("OFAC SDN List Import")
    print("=" * 60)
    print(f"CSV Source: {CSV_PATH}")
    print(f"Database Target: {DB_PATH}")
    print("=" * 60)

    # Create database
    create_database()

    # Import data
    import_csv()

    print("\nDatabase ready for use!")


if __name__ == "__main__":
    main()
