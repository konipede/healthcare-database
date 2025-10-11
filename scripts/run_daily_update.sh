#!/bin/bash
#
# Shell script to run daily Boston health code violations update
# This script is designed to be run by cron
#
# Add to crontab with:
#   crontab -e
# Then add this line to run daily at 2 AM:
#   0 2 * * * /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database/scripts/run_daily_update.sh

# Navigate to project directory
cd /Users/keremonipede/Desktop/Healthcode_violations/healthcare-database || exit 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Set log file with date
LOG_FILE="logs/daily_update_$(date +%Y%m%d).log"

# Print header to log
echo "========================================" >> "$LOG_FILE"
echo "Daily Update Run: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..." >> "$LOG_FILE"
    source venv/bin/activate
fi

# Run the Python update script
# Output both stdout and stderr to log file
python3 scripts/daily_update.py >> "$LOG_FILE" 2>&1

# Capture exit code
EXIT_CODE=$?

# Print footer to log
echo "" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Keep only last 30 days of logs (cleanup)
find logs/ -name "daily_update_*.log" -type f -mtime +30 -delete 2>/dev/null

exit $EXIT_CODE

