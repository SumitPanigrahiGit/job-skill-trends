-- Q1: most common skills overall
SELECT skill, COUNT(*) AS jobs
FROM job_skills
GROUP BY skill
ORDER BY jobs DESC
LIMIT 10;

-- Q2: top 3 skills inside each category (window function)
WITH counts AS (
    SELECT j.category, s.skill, COUNT(*) AS jobs
    FROM job_skills s
    JOIN jobs j ON j.id = s.job_id
    GROUP BY j.category, s.skill
),
ranked AS (
    SELECT category, skill, jobs,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY jobs DESC, skill) AS rn
    FROM counts
)
SELECT category, skill, jobs
FROM ranked
WHERE rn <= 3
ORDER BY category, rn;

-- Q3: jobs published per day
SELECT substr(published_at, 1, 10) AS day, COUNT(*) AS jobs
FROM jobs
GROUP BY day
ORDER BY day DESC;

-- Q4: rising skills: jobs in the latest 7 days vs the 7 days before (needs a few weeks of data)
WITH latest AS (SELECT MAX(substr(published_at, 1, 10)) AS d FROM jobs),
periods AS (
    SELECT s.skill,
           SUM(CASE WHEN julianday((SELECT d FROM latest)) - julianday(substr(j.published_at, 1, 10)) < 7
                    THEN 1 ELSE 0 END) AS last_7,
           SUM(CASE WHEN julianday((SELECT d FROM latest)) - julianday(substr(j.published_at, 1, 10)) BETWEEN 7 AND 13.999
                    THEN 1 ELSE 0 END) AS prev_7
    FROM job_skills s
    JOIN jobs j ON j.id = s.job_id
    GROUP BY s.skill
)
SELECT skill, last_7, prev_7, last_7 - prev_7 AS change
FROM periods
WHERE last_7 + prev_7 > 0
ORDER BY change DESC, last_7 DESC
LIMIT 10;
