-- aggregate_frames.sql
-- Recommended primary query: frame counts grouped by month, computed in BigQuery.
-- Downloads ~40 rows instead of millions. Stays well within the 1 TB free tier.
--
-- Each frame column counts articles where at least one keyword from that frame
-- appears in AllNames or Quotations (binary presence per article, not hit count).
--
-- Keyword patterns derived from src/dictionaries.py FRAME_DICTS.
-- Run src/build_query.py to regenerate the REGEXP patterns if dictionaries change.

SELECT
  FORMAT_DATE(
    '%Y-%m',
    PARSE_DATE('%Y%m%d', SUBSTR(CAST(DATE AS STRING), 1, 8))
  ) AS month,

  COUNT(*) AS total_articles,

  -- Frame 1: Innovation & opportunity
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'innovation|innovative|breakthrough|opportunity|promise|benefit|potential|growth|boost|productivity|efficiency|transform|progress|competitiveness')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'innovation|breakthrough|opportunity|productivity')
  ) AS frame_innovation_opportunity,

  -- Frame 2: Risk & safety
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'\brisk\b|\bharm\b|\bharms\b|danger|threat|\bsafety\b|unsafe|misuse|abuse|catastrophic|existential|\bcrisis\b')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'\brisk\b|danger|threat|\bsafety\b|catastrophic')
  ) AS frame_risk_safety,

  -- Frame 3: Regulation & governance
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'regulation|regulatory|regulator|\blaw\b|legislation|\bpolicy\b|\brules\b|oversight|compliance|enforcement|framework|standard|\baudit\b')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'regulation|regulatory|legislation|oversight|compliance')
  ) AS frame_regulation_governance,

  -- Frame 4: Rights & privacy
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'privacy|data protection|personal data|human rights|fundamental rights|civil liberties|surveillance|\bbias\b|fairness|transparency|consent')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'privacy|surveillance|\bbias\b|fairness|transparency')
  ) AS frame_rights_privacy,

  -- Frame 5: Economic competition & labour
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'\bjobs\b|\bworkers\b|automation|labour market|labor market|\bworkforce\b|competition|market power|monopoly|\brace\b|competitiveness|investment')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'\bjobs\b|\bworkers\b|automation|\bworkforce\b|monopoly')
  ) AS frame_economic_competition_labour,

  -- Frame 6: Misinformation & integrity
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'misinformation|disinformation|deepfake|fake news|synthetic media|manipulation|propaganda|\bscam\b|impersonation|information integrity')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'misinformation|disinformation|deepfake|propaganda')
  ) AS frame_misinformation_integrity

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) >= '2022-11-01'
  AND DATE(_PARTITIONTIME) <= '2026-06-30'

  -- GenAI filter
  AND (
    REGEXP_CONTAINS(LOWER(AllNames),
      r'chatgpt|generative ai|genai|gen ai|large language model|\bllm\b|foundation model|frontier model|gpt-4|gpt4|gpt-5|gpt5|\bclaude\b|gemini|\bbard\b|dall-e|dalle|stable diffusion|midjourney|text-to-image|image generator')
    OR REGEXP_CONTAINS(LOWER(Quotations),
      r'chatgpt|generative ai|large language model|foundation model|frontier model')
  )

  -- Governance filter
  AND (
    REGEXP_CONTAINS(LOWER(Quotations),
      r'governance|regulation|regulatory|regulator|\bpolicy\b|oversight|\blaw\b|legislation|\bai act\b|eu ai act|framework|guidelines|compliance|enforcement|accountability|liability|responsible ai|trustworthy ai|ethical ai|risk management|guardrails|safeguards|ai safety|human rights|privacy|data protection|misinformation|deepfake')
    OR REGEXP_CONTAINS(V2Themes, r'ECON_REGULATION|HUMAN_RIGHTS|UNGP')
  )

GROUP BY month
ORDER BY month;
