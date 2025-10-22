#!/usr/bin/env python3
"""
Sync the updated database from GitHub back to local machine
Run this script when you want to get the latest data from GitHub Actions
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Sync database from GitHub"""
    print("Syncing database from GitHub...")
    
    try:
        # Pull latest changes from GitHub
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Successfully synced database from GitHub")
            print(result.stdout)
        else:
            print("✗ Error syncing from GitHub:")
            print(result.stderr)
            return 1
            
    except Exception as e:
        print(f"✗ Error running git pull: {e}")
        return 1
    
    # Check if database was updated
    db_path = Path("boston.db")
    if db_path.exists():
        print(f"✓ Database file exists: {db_path}")
        print(f"  Size: {db_path.stat().st_size / (1024*1024):.1f} MB")
    else:
        print("✗ Database file not found")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
