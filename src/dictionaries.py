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
    "gemini",
    "bard",
    "dall-e",
    "dalle",
    "stable diffusion",
    "midjourney",
    "text-to-image",
    "image generator",
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

# GKG fields we run keyword matching against (excludes V2Themes, handled separately)
GKG_TEXT_COLS: list[str] = ["AllNames", "Quotations"]

# ---------------------------------------------------------------------------
# Frame taxonomy (6 frames)
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
    ],
}

FRAME_COLS: list[str] = [f"frame_{name}" for name in FRAME_DICTS]

# ---------------------------------------------------------------------------
# Milestone events for event-study analysis (RQ3)
# ---------------------------------------------------------------------------

MILESTONES: list[dict] = [
    {
        "name": "chatgpt_launch",
        "date": "2022-11-30",
        "description": "ChatGPT public launch — starting anchor of study period",
    },
    {
        "name": "bletchley_summit",
        "date": "2023-11-01",
        "description": "UK AI Safety Summit at Bletchley Park",
    },
    {
        "name": "eu_ai_act",
        "date": "2024-03-13",
        "description": "EU AI Act adopted by the European Parliament",
    },
    {
        "name": "seoul_summit",
        "date": "2024-05-21",
        "description": "Seoul AI Safety Summit — major international follow-up",
    },
    {
        "name": "un_ai_resolution",
        "date": "2025-08-28",
        "description": "UN General Assembly adopts landmark AI governance resolution establishing a scientific panel and global dialogue",
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
