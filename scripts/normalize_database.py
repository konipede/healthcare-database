#!/usr/bin/env python3
"""
Normalize the database by creating a violation_codes table
This separates violation codes from their descriptions to eliminate redundancy
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("boston.db")

def main():
    """
    Migrate database to use normalized violation codes table
    """
    print("Starting database normalization...")
    print("="*70)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Step 1: Create violation_codes table
        print("\n1. Creating violation_codes table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violation_codes (
                code TEXT PRIMARY KEY,
                description TEXT
            )
        """)
        
        # Step 2: Populate violation_codes with unique code/description pairs
        print("2. Extracting unique violation codes and descriptions...")
        cursor.execute("""
            INSERT OR IGNORE INTO violation_codes (code, description)
            SELECT DISTINCT 
                COALESCE(violation_code, 'UNKNOWN') as code,
                violation_desc as description
            FROM violations
            WHERE violation_code IS NOT NULL
        """)
        
        # Also add the NULL case
        cursor.execute("""
            INSERT OR IGNORE INTO violation_codes (code, description)
            VALUES ('UNKNOWN', NULL)
        """)
        
        # Step 3: Get counts
        cursor.execute("SELECT COUNT(*) FROM violation_codes")
        code_count = cursor.fetchone()[0]
        print(f"   ✓ Created {code_count} unique violation codes")
        
        # Step 4: Show some examples
        print("\n3. Sample violation codes:")
        cursor.execute("""
            SELECT code, description 
            FROM violation_codes 
            WHERE code != 'UNKNOWN'
            ORDER BY code 
            LIMIT 5
        """)
        for code, desc in cursor.fetchall():
            print(f"   {code}: {desc}")
        
        # Step 5: Create index for performance
        print("\n4. Creating index on violation_codes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_violation_code 
            ON violation_codes(code)
        """)
        
        # Step 6: Verify data integrity
        print("\n5. Verifying data integrity...")
        
        # Check for violations with codes not in violation_codes table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM violations v
            LEFT JOIN violation_codes vc ON v.violation_code = vc.code
            WHERE v.violation_code IS NOT NULL AND vc.code IS NULL
        """)
        orphaned = cursor.fetchone()[0]
        
        if orphaned > 0:
            print(f"   ⚠ Warning: {orphaned} violations have codes not in violation_codes table")
        else:
            print(f"   ✓ All violation codes are properly linked")
        
        # Show statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_violations,
                COUNT(DISTINCT violation_code) as unique_codes_in_violations,
                (SELECT COUNT(*) FROM violation_codes) as codes_in_lookup_table
            FROM violations
        """)
        stats = cursor.fetchone()
        
        print("\n" + "="*70)
        print("DATABASE STATISTICS:")
        print("="*70)
        print(f"Total violations: {stats[0]:,}")
        print(f"Unique codes in violations table: {stats[1]}")
        print(f"Codes in violation_codes table: {stats[2]}")
        
        conn.commit()
        
        print("\n✓ Database normalization complete!")
        print("\nNote: The violations table still contains violation_desc for now.")
        print("You can now query with JOINs to get code descriptions:")
        print("  SELECT v.*, vc.description FROM violations v")
        print("  JOIN violation_codes vc ON v.violation_code = vc.code")
        
        return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

