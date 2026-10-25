# job-skill-trends

A small data-engineering project: collect remote job postings once or twice a day, store them in SQLite, and answer questions about which skills are in demand and which are rising.

**Data source:** job data comes from the [Remotive](https://remotive.com) public API. Remotive is credited as the source. This repo does not contain or republish the job listings; it only holds the code and aggregate results.

## What it does
- `load_jobs.py` fetches jobs, de-duplicates by job id, records `first_seen_at`, and logs every fetch in `fetch_log`. It refuses to fetch again within 6 hours, to respect the API's guidance of about 4 fetches a day.
- `queries.sql` answers: top skills, top skills per category (window function), jobs per day, and rising skills (last 7 days vs the 7 days before).
- `run_queries.py` runs all queries and prints tables.

## Run it
```
python load_jobs.py
python run_queries.py
```

## Status
Day 24: daily loader and trend query. Next: more data over time, a chart, and then a cloud version.
