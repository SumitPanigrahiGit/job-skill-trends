"""Build dashboard.html from jobs.db (aggregates only, no raw job listings).

Usage:  python make_dashboard.py
Output: dashboard.html  (one self-contained file, no libraries, open it in a browser)
Data source: Remotive (https://remotive.com). Credit shown on the page.
"""
import html
import sqlite3
from datetime import datetime, timezone

DB = "jobs.db"
OUT = "dashboard.html"


def q(con, sql):
    return con.execute(sql).fetchall()


def bars(rows, label_w=150):
    """Horizontal bar chart as inline SVG. rows = [(label, value)]."""
    if not rows:
        return "<p class='mu'>No data yet.</p>"
    mx = max(v for _, v in rows) or 1
    h = 28
    out = [f"<svg viewBox='0 0 640 {h * len(rows) + 4}' width='100%' role='img' aria-label='bar chart'>"]
    for i, (lab, v) in enumerate(rows):
        y = i * h + 2
        w = max(2, int((640 - label_w - 60) * v / mx))
        out.append(f"<text x='0' y='{y + 18}' class='lab'>{html.escape(str(lab))[:22]}</text>")
        out.append(f"<rect x='{label_w}' y='{y + 4}' width='{w}' height='16' rx='3' class='bar'/>")
        out.append(f"<text x='{label_w + w + 6}' y='{y + 18}' class='val'>{v}</text>")
    out.append("</svg>")
    return "".join(out)


def main():
    con = sqlite3.connect(DB)
    total = q(con, "SELECT COUNT(*) FROM jobs")[0][0]
    n_skills = q(con, "SELECT COUNT(DISTINCT skill) FROM job_skills")[0][0]
    first_day = q(con, "SELECT MIN(substr(published_at,1,10)) FROM jobs")[0][0] or "-"
    last_day = q(con, "SELECT MAX(substr(published_at,1,10)) FROM jobs")[0][0] or "-"

    top = q(con, "SELECT skill, COUNT(*) c FROM job_skills GROUP BY skill ORDER BY c DESC, skill LIMIT 12")
    per_day = q(con, "SELECT substr(published_at,1,10) d, COUNT(*) c FROM jobs "
                     "GROUP BY d ORDER BY d DESC LIMIT 14")[::-1]
    cats = q(con, """
        WITH counts AS (
            SELECT j.category cat, s.skill sk, COUNT(*) c
            FROM job_skills s JOIN jobs j ON j.id = s.job_id GROUP BY j.category, s.skill),
        ranked AS (
            SELECT cat, sk, c, ROW_NUMBER() OVER (PARTITION BY cat ORDER BY c DESC, sk) rn FROM counts)
        SELECT cat, sk, c FROM ranked WHERE rn <= 3 ORDER BY cat, rn""")
    by_cat = {}
    for cat, sk, c in cats:
        by_cat.setdefault(cat or "other", []).append(f"{sk} ({c})")
    cat_rows = "".join(
        f"<tr><td>{html.escape(c)}</td><td>{html.escape(', '.join(v))}</td></tr>" for c, v in by_cat.items())

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Job Skill Trends</title>
<style>
:root{{--bg:#f7f8fa;--card:#fff;--tx:#161a20;--mu:#5d6675;--ac:#1d4ed8;--bd:#e3e6eb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0e1013;--card:#171a1f;--tx:#e8eaed;--mu:#9aa3b2;--ac:#7aa2ff;--bd:#272c34}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:820px;margin:0 auto;padding:32px 16px}}
h1{{margin:0 0 4px;font-size:1.6rem}}h2{{font-size:1.05rem;margin:0 0 10px}}
.mu{{color:var(--mu)}}a{{color:var(--ac)}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px;margin-bottom:14px}}
.num{{font-size:1.6rem;font-weight:700}}
.bar{{fill:var(--ac)}}.lab,.val{{fill:var(--tx);font-size:13px}}.val{{fill:var(--mu)}}
table{{width:100%;border-collapse:collapse}}td{{padding:8px 4px;border-top:1px solid var(--bd);vertical-align:top}}
</style></head><body><main>
<h1>Job Skill Trends</h1>
<p class="mu">Which skills show up most in remote job postings. Updated {datetime.now(timezone.utc):%Y-%m-%d} UTC.</p>
<div class="stats">
<div class="card"><div class="num">{total}</div><div class="mu">jobs tracked</div></div>
<div class="card"><div class="num">{n_skills}</div><div class="mu">distinct skills</div></div>
<div class="card"><div class="num">{html.escape(first_day)}</div><div class="mu">earliest posting</div></div>
<div class="card"><div class="num">{html.escape(last_day)}</div><div class="mu">latest posting</div></div>
</div>
<div class="card"><h2>Most requested skills</h2>{bars(top)}</div>
<div class="card"><h2>Jobs published per day (last 14 days with data)</h2>{bars(per_day, 90)}</div>
<div class="card"><h2>Top 3 skills per category</h2><table>{cat_rows}</table></div>
<p class="mu">Pipeline: EventBridge, Lambda, S3, Athena. Source code:
<a href="https://github.com/SumitPanigrahiGit/job-skill-trends">job-skill-trends</a>.
Job data from <a href="https://remotive.com">Remotive</a>. Only aggregate counts are shown here.</p>
</main></body></html>"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {OUT} ({total} jobs, {n_skills} skills)")
    con.close()


if __name__ == "__main__":
    main()
