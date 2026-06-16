-- event_windows.sql
-- Focused extraction limited to ±3-month windows around each milestone event.
-- Cheaper than running the full date range when iterating on event-study logic.
--
-- Milestone dates and windows (from src/dictionaries.py MILESTONES; regenerate
-- this file's CASE tags/window bounds if MILESTONES changes):
--   chatgpt_launch       2022-11-30  -> window 2022-08-01 to 2023-02-28
--   pause_ai_letter      2023-03-22  -> window 2022-12-01 to 2023-06-30
--   bletchley_summit     2023-11-01  -> window 2023-08-01 to 2024-02-29
--   eu_ai_act_agreement  2023-12-08  -> window 2023-09-01 to 2024-03-31
--   seoul_summit         2024-05-21  -> window 2024-02-01 to 2024-08-31
--   eu_ai_act_in_force   2024-08-01  -> window 2024-05-01 to 2024-11-30
--   gpai_obligations     2025-08-02  -> window 2025-05-01 to 2025-11-30
--
-- (The previous version of this file under-covered bletchley_summit by one
-- month, ending its window 2024-01-31 instead of 2024-02-29 — fixed here.)
--
-- Windows overlap (most notably bletchley_summit and eu_ai_act_agreement,
-- ~1 month apart — see MERGE_PLAN.md); a row may match multiple milestones
-- via the CASE tag, which assigns the FIRST matching window in the order
-- listed below. The Python event_study()/event_study_agg() functions
-- re-filter by relative month from the canonical MILESTONES list directly,
-- so this CASE tag is for convenience when working with this narrower
-- extract, not the source of truth.
--
-- GenAI/Governance filters below are identical to extract_genai_gov.sql and
-- aggregate_frames.sql — see src/build_query.py to regenerate.

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
    WHEN DATE(_PARTITIONTIME) BETWEEN '2022-12-01' AND '2023-06-30'
      THEN 'pause_ai_letter'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2023-08-01' AND '2024-02-29'
      THEN 'bletchley_summit'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2023-09-01' AND '2024-03-31'
      THEN 'eu_ai_act_agreement'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2024-02-01' AND '2024-08-31'
      THEN 'seoul_summit'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2024-05-01' AND '2024-11-30'
      THEN 'eu_ai_act_in_force'
    WHEN DATE(_PARTITIONTIME) BETWEEN '2025-05-01' AND '2025-11-30'
      THEN 'gpai_obligations'
    ELSE NULL
  END AS milestone_window

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE (
  (DATE(_PARTITIONTIME) >= '2022-08-01' AND DATE(_PARTITIONTIME) <= '2023-02-28')
  OR (DATE(_PARTITIONTIME) >= '2022-12-01' AND DATE(_PARTITIONTIME) <= '2023-06-30')
  OR (DATE(_PARTITIONTIME) >= '2023-08-01' AND DATE(_PARTITIONTIME) <= '2024-02-29')
  OR (DATE(_PARTITIONTIME) >= '2023-09-01' AND DATE(_PARTITIONTIME) <= '2024-03-31')
  OR (DATE(_PARTITIONTIME) >= '2024-02-01' AND DATE(_PARTITIONTIME) <= '2024-08-31')
  OR (DATE(_PARTITIONTIME) >= '2024-05-01' AND DATE(_PARTITIONTIME) <= '2024-11-30')
  OR (DATE(_PARTITIONTIME) >= '2025-05-01' AND DATE(_PARTITIONTIME) <= '2025-11-30')
)

-- GenAI filter (identical predicate to extract_genai_gov.sql)
AND (
  LOWER(AllNames) LIKE '%chatgpt%'
  OR LOWER(AllNames) LIKE '%generative ai%'
  OR LOWER(AllNames) LIKE '%genai%'
  OR LOWER(AllNames) LIKE '%gen ai%'
  OR LOWER(AllNames) LIKE '%large language model%'
  OR LOWER(AllNames) LIKE '%llm%'
  OR LOWER(AllNames) LIKE '%foundation model%'
  OR LOWER(AllNames) LIKE '%frontier model%'
  OR LOWER(AllNames) LIKE '%gpt-4%'
  OR LOWER(AllNames) LIKE '%gpt4%'
  OR LOWER(AllNames) LIKE '%gpt-5%'
  OR LOWER(AllNames) LIKE '%gpt5%'
  OR LOWER(AllNames) LIKE '%claude%'
  OR LOWER(AllNames) LIKE '%anthropic%'
  OR LOWER(AllNames) LIKE '%gemini%'
  OR LOWER(AllNames) LIKE '%bard%'
  OR LOWER(AllNames) LIKE '%dall-e%'
  OR LOWER(AllNames) LIKE '%dalle%'
  OR LOWER(AllNames) LIKE '%stable diffusion%'
  OR LOWER(AllNames) LIKE '%midjourney%'
  OR LOWER(AllNames) LIKE '%text-to-image%'
  OR LOWER(AllNames) LIKE '%image generator%'
  OR LOWER(AllNames) LIKE '%copilot%'
  OR LOWER(AllNames) LIKE '%grok%'
  OR LOWER(AllNames) LIKE '%llama%'
  OR LOWER(Quotations) LIKE '%chatgpt%'
  OR LOWER(Quotations) LIKE '%generative ai%'
  OR LOWER(Quotations) LIKE '%large language model%'
  OR LOWER(Quotations) LIKE '%foundation model%'
  OR LOWER(Quotations) LIKE '%frontier model%'
  OR LOWER(Quotations) LIKE '%anthropic%'
)

-- Governance filter (identical predicate to extract_genai_gov.sql)
AND (
  LOWER(Quotations) LIKE '%governance%'
  OR LOWER(Quotations) LIKE '%regulation%'
  OR LOWER(Quotations) LIKE '%regulatory%'
  OR LOWER(Quotations) LIKE '%regulator%'
  OR LOWER(Quotations) LIKE '%policy%'
  OR LOWER(Quotations) LIKE '%oversight%'
  OR LOWER(Quotations) LIKE '%legislation%'
  OR LOWER(Quotations) LIKE '%ai act%'
  OR LOWER(Quotations) LIKE '%eu ai act%'
  OR LOWER(Quotations) LIKE '%compliance%'
  OR LOWER(Quotations) LIKE '%enforcement%'
  OR LOWER(Quotations) LIKE '%accountability%'
  OR LOWER(Quotations) LIKE '%liability%'
  OR LOWER(Quotations) LIKE '%responsible ai%'
  OR LOWER(Quotations) LIKE '%trustworthy ai%'
  OR LOWER(Quotations) LIKE '%ethical ai%'
  OR LOWER(Quotations) LIKE '%risk management%'
  OR LOWER(Quotations) LIKE '%guardrails%'
  OR LOWER(Quotations) LIKE '%safeguards%'
  OR LOWER(Quotations) LIKE '%ai safety%'
  OR LOWER(Quotations) LIKE '%human rights%'
  OR LOWER(Quotations) LIKE '%privacy%'
  OR LOWER(Quotations) LIKE '%data protection%'
  OR LOWER(Quotations) LIKE '%misinformation%'
  OR LOWER(Quotations) LIKE '%deepfake%'
  OR V2Themes LIKE '%ECON_REGULATION%'
  OR V2Themes LIKE '%UNGP%'
  OR V2Themes LIKE '%HUMAN_RIGHTS%'
  OR V2Themes LIKE '%EPU_CATS_REGULATION%'
  OR V2Themes LIKE '%EPU_POLICY_LAW%'
  OR V2Themes LIKE '%EPU_POLICY_REGULATION%'
  OR V2Themes LIKE '%LEGISLATION%'
  OR V2Themes LIKE '%WB_831_GOVERNANCE%'
  OR V2Themes LIKE '%WB_2089_ETHICS_AND_CODES_OF_CONDUCT%'
  OR V2Themes LIKE '%WB_845_LEGAL_AND_REGULATORY_FRAMEWORK%'
  OR V2Themes LIKE '%WB_851_INTELLECTUAL_PROPERTY_RIGHTS%'
  OR V2Themes LIKE '%WB_838_PUBLIC_ACCOUNTABILITY_MECHANISMS%'
  OR V2Themes LIKE '%WB_279_ICT_STRATEGY_POLICY_AND_REGULATION%'
  OR V2Themes LIKE '%WB_282_ICT_POLICY_REGULATORY_FRAMEWORK%'
  OR LOWER(DocumentIdentifier) LIKE '%-regulat%'
  OR LOWER(DocumentIdentifier) LIKE '%-policy-%'
  OR LOWER(DocumentIdentifier) LIKE '%-legislat%'
  OR LOWER(DocumentIdentifier) LIKE '%-governance-%'
  OR LOWER(DocumentIdentifier) LIKE '%-safety-%'
  OR LOWER(DocumentIdentifier) LIKE '%-security-%'
  OR LOWER(DocumentIdentifier) LIKE '%-threat%'
  OR LOWER(DocumentIdentifier) LIKE '%-warns-%'
  OR LOWER(DocumentIdentifier) LIKE '%-warning-%'
  OR LOWER(DocumentIdentifier) LIKE '%-ethic%'
  OR LOWER(DocumentIdentifier) LIKE '%-privacy-%'
  OR LOWER(DocumentIdentifier) LIKE '%-rights-%'
  OR LOWER(DocumentIdentifier) LIKE '%-oversight-%'
  OR LOWER(DocumentIdentifier) LIKE '%-copyright%'
  OR LOWER(DocumentIdentifier) LIKE '%-lawsuit%'
  OR LOWER(DocumentIdentifier) LIKE '%-banned-%'
  OR LOWER(DocumentIdentifier) LIKE '%-ban-%'
  OR LOWER(DocumentIdentifier) LIKE '%-ai-act%'
);
