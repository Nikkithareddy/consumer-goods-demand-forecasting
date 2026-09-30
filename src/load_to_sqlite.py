"""Load the CSV into SQLite and run queries.sql, printing each result set."""
import sqlite3
import pandas as pd

df = pd.read_csv("data/daily_sales.csv")
con = sqlite3.connect(":memory:")
df.to_sql("sales", con, index=False)

with open("sql/queries.sql") as f:
    script = f.read()

statements = [s.strip() for s in script.split(";") if s.strip() and not s.strip().startswith("--")]
# Re-split keeping comments attached to their statement for readability
blocks, cur = [], []
for line in script.splitlines():
    cur.append(line)
    if line.strip().endswith(";"):
        blocks.append("\n".join(cur))
        cur = []

for block in blocks:
    sql = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--") and l.strip())
    if not sql.strip():
        continue
    label = next((l for l in block.splitlines() if l.strip().startswith("-- ")), "").strip("- ")
    print(f"\n=== {label} ===")
    print(pd.read_sql_query(sql, con).to_string(index=False))
