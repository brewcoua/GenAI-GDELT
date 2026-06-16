"""
Single source of truth for all keyword lexicons, frame dictionaries, and milestone events.
All SQL queries and preprocessing functions derive their term lists from here.
"""

# ---------------------------------------------------------------------------
# Corpus definition lexicons
# ---------------------------------------------------------------------------

GENAI_LEXICON: list[str] = [
    "chatgpt",
    "generative ai",
    "genai",
    "gen ai",
    "large language model",
    "llm",
    "foundation model",
    "frontier model",
    "gpt-4",
    "gpt4",
    "gpt-5",
    "gpt5",
    "claude",
    "anthropic",
    "gemini",
    "bard",
    "dall-e",
    "dalle",
    "stable diffusion",
    "midjourney",
    "text-to-image",
    "image generator",
    # added from Alt_impl/GDELT_Web_Sci.ipynb (cell 2) — model/vendor names not
    # previously covered by the text-field lexicon above
    "copilot",
    "grok",
    "llama",
]

GOV_LEXICON: list[str] = [
    "governance",
    "regulation",
    "regulatory",
    "regulator",
    "policy",
    "oversight",
    "law",
    "legislation",
    "act",
    "ai act",
    "eu ai act",
    "framework",
    "guidelines",
    "compliance",
    "enforcement",
    "accountability",
    "liability",
    "responsible ai",
    "trustworthy ai",
    "ethical ai",
    "risk management",
    "guardrails",
    "safeguards",
    "ai safety",
    "human rights",
    "privacy",
    "data protection",
    "misinformation",
    "deepfake",
]

# GDELT V2Themes codes that signal a regulatory/legal/ethics/rights dimension.
# Ported from Alt_impl/GDELT_Web_Sci.ipynb (cell 2), merged with the three codes
# the original extract_genai_gov.sql already checked (ECON_REGULATION, UNGP,
# HUMAN_RIGHTS). Used as additional OR-branches inside the governance filter,
# not as a standalone corpus criterion — see MERGE_PLAN.md for why that
# distinction matters (Alt_impl's own query only used these as a derived
# column, not a filter, which silently drops the "and governance" half of the
# corpus definition in PLAN.md).
GOV_THEME_TAGS: list[str] = [
    "ECON_REGULATION",
    "UNGP",
    "HUMAN_RIGHTS",
    "EPU_CATS_REGULATION",
    "EPU_POLICY_LAW",
    "EPU_POLICY_REGULATION",
    "LEGISLATION",
    "WB_831_GOVERNANCE",
    "WB_2089_ETHICS_AND_CODES_OF_CONDUCT",
    "WB_845_LEGAL_AND_REGULATORY_FRAMEWORK",
    "WB_851_INTELLECTUAL_PROPERTY_RIGHTS",
    "WB_838_PUBLIC_ACCOUNTABILITY_MECHANISMS",
    "WB_279_ICT_STRATEGY_POLICY_AND_REGULATION",
    "WB_282_ICT_POLICY_REGULATORY_FRAMEWORK",
]

# URL-slug substrings (matched against DocumentIdentifier) that signal a
# governance dimension. Ported from Alt_impl cell 2; "-regulation" dropped
# as redundant since "-regulat" already matches it.
GOV_URL_SLUGS: list[str] = [
    "-regulat",
    "-policy-",
    "-legislat",
    "-governance-",
    "-safety-",
    "-security-",
    "-threat",
    "-warns-",
    "-warning-",
    "-ethic",
    "-privacy-",
    "-rights-",
    "-oversight-",
    "-copyright",
    "-lawsuit",
    "-banned-",
    "-ban-",
    "-ai-act",
]

# GKG fields we run keyword matching against (excludes V2Themes, handled separately)
GKG_TEXT_COLS: list[str] = ["AllNames", "Quotations"]

# ---------------------------------------------------------------------------
# Frame taxonomy (6 frames)
#
# Keyword lists below are the original dictionaries enriched with vocabulary
# ported from Alt_impl/GDELT_Web_Sci.ipynb (cell 7), which organized each
# frame into 4 narrower sub-themes. The 6 top-level frame names are unchanged
# (they're already committed in paper_setup.pdf's abstract) — only the
# keyword sets are richer.
#
# Two categories of Alt_impl vocabulary were deliberately left out, and
# should stay out unless explicitly re-justified (see MERGE_PLAN.md):
#   1. Three "FINAL ADDITIONS" patches Alt_impl added after manually
#      spotting single 2025/2026 incidents (military/pentagon/defense terms
#      in risk->security_cyber; poisons/poisoning/hospitalized in
#      risk->harm_to_vulnerable; antisemitic/hate-speech/"woke"/anti-white/
#      anti-black in rights_privacy->bias_discrimination). These read as
#      reactive, incident-specific overfitting rather than general framing
#      vocabulary, and the politically loaded terms risk miscoding unrelated
#      stories.
#   2. A handful of bare, topic-agnostic English words from Alt_impl's
#      sub-themes (e.g. "code", "write", "research", "advanced", "update",
#      "passes", "vs", "war", "eu", "national", "worth", "verify",
#      "detection") that would mostly match on word frequency rather than
#      framing signal — notably so here because frame counting in
#      preprocessing.py uses plain substring matching with no word-boundary
#      protection. Multi-word phrases and more specific single words were
#      kept.
# ---------------------------------------------------------------------------

FRAME_DICTS: dict[str, list[str]] = {
    "innovation_opportunity": [
        "innovation",
        "innovative",
        "breakthrough",
        "opportunity",
        "promise",
        "benefit",
        "potential",
        "growth",
        "boost",
        "productivity",
        "efficiency",
        "transform",
        "progress",
        "competitiveness",
        # capability_breakthrough
        "powerful",
        "smarter",
        "human level",
        "milestone",
        "cutting edge",
        "state of the art",
        "most capable",
        "outperforms",
        "aces",
        "beats humans",
        "superhuman",
        "reasoning",
        # product_launch
        "launches",
        "launch",
        "unveils",
        "unveiled",
        "releases",
        "released",
        "rolls out",
        "introduces",
        "introducing",
        "debuts",
        "new model",
        "new feature",
        "new tool",
        "announces",
        "announced",
        "rollout",
        "upgrade",
        # productivity_efficiency
        "automate",
        "workflow",
        "save time",
        "streamline",
        "augment",
        "assistant",
        "help you",
        "coding",
        # scientific_advance
        "scientific",
        "discovery",
        "study finds",
        "medical",
        "diagnosis",
        "drug discovery",
        "healthcare",
        "cancer",
        "scientists",
    ],
    "risk_safety": [
        "risk",
        "risks",
        "harm",
        "harms",
        "danger",
        "threat",
        "safety",
        "unsafe",
        "misuse",
        "abuse",
        "catastrophic",
        "existential",
        "crisis",
        # existential_safety
        "ai safety",
        "extinction",
        "out of control",
        "rogue",
        "doomsday",
        "warns",
        "warning",
        "fears",
        "scary",
        "alarming",
        "alarm",
        # security_cyber (base only — military/defense addition excluded, see above)
        "cyber",
        "cybersecurity",
        "hack",
        "hacking",
        "hackers",
        "malware",
        "phishing",
        "exploit",
        "breach",
        "weapon",
        "weapons",
        "drone",
        "drones",
        "national security",
        "attack",
        "scam",
        "scams",
        # reliability_hallucination
        "hallucination",
        "hallucinate",
        "hallucinations",
        "inaccurate",
        "fabricated",
        "unreliable",
        "flawed",
        "made up",
        "makes up",
        "lies",
        "false",
        "wrong",
        "accuracy",
        "errors",
        "mistakes",
        "confidently wrong",
        # harm_to_vulnerable (base only — poisoning/hospitalized addition excluded, see above)
        "teen",
        "teens",
        "children",
        "kids",
        "child",
        "mental health",
        "suicide",
        "self harm",
        "vulnerable",
        "addiction",
        "students",
    ],
    "regulation_governance": [
        "regulation",
        "regulatory",
        "regulator",
        "law",
        "legislation",
        "policy",
        "rules",
        "oversight",
        "compliance",
        "enforcement",
        "framework",
        "standard",
        "audit",
        # law_legislation
        "governance",
        "regulate",
        "regulating",
        "ai act",
        "guidelines",
        "code of practice",
        "laws",
        # bans_restrictions
        "ban",
        "banned",
        "bans",
        "restrict",
        "restricted",
        "restrictions",
        "prohibit",
        "moratorium",
        "pause",
        "blocks",
        "blocked",
        "blocking",
        # government_oversight
        "regulators",
        "ftc",
        "congress",
        "senate",
        "white house",
        "watchdog",
        "probe",
        "investigation",
        "investigating",
        "antitrust",
        "lawmakers",
        "brussels",
        "government",
        # litigation_legal
        "lawsuit",
        "lawsuits",
        "sued",
        "sues",
        "suing",
        "court",
        "legal",
        "settlement",
        "settle",
        "liability",
        "trial",
        "judge",
        "litigation",
    ],
    "rights_privacy": [
        "privacy",
        "data protection",
        "personal data",
        "human rights",
        "fundamental rights",
        "civil liberties",
        "surveillance",
        "bias",
        "fairness",
        "transparency",
        "consent",
        # data_privacy
        "gdpr",
        "data collection",
        "data breach",
        "scraping",
        "scraped",
        "your data",
        "user data",
        # copyright_ip
        "copyright",
        "intellectual property",
        "plagiarism",
        "infringement",
        "authors",
        "artists",
        "training data",
        "stolen",
        "pirated",
        "copyrighted",
        "creators",
        # surveillance
        "spying",
        "facial recognition",
        "tracking",
        "monitor",
        "monitoring",
        "spy",
        # bias_discrimination (base only — antisemitic/hate-speech/"woke" addition excluded, see above)
        "biased",
        "discrimination",
        "racist",
        "racism",
        "sexist",
        "discriminate",
        "stereotypes",
        "prejudice",
    ],
    "economic_competition_labour": [
        "jobs",
        "workers",
        "automation",
        "labour market",
        "labor market",
        "workforce",
        "competition",
        "market power",
        "monopoly",
        "race",
        "competitiveness",
        "investment",
        # jobs_labor
        "job",
        "layoffs",
        "unemployment",
        "replace",
        "replacing",
        "replaced",
        "labor",
        "hiring",
        "career",
        "employees",
        "white collar",
        # market_investment
        "invest",
        "funding",
        "valuation",
        "billion",
        "trillion",
        "stocks",
        "revenue",
        "profit",
        "ipo",
        "startup",
        "raises",
        "raised",
        "deal",
        "funding round",
        "market value",
        # geopolitical_race
        "china",
        "chinese",
        "arms race",
        "ai race",
        "sovereignty",
        "dominance",
        "us china",
        "beijing",
        "race for",
        # corporate_competition
        "rival",
        "rivals",
        "compete",
        "competing",
        "competitor",
        "competitors",
        "takes on",
        "versus",
        "battle",
        "race to",
        "challenger",
        "outpace",
        "showdown",
        "catch up",
    ],
    "misinformation_integrity": [
        "misinformation",
        "disinformation",
        "deepfake",
        "fake news",
        "synthetic media",
        "manipulation",
        "propaganda",
        "scam",
        "impersonation",
        "information integrity",
        # deepfakes
        "deepfakes",
        "cloned voice",
        "face swap",
        "fake video",
        "fake image",
        "fake photos",
        # fabricated_content
        "false information",
        "fabricated content",
        "fake content",
        # propaganda_manipulation
        "manipulate",
        "election",
        "elections",
        "fraud",
        "impersonate",
        "voters",
        # trust_authenticity
        "authenticity",
        "credibility",
        "watermark",
        "detect ai",
        "ai detector",
    ],
}

FRAME_COLS: list[str] = [f"frame_{name}" for name in FRAME_DICTS]

# ---------------------------------------------------------------------------
# Milestone events for event-study analysis (RQ3)
# ---------------------------------------------------------------------------

# Merged with the milestone set from Alt_impl/GDELT_Web_Sci.ipynb (referenced in
# results_section.md cell 15, though the MILESTONES variable itself was never
# defined in that notebook's visible cells — see MERGE_PLAN.md). Dropped main's
# out-of-window `un_ai_resolution` (2025-08-28, beyond the Jun-2026 data range)
# and Alt_impl's lower-signal `prohibited_practices`/`eu_omnibus` entries to
# hold the merged list to ~6-7 per PLAN.md's page-budget guidance.
#
# NOTE: bletchley_summit and eu_ai_act_agreement are only ~1 month apart, so
# their +/-3-month event-study windows overlap heavily. This is a known,
# documented limitation (Alt_impl's own results_section.md flags it explicitly:
# "the late-2023 milestones cluster temporally... not statistically
# independent") — carried forward as a caveat rather than algorithmically
# resolved, consistent with this project's lightweight/transparent methodology.
MILESTONES: list[dict] = [
    {
        "name": "chatgpt_launch",
        "date": "2022-11-30",
        "description": "ChatGPT public launch — starting anchor of study period",
    },
    {
        "name": "pause_ai_letter",
        "date": "2023-03-22",
        "description": "Future of Life Institute 'Pause Giant AI Experiments' open letter",
    },
    {
        "name": "bletchley_summit",
        "date": "2023-11-01",
        "description": "UK AI Safety Summit at Bletchley Park",
    },
    {
        "name": "eu_ai_act_agreement",
        "date": "2023-12-08",
        "description": "EU AI Act political agreement reached in trilogue negotiations",
    },
    {
        "name": "seoul_summit",
        "date": "2024-05-21",
        "description": "Seoul AI Safety Summit — major international follow-up",
    },
    {
        "name": "eu_ai_act_in_force",
        "date": "2024-08-01",
        "description": "EU AI Act enters into force — routine implementation milestone, used as a null-result contrast to the 2023 agenda-setting events",
    },
    {
        "name": "gpai_obligations",
        "date": "2025-08-02",
        "description": "EU AI Act general-purpose AI model obligations become applicable",
    },
]

# ---------------------------------------------------------------------------
# FIPS 10-4 country codes for EU member states (for region labelling)
# ---------------------------------------------------------------------------

EU_FIPS_CODES: set[str] = {
    "AU",  # Austria
    "BE",  # Belgium
    "BU",  # Bulgaria
    "HR",  # Croatia
    "CY",  # Cyprus
    "EZ",  # Czech Republic
    "DA",  # Denmark
    "EN",  # Estonia
    "FI",  # Finland
    "FR",  # France
    "GM",  # Germany
    "GR",  # Greece
    "HU",  # Hungary
    "EI",  # Ireland
    "IT",  # Italy
    "LG",  # Latvia
    "LH",  # Lithuania
    "LU",  # Luxembourg
    "MT",  # Malta
    "NL",  # Netherlands
    "PL",  # Poland
    "PO",  # Portugal
    "RO",  # Romania
    "LO",  # Slovakia
    "SI",  # Slovenia
    "SP",  # Spain
    "SW",  # Sweden
}
