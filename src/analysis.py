"""
Core analytical functions for the three research questions.

All functions are pure: they take a preprocessed DataFrame and return
a DataFrame or dict. No I/O or plotting happens here.
"""

from __future__ import annotations

import pandas as pd

from src.dictionaries import FRAME_COLS, MILESTONES

# ---------------------------------------------------------------------------
# RQ1 — Monthly coverage volume
# ---------------------------------------------------------------------------

def monthly_volume(df: pd.DataFrame, month_col: str = "month") -> pd.Series:
    """Count records per month.

    Returns a Series indexed by Period[M], suitable for Figure 1.
    """
    return df.groupby(month_col).size().rename("count").sort_index()


# ---------------------------------------------------------------------------
# RQ2 — Frame distribution over time
# ---------------------------------------------------------------------------

def frame_shares(df: pd.DataFrame, month_col: str = "month") -> pd.DataFrame:
    """Compute monthly proportion of dominant-frame assignments.

    Returns a DataFrame with months as index and one column per frame (proportions).
    """
    present = [c for c in FRAME_COLS if c in df.columns]
    if not present:
        raise ValueError("No frame columns found. Run assign_frame_flags first.")

    monthly_hits = df.groupby(month_col)[present].sum()
    row_totals = monthly_hits.sum(axis=1).replace(0, pd.NA)
    shares = monthly_hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    return shares.sort_index()


# ---------------------------------------------------------------------------
# RQ3 — Event study around major milestones
# ---------------------------------------------------------------------------

def event_study(
    df: pd.DataFrame,
    milestone_name: str,
    window: int = 3,
    month_col: str = "month",
) -> dict[str, pd.DataFrame]:
    """Compute volume and frame shares for each relative month around a milestone.

    Computes the window directly from the 'month' column so that overlapping
    milestone windows do not affect results.

    Parameters
    ----------
    df:
        Preprocessed DataFrame with a 'month' (Period[M]) column.
    milestone_name:
        The 'name' key from MILESTONES (e.g. 'eu_ai_act').
    window:
        Number of months on each side of the event to include.

    Returns
    -------
    dict with keys:
        'volume'  — Series: rel_month → article count
        'shares'  — DataFrame: rel_month × frame proportions
    """
    milestone = next((m for m in MILESTONES if m["name"] == milestone_name), None)
    if milestone is None:
        raise ValueError(f"Unknown milestone: '{milestone_name}'. Check MILESTONES in dictionaries.py.")

    pivot = pd.Period(milestone["date"][:7], freq="M")

    def _months_diff(p: "pd.Period") -> int:
        return (p.year - pivot.year) * 12 + (p.month - pivot.month)

    rel_months: list[int] = []
    for period in df[month_col]:
        try:
            rel_months.append(_months_diff(period))
        except Exception:
            rel_months.append(999)

    df = df.copy()
    df["_rel_month"] = rel_months
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

    return {"volume": volume, "shares": shares}


# ---------------------------------------------------------------------------
# Optional — Regional comparison (Figure 4)
# ---------------------------------------------------------------------------

def region_comparison(
    df: pd.DataFrame,
    region_col: str = "region",
    regions: list[str] | None = None,
) -> pd.DataFrame:
    """Compute frame shares grouped by region.

    Returns a DataFrame with regions as index and frame proportions as columns.
    """
    regions = regions or ["US", "EU", "UK"]
    subset = df[df[region_col].isin(regions)]
    present = [c for c in FRAME_COLS if c in subset.columns]
    hits = subset.groupby(region_col)[present].sum()
    row_totals = hits.sum(axis=1).replace(0, pd.NA)
    shares = hits.div(row_totals, axis=0).fillna(0)
    shares.columns = [c.replace("frame_", "") for c in shares.columns]
    return shares
