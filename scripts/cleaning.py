import sqlite3

with sqlite3.connect("boston.db") as conn:
    cur = conn.cursor()
    # Replace literal 'nan' strings with NULL
    cur.execute("""
        UPDATE violations
        SET violation_code = NULL
        WHERE violation_code IS NULL OR violation_code = 'nan'
    """)
    conn.commit()

print("Cleaned 'nan' codes to NULL")
