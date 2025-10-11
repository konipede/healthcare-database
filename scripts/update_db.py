#!/usr/bin/env python3
"""
Update database with new data from API fetch
Handles deduplication and incremental updates
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

DB_PATH = Path("boston.db")
CSV_PATH = Path("raw/inspections_latest.csv")
TABLE = "violations"

# CSV column to database column mapping
COLUMN_MAP = {
    "businessname": "business_name",
    "address": "address",
    "violation": "violation_code",
    "violdesc": "violation_desc",
    "violdttm": "date",
    "result": "status",
    # Neighborhood is not in the API data, will be NULL
}

def get_existing_records_hash(conn):
    """
    Create a set of hashes for existing records to detect duplicates
    Uses combination of key fields to identify unique violations
    """
    try:
        query = """
            SELECT business_name, address, violation_code, date
            FROM violations
        """
        df = pd.read_sql_query(query, conn)
        
        if len(df) == 0:
            return set()
        
        # Create a hash of key fields to identify duplicates
        df['record_hash'] = df.apply(
            lambda row: hash((
                str(row['business_name']).strip().lower() if pd.notna(row['business_name']) else '',
                str(row['address']).strip().lower() if pd.notna(row['address']) else '',
                str(row['violation_code']).strip() if pd.notna(row['violation_code']) else '',
                str(row['date']) if pd.notna(row['date']) else ''
            )),
            axis=1
        )
        return set(df['record_hash'].values)
    except Exception as e:
        print(f"Error getting existing records: {e}")
        return set()

def clean_and_map_data(df):
    """
    Clean and map CSV data to database schema
    """
    # Normalize headers (lowercase, replace spaces with underscores)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    print(f"CSV columns: {list(df.columns)}")
    
    # Map columns that exist
    available_src = [src for src in COLUMN_MAP if src in df.columns]
    missing_src = [src for src in COLUMN_MAP if src not in df.columns]
    
    if missing_src:
        print(f"Note: These expected columns were not found: {missing_src}")
    
    # Select and rename columns
    df = df[available_src].rename(columns={src: COLUMN_MAP[src] for src in available_src})
    
    # Clean violation_code
    if "violation_code" in df.columns:
        df["violation_code"] = df["violation_code"].astype(str).str.strip()
        # Replace 'nan' string with None
        df.loc[df["violation_code"] == 'nan', "violation_code"] = None
    
    # Clean and parse date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")
        # Replace 'NaT' string with None
        df.loc[df["date"] == 'NaT', "date"] = None
    
    # Clean business_name and address
    if "business_name" in df.columns:
        df["business_name"] = df["business_name"].astype(str).str.strip()
        df.loc[df["business_name"] == 'nan', "business_name"] = None
    
    if "address" in df.columns:
        df["address"] = df["address"].astype(str).str.strip()
        df.loc[df["address"] == 'nan', "address"] = None
    
    return df

def update_violation_codes(conn, df):
    """
    Update the violation_codes table with any new codes from the data
    
    Args:
        conn: Database connection
        df: DataFrame with violation data
    """
    # Extract unique code/description pairs
    if 'violation_code' in df.columns and 'violation_desc' in df.columns:
        # Get unique combinations
        code_desc = df[['violation_code', 'violation_desc']].drop_duplicates()
        code_desc = code_desc[code_desc['violation_code'].notna()]
        
        # Insert new codes (ignore if they already exist)
        inserted = 0
        for _, row in code_desc.iterrows():
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO violation_codes (code, description) VALUES (?, ?)",
                    (row['violation_code'], row['violation_desc'])
                )
                inserted += conn.total_changes
            except Exception as e:
                pass  # Ignore errors for existing codes
        
        if inserted > 0:
            print(f"  Added {inserted} new violation codes to lookup table")
        
        return inserted
    return 0

def main():
    """
    Main function to update database with new data
    """
    # Check if CSV file exists
    if not CSV_PATH.exists():
        print(f"ERROR: No data file found at {CSV_PATH}")
        print("Run fetch_api_data.py first to download data")
        return False
    
    # Read CSV
    print(f"Reading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df):,} records from CSV")
    
    if len(df) == 0:
        print("No records to process")
        return False
    
    # Clean and map data
    df = clean_and_map_data(df)
    print(f"Processed {len(df):,} records")
    
    # Create record hash for deduplication
    df['record_hash'] = df.apply(
        lambda row: hash((
            str(row.get('business_name', '')).strip().lower() if pd.notna(row.get('business_name')) else '',
            str(row.get('address', '')).strip().lower() if pd.notna(row.get('address')) else '',
            str(row.get('violation_code', '')).strip() if pd.notna(row.get('violation_code')) else '',
            str(row.get('date', '')) if pd.notna(row.get('date')) else ''
        )),
        axis=1
    )
    
    # Connect to database and filter duplicates
    print(f"\nConnecting to database: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        # First, update the violation_codes lookup table
        print("Updating violation codes lookup table...")
        update_violation_codes(conn, df)
        
        # Get existing record hashes
        print("Checking for duplicates...")
        existing_hashes = get_existing_records_hash(conn)
        print(f"Found {len(existing_hashes):,} existing unique records in database")
        
        # Filter out existing records
        new_records = df[~df['record_hash'].isin(existing_hashes)].copy()
        new_records = new_records.drop('record_hash', axis=1)
        
        if len(new_records) == 0:
            print("\n✓ No new records to insert (all records already exist)")
            return True
        
        # Insert new records
        print(f"\nInserting {len(new_records):,} new records...")
        new_records.to_sql(TABLE, conn, if_exists="append", index=False)
        
        # Get total count
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
        total = cur.fetchone()[0]
        
        print(f"\n✓ Successfully inserted {len(new_records):,} new records")
        print(f"✓ Skipped {len(df) - len(new_records):,} duplicate records")
        print(f"✓ Total records in database: {total:,}")
        
        return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

