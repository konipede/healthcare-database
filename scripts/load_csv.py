# scripts/load_csv.py
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("boston.db")
CSV_PATH = Path("raw/inspections.csv")   # change if your file has a different name
TABLE = "violations"

# CSV -> DB column mapping.
# Left side: expected CSV header (after lowercasing and replacing spaces with underscores)
# Right side: column name in the database.
COLUMN_MAP = {
    "businessname": "business_name",   # establishment name
    "address": "address",              # street address
    "violation": "violation_code",     # e.g., '13-2-304/402.11'
    "violdesc": "violation_desc",      # human-readable description
    "violdttm": "date",                # violation datetime -> we'll coerce to YYYY-MM-DD
    "result": "status",                # Pass/Fail/Re-inspect, etc.
    # no neighborhood column in this dataset; we’ll leave it NULL for now
}

def main():
    # 1) Read CSV
    df = pd.read_csv(CSV_PATH)

    # 2) Normalize headers
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # 3) Work out which columns we can map
    available_src = [src for src in COLUMN_MAP if src in df.columns]
    missing_src = [src for src in COLUMN_MAP if src not in df.columns]
    df = df[available_src].rename(columns={src: COLUMN_MAP[src] for src in available_src})

    print("Detected CSV columns:", list(df.columns))
    print("Mapped columns:", available_src)
    if missing_src:
        print("Note: these expected CSV headers were not found and were skipped:", missing_src)

    # 4) Cleanup
    if "violation_code" in df.columns:
        df["violation_code"] = df["violation_code"].astype(str).str.strip()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date.astype("string")

    # 5) Load into SQLite
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(TABLE, conn, if_exists="append", index=False)

    print(f"Loaded {len(df):,} rows into {TABLE}")

if __name__ == "__main__":
    main()
