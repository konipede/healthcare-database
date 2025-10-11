# Quick Start Guide - Boston Health Code Violations Automation

## Initial Setup (One-Time)

### 1. Install Dependencies
```bash
cd /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database
pip install -r requirements.txt
```

### 2. Initialize Database (if not already done)
```bash
python3 scripts/setup_db.py
```

### 3. Do Initial Full Data Load
```bash
# This will take a few minutes to download ~850K records
python3 scripts/fetch_api_data.py --full
python3 scripts/update_db.py
```

## Setting Up Daily Automation

### 1. Test the Daily Update Script
```bash
python3 scripts/daily_update.py
```

### 2. Set Up Cron Job
```bash
# Open crontab editor
crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database/scripts/run_daily_update.sh

# Save and exit (in vi: press Esc, type :wq, press Enter)
```

### 3. Verify Cron is Set Up
```bash
crontab -l
```

## Manual Operations

### Check Database Status
```bash
# Count total records
sqlite3 boston.db "SELECT COUNT(*) as total_records FROM violations;"

# See latest violations
sqlite3 boston.db "SELECT date, COUNT(*) as count FROM violations GROUP BY date ORDER BY date DESC LIMIT 10;"

# Top violations
sqlite3 boston.db "SELECT violation_code, COUNT(*) as count FROM violations GROUP BY violation_code ORDER BY count DESC LIMIT 10;"
```

### View Logs
```bash
# Today's log
tail -f logs/daily_update_$(date +%Y%m%d).log

# Recent logs
ls -lht logs/ | head -10

# Search for errors
grep -i error logs/*.log
```

### Manual Data Update
```bash
# Fetch and update (this is what the cron job runs)
python3 scripts/daily_update.py
```

## Project Structure
```
healthcare-database/
├── scripts/
│   ├── fetch_api_data.py      # Downloads data from API
│   ├── update_db.py            # Updates database
│   ├── daily_update.py         # Master script (runs both)
│   ├── run_daily_update.sh     # Shell wrapper for cron
│   └── setup_db.py             # Initialize database
├── logs/                        # Daily update logs
├── raw/                         # Downloaded CSV files
├── boston.db                    # SQLite database
└── requirements.txt             # Python dependencies
```

## How It Works

1. **Daily at 2 AM** (via cron):
   - `run_daily_update.sh` runs
   - Calls `daily_update.py`
   - Which runs:
     - `fetch_api_data.py` - Downloads latest data from Boston API
     - `update_db.py` - Updates database with new records only (deduplicates)

2. **Deduplication**: The system automatically skips records that already exist in the database (based on business name, address, violation code, and date)

3. **Logging**: All operations are logged to `logs/daily_update_YYYYMMDD.log`

## Troubleshooting

### Cron not running?
```bash
# Check if cron is active on macOS
sudo launchctl list | grep cron

# View recent cron activity
log show --predicate 'process == "cron"' --last 1d
```

### Database issues?
```bash
# Check database file exists and is accessible
ls -lh boston.db

# Check what processes are using it
lsof boston.db
```

### API not working?
```bash
# Test API directly
curl "https://data.boston.gov/api/3/action/datastore_search?resource_id=4582bec6-2b4f-4f9e-bc55-cbaa73117f4c&limit=1"
```

## Next Steps

- Review `AUTOMATION_README.md` for detailed documentation
- Set up database backups
- Configure email notifications for failures (optional)
- Explore the data using Jupyter notebooks in `notebooks/`

