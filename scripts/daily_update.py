#!/usr/bin/env python3
"""
Master script to fetch API data and update database
Run this daily via cron for automated updates
"""
import sys
from pathlib import Path
from datetime import datetime
import importlib.util

# Get the scripts directory
SCRIPTS_DIR = Path(__file__).parent

def import_module_from_path(module_name, file_path):
    """
    Dynamically import a module from a file path
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    """
    Main function to orchestrate daily data update
    """
    print(f"\n{'='*70}")
    print(f"Boston Health Code Violations - Daily Update")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    success = True
    
    try:
        # Step 1: Fetch data from API
        print("STEP 1: Fetching data from Boston Open Data API")
        print("-" * 70)
        
        fetch_module = import_module_from_path(
            "fetch_api_data",
            SCRIPTS_DIR / "fetch_api_data.py"
        )
        
        csv_file = fetch_module.main(incremental=True, days_back=7)
        
        if not csv_file or not Path(csv_file).exists():
            print("\n✗ ERROR: No data file created")
            success = False
        else:
            print(f"\n✓ Data fetch completed successfully\n")
        
    except Exception as e:
        print(f"\n✗ ERROR in data fetch: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    if not success:
        print("\n" + "="*70)
        print("Daily Update FAILED at data fetch stage")
        print("="*70 + "\n")
        return 1
    
    try:
        # Step 2: Update database
        print("\nSTEP 2: Updating database with new records")
        print("-" * 70)
        
        update_module = import_module_from_path(
            "update_db",
            SCRIPTS_DIR / "update_db.py"
        )
        
        db_success = update_module.main()
        
        if not db_success:
            print("\n✗ ERROR: Database update failed")
            success = False
        else:
            print(f"\n✓ Database update completed successfully\n")
        
    except Exception as e:
        print(f"\n✗ ERROR in database update: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Final summary
    print("\n" + "="*70)
    if success:
        print(f"✓ Daily Update COMPLETED SUCCESSFULLY")
    else:
        print(f"✗ Daily Update FAILED")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

