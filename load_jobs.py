"""Daily loader for the job-skill-trends project.

Usage:
    python load_jobs.py                      # all categories, one request
    python load_jobs.py --category software-dev
    python load_jobs.py --force              # ignore the 6-hour safety gap

Rules this script follows (from Remotive's API docs):
  * at most about 4 fetches a day: it refuses to fetch again within 6 hours
  * jobs are stored once (de-duplicated by Remotive's job id)
Every run is logged in the fetch_log table, so the dataset grows over time.
Data source: Remotive (https://remotive.com). Always credit Remotive.
"""
import argparse
import json
import os
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

DB = "jobs.db"
RAW_DIR = "raw"
BASE_URL = "https://remotive.com/api/remote-jobs"
MIN_GAP_HOURS = 6


def now_utc():
    return datetime.now(timezone.utc)


def fetch(category=None):
    params = {"limit": 100}
    if category:
        params["category"] = category
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "job-skill-trends-student-project"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def setup(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT, company TEXT, category TEXT, job_type TEXT,
            location TEXT, published_at TEXT, url TEXT
        );
        CREATE TABLE IF NOT EXISTS job_skills (
            job_id INTEGER, skill TEXT, PRIMARY KEY (job_id, skill)
        );
        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TEXT, category TEXT, jobs_received INTEGER, new_jobs INTEGER
        );
    """)
    # upgrade an older database: add the columns we now need
    cols = {r[1] for r in con.execute("PRAGMA table_info(jobs)")}
    if "first_seen_at" not in cols:
        con.execute("ALTER TABLE jobs ADD COLUMN first_seen_at TEXT")
        con.execute("UPDATE jobs SET first_seen_at = ? WHERE first_seen_at IS NULL",
                    (now_utc().isoformat(timespec="seconds"),))
    con.commit()


def last_fetch_age_hours(con):
    row = con.execute("SELECT MAX(fetched_at) FROM fetch_log").fetchone()
    if not row or not row[0]:
        return None
    return (now_utc() - datetime.fromisoformat(row[0])).total_seconds() / 3600


def store(con, jobs):
    new = 0
    stamp = now_utc().isoformat(timespec="seconds")
    for j in jobs:
        jid = j.get("id")
        if jid is None:
            continue
        exists = con.execute("SELECT 1 FROM jobs WHERE id = ?", (jid,)).fetchone()
        if not exists:
            new += 1
            con.execute(
                "INSERT INTO jobs (id, title, company, category, job_type, location,"
                " published_at, url, first_seen_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (jid, j.get("title"), j.get("company_name"), j.get("category"),
                 j.get("job_type"), j.get("candidate_required_location"),
                 j.get("publication_date"), j.get("url"), stamp))
        tags = j.get("tags") or []
        if isinstance(tags, str):
            tags = tags.split(",")
        for t in tags:
            t = str(t).strip().lower()
            if t:
                con.execute("INSERT OR IGNORE INTO job_skills VALUES (?,?)", (jid, t))
    return new


def main(argv=None, fetch_fn=fetch):
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", help="Remotive category slug, e.g. software-dev")
    ap.add_argument("--force", action="store_true", help="ignore the safety gap")
    args = ap.parse_args(argv)

    con = sqlite3.connect(DB)
    setup(con)

    age = last_fetch_age_hours(con)
    if age is not None and age < MIN_GAP_HOURS and not args.force:
        print(f"Last fetch was {age:.1f} hours ago. Remotive asks for at most ~4 fetches a day.")
        print(f"Try again in {MIN_GAP_HOURS - age:.1f} hours (or use --force if you must).")
        con.close()
        return

    data = fetch_fn(args.category)
    jobs = data.get("jobs", [])
    os.makedirs(RAW_DIR, exist_ok=True)
    name = now_utc().strftime("%Y%m%dT%H%M%SZ") + ".json"
    with open(os.path.join(RAW_DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f)

    new = store(con, jobs)
    con.execute("INSERT INTO fetch_log (fetched_at, category, jobs_received, new_jobs)"
                " VALUES (?,?,?,?)",
                (now_utc().isoformat(timespec="seconds"), args.category or "all", len(jobs), new))
    con.commit()

    total = con.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    skills = con.execute("SELECT COUNT(DISTINCT skill) FROM job_skills").fetchone()[0]
    print(f"Received {len(jobs)} jobs, {new} new. Database now has {total} jobs and {skills} distinct skills.")
    con.close()


if __name__ == "__main__":
    main()
