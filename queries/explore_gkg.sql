-- explore_gkg.sql
-- Exploratory queries to validate field contents before running full extraction.
-- Run one block at a time in BigQuery; each costs only a small partition scan.
-- Replace DATE literals as needed.

-- ============================================================
-- 1. Sample 20 records mentioning "chatgpt" in AllNames
--    to verify field structure and content.
-- ============================================================
SELECT
  DATE,
  SourceCommonName,
  DocumentIdentifier,
  LEFT(AllNames, 300)     AS AllNames_preview,
  LEFT(Quotations, 400)   AS Quotations_preview,
  LEFT(V2Themes, 300)     AS V2Themes_preview,
  V2Tone,
  LEFT(V2Locations, 200)  AS V2Locations_preview
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) >= '2023-01-01'
  AND DATE(_PARTITIONTIME) <  '2023-02-01'
  AND LOWER(AllNames) LIKE '%chatgpt%'
LIMIT 20;


-- ============================================================
-- 2. Most frequent V2Themes tokens that co-occur with ChatGPT
--    mentions — helps identify governance-relevant theme codes.
-- ============================================================
SELECT
  theme,
  COUNT(*) AS n
FROM `gdelt-bq.gdeltv2.gkg_partitioned`,
  UNNEST(SPLIT(V2Themes, ';')) AS theme
WHERE DATE(_PARTITIONTIME) >= '2023-01-01'
  AND DATE(_PARTITIONTIME) <  '2023-07-01'
  AND LOWER(AllNames) LIKE '%chatgpt%'
  AND theme != ''
GROUP BY theme
ORDER BY n DESC
LIMIT 100;


-- ============================================================
-- 3. Monthly count of AI entity mentions — quick coverage check.
-- ============================================================
SELECT
  DATE(DATE_TRUNC(PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING)), MONTH)) AS month,
  COUNT(*) AS n_articles
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) >= '2022-11-01'
  AND DATE(_PARTITIONTIME) <  '2026-07-01'
  AND (
    LOWER(AllNames) LIKE '%chatgpt%'
    OR LOWER(AllNames) LIKE '%openai%'
    OR LOWER(AllNames) LIKE '%gemini%'
    OR LOWER(AllNames) LIKE '%large language model%'
    OR LOWER(AllNames) LIKE '%gpt-4%'
  )
GROUP BY month
ORDER BY month;


-- ============================================================
-- 4. Check Quotations field for governance keywords
--    to validate governance detection via that field.
-- ============================================================
SELECT
  LEFT(Quotations, 600) AS Quotations_preview,
  SourceCommonName,
  DATE
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) >= '2024-01-01'
  AND DATE(_PARTITIONTIME) <  '2024-04-01'
  AND LOWER(AllNames) LIKE '%chatgpt%'
  AND (
    LOWER(Quotations) LIKE '%regulation%'
    OR LOWER(Quotations) LIKE '%governance%'
    OR LOWER(Quotations) LIKE '%ai act%'
  )
LIMIT 20;
