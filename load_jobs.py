"""Day 22: fetch Remotive jobs ONCE, keep the raw JSON, load a clean SQLite database.

Run:  python load_jobs.py
Re-running reuses remotive_raw.json, so you do not hit the API again.
Delete remotive_raw.json only when you really want fresh data.
"""
import json
import os
import sqlite3
import urllib.request

RAW = "remotive_raw.json"
DB = "jobs.db"
URL = "https://remotive.com/api/remote-jobs?limit=100"


def fetch_raw():
    req = urllib.request.Request(URL, headers={"User-Agent": "placement-platform-student-project"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    with open(RAW, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def load_raw():
    if os.path.exists(RAW):
        print(f"Using saved {RAW} (no API call)")
        with open(RAW, encoding="utf-8") as f:
            return json.load(f)
    print("Fetching from Remotive (one request)...")
    return fetch_raw()


def main():
    data = load_raw()
    jobs = data.get("jobs", [])
    print(f"Jobs received: {len(jobs)}")
    if not jobs:
        print("No jobs found. Open remotive_raw.json and tell me what it contains.")
        return
    print("Fields in one job:", sorted(jobs[0].keys()))

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            company TEXT,
            category TEXT,
            job_type TEXT,
            location TEXT,
            published_at TEXT,
            url TEXT
        );
        CREATE TABLE IF NOT EXISTS job_skills (
            job_id INTEGER,
            skill TEXT,
            PRIMARY KEY (job_id, skill)
        );
    """)
    for j in jobs:
        jid = j.get("id")
        if jid is None:
            continue
        cur.execute(
            "INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?,?,?)",
            (jid, j.get("title"), j.get("company_name"), j.get("category"),
             j.get("job_type"), j.get("candidate_required_location"),
             j.get("publication_date"), j.get("url")),
        )
        tags = j.get("tags") or []
        if isinstance(tags, str):
            tags = tags.split(",")
        for t in tags:
            t = str(t).strip().lower()
            if t:
                cur.execute("INSERT OR IGNORE INTO job_skills VALUES (?,?)", (jid, t))
    con.commit()
    for table in ("jobs", "job_skills"):
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {n} rows")
    con.close()
    print(f"Done. Database file: {DB}")


if __name__ == "__main__":
    main()
