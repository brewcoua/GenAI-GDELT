"""
Single source of truth for all keyword lexicons, frame dictionaries, and milestone events.
All SQL queries (generated dynamically by src/build_query.py — see that module's
docstring; queries/*.sql are regenerated artifacts, never hand-edited) and preprocessing
functions derive their term lists from here.
"""

# ---------------------------------------------------------------------------
# Study date range (BigQuery _PARTITIONTIME filter bounds for every query)
# ---------------------------------------------------------------------------

STUDY_START_DATE = "2022-11-01"
STUDY_END_DATE = "2026-06-30"

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
    "copilot",
    "grok",
    "llama",
]

# Subset of GENAI_LEXICON checked against Quotations (free text), as opposed to
# the full list above which is checked against AllNames (GDELT's NER-extracted
# entity field). Brand/product names are precise and cheap to match in AllNames;
# Quotations is a much longer field, so only broad contextual phrases are
# checked there to control scan cost and avoid false hits from short/ambiguous
# product names (e.g. "Bard", "Grok") appearing as ordinary words inside quotes.
#
# Structured as {iso-639-1 code: [terms]} so non-English EU articles whose
# quoted text is in French, German, etc. are captured. build_query.py flattens
# this to a single list before generating SQL.
GENAI_LEXICON_CONTEXTUAL: dict[str, list[str]] = {
    "en": [
        "chatgpt",
        "generative ai",
        "large language model",
        "foundation model",
        "frontier model",
        "anthropic",
    ],
    "fr": [
        "ia générative",
        "intelligence artificielle générative",
        "grand modèle de langage",
        "modèle de langage",
        "modèle de fondation",
    ],
    "de": [
        "generative ki",
        "generative künstliche intelligenz",
        "großes sprachmodell",
        "sprachmodell",
        "basismodell",
    ],
    "es": [
        "ia generativa",
        "inteligencia artificial generativa",
        "modelo de lenguaje grande",
        "modelo de lenguaje",
        "modelo fundacional",
    ],
    "it": [
        "ia generativa",
        "intelligenza artificiale generativa",
        "modello linguistico",
        "modello di linguaggio",
        "modello fondazionale",
    ],
    "nl": [
        "generatieve ai",
        "generatieve kunstmatige intelligentie",
        "groot taalmodel",
        "taalmodel",
        "basismodel",
    ],
    "pl": [
        "generatywna ai",
        "generatywna sztuczna inteligencja",
        "duży model językowy",
        "model językowy",
        "model podstawowy",
    ],
    "pt": [
        "ia generativa",
        "inteligência artificial generativa",
        "grande modelo de linguagem",
        "modelo de linguagem",
        "modelo fundacional",
    ],
}

# Structured as {iso-639-1 code: [terms]} to reduce the English-language bias
# introduced by matching only against English quotations. build_query.py flattens
# this before generating SQL. The GenAI AND-filter guards against false positives
# from common governance words in unrelated articles.
#
# Notes on specific exclusions / per-language decisions:
#   - "act" is excluded from "en" (substring-unsafe — see comment below).
#     "ai act" / "eu ai act" are safe and kept in "en"; EU press commonly uses
#     these English phrases even in non-English articles, so no translation needed.
#   - "deepfake" is kept in "en" only — it is a universal loanword used across
#     all EU languages without translation.
#   - German "datenschutz" covers both "privacy" and "data protection"; listed
#     once to avoid duplicate LIKE clauses.
#   - "compliance" and "governance" are international business/legal terms used
#     verbatim in German, Dutch, and Italian press; they remain in those sections.
GOV_LEXICON: dict[str, list[str]] = {
    "en": [
        "governance",
        "regulation",
        "regulatory",
        "regulator",
        "policy",
        "oversight",
        "law",
        "legislation",
        # "act" deliberately excluded: as a bare substring it matches "fact",
        # "react", "impact", "contact", "interact", "transaction", "exactly",
        # "enact", "actor", "actually" etc. — the same "don't put substring-unsafe
        # bare words in a dict that drives substring matching" rule FRAME_DICTS
        # documents below. "ai act" / "eu ai act" are kept since they're specific
        # enough not to collide.
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
    ],
    "fr": [
        "gouvernance",
        "réglementation",
        "régulation",
        "réglementaire",
        "régulateur",
        "politique",
        "surveillance",
        "loi",
        "législation",
        "cadre réglementaire",
        "lignes directrices",
        "conformité",
        "mise en application",
        "reddition de comptes",
        "responsabilité civile",
        "ia responsable",
        "ia digne de confiance",
        "ia éthique",
        "gestion des risques",
        "garde-fous",
        "garanties",
        "sécurité de l'ia",
        "droits humains",
        "droits de l'homme",
        "vie privée",
        "protection des données",
        "désinformation",
    ],
    "de": [
        "governance",
        "regulierung",
        "regulatorisch",
        "aufsichtsbehörde",
        "richtlinie",
        "aufsicht",
        "gesetz",
        "gesetzgebung",
        "rechtsrahmen",
        "leitlinien",
        "compliance",
        "durchsetzung",
        "rechenschaftspflicht",
        "haftung",
        "verantwortungsvolle ki",
        "vertrauenswürdige ki",
        "ethische ki",
        "risikomanagement",
        "leitplanken",
        "schutzmaßnahmen",
        "ki-sicherheit",
        "menschenrechte",
        "datenschutz",  # covers both "privacy" and "data protection" in German
        "desinformation",
    ],
    "es": [
        "gobernanza",
        "regulación",
        "regulatorio",
        "regulador",
        "política",
        "supervisión",
        "ley",
        "legislación",
        "marco regulatorio",
        "directrices",
        "cumplimiento",
        "aplicación",
        "rendición de cuentas",
        "responsabilidad",
        "ia responsable",
        "ia confiable",
        "ia ética",
        "gestión de riesgos",
        "salvaguardas",
        "salvaguardias",
        "seguridad de la ia",
        "derechos humanos",
        "privacidad",
        "protección de datos",
        "desinformación",
    ],
    "it": [
        "governance",
        "regolamentazione",
        "normativo",
        "regolatorio",
        "autorità di regolazione",
        "politica",
        "supervisione",
        "legge",
        "legislazione",
        "quadro normativo",
        "linee guida",
        "conformità",
        "applicazione",
        "responsabilità",
        "ia responsabile",
        "ia affidabile",
        "ia etica",
        "gestione del rischio",
        "salvaguardie",
        "garanzie",
        "sicurezza dell'ia",
        "diritti umani",
        "riservatezza",
        "protezione dei dati",
        "disinformazione",
    ],
    "nl": [
        "governance",
        "regulering",
        "regelgeving",
        "regelgevend",
        "toezichthouder",
        "beleid",
        "toezicht",
        "wet",
        "wetgeving",
        "kader",
        "richtlijnen",
        "naleving",
        "handhaving",
        "verantwoording",
        "aansprakelijkheid",
        "verantwoorde ai",
        "betrouwbare ai",
        "ethische ai",
        "risicobeheer",
        "vangrails",
        "waarborgen",
        "ai-veiligheid",
        "mensenrechten",
        "privacy",
        "gegevensbescherming",
        "desinformatie",
    ],
    "pl": [
        "zarządzanie",
        "regulacja",
        "regulacyjny",
        "organ regulacyjny",
        "polityka",
        "nadzór",
        "prawo",
        "ustawodawstwo",
        "ramy prawne",
        "wytyczne",
        "zgodność",
        "egzekwowanie",
        "rozliczalność",
        "odpowiedzialność",
        "odpowiedzialna ai",
        "godna zaufania ai",
        "etyczna ai",
        "zarządzanie ryzykiem",
        "zabezpieczenia",
        "środki ochrony",
        "bezpieczeństwo ai",
        "prawa człowieka",
        "prywatność",
        "ochrona danych",
        "dezinformacja",
    ],
    "pt": [
        "governança",
        "regulamentação",
        "regulação",
        "regulatório",
        "regulador",
        "política",
        "supervisão",
        "fiscalização",
        "lei",
        "legislação",
        "quadro regulatório",
        "diretrizes",
        "conformidade",
        "aplicação",
        "responsabilização",
        "prestação de contas",
        "ia responsável",
        "ia confiável",
        "ia ética",
        "gestão de riscos",
        "salvaguardas",
        "garantias",
        "segurança da ia",
        "direitos humanos",
        "privacidade",
        "proteção de dados",
        "desinformação",
    ],
    "ro": [
        "guvernanță",
        "reglementare",
        "regulatorie",
        "autoritate de reglementare",
        "politică",
        "supraveghere",
        "lege",
        "legislație",
        "cadru normativ",
        "orientări",
        "conformitate",
        "aplicare",
        "răspundere",
        "ia responsabilă",
        "siguranța ia",
        "gestionarea riscurilor",
        "garanții",
        "drepturile omului",
        "confidențialitate",
        "viața privată",
        "protecția datelor",
        "dezinformare",
    ],
}

# GDELT V2Themes codes that signal a regulatory/legal/ethics/rights dimension.
# All codes verified against the existing raw corpus (LIKE-substring hit counts
# measured on gdelt_genai_gov.csv). Codes are matched via SQL LIKE '%code%' so a
# shorter prefix can intentionally catch multiple more-specific codes
# (e.g. "HUMAN_RIGHTS" catches WB_2203_HUMAN_RIGHTS, SELF_IDENTIFIED_HUMAN_RIGHTS,
# WB_2507_HUMAN_RIGHTS_ABUSES_AND_VIOLATIONS etc.; "WB_282_ICT_POLICY_REGULATORY_FRAMEWORK"
# catches the full WB_282_ICT_POLICY_REGULATORY_FRAMEWORK_AND_INSTITUTIONS code).
#
# Removed from the original list (0 LIKE hits in corpus — do not exist in GDELT):
#   ECON_REGULATION, UNGP (too broad — 83% is UNGP_FORESTS_RIVERS_OCEANS),
#   EPU_POLICY_NATIONAL_SECURITY, TAX_WORLDLEGALRIGHTS, TAX_WORLDLEGALRIGHTS_PRIVACY
GOV_THEME_TAGS: list[str] = [
    # --- Policy / regulatory / legal framework ---
    "EPU_CATS_REGULATION",              # 223K hits
    "EPU_POLICY_LAW",                   # 463K hits
    "EPU_POLICY_REGULATION",            # 49K hits
    "LEGISLATION",                      # 511K hits
    "WB_831_GOVERNANCE",                # 373K hits
    "WB_845_LEGAL_AND_REGULATORY_FRAMEWORK",  # 103K hits
    "WB_279_ICT_STRATEGY_POLICY_AND_REGULATION",       # 779 hits
    "WB_282_ICT_POLICY_REGULATORY_FRAMEWORK",          # 634 hits (prefix-matches _AND_INSTITUTIONS)
    # --- Ethics / accountability / rights ---
    "WB_2089_ETHICS_AND_CODES_OF_CONDUCT",  # 36K hits
    "WB_838_PUBLIC_ACCOUNTABILITY_MECHANISMS",  # 34K hits
    "WB_851_INTELLECTUAL_PROPERTY_RIGHTS",  # 46K hits
    "HUMAN_RIGHTS",                     # 76K hits (prefix-matches WB_2203_HUMAN_RIGHTS etc.)
    "UNGP_POLITICAL_FREEDOMS",          # 52K hits
    "UNGP_FREEDOM_FROM_DISCRIMINATION", # 45K hits
    "UNGP_CRIME_VIOLENCE",              # 155K hits
    # --- Digital / ICT governance ---
    "WB_133_INFORMATION_AND_COMMUNICATION_TECHNOLOGIES",  # 284K hits
    "WB_678_DIGITAL_GOVERNMENT",        # 272K hits
    "WB_670_ICT_SECURITY",              # 33K hits
    # --- Security / safety ---
    "EPU_CATS_NATIONAL_SECURITY",       # 166K hits
    "CYBER_ATTACK",                     # 28K hits
    # --- Legal proceedings / enforcement ---
    "WB_840_JUSTICE",                   # 257K hits
    "WB_1014_CRIMINAL_JUSTICE",         # 165K hits
    "TRIAL",                            # 196K hits
    # --- Privacy / data protection ---
    "WB_2369_DATA_PRIVACY",             # 3K hits (specific and high-precision)
    # --- Democratic / electoral context ---
    "ELECTION",                         # 121K hits
    "ELECTION_FRAUD",                   # 4K hits
    # --- Governance actors ---
    "GENERAL_GOVERNMENT",               # 313K hits
    "TAX_FNCACT_REGULATOR",             # 14K hits
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
