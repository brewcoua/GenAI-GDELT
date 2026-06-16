-- aggregate_frames.sql
-- Recommended primary query: frame counts grouped by month, computed in BigQuery.
-- Downloads ~40 rows instead of millions. Stays well within the 1 TB free tier.
--
-- Each frame column counts articles where at least one keyword from that frame
-- appears in AllNames or Quotations (binary presence per article, not hit
-- count — this must stay binary to match the dominant-frame logic in
-- src/preprocessing.py, and to match extract_genai_gov.sql's corpus
-- definition, the GenAI/Governance filters below must stay IDENTICAL to the
-- ones in that file; see MERGE_PLAN.md).
--
-- Keyword patterns derived from src/dictionaries.py FRAME_DICTS, enriched
-- with sub-theme vocabulary ported from Alt_impl/GDELT_Web_Sci.ipynb (see
-- MERGE_PLAN.md for what was deliberately excluded). Quotations patterns
-- cover the full enriched dictionaries; AllNames patterns keep the original
-- smaller, higher-precision subset since AllNames is a secondary signal.
-- Run src/build_query.py to regenerate the GenAI/Governance LIKE blocks if
-- dictionaries change (the per-frame REGEXP patterns are currently
-- hand-derived from FRAME_DICTS and not yet auto-generated).

SELECT
  FORMAT_DATE(
    '%Y-%m',
    PARSE_DATE('%Y%m%d', SUBSTR(CAST(DATE AS STRING), 1, 8))
  ) AS month,

  COUNT(*) AS total_articles,

  -- Frame 1: Innovation & opportunity
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'innovation|innovative|breakthrough|opportunity|promise|benefit|potential|growth|\bboost\b|productivity|efficiency|transform|progress|competitiveness|powerful|smarter|human level|milestone|cutting edge|state of the art|most capable|outperforms|\baces\b|beats humans|superhuman|reasoning|launches|launch|unveils|unveiled|releases|released|rolls out|introduces|introducing|debuts|new model|new feature|new tool|announces|announced|rollout|upgrade|automate|workflow|save time|streamline|augment|assistant|help you|coding|scientific|discovery|study finds|medical|diagnosis|drug discovery|healthcare|cancer|scientists')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'innovation|breakthrough|opportunity|productivity')
  ) AS frame_innovation_opportunity,

  -- Frame 2: Risk & safety
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'\brisk\b|\brisks\b|\bharm\b|\bharms\b|danger|threat|safety|unsafe|misuse|\babuse\b|catastrophic|existential|crisis|ai safety|extinction|out of control|\brogue\b|doomsday|\bwarns\b|warning|\bfears\b|\bscary\b|alarming|\balarm\b|\bcyber\b|cybersecurity|\bhack\b|hacking|hackers|malware|phishing|exploit|breach|weapon|weapons|\bdrone\b|drones|national security|attack|\bscam\b|\bscams\b|hallucination|hallucinate|hallucinations|inaccurate|fabricated|unreliable|flawed|made up|makes up|\blies\b|\bfalse\b|\bwrong\b|accuracy|errors|mistakes|confidently wrong|\bteen\b|\bteens\b|children|\bkids\b|\bchild\b|mental health|suicide|self harm|vulnerable|addiction|students')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'\brisk\b|danger|threat|\bsafety\b|catastrophic')
  ) AS frame_risk_safety,

  -- Frame 3: Regulation & governance
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'regulation|regulatory|regulator|\blaw\b|legislation|policy|\brules\b|oversight|compliance|enforcement|framework|standard|\baudit\b|governance|regulate|regulating|ai act|guidelines|code of practice|\blaws\b|\bban\b|banned|\bbans\b|restrict|restricted|restrictions|prohibit|moratorium|\bpause\b|blocks|blocked|blocking|regulators|\bftc\b|congress|senate|white house|watchdog|\bprobe\b|investigation|investigating|antitrust|lawmakers|brussels|government|lawsuit|lawsuits|\bsued\b|\bsues\b|\bsuing\b|\bcourt\b|\blegal\b|settlement|settle|liability|\btrial\b|\bjudge\b|litigation')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'regulation|regulatory|legislation|oversight|compliance')
  ) AS frame_regulation_governance,

  -- Frame 4: Rights & privacy
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'privacy|data protection|personal data|human rights|fundamental rights|civil liberties|surveillance|\bbias\b|fairness|transparency|consent|\bgdpr\b|data collection|data breach|scraping|scraped|your data|user data|copyright|intellectual property|plagiarism|infringement|authors|artists|training data|stolen|pirated|copyrighted|creators|spying|facial recognition|tracking|monitor|monitoring|\bspy\b|biased|discrimination|racist|racism|sexist|discriminate|stereotypes|prejudice')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'privacy|surveillance|\bbias\b|fairness|transparency')
  ) AS frame_rights_privacy,

  -- Frame 5: Economic competition & labour
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'\bjobs\b|workers|automation|labour market|labor market|workforce|competition|market power|monopoly|\brace\b|competitiveness|investment|\bjob\b|layoffs|unemployment|replace|replacing|replaced|\blabor\b|hiring|career|employees|white collar|invest|funding|valuation|billion|trillion|stocks|revenue|profit|\bipo\b|startup|raises|raised|\bdeal\b|funding round|market value|\bchina\b|chinese|arms race|ai race|sovereignty|dominance|us china|beijing|race for|\brival\b|rivals|compete|competing|competitor|competitors|takes on|versus|battle|race to|challenger|outpace|showdown|catch up')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'\bjobs\b|\bworkers\b|automation|\bworkforce\b|monopoly')
  ) AS frame_economic_competition_labour,

  -- Frame 6: Misinformation & integrity
  COUNTIF(REGEXP_CONTAINS(LOWER(Quotations),
    r'misinformation|disinformation|deepfake|fake news|synthetic media|manipulation|propaganda|\bscam\b|impersonation|information integrity|deepfakes|cloned voice|face swap|fake video|fake image|fake photos|false information|fabricated content|fake content|manipulate|election|elections|\bfraud\b|impersonate|voters|authenticity|credibility|watermark|detect ai|ai detector')
    OR REGEXP_CONTAINS(LOWER(AllNames),
    r'misinformation|disinformation|deepfake|propaganda')
  ) AS frame_misinformation_integrity

FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE DATE(_PARTITIONTIME) >= '2022-11-01'
  AND DATE(_PARTITIONTIME) <= '2026-06-30'

  -- GenAI filter (identical predicate to extract_genai_gov.sql)
  AND (
    REGEXP_CONTAINS(LOWER(AllNames),
      r'chatgpt|generative ai|genai|gen ai|large language model|\bllm\b|foundation model|frontier model|gpt-4|gpt4|gpt-5|gpt5|\bclaude\b|anthropic|gemini|\bbard\b|dall-e|dalle|stable diffusion|midjourney|text-to-image|image generator|copilot|\bgrok\b|\bllama\b')
    OR REGEXP_CONTAINS(LOWER(Quotations),
      r'chatgpt|generative ai|large language model|foundation model|frontier model|anthropic')
  )

  -- Governance filter (identical predicate to extract_genai_gov.sql:
  -- keyword-in-Quotations OR theme-tag-in-V2Themes OR url-slug-in-DocumentIdentifier)
  AND (
    REGEXP_CONTAINS(LOWER(Quotations),
      r'governance|regulation|regulatory|regulator|\bpolicy\b|oversight|\blaw\b|legislation|\bai act\b|eu ai act|framework|guidelines|compliance|enforcement|accountability|liability|responsible ai|trustworthy ai|ethical ai|risk management|guardrails|safeguards|ai safety|human rights|privacy|data protection|misinformation|deepfake')
    OR REGEXP_CONTAINS(V2Themes,
      r'ECON_REGULATION|UNGP|HUMAN_RIGHTS|EPU_CATS_REGULATION|EPU_POLICY_LAW|EPU_POLICY_REGULATION|LEGISLATION|WB_831_GOVERNANCE|WB_2089_ETHICS_AND_CODES_OF_CONDUCT|WB_845_LEGAL_AND_REGULATORY_FRAMEWORK|WB_851_INTELLECTUAL_PROPERTY_RIGHTS|WB_838_PUBLIC_ACCOUNTABILITY_MECHANISMS|WB_279_ICT_STRATEGY_POLICY_AND_REGULATION|WB_282_ICT_POLICY_REGULATORY_FRAMEWORK')
    OR REGEXP_CONTAINS(LOWER(DocumentIdentifier),
      r'-regulat|-policy-|-legislat|-governance-|-safety-|-security-|-threat|-warns-|-warning-|-ethic|-privacy-|-rights-|-oversight-|-copyright|-lawsuit|-banned-|-ban-|-ai-act')
  )

GROUP BY month
ORDER BY month;
