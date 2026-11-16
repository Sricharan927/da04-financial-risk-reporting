import sqlite3
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
DB = Path("data/processed/finance.db")
DB.parent.mkdir(parents=True, exist_ok=True)

tables = ["chart_of_accounts", "transactions", "budgets", "customers", "loans"]

conn = sqlite3.connect(DB)
for name in tables:
    df = pd.read_csv(RAW / f"{name}.csv")
    df.to_sql(name, conn, if_exists="replace", index=False)
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"{name}: {count} rows")
conn.close()
print("Database created at", DB.resolve())