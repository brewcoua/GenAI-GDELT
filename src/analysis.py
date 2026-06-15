"""
Core analytical functions for the three research questions.

All functions are pure: they take a DataFrame and return a DataFrame or dict.
No I/O or plotting happens here.

Two data paths are supported:

  Aggregated path (recommended, free):
    Input: output of aggregate_frames.sql — one row per month, columns:
      month, total_articles, frame_innovation_opportunity, frame_risk_safety, ...
    Functions: monthly_volume_agg, frame_shares_agg, event_study_agg

  Raw path (for spot-checking only):
    Input: output of extract_genai_gov.sql run through preprocessing.run_pipeline()
      — one row per article with frame_* columns
    Functions: monthly_volume, frame_shares, event_study, region_comparison
"""

from __future__ import annotations

import pandas as pd

from src.dictionaries import FRAME_COLS, MILESTONES

_AGG_FRAME_COLS = [
    "frame_innovation_opportunity",
    "frame_risk_safety",
    "frame_regulation_governance",
    "frame_rights_privacy",
    "frame_economic_competition_labour",
    "frame_misinformation_integrity",
]


def _parse_month_col(df: pd.DataFrame, col: str = "month") -> pd.Series:
    """Ensure the month column is Period[M], parsing strings if needed."""
    s = df[col]
    if not isinstance(s.iloc[0], pd.Period):
        s = s.astype(str).apply(lambda x: pd.Period(x, freq="M"))
    return s


def _months_diff(p: pd.Period, pivot: pd.Period) -> int:
    return (p.year - pivot.year) * 12 + (p.month - pivot.month)


# ============================================================================
# AGGREGATED PATH — use these when working with aggregate_frames.sql output
# ============================================================================

def load_agg(path: str) -> pd.DataFrame:
    """Load the CSV produced by aggregate_frames.sql and parse the month column."""
    df = pd.read_csv(path)
    df["month"] = _parse_month_col(df)
    return df.sort_values("month").reset_index(drop=True)


def monthly_volume_agg(agg_df: pd.DataFrame) -> pd.Series:
    """Extract monthly article counts from the aggregated DataFrame.

    Returns a Series indexed by Period[M] — directly used for Figure 1.
    """
    return agg_df.set_index("month")["total_articles"].rename("count")


def frame_shares_agg(agg_df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly frame proportions from the aggregated DataFrame.

    Returns a DataFrame: month index × frame-name columns (proportions).
    Used for Figure 2.
    """
    present = [c for c in _AGG_FRAME_COLS if c in agg_df.columns]
    if not present:
        raise ValueError("No frame columns found. Expected output of aggregate_frames.sql.")

    hits = agg_df[present].copy()
    row_totals = hits.sum(axis=1).replace(0, pd.NA)
    shares = hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    shares.index = _parse_month_col(agg_df)
    return shares.sort_index()


def event_study_agg(
    agg_df: pd.DataFrame,
    milestone_name: str,
    window: int = 3,
) -> dict[str, pd.Series | pd.DataFrame]:
    """Compute volume and frame shares per relative month around a milestone.

    Works on the aggregated monthly DataFrame (output of aggregate_frames.sql).
    No raw rows needed — all months already summarised.

    Returns
    -------
    dict with keys:
        'volume'  — Series: rel_month → article count
        'shares'  — DataFrame: rel_month × frame proportions
        'milestone' — dict with name, date, description
    """
    milestone = next((m for m in MILESTONES if m["name"] == milestone_name), None)
    if milestone is None:
        raise ValueError(f"Unknown milestone '{milestone_name}'. Check MILESTONES in dictionaries.py.")

    pivot = pd.Period(milestone["date"][:7], freq="M")

    months = _parse_month_col(agg_df)
    agg_df = agg_df.copy()
    agg_df["_rel_month"] = months.apply(lambda p: _months_diff(p, pivot))

    subset = agg_df[agg_df["_rel_month"].between(-window, window)].copy()
    if subset.empty:
        raise ValueError(f"No data within ±{window} months of '{milestone_name}'.")

    volume = subset.set_index("_rel_month")["total_articles"].rename("count")
    volume = volume.reindex(range(-window, window + 1), fill_value=0)

    present = [c for c in _AGG_FRAME_COLS if c in subset.columns]
    hits = subset[present].copy()
    hits.index = subset["_rel_month"].values
    row_totals = hits.sum(axis=1).replace(0, pd.NA)
    shares = hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    shares = shares.reindex(range(-window, window + 1), fill_value=0)

    return {"volume": volume, "shares": shares, "milestone": milestone}


# ============================================================================
# RAW PATH — use these when working with preprocessed per-article data
# ============================================================================

def monthly_volume(df: pd.DataFrame, month_col: str = "month") -> pd.Series:
    """Count records per month from a per-article DataFrame.

    Returns a Series indexed by Period[M].
    """
    return df.groupby(month_col).size().rename("count").sort_index()


def frame_shares(df: pd.DataFrame, month_col: str = "month") -> pd.DataFrame:
    """Compute monthly frame proportions from a per-article DataFrame.

    Returns a DataFrame: month index × frame-name columns (proportions).
    """
    present = [c for c in FRAME_COLS if c in df.columns]
    if not present:
        raise ValueError("No frame columns found. Run assign_frame_flags first.")

    monthly_hits = df.groupby(month_col)[present].sum()
    row_totals = monthly_hits.sum(axis=1).replace(0, pd.NA)
    shares = monthly_hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    return shares.sort_index()


def event_study(
    df: pd.DataFrame,
    milestone_name: str,
    window: int = 3,
    month_col: str = "month",
) -> dict[str, pd.Series | pd.DataFrame]:
    """Compute volume and frame shares per relative month from per-article data."""
    milestone = next((m for m in MILESTONES if m["name"] == milestone_name), None)
    if milestone is None:
        raise ValueError(f"Unknown milestone '{milestone_name}'. Check MILESTONES in dictionaries.py.")

    pivot = pd.Period(milestone["date"][:7], freq="M")

    df = df.copy()
    df["_rel_month"] = df[month_col].apply(lambda p: _months_diff(p, pivot))
    subset = df[df["_rel_month"].between(-window, window)].copy()

    if subset.empty:
        raise ValueError(f"No rows within ±{window} months of milestone '{milestone_name}'.")

    volume = subset.groupby("_rel_month").size().rename("count")
    volume = volume.reindex(range(-window, window + 1), fill_value=0)

    present = [c for c in FRAME_COLS if c in subset.columns]
    monthly_hits = subset.groupby("_rel_month")[present].sum()
    row_totals = monthly_hits.sum(axis=1).replace(0, pd.NA)
    shares = monthly_hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    shares = shares.reindex(range(-window, window + 1), fill_value=0)

    return {"volume": volume, "shares": shares, "milestone": milestone}


def region_comparison(
    df: pd.DataFrame,
    region_col: str = "region",
    regions: list[str] | None = None,
) -> pd.DataFrame:
    """Compute frame shares grouped by region from per-article data."""
    regions = regions or ["US", "EU", "UK"]
    subset = df[df[region_col].isin(regions)]
    present = [c for c in FRAME_COLS if c in subset.columns]
    hits = subset.groupby(region_col)[present].sum()
    row_totals = hits.sum(axis=1).replace(0, pd.NA)
    shares = hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    return shares


# ============================================================================
# ADDITIONAL ANALYSES — supplementary statistics and plots
# ============================================================================

def frame_counts_agg(agg_df: pd.DataFrame) -> pd.DataFrame:
    """Return absolute monthly keyword hit counts per frame from the aggregated DataFrame.

    Returns a DataFrame indexed by Period[M] with one column per frame (short names).
    """
    present = [c for c in _AGG_FRAME_COLS if c in agg_df.columns]
    counts = agg_df[present].copy()
    counts.columns = [c.replace("frame_", "") for c in counts.columns]
    counts.index = _parse_month_col(agg_df)
    return counts.sort_index()


def tone_over_time(df: pd.DataFrame, month_col: str = "month") -> pd.Series:
    """Return mean tone score per month from a per-article DataFrame.

    Requires 'tone' column (output of parse_tone).
    Returns a Series indexed by Period[M].
    """
    if "tone" not in df.columns:
        raise ValueError("'tone' column not found. Run parse_tone first.")
    return df.groupby(month_col)["tone"].mean().sort_index()


def frame_coverage_rate(df: pd.DataFrame) -> dict:
    """Return frame coverage statistics from a per-article DataFrame.

    Returns dict with keys: total, zero_frame_pct, any_frame_pct, multi_frame_pct.
    """
    present = [c for c in FRAME_COLS if c in df.columns]
    if not present:
        raise ValueError("No frame columns found. Run assign_frame_flags first.")
    total = len(df)
    any_hit = df[present].sum(axis=1) > 0
    multi_hit = df[present].gt(0).sum(axis=1) > 1
    return {
        "total": total,
        "zero_frame_pct": float((~any_hit).mean()),
        "any_frame_pct": float(any_hit.mean()),
        "multi_frame_pct": float(multi_hit.mean()),
    }


def source_concentration(df: pd.DataFrame, top_n: int = 20) -> tuple[pd.Series, float]:
    """Return (top_sources Series, HHI float) from a per-article DataFrame.

    HHI (Herfindahl-Hirschman Index) ranges from 0 (equal distribution) to 1 (monopoly).
    Requires 'SourceCommonName' column.
    """
    if "SourceCommonName" not in df.columns:
        raise ValueError("'SourceCommonName' column not found in DataFrame.")
    counts = df["SourceCommonName"].value_counts()
    shares = counts / counts.sum()
    hhi = float((shares ** 2).sum())
    return counts.head(top_n), hhi
