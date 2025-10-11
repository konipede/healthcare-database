# Boston Health Code Violations - Automated Data Updates

This document explains how to set up and use the automated daily data update system for the Boston Health Code Violations database.

## Overview

The automation system downloads data from the Boston Open Data API daily and updates the SQLite database with new violation records. It includes:

- **API data fetching** from Boston's Socrata Open Data portal
- **Automatic deduplication** to avoid inserting duplicate records
- **Incremental updates** (only fetches recent data by default)
- **Daily scheduling** via cron jobs
- **Logging** for monitoring and debugging

## Project Structure

```
healthcare-database/
├── scripts/
│   ├── fetch_api_data.py      # Downloads data from Boston API
│   ├── update_db.py            # Updates database with new data
│   ├── daily_update.py         # Master orchestration script
│   ├── run_daily_update.sh     # Shell wrapper for cron
│   ├── setup_db.py             # Database schema setup
│   ├── load_csv.py             # Manual CSV loading (legacy)
│   ├── cleaning.py             # Data cleaning utilities
│   └── queries.py              # Query helper functions
├── logs/                        # Log files (auto-created)
├── raw/                         # Downloaded CSV files (auto-created)
├── boston.db                    # SQLite database
└── requirements.txt             # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

First, ensure you have Python 3.7+ installed. Then install the required packages:

```bash
cd /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database
pip install -r requirements.txt
```

Or if you prefer using a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize the Database

If you haven't already created the database, run:

```bash
python3 scripts/setup_db.py
```

This creates the `boston.db` SQLite database with the proper schema.

### 3. Test the Scripts Manually

Before setting up automation, test each script:

#### Test API Fetching
```bash
# Fetch last 7 days of data
python3 scripts/fetch_api_data.py

# Fetch all data (initial full load)
python3 scripts/fetch_api_data.py --full

# Fetch last 30 days
python3 scripts/fetch_api_data.py --days=30
```

#### Test Database Update
```bash
python3 scripts/update_db.py
```

#### Test Complete Daily Update Process
```bash
python3 scripts/daily_update.py
```

### 4. Set Up Daily Automation with Cron

#### Option A: Using the Shell Script (Recommended)

1. Make sure the shell script is executable:
   ```bash
   chmod +x scripts/run_daily_update.sh
   ```

2. Open your crontab:
   ```bash
   crontab -e
   ```

3. Add this line to run daily at 2:00 AM:
   ```
   0 2 * * * /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database/scripts/run_daily_update.sh
   ```

4. Save and exit the editor (in vi/vim: press `Esc`, type `:wq`, press Enter)

#### Option B: Direct Python Script in Cron

Alternatively, you can call the Python script directly:

```
0 2 * * * cd /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database && /usr/bin/python3 scripts/daily_update.py >> logs/daily_update.log 2>&1
```

#### Cron Schedule Examples

- `0 2 * * *` - Daily at 2:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 2 * * 1` - Every Monday at 2:00 AM
- `30 3 * * *` - Daily at 3:30 AM

### 5. Verify Cron Setup

Check that your cron job is registered:

```bash
crontab -l
```

## Script Details

### fetch_api_data.py

Downloads data from the Boston Open Data API (Socrata platform).

**Usage:**
```bash
python3 scripts/fetch_api_data.py              # Incremental (last 7 days)
python3 scripts/fetch_api_data.py --full       # Full download
python3 scripts/fetch_api_data.py --days=14    # Last 14 days
```

**API Details:**
- Endpoint: `https://data.boston.gov/api/3/action/datastore_search`
- Resource ID: `4582bec6-2b4f-4f9e-bc55-cbaa73117f4c`
- Dataset: Food Establishment Inspections
- Platform: CKAN (not Socrata)
- No API key required (but recommended for higher rate limits)

**To get an API token (optional but recommended):**
1. Go to https://data.boston.gov
2. Create a free account
3. Go to your profile → Developer Settings
4. Create an app token
5. Add it to `fetch_api_data.py` by setting `API_TOKEN = "your-token-here"`

**Output:**
- `raw/inspections_latest.csv` - Latest data download
- `raw/inspections_YYYYMMDD_HHMMSS.csv` - Timestamped backup

### update_db.py

Updates the database with new records from the downloaded CSV file.

**Features:**
- Automatic deduplication using business name, address, violation code, and date
- Handles missing/malformed data gracefully
- Reports statistics on inserted vs. skipped records

**Usage:**
```bash
python3 scripts/update_db.py
```

### daily_update.py

Master orchestration script that runs both fetch and update operations.

**Usage:**
```bash
python3 scripts/daily_update.py
```

**What it does:**
1. Fetches new data from the API (last 7 days)
2. Updates the database with new records
3. Reports success/failure status
4. Provides detailed logging

## Monitoring

### Check Logs

Logs are stored in the `logs/` directory:

```bash
# View today's log
tail -f logs/daily_update_$(date +%Y%m%d).log

# View all recent logs
ls -lht logs/

# Search for errors
grep -i error logs/daily_update_*.log
```

### Verify Data Updates

Check when the database was last updated:

```bash
sqlite3 boston.db "SELECT date, COUNT(*) FROM violations GROUP BY date ORDER BY date DESC LIMIT 10;"
```

Check total record count:

```bash
sqlite3 boston.db "SELECT COUNT(*) FROM violations;"
```

### Test the Daily Update Manually

Run the daily update script manually to test:

```bash
python3 scripts/daily_update.py
```

## Troubleshooting

### No Data Being Downloaded

1. Check your internet connection
2. Verify the API endpoint is accessible:
   ```bash
   curl "https://data.boston.gov/resource/qndu-wx8w.json?$limit=1"
   ```
3. Check if the dataset ID has changed on the Boston Open Data portal

### Cron Job Not Running

1. Check cron is running:
   ```bash
   # On macOS
   sudo launchctl list | grep cron
   
   # Enable cron on macOS if needed
   sudo launchctl load -w /System/Library/LaunchDaemons/com.vix.cron.plist
   ```

2. Check cron logs:
   ```bash
   # On macOS
   log show --predicate 'process == "cron"' --last 1d
   ```

3. Verify the script paths in your crontab are absolute paths

4. Make sure scripts are executable:
   ```bash
   chmod +x scripts/*.py
   chmod +x scripts/*.sh
   ```

### Database Lock Issues

If you get "database is locked" errors:

1. Make sure no other processes are using the database
2. Close any Jupyter notebooks connected to the database
3. Check for zombie processes:
   ```bash
   lsof boston.db
   ```

### Permission Issues

If cron can't write to logs:

```bash
chmod 755 logs/
chmod 644 logs/*.log
```

## Advanced Configuration

### Change Update Frequency

Edit the `fetch_api_data.py` script and modify the `days_back` parameter in the `main()` function, or pass it as an argument:

```python
# In daily_update.py, modify:
csv_file = fetch_module.main(incremental=True, days_back=14)  # Last 14 days
```

### Add Email Notifications

Install `mailx` or similar and modify `run_daily_update.sh`:

```bash
# At the end of run_daily_update.sh
if [ $EXIT_CODE -ne 0 ]; then
    echo "Daily update failed! Check logs at $LOG_FILE" | mail -s "Boston DB Update Failed" your@email.com
fi
```

### Database Backup

Add to cron for weekly database backups:

```bash
# Backup database every Sunday at 3 AM
0 3 * * 0 cp /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database/boston.db /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database/backups/boston_$(date +\%Y\%m\%d).db
```

## API Information

### Boston Open Data Portal

- **Portal**: https://data.boston.gov
- **Platform**: CKAN Open Data
- **Dataset**: Food Establishment Inspections
- **Resource ID**: 4582bec6-2b4f-4f9e-bc55-cbaa73117f4c
- **API Documentation**: https://docs.ckan.org/en/latest/api/

### Data Fields

The API provides (selected fields used by our database):
- `businessname` - Name of the establishment → `business_name`
- `address` - Street address → `address`
- `violation` - Violation code (e.g., "13-2-304") → `violation_code`
- `violdesc` - Violation description → `violation_desc`
- `violdttm` - Violation date/time → `date`
- `result` - Inspection result (Pass/Fail) → `status`

Additional fields available (not currently stored):
- `licenseno`, `licstatus`, `licensecat` - License information
- `dbaname`, `legalowner` - Business ownership details
- `city`, `state`, `zip` - Location details
- `comments` - Inspector comments

### Rate Limits

- **Without API token**: 1,000 requests per day
- **With API token**: 10,000 requests per day

## Database Schema

```sql
CREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT,
    address TEXT,
    violation_code TEXT,
    violation_desc TEXT,
    neighborhood TEXT,
    date TEXT,
    status TEXT
);

CREATE INDEX idx_code ON violations(violation_code);
CREATE INDEX idx_date ON violations(date);
CREATE INDEX idx_neighborhood ON violations(neighborhood);
```

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check logs for errors
2. **Monthly**: Verify data is updating correctly
3. **Quarterly**: Review and clean up old log files
4. **Yearly**: Backup the database

### Getting Help

If you encounter issues:

1. Check the logs in `logs/` directory
2. Run scripts manually to see detailed error messages
3. Verify the Boston Open Data API is operational
4. Check the dataset hasn't changed or been deprecated

## License & Data Attribution

This project uses data from the City of Boston Open Data portal. Please review Boston's data usage policies at https://data.boston.gov for attribution and usage requirements.

