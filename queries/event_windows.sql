-- event_windows.sql
-- Focused extraction limited to ±3-month windows around each milestone event.
-- Cheaper than running the full date range when iterating on event-study logic.
--
-- Milestone dates (from src/dictionaries.py MILESTONES):
--   chatgpt_launch   2022-11-30  → window 2022-08-01 to 2023-02-28
--   bletchley_summit 2023-11-01  → window 2023-08-01 to 2024-01-31
--   eu_ai_act        2024-03-13  → window 2023-12-01 to 2024-06-30
--   seoul_summit     2024-05-21  → window 2024-02-01 to 2024-08-31
--
-- Windows overlap; a row may match multiple milestones via the CASE tag.
-- The Python event_study() function re-filters by 'milestone_window' column.

SELECT
  DATE,
  SourceCommonName,
  DocumentIdentifier,
  V2Themes,
  V2Tone,
  V2Locations,
  AllNames,
  Quotations,

  -- Tag each row with the first matching milestone window
  CASE
    WHEN DATE(_PARTITIONTIME) BETWEEN '2022-08-01' AND '2023-02-28'
      THEN 'chatgpt_launch'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2023-08-01' AND '2024-01-31'
      THEN 'bletchley_summit'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2023-12-01' AND '2024-06-30'
      THEN 'eu_ai_act'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2024-02-01' AND '2024-08-31'
      THEN 'seoul_summit'
    ELSE NULL
  END AS milestone_window

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE (
  (DATE(_PARTITIONTIME) >= '2022-08-01' AND DATE(_PARTITIONTIME) <= '2023-02-28')
  OR (DATE(_PARTITIONTIME) >= '2023-08-01' AND DATE(_PARTITIONTIME) <= '2024-01-31')
  OR (DATE(_PARTITIONTIME) >= '2023-12-01' AND DATE(_PARTITIONTIME) <= '2024-06-30')
  OR (DATE(_PARTITIONTIME) >= '2024-02-01' AND DATE(_PARTITIONTIME) <= '2024-08-31')
)

-- GenAI filter (same as extract_genai_gov.sql)
AND (
  LOWER(AllNames) LIKE '%chatgpt%'
  OR LOWER(AllNames) LIKE '%generative ai%'
  OR LOWER(AllNames) LIKE '%large language model%'
  OR LOWER(AllNames) LIKE '%openai%'
  OR LOWER(AllNames) LIKE '%gemini%'
  OR LOWER(AllNames) LIKE '%gpt-4%'
  OR LOWER(AllNames) LIKE '%claude%'
  OR LOWER(Quotations) LIKE '%chatgpt%'
  OR LOWER(Quotations) LIKE '%generative ai%'
  OR LOWER(Quotations) LIKE '%large language model%'
)

-- Governance filter (same as extract_genai_gov.sql)
AND (
  LOWER(Quotations) LIKE '%regulation%'
  OR LOWER(Quotations) LIKE '%governance%'
  OR LOWER(Quotations) LIKE '%policy%'
  OR LOWER(Quotations) LIKE '%oversight%'
  OR LOWER(Quotations) LIKE '%ai act%'
  OR LOWER(Quotations) LIKE '%ai safety%'
  OR LOWER(Quotations) LIKE '%privacy%'
  OR V2Themes LIKE '%ECON_REGULATION%'
);
