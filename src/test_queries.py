from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "born_at_risk_ms.db"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    county_name,
    maternal_infant_outcome_score,
    chronic_disease_score,
    social_vulnerability_score,
    access_resource_barrier_score,
    final_priority_score,
    priority_level
FROM priority_scores
ORDER BY final_priority_score DESC
LIMIT 10;
"""

results = pd.read_sql_query(query, conn)

print(results.to_string(index=False))

conn.close()