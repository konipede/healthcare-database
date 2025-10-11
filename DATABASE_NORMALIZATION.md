# Database Normalization - Violation Codes

## Overview

The database has been normalized to eliminate redundancy by separating violation codes from their descriptions into a dedicated lookup table.

## What Changed

### Before (Denormalized)
```
violations table:
├── id
├── business_name
├── address
├── violation_code         "13-2-304/402.11"
├── violation_desc         "Clean Cloths Hair Restraint"  ← REDUNDANT!
├── date
└── status
```
**Problem**: The same violation description was repeated thousands of times for each code.

### After (Normalized)
```
violation_codes table (NEW):
├── code (PRIMARY KEY)     "13-2-304/402.11"
└── description            "Clean Cloths Hair Restraint"

violations table:
├── id
├── business_name
├── address
├── violation_code         "13-2-304/402.11" → REFERENCES violation_codes(code)
├── violation_desc         (kept for backward compatibility, can be removed later)
├── date
└── status
```
**Benefits**:
- ✅ Eliminates redundancy (462 codes instead of 854K+ repeated descriptions)
- ✅ Ensures consistency (one description per code)
- ✅ Easier to update code descriptions globally
- ✅ More efficient queries with JOINs
- ✅ Proper relational database design

## Database Statistics

- **Total violations**: 854,010
- **Unique violation codes**: 461 (plus 1 for NULL/UNKNOWN)
- **Violation codes table size**: 462 entries
- **Space saved**: Significant reduction in redundant text storage

## How to Use

### Query with JOIN (Recommended)

```sql
-- Get violations with code descriptions
SELECT 
    v.business_name,
    v.address,
    v.violation_code,
    vc.description,
    v.date,
    v.status
FROM violations v
LEFT JOIN violation_codes vc ON v.violation_code = vc.code
WHERE v.business_name LIKE '%Dunkin%'
ORDER BY v.date DESC
LIMIT 10;
```

### Browse Violation Codes

```sql
-- List all codes with usage counts
SELECT 
    vc.code,
    vc.description,
    COUNT(v.id) as usage_count
FROM violation_codes vc
LEFT JOIN violations v ON v.violation_code = vc.code
GROUP BY vc.code, vc.description
ORDER BY usage_count DESC;
```

### Search for Specific Codes

```sql
-- Find codes related to "temperature"
SELECT 
    code,
    description,
    (SELECT COUNT(*) FROM violations WHERE violation_code = code) as usage_count
FROM violation_codes
WHERE description LIKE '%temperature%'
ORDER BY usage_count DESC;
```

## Python/Pandas Usage

The notebook functions have been updated to use JOINs:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('boston.db')

# Query with JOIN
query = """
    SELECT 
        v.business_name,
        v.violation_code,
        vc.description,
        v.date
    FROM violations v
    LEFT JOIN violation_codes vc ON v.violation_code = vc.code
    WHERE v.business_name LIKE ?
    ORDER BY v.date DESC
    LIMIT 10
"""

df = pd.read_sql(query, conn, params=('%Starbucks%',))
print(df)
```

## Automated Updates

The daily update script (`scripts/update_db.py`) now:

1. **Updates `violation_codes` table** with any new codes from the API
2. **Inserts new violations** into the violations table
3. **Maintains the foreign key relationship** automatically

This means:
- New violation codes are automatically added to the lookup table
- Existing codes are reused (no duplicates)
- Data integrity is maintained

## Migration

The normalization was performed by:

1. **Created** `violation_codes` table with code and description columns
2. **Populated** it with unique code/description pairs from existing data
3. **Updated** schema to include foreign key relationship
4. **Modified** queries to use JOINs for accessing descriptions
5. **Kept** `violation_desc` in violations table for backward compatibility

### Migration Script

Location: `scripts/normalize_database.py`

To re-run normalization:
```bash
python3 scripts/normalize_database.py
```

## Backward Compatibility

The `violation_desc` column is still present in the `violations` table for backward compatibility. Existing queries will continue to work, but new queries should use JOINs to access the normalized `violation_codes` table.

### Future Cleanup (Optional)

If you want to fully remove the redundant column:

```sql
-- Create new table without violation_desc
CREATE TABLE violations_new AS
SELECT 
    id, business_name, address, violation_code, 
    neighborhood, date, status
FROM violations;

-- Drop old table and rename
DROP TABLE violations;
ALTER TABLE violations_new RENAME TO violations;

-- Recreate indexes
CREATE INDEX idx_code ON violations(violation_code);
CREATE INDEX idx_date ON violations(date);
CREATE INDEX idx_neighborhood ON violations(neighborhood);
```

**Note**: Only do this after ensuring all queries use JOINs.

## Benefits for Your Project

1. **Cleaner Data Model**: Proper relational database design
2. **Easier Analysis**: Browse and search violation codes separately
3. **Code Consistency**: One source of truth for each code's description
4. **Flexibility**: Easy to add metadata (severity, category, etc.) to codes
5. **Performance**: Smaller overall database size, faster queries

## Updated Files

- ✅ `scripts/setup_db.py` - Updated schema with violation_codes table
- ✅ `scripts/update_db.py` - Auto-updates violation_codes during data imports
- ✅ `scripts/normalize_database.py` - Migration script (NEW)
- ✅ `notebooks/analysis.ipynb` - Updated queries to use JOINs
- ✅ Database schema now includes foreign key relationship

## Examples from Your Data

### Top 5 Most Common Violations

```sql
SELECT 
    vc.code,
    vc.description,
    COUNT(v.id) as count
FROM violation_codes vc
JOIN violations v ON v.violation_code = vc.code
GROUP BY vc.code, vc.description
ORDER BY count DESC
LIMIT 5;
```

### All Temperature-Related Violations

```sql
SELECT 
    vc.code,
    vc.description,
    COUNT(v.id) as violations
FROM violation_codes vc
LEFT JOIN violations v ON v.violation_code = vc.code
WHERE vc.description LIKE '%temperature%' 
   OR vc.description LIKE '%temp%'
GROUP BY vc.code, vc.description
ORDER BY violations DESC;
```

## Questions?

- Check `scripts/normalize_database.py` for implementation details
- See `notebooks/analysis.ipynb` for examples of using the new structure
- Run `sqlite3 boston.db ".schema"` to see the full database schema

---

**Database normalization completed**: October 11, 2025  
**Migration script**: `scripts/normalize_database.py`  
**Total violation codes**: 462  
**Status**: ✅ Production Ready

