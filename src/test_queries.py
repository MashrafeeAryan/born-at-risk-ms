from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "born_at_risk_ms.db"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    c.county_name,
    chr.low_birth_weight_pct,
    sv.svi_overall,
    ph.diabetes_pct,
    ph.obesity_pct,
    ph.uninsured_places_pct
FROM counties c
JOIN county_health_rankings chr
    ON c.county_fips = chr.county_fips
JOIN social_vulnerability sv
    ON c.county_fips = sv.county_fips
JOIN places_health ph
    ON c.county_fips = ph.county_fips
ORDER BY chr.low_birth_weight_pct DESC
LIMIT 10;
"""

results = pd.read_sql_query(query, conn)

print(results)

conn.close()