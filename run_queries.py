"""Run every query in queries.sql against jobs.db and print the results as tables."""
import sqlite3

con = sqlite3.connect("jobs.db")
sql = open("queries.sql", encoding="utf-8").read()
for i, stmt in enumerate(s.strip() for s in sql.split(";")):
    body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
    if not body:
        continue
    cur = con.execute(body)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    print(f"\n=== Query {i + 1} ({len(rows)} rows) ===")
    print(" | ".join(cols))
    print("-" * 40)
    for r in rows[:15]:
        print(" | ".join(str(x) for x in r))
