"""
Preprocessing pipeline for raw GDELT GKG exports.

Expected input: DataFrame with columns produced by extract_genai_gov.sql —
    DATE, SourceCommonName, DocumentIdentifier, V2Themes, V2Tone,
    V2Locations, AllNames, Quotations
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from src.dictionaries import EU_FIPS_CODES, FRAME_DICTS, FRAME_COLS, GKG_TEXT_COLS, MILESTONES

# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def load_raw(path: str | Path) -> pd.DataFrame:
    """Read a parquet or CSV file from data/raw/ and return a DataFrame."""
    p = Path(path)
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p, low_memory=False)


# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------

def parse_dates(df: pd.DataFrame, date_col: str = "DATE") -> pd.DataFrame:
    """Convert GDELT DATE (YYYYMMDDhhmmss integer or string) to datetime.

    Adds 'year' (int) and 'month' (Period[M]) columns.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col].astype(str).str[:8], format="%Y%m%d", errors="coerce")
    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.to_period("M")
    return df


# ---------------------------------------------------------------------------
# Basic cleaning
# ---------------------------------------------------------------------------

def lower_cols(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """Lowercase the given columns (default: GKG_TEXT_COLS). Operates in place."""
    cols = cols or GKG_TEXT_COLS
    for col in cols:
        if col in df.columns:
            df[col] = df[col].fillna("").str.lower()
    return df


def drop_dupes(df: pd.DataFrame, key_col: str = "DocumentIdentifier") -> pd.DataFrame:
    """Remove duplicate records by document URL, keeping the first occurrence."""
    return df.drop_duplicates(subset=[key_col]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Headline fallback from URL slug
#
# A large share of GKG records have an empty/NaN Quotations field, which
# starves keyword/frame matching for those rows. Most article URLs encode a
# readable headline slug, so this derives one and uses it to backfill
# Quotations only where it's missing.
# ---------------------------------------------------------------------------

_URL_EXT_PATTERN = re.compile(r"\.(html?|cms|ece|aspx?|php|stm)$")
_URL_ID_BLOCK_PATTERN = re.compile(r"[_\-]\d{4,}")
_URL_BARE_NUM_PATTERN = re.compile(r"\b\d{4,}\b")
_URL_SEP_PATTERN = re.compile(r"[\-_]+")
_URL_PUNCT_PATTERN = re.compile(r"[^a-z0-9 ]+")
_URL_WS_PATTERN = re.compile(r"\s+")


def _url_to_headline(url: str) -> str:
    """Derive a readable headline-like string from an article URL's slug."""
    url = str(url).lower()
    url = re.sub(r"^https?://", "", url)
    url = url.split("?", 1)[0]
    # drop the domain (everything up to and including the first '/')
    parts = url.split("/", 1)
    path = parts[1] if len(parts) > 1 else parts[0]
    # the longest path segment is almost always the headline slug
    segments = [s for s in path.split("/") if s]
    if not segments:
        return ""
    slug = max(segments, key=len)
    slug = _URL_EXT_PATTERN.sub("", slug)
    slug = _URL_ID_BLOCK_PATTERN.sub(" ", slug)  # -123031700145, _98722849
    slug = _URL_BARE_NUM_PATTERN.sub(" ", slug)  # bare long numbers
    slug = _URL_SEP_PATTERN.sub(" ", slug)
    slug = _URL_PUNCT_PATTERN.sub(" ", slug)
    return _URL_WS_PATTERN.sub(" ", slug).strip()


def extract_headline_from_url(
    df: pd.DataFrame,
    url_col: str = "DocumentIdentifier",
    quotations_col: str = "Quotations",
) -> pd.DataFrame:
    """Backfill empty/NaN Quotations with a headline derived from the URL slug.

    Adds a 'headline_text' column (always populated) and overwrites
    quotations_col only for rows where it was empty, so frame matching has
    text to work with for rows that previously had none.
    """
    df = df.copy()
    df["headline_text"] = df[url_col].apply(_url_to_headline)
    if quotations_col in df.columns:
        empty = df[quotations_col].isna() | (df[quotations_col].astype(str).str.strip() == "")
        df.loc[empty, quotations_col] = df.loc[empty, "headline_text"]
    return df


# ---------------------------------------------------------------------------
# V2Tone parsing
# ---------------------------------------------------------------------------

_TONE_COLS = ["tone", "pos_score", "neg_score", "polarity", "act_ref_density", "self_ref_density", "word_count"]


def parse_tone(df: pd.DataFrame, tone_col: str = "V2Tone") -> pd.DataFrame:
    """Split V2Tone comma-separated string into 7 numeric columns."""
    if tone_col not in df.columns:
        return df
    tone_df = (
        df[tone_col]
        .fillna("")
        .str.split(",", expand=True)
        .iloc[:, :7]
        .apply(pd.to_numeric, errors="coerce")
    )
    tone_df.columns = _TONE_COLS[: len(tone_df.columns)]
    return pd.concat([df, tone_df], axis=1)


# ---------------------------------------------------------------------------
# Location / region labelling
# ---------------------------------------------------------------------------

_LOC_PATTERN = re.compile(r"^[1-5]#[^#]*#([A-Z]{2})#")


def _extract_country_code(loc_str: str) -> str:
    """Extract FIPS 10-4 country code from the first V2Locations entry."""
    if not loc_str:
        return ""
    first = loc_str.split(";")[0]
    m = _LOC_PATTERN.match(first)
    return m.group(1) if m else ""


def parse_country(df: pd.DataFrame, loc_col: str = "V2Locations") -> pd.DataFrame:
    """Add 'country_code' (FIPS) and 'region' (US/EU/UK/Other) columns."""
    df = df.copy()
    if loc_col not in df.columns:
        df["country_code"] = ""
        df["region"] = "Other"
        return df
    df["country_code"] = df[loc_col].fillna("").apply(_extract_country_code)
    df["region"] = df["country_code"].apply(_map_region)
    return df


def _map_region(code: str) -> str:
    if code == "US":
        return "US"
    if code == "UK":
        return "UK"
    if code in EU_FIPS_CODES:
        return "EU"
    return "Other"


# ---------------------------------------------------------------------------
# Frame assignment
# ---------------------------------------------------------------------------

def assign_frame_flags(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """Count keyword hits per frame across text columns.

    Adds one int column per frame (e.g. 'frame_risk_safety').
    """
    cols = cols or GKG_TEXT_COLS
    df = df.copy()
    combined = df[[c for c in cols if c in df.columns]].fillna("").apply(
        lambda row: " ".join(row), axis=1
    )
    for frame_name, keywords in FRAME_DICTS.items():
        col = f"frame_{frame_name}"
        pattern = "|".join(re.escape(kw) for kw in keywords)
        df[col] = combined.str.count(pattern)
    return df


def assign_dominant_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'dominant_frame' column: frame with highest hit count.

    Ties are broken alphabetically by frame name.
    """
    df = df.copy()
    present_cols = [c for c in FRAME_COLS if c in df.columns]
    if not present_cols:
        df["dominant_frame"] = None
        return df
    df["dominant_frame"] = df[present_cols].idxmax(axis=1).str.replace("frame_", "", regex=False)
    # articles with zero hits on all frames get None
    df.loc[df[present_cols].max(axis=1) == 0, "dominant_frame"] = None
    return df


# ---------------------------------------------------------------------------
# Event-study windows
# ---------------------------------------------------------------------------

def add_event_windows(
    df: pd.DataFrame,
    milestones: list[dict] | None = None,
    window: int = 3,
    month_col: str = "month",
) -> pd.DataFrame:
    """For each milestone, tag rows within ±window months.

    Adds 'event_name' and 'rel_month' columns.
    Rows not within any window retain NaN.
    """
    milestones = milestones or MILESTONES
    df = df.copy()
    df["event_name"] = pd.NA
    df["rel_month"] = pd.NA

    for milestone in milestones:
        pivot = pd.Period(milestone["date"][:7], freq="M")
        for offset in range(-window, window + 1):
            target = pivot + offset
            # Only assign if the row has not already been claimed by an earlier milestone
            mask = (df[month_col] == target) & df["event_name"].isna()
            df.loc[mask, "event_name"] = milestone["name"]
            df.loc[mask, "rel_month"] = offset

    return df


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the full preprocessing pipeline in the correct order."""
    df = parse_dates(df)
    df = lower_cols(df)
    df = drop_dupes(df)
    df = extract_headline_from_url(df)
    df = parse_tone(df)
    df = parse_country(df)
    df = assign_frame_flags(df)
    df = assign_dominant_frame(df)
    df = add_event_windows(df)
    return df
