# scripts/setup_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("boston.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- auto row id (no CSV id required)
    business_name TEXT,
    address TEXT,
    violation_code TEXT,
    violation_desc TEXT,
    neighborhood TEXT,
    date TEXT,                              -- store as 'YYYY-MM-DD' text
    status TEXT
);

CREATE INDEX IF NOT EXISTS idx_code ON violations(violation_code);
CREATE INDEX IF NOT EXISTS idx_date ON violations(date);
CREATE INDEX IF NOT EXISTS idx_neighborhood ON violations(neighborhood);
"""

def main():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
    print("Initialized schema in boston.db")

if __name__ == "__main__":
    main()
