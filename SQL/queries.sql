-- =====================================================
--  PatentsView — Analytical SQL Queries
--  Run against: patents.db
--  Tool: sqlite3 patents.db < queries.sql
--        OR use DB Browser for SQLite
-- =====================================================


-- ─────────────────────────────────────────────────
--  Q1: Total patents
-- ─────────────────────────────────────────────────
SELECT
    COUNT(*) AS total_patents
FROM patents;


-- ─────────────────────────────────────────────────
--  Q2: Top companies by patent count
-- ─────────────────────────────────────────────────
SELECT
    c.name,
    COUNT(pc.patent_id) AS patent_count
FROM companies c
JOIN patent_companies pc ON c.company_id = pc.company_id
GROUP BY c.company_id
ORDER BY patent_count DESC
LIMIT 20;


-- ─────────────────────────────────────────────────
--  Q3: Patents per year
-- ─────────────────────────────────────────────────
SELECT
    year,
    COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;


-- ─────────────────────────────────────────────────
--  Q4: Top technology fields
-- ─────────────────────────────────────────────────
SELECT
    wipo_sector_title AS sector,
    wipo_field_title AS field,
    COUNT(*) AS patent_count
FROM technologies
GROUP BY wipo_sector_title, wipo_field_title
ORDER BY patent_count DESC
LIMIT 20;


-- ─────────────────────────────────────────────────
--  Q5: Patent join sample: patents + companies + technologies
-- ─────────────────────────────────────────────────
SELECT
    p.patent_id,
    p.title,
    p.year,
    c.name AS company,
    t.wipo_sector_title AS sector,
    t.wipo_field_title AS tech_field
FROM patents p
LEFT JOIN patent_companies pc ON p.patent_id = pc.patent_id
LEFT JOIN companies c ON pc.company_id = c.company_id
LEFT JOIN technologies t ON p.patent_id = t.patent_id
ORDER BY p.year DESC
LIMIT 100;


-- ─────────────────────────────────────────────────
--  Q6: Top tech sector per decade
-- ─────────────────────────────────────────────────
WITH decade_tech AS (
    SELECT
        (p.year / 10) * 10 AS decade,
        t.wipo_sector_title AS sector,
        COUNT(*) AS patent_count
    FROM patents p
    JOIN technologies t ON p.patent_id = t.patent_id
    WHERE p.year IS NOT NULL
    GROUP BY decade, sector
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY decade
               ORDER BY patent_count DESC
           ) AS rank_in_decade
    FROM decade_tech
)
SELECT decade, sector, patent_count, rank_in_decade
FROM ranked
WHERE rank_in_decade <= 3
ORDER BY decade, rank_in_decade;


-- ─────────────────────────────────────────────────
--  Q7: Company ranking by patent count
-- ─────────────────────────────────────────────────
SELECT
    c.name,
    COUNT(pc.patent_id) AS patent_count,
    RANK() OVER (ORDER BY COUNT(pc.patent_id) DESC) AS rank
FROM companies c
JOIN patent_companies pc ON c.company_id = pc.company_id
GROUP BY c.company_id
ORDER BY rank
LIMIT 25;


-- ─────────────────────────────────────────────────
--  Bonus: Tech field growth ratio
-- ─────────────────────────────────────────────────
WITH tech_counts AS (
    SELECT
        t.wipo_field_title AS field,
        SUM(CASE WHEN p.year >= strftime('%Y', 'now') - 4 THEN 1 ELSE 0 END) AS recent_count,
        SUM(CASE WHEN p.year < strftime('%Y', 'now') - 4 THEN 1 ELSE 0 END) AS earlier_count
    FROM patents p
    JOIN technologies t ON p.patent_id = t.patent_id
    WHERE p.year IS NOT NULL
    GROUP BY t.wipo_field_title
)
SELECT
    field,
    recent_count,
    earlier_count,
    CASE
        WHEN earlier_count = 0 THEN NULL
        ELSE ROUND(1.0 * recent_count / earlier_count, 2)
    END AS growth_ratio
FROM tech_counts
WHERE recent_count > 0
ORDER BY growth_ratio DESC, recent_count DESC
LIMIT 20;
