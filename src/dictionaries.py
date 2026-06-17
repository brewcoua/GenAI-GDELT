"""
Term lists, frame dictionaries, and milestone events.
Source data lives in data/lexicons/*.yaml — edit those files, not this one.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_LEXICONS = Path(__file__).parent.parent / "data" / "lexicons"


def _load(name: str) -> dict:
    return yaml.safe_load((_LEXICONS / name).read_text(encoding="utf-8"))


def _flatten(d: dict[str, list[str]]) -> list[str]:
    return [term for terms in d.values() for term in terms]


_genai  = _load("genai.yaml")
_gov    = _load("governance.yaml")
_frames = _load("frames.yaml")

# ---------------------------------------------------------------------------
# Study date range
# ---------------------------------------------------------------------------

STUDY_START_DATE = "2022-11-01"
STUDY_END_DATE   = "2026-06-30"

# ---------------------------------------------------------------------------
# Corpus definition lexicons
# ---------------------------------------------------------------------------

GENAI_LEXICON: list[str] = _genai["genai_lexicon"]

# Language-keyed dict; build_query.py flattens it before generating SQL.
GENAI_LEXICON_CONTEXTUAL: dict[str, list[str]] = _genai["genai_lexicon_contextual"]

# Language-keyed dict; build_query.py flattens it before generating SQL.
GOV_LEXICON: dict[str, list[str]] = _gov["gov_lexicon"]

GOV_THEME_TAGS: list[str] = _gov["gov_theme_tags"]
GOV_URL_SLUGS:  list[str] = _gov["gov_url_slugs"]

# ---------------------------------------------------------------------------
# Frame taxonomy
# ---------------------------------------------------------------------------

# Each frame's per-language term lists are flattened into a single list so
# downstream code (preprocessing.py, build_query.py) sees dict[str, list[str]].
FRAME_DICTS: dict[str, list[str]] = {
    frame: _flatten(langs) for frame, langs in _frames.items()
}

FRAME_COLS: list[str] = [f"frame_{name}" for name in FRAME_DICTS]

# GKG fields used for keyword matching (V2Themes is handled separately via theme codes)
GKG_TEXT_COLS: list[str] = ["AllNames", "Quotations"]

# ---------------------------------------------------------------------------
# Milestone events for event-study analysis
# ---------------------------------------------------------------------------

MILESTONES: list[dict] = _load("milestones.yaml")

# ---------------------------------------------------------------------------
# FIPS 10-4 country codes for EU member states
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
