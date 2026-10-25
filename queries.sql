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
