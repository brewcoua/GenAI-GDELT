"""
Core analytical functions for the three research questions.

All functions are pure: they take a DataFrame and return a DataFrame or dict.
No I/O or plotting happens here.

Input: output of extract_genai_gov.sql run through preprocessing.run_pipeline()
  — one row per article with frame_* integer columns (keyword hit counts),
    plus month (Period[M]), region, event_name, rel_month columns.
"""

from __future__ import annotations

import pandas as pd

from src.dictionaries import FRAME_COLS, MILESTONES


def _months_diff(p: pd.Period, pivot: pd.Period) -> int:
    return (p.year - pivot.year) * 12 + (p.month - pivot.month)


# ============================================================================
# MONTHLY AGGREGATES
# ============================================================================

def monthly_volume(df: pd.DataFrame, month_col: str = "month") -> pd.Series:
    """Count records per month from a per-article DataFrame.

    Returns a Series indexed by Period[M].
    """
    return df.groupby(month_col).size().rename("count").sort_index()


def frame_shares(df: pd.DataFrame, month_col: str = "month") -> pd.DataFrame:
    """Compute monthly frame prevalence rates from a per-article DataFrame.

    Each value is the fraction of that month's articles that matched the frame
    (frames are multi-label, so column values can sum to more than 1).
    Returns a DataFrame: month index × frame-name columns (rates 0–1+).
    """
    present = [c for c in FRAME_COLS if c in df.columns]
    if not present:
        raise ValueError("No frame columns found. Run assign_frame_flags first.")

    monthly_counts = df.groupby(month_col).size().rename("count")
    monthly_hits = df.groupby(month_col)[present].sum()
    shares = monthly_hits.div(monthly_counts, axis=0).fillna(0)
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
    monthly_counts = subset.groupby("_rel_month").size()
    shares = monthly_hits.div(monthly_counts, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    shares = shares.reindex(range(-window, window + 1), fill_value=0)

    return {"volume": volume, "shares": shares, "milestone": milestone}


def region_comparison(
    df: pd.DataFrame,
    region_col: str = "region",
    regions: list[str] | None = None,
) -> pd.DataFrame:
    """Compute frame prevalence rates grouped by region from per-article data.

    Each value is the fraction of that region's articles that matched the frame
    (multi-label, so row values can sum to more than 1).
    """
    regions = regions or ["US", "EU", "UK"]
    subset = df[df[region_col].isin(regions)]
    present = [c for c in FRAME_COLS if c in subset.columns]
    hits = subset.groupby(region_col, observed=True)[present].sum()
    total_articles = subset.groupby(region_col, observed=True).size()
    shares = hits.div(total_articles, axis=0).fillna(0.0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    return shares


# ============================================================================
# REGIONAL FRAMING GAP — does the US, EU and UK frame GenAI governance
# differently, and does the gap move around the (EU-heavy) milestones?
# ============================================================================

def _bucket_period(months: pd.Series, freq: str) -> pd.Series:
    """Map a Series of monthly Periods (or strings) onto coarser Periods.

    freq is a pandas offset alias: 'M' (month), 'Q' (quarter), 'Y'/'A' (year).
    Quarterly is the sensible default for regional splits, since per-region
    monthly counts get thin and noisy once the corpus is divided three ways.
    """
    if len(months) and not isinstance(months.iloc[0], pd.Period):
        months = months.astype(str).apply(lambda x: pd.Period(x, freq="M"))
    if freq.upper().startswith("M"):
        return months
    return months.apply(lambda p: p.asfreq(freq))


def region_frame_shares_over_time(
    df: pd.DataFrame,
    regions: list[str] | None = None,
    freq: str = "Q",
    month_col: str = "month",
    region_col: str = "region",
) -> pd.DataFrame:
    """Frame shares per region per time bucket, in long (tidy) form.

    Within each (region, period) cell, shares sum to 1 across the six frames
    — the same normalisation used by frame_shares()/frame_shares_agg(), so the
    regional series are directly comparable to the pooled Figure 2 series.

    Returns
    -------
    DataFrame with columns: region, period (Period), frame (short name), share.
    """
    regions = regions or ["US", "EU", "UK"]
    present = [c for c in FRAME_COLS if c in df.columns]
    if not present:
        raise ValueError("No frame columns found. Run assign_frame_flags first.")

    subset = df[df[region_col].isin(regions)].copy()
    if subset.empty:
        raise ValueError(f"No rows for regions {regions} in column '{region_col}'.")
    subset["_period"] = _bucket_period(subset[month_col], freq)

    grouped = subset.groupby([region_col, "_period"], observed=True)[present].sum()
    totals = subset.groupby([region_col, "_period"], observed=True).size()
    shares = grouped.div(totals, axis=0).fillna(0.0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]

    long = (
        shares.reset_index()
        .melt(id_vars=[region_col, "_period"], var_name="frame", value_name="share")
        .rename(columns={region_col: "region", "_period": "period"})
    )
    return long.sort_values(["frame", "region", "period"]).reset_index(drop=True)


def framing_gap(
    df: pd.DataFrame,
    frame: str,
    region_a: str = "US",
    region_b: str = "EU",
    freq: str = "Q",
    month_col: str = "month",
    region_col: str = "region",
) -> pd.Series:
    """Time series of (region_a share − region_b share) for one frame.

    Positive values mean region_a leans into the frame more than region_b in
    that period (e.g. a positive 'regulation_governance' US−EU gap would mean
    US coverage was *more* regulation-framed than EU coverage).

    Returns a Series indexed by Period, named '<region_a>_minus_<region_b>'.
    """
    panel = region_frame_shares_over_time(
        df, regions=[region_a, region_b], freq=freq,
        month_col=month_col, region_col=region_col,
    )
    sub = panel[panel["frame"] == frame]
    if sub.empty:
        raise ValueError(
            f"Unknown frame '{frame}'. Expected one of {sorted(panel['frame'].unique())}."
        )
    wide = sub.pivot(index="period", columns="region", values="share")
    for r in (region_a, region_b):
        if r not in wide.columns:
            wide[r] = 0.0
    return (wide[region_a] - wide[region_b]).rename(f"{region_a}_minus_{region_b}").sort_index()


def regional_gap_summary(
    df: pd.DataFrame,
    regions: list[str] | None = None,
    region_col: str = "region",
) -> pd.DataFrame:
    """Pooled (whole-corpus) frame share per region plus pairwise gaps.

    Returns a DataFrame indexed by frame, with one column per region holding
    its overall frame share, and one 'gap_<a>_<b>' column per region pair
    holding the share difference (region_a − region_b).
    """
    regions = regions or ["US", "EU", "UK"]
    shares = region_comparison(df, region_col=region_col, regions=regions).T
    out = shares.copy()
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            a, b = regions[i], regions[j]
            if a in shares.columns and b in shares.columns:
                out[f"gap_{a}_{b}"] = shares[a] - shares[b]
    return out


# ============================================================================
# ADDITIONAL ANALYSES — supplementary statistics and plots
# ============================================================================

def tone_over_time(df: pd.DataFrame, month_col: str = "month") -> pd.Series:
    """Return mean tone score per month from a per-article DataFrame.

    Requires 'tone' column (output of parse_tone).
    Returns a Series indexed by Period[M].
    """
    if "tone" not in df.columns:
        raise ValueError("'tone' column not found. Run parse_tone first.")
    return df.groupby(month_col)["tone"].mean().sort_index()


def tone_by_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Mean, std, and count of tone score per dominant frame.

    Requires 'tone' (parse_tone) and 'dominant_frame' (assign_dominant_frame).
    Returns a DataFrame indexed by frame name with columns: mean, std, count.
    """
    if "tone" not in df.columns:
        raise ValueError("'tone' column not found. Run parse_tone first.")
    if "dominant_frame" not in df.columns:
        raise ValueError("'dominant_frame' column not found. Run assign_dominant_frame first.")
    return (
        df.dropna(subset=["dominant_frame"])
        .groupby("dominant_frame")["tone"]
        .agg(["mean", "std", "count"])
    )


def tone_by_region(
    df: pd.DataFrame,
    region_col: str = "region",
    regions: list[str] | None = None,
) -> pd.DataFrame:
    """Mean, std, and count of tone score per region.

    Requires 'tone' column (output of parse_tone).
    Returns a DataFrame indexed by region with columns: mean, std, count.
    """
    if "tone" not in df.columns:
        raise ValueError("'tone' column not found. Run parse_tone first.")
    regions = regions or ["US", "EU", "UK"]
    return (
        df[df[region_col].isin(regions)]
        .groupby(region_col)["tone"]
        .agg(["mean", "std", "count"])
    )


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
