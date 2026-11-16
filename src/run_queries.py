"""Run the SQL files against the database and save results as CSV."""
import sqlite3
from pathlib import Path
import pandas as pd

DB = Path("data/processed/finance.db")
OUT = Path("reports")
OUT.mkdir(exist_ok=True)

conn = sqlite3.connect(DB)
for name in ["pnl", "budget_vs_actual"]:
    sql = Path(f"sql/{name}.sql").read_text(encoding="utf-8-sig")
    df = pd.read_sql_query(sql, conn)
    df.to_csv(OUT / f"{name}.csv", index=False)
    print(f"\n=== {name} ({len(df)} rows) ===")
    print(df.head(6).to_string(index=False))
conn.close()
