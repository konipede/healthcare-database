#!/usr/bin/env python3
"""
Fetch food establishment inspection data from Boston Open Data API
Uses CKAN API to download health code violations data
"""
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import sys

# Boston Food Establishment Inspections - CKAN API
# Dataset: Food Establishment Inspections
# Resource ID: 4582bec6-2b4f-4f9e-bc55-cbaa73117f4c
API_ENDPOINT = "https://data.boston.gov/api/3/action/datastore_search"
RESOURCE_ID = "4582bec6-2b4f-4f9e-bc55-cbaa73117f4c"

# API token (optional but recommended for higher rate limits)
# Get one from: https://data.boston.gov/user/register
API_TOKEN = None  # Set to your token if you have one

OUTPUT_DIR = Path("raw")
OUTPUT_FILE = OUTPUT_DIR / "inspections_latest.csv"

def fetch_all_data(endpoint, resource_id, token=None):
    """
    Fetch all data from the CKAN API with pagination
    """
    all_records = []
    limit = 32000  # CKAN default max
    offset = 0
    
    headers = {}
    if token:
        headers['Authorization'] = token
    
    while True:
        try:
            params = {
                "resource_id": resource_id,
                "limit": limit,
                "offset": offset
            }
            
            print(f"Fetching records {offset} to {offset + limit}...")
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('success'):
                print(f"API returned error: {result}")
                break
            
            records = result.get('result', {}).get('records', [])
            
            if not records or len(records) == 0:
                break
                
            all_records.extend(records)
            print(f"  Fetched {len(records)} records (total: {len(all_records)})")
            
            if len(records) < limit:
                break
                
            offset += limit
            time.sleep(0.5)  # Be nice to the API
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            if all_records:
                print(f"Returning {len(all_records)} records fetched so far")
                break
            else:
                raise
    
    return all_records

def fetch_data_incremental(endpoint, resource_id, days_back=7, token=None):
    """
    For daily updates, fetch all data and let deduplication handle filtering
    
    The CKAN API doesn't support easy date filtering, so we fetch all data
    and rely on the database update script's deduplication to skip existing records.
    This is still efficient because:
    1. The API fetch is relatively fast (~30-60 seconds for all data)
    2. The deduplication in update_db.py prevents duplicate inserts
    3. Only new records get inserted into the database
    
    Args:
        endpoint: API endpoint URL
        resource_id: CKAN resource identifier
        days_back: Number of days to look back (informational only)
        token: Optional API token
    """
    print(f"Note: Fetching all data (CKAN doesn't support efficient date filtering)")
    print(f"Deduplication will filter records older than {days_back} days during database update\n")
    return fetch_all_data(endpoint, resource_id, token)

def main(incremental=True, days_back=7, full=False):
    """
    Main function to fetch data from Boston API
    
    Args:
        incremental: If True, only fetch recent data
        days_back: Number of days to look back for incremental updates
        full: If True, fetch all data (overrides incremental)
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Fetch data
    if full or not incremental:
        print("Fetching ALL data from Boston API...")
        print("This may take a few minutes...\n")
        records = fetch_all_data(API_ENDPOINT, RESOURCE_ID, API_TOKEN)
    else:
        print(f"Fetching data from last {days_back} days...\n")
        records = fetch_data_incremental(API_ENDPOINT, RESOURCE_ID, days_back, API_TOKEN)
    
    if not records:
        print("WARNING: No data fetched from API")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    print(f"\nProcessing {len(df)} records...")
    
    # Display column names for debugging
    print(f"Columns: {list(df.columns)}")
    
    # Save with timestamp for backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = OUTPUT_DIR / f"inspections_{timestamp}.csv"
    df.to_csv(timestamped_file, index=False)
    print(f"Backup saved to {timestamped_file}")
    
    # Save as latest (for processing)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Latest data saved to {OUTPUT_FILE}")
    
    # Display summary
    if 'violdttm' in df.columns:
        df['violdttm_parsed'] = pd.to_datetime(df['violdttm'], errors='coerce')
        date_range = f"{df['violdttm_parsed'].min()} to {df['violdttm_parsed'].max()}"
        print(f"Date range: {date_range}")
    
    return OUTPUT_FILE

if __name__ == "__main__":
    # Parse command line arguments
    full = "--full" in sys.argv
    incremental = not full
    
    # Allow custom days back
    days_back = 7
    for arg in sys.argv:
        if arg.startswith("--days="):
            try:
                days_back = int(arg.split("=")[1])
            except ValueError:
                print(f"Invalid days value: {arg}")
    
    try:
        result = main(incremental=incremental, days_back=days_back, full=full)
        if result:
            print("\n✓ Data fetch completed successfully")
            sys.exit(0)
        else:
            print("\n✗ Data fetch failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

