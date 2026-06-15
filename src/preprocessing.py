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
    df = parse_tone(df)
    df = parse_country(df)
    df = assign_frame_flags(df)
    df = assign_dominant_frame(df)
    df = add_event_windows(df)
    return df
