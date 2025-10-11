import sqlite3
from contextlib import closing

DB_PATH = "boston.db"

def run(sql: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn, closing(conn.cursor()) as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def top_violation_codes(n: int = 10):
    return run("""
        SELECT violation_code, COUNT(*) AS cnt
        FROM violations
        GROUP BY violation_code
        ORDER BY cnt DESC
        LIMIT ?
    """, (n,))

def top_descriptions(n: int = 10):
    return run("""
        SELECT violation_desc, COUNT(*) AS cnt
        FROM violations
        GROUP BY violation_desc
        ORDER BY cnt DESC
        LIMIT ?
    """, (n,))
