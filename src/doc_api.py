"""
GDELT DOC 2.0 API client — completely free, no account or credentials needed.

Used for quick monthly volume checks and cross-validation of RQ1/RQ3 results
without touching BigQuery. Covers Jan 2017 onwards.

API docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""

from __future__ import annotations

import pandas as pd
import requests

from src.dictionaries import GENAI_LEXICON, GOV_LEXICON

_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Core terms from each lexicon that work well with the DOC API query syntax.
# The full lexicons are too long for a URL; these cover the most salient signals.
_GENAI_CORE = [
    "chatgpt",
    '"generative ai"',
    '"large language model"',
    "openai",
    "gemini",
    '"stable diffusion"',
    "midjourney",
    '"foundation model"',
]

_GOV_CORE = [
    "regulation",
    "governance",
    "policy",
    "oversight",
    '"ai act"',
    '"ai safety"',
    "privacy",
    '"data protection"',
]


def build_doc_query(genai_terms: list[str] | None = None, gov_terms: list[str] | None = None) -> str:
    """Build a DOC 2.0 API query string combining GenAI and governance terms.

    Uses OR within each group and AND between groups (space-separated groups).
    """
    genai = genai_terms or _GENAI_CORE
    gov = gov_terms or _GOV_CORE
    genai_clause = " OR ".join(genai)
    gov_clause = " OR ".join(gov)
    return f"({genai_clause}) ({gov_clause})"


def fetch_timeline_vol(
    query: str | None = None,
    start: str = "20221101000000",
    end: str = "20260601000000",
    smooth: bool = False,
) -> pd.DataFrame:
    """Fetch monthly article volume from the GDELT DOC 2.0 API.

    Parameters
    ----------
    query:
        DOC API query string. Defaults to build_doc_query().
    start / end:
        Date range in YYYYMMDDhhmmss format.
    smooth:
        If True, use timelinevolnorm (normalised by total news volume).
        If False (default), use timelinevolraw (raw article counts).

    Returns
    -------
    DataFrame with columns: month (Period[M]), volume (float).
    """
    query = query or build_doc_query()
    mode = "timelinevolnorm" if smooth else "timelinevolraw"
    params = {
        "query": query,
        "mode": mode,
        "format": "json",
        "startdatetime": start,
        "enddatetime": end,
    }
    resp = requests.get(_BASE_URL, params=params, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    # Response shape: {"timeline": [{"series": "...", "data": [{...}, ...]}]}
    series = data.get("timeline", [])
    if not series or not series[0].get("data"):
        raise ValueError("DOC API returned no timeline data. Check query or date range.")

    records = series[0]["data"]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"].str.replace("T", " ").str[:16], errors="coerce")
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["value"].sum().reset_index()
    monthly.columns = ["month", "volume"]
    return monthly.sort_values("month").reset_index(drop=True)


def fetch_timeline_tone(
    query: str | None = None,
    start: str = "20221101000000",
    end: str = "20260601000000",
) -> pd.DataFrame:
    """Fetch monthly average tone from the GDELT DOC 2.0 API.

    Returns
    -------
    DataFrame with columns: month (Period[M]), tone (float).
    Tone is positive = more positive coverage, negative = more negative.
    """
    query = query or build_doc_query()
    params = {
        "query": query,
        "mode": "timelinetone",
        "format": "json",
        "startdatetime": start,
        "enddatetime": end,
    }
    resp = requests.get(_BASE_URL, params=params, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    series = data.get("timeline", [])
    if not series or not series[0].get("data"):
        raise ValueError("DOC API returned no tone data. Check query or date range.")

    records = series[0]["data"]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"].str.replace("T", " ").str[:16], errors="coerce")
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["value"].mean().reset_index()
    monthly.columns = ["month", "tone"]
    return monthly.sort_values("month").reset_index(drop=True)
