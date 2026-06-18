"""Robustness checks for the event study (W1) and the Regulation frame overlap (W3).

W1 — Significance of milestone framing shifts:
    For each milestone we recompute the adaptive symmetric window (mirroring
    notebooks/03_analysis.ipynb cell 11) and test each frame's pre/post prevalence
    delta with a label-permutation test. A placebo test on random non-milestone
    dates gives the chance baseline.

W3 — Regulation-frame circularity:
    The Regulation frame dictionary reuses terms from the corpus governance filter.
    We recompute a "pruned" confirmed Regulation flag with those shared terms removed
    and report how much the frame's prevalence and milestone deltas change.

Run:  python scripts/robustness_checks.py
Outputs numbers to stdout and writes data/processed/event_studies_significance.parquet
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dictionaries import FRAME_DICTS, GKG_TEXT_COLS, MILESTONES  # noqa: E402

INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
LEXICONS = ROOT / "data" / "lexicons"

FRAMES = list(FRAME_DICTS.keys())            # 6 frame names
FRAME_COLS = [f"frame_{f}" for f in FRAMES]
MIN_WINDOW = 5      # days; matches notebook
MAX_WINDOW = 90     # days; matches notebook
N_PERM = 10_000
SEED = 20260618
rng = np.random.default_rng(SEED)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def load_article_level() -> pd.DataFrame:
    """One row per article: date + confirmed binary frame flags (kw>0 & emb>0)."""
    cf = pd.read_parquet(PROCESSED / "ml_frame_confirmed.parquet",
                         columns=["DocumentIdentifier", *FRAME_COLS])
    dates = pd.read_parquet(INTERIM / "gdelt_preprocessed.parquet",
                            columns=["DocumentIdentifier", "DATE"])
    df = cf.merge(dates, on="DocumentIdentifier", how="left")
    df["date"] = pd.to_datetime(df["DATE"]).dt.normalize()
    return df


def adaptive_window(m_date: pd.Timestamp, m_dates, data_start, data_end) -> int:
    idx = m_dates.index(m_date)
    prev_m = m_dates[idx - 1] if idx > 0 else data_start
    next_m = m_dates[idx + 1] if idx < len(m_dates) - 1 else data_end
    pre_days = (m_date - max(prev_m, data_start)).days
    post_days = (min(next_m, data_end) - m_date).days
    return min(pre_days, post_days, MAX_WINDOW)


def permutation_pvalues(pre: np.ndarray, post: np.ndarray) -> np.ndarray:
    """Two-sided p per frame for delta = mean(post) - mean(pre) via label permutation.

    pre/post: (n_pre, k) / (n_post, k) binary arrays. Returns (k,) p-values.
    """
    pooled = np.vstack([pre, post])
    n_pre = pre.shape[0]
    n = pooled.shape[0]
    obs = post.mean(0) - pre.mean(0)
    col_sum = pooled.sum(0)                       # (k,)
    ge = np.zeros(pooled.shape[1])
    for _ in range(N_PERM):
        perm = rng.permutation(n)
        pre_sum = pooled[perm[:n_pre]].sum(0)
        d = (col_sum - pre_sum) / (n - n_pre) - pre_sum / n_pre   # post_mean - pre_mean
        ge += np.abs(d) >= np.abs(obs) - 1e-12
    return (ge + 1) / (N_PERM + 1)                # add-one smoothing


def run_event_significance(df: pd.DataFrame) -> pd.DataFrame:
    m_dates = sorted(pd.Timestamp(m["date"]) for m in MILESTONES)
    data_start, data_end = df["date"].min(), df["date"].max()
    rows = []
    for m in MILESTONES:
        m_date = pd.Timestamp(m["date"])
        w = adaptive_window(m_date, m_dates, data_start, data_end)
        if w < MIN_WINDOW:
            rows.append({"milestone": m["name"], "window_days": w, "reliable": False})
            continue
        pre = df[(df["date"] >= m_date - pd.Timedelta(days=w)) & (df["date"] < m_date)]
        post = df[(df["date"] > m_date) & (df["date"] <= m_date + pd.Timedelta(days=w))]
        pre_a, post_a = pre[FRAME_COLS].to_numpy(float), post[FRAME_COLS].to_numpy(float)
        delta = (post_a.mean(0) - pre_a.mean(0)) * 100      # percentage points
        pvals = permutation_pvalues(pre_a, post_a)
        row = {"milestone": m["name"], "window_days": w, "reliable": True,
               "n_pre": len(pre), "n_post": len(post)}
        for f, d, p in zip(FRAMES, delta, pvals):
            row[f"d_{f}"] = round(float(d), 2)
            row[f"p_{f}"] = round(float(p), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def run_placebo(df: pd.DataFrame, windows=None, n_draws: int = 400) -> dict:
    """Window-matched placebo: delta distribution at random non-milestone dates.

    For each window length we draw random pivot dates (≥ window away from any real
    milestone) and record the same pre/post delta. Returns the 95% range per window
    for Regulation and Risk, the fair baseline for ordinary temporal variation.
    """
    if windows is None:
        windows = sorted({29, 37, 42, 72, 90})
    m_dates = [pd.Timestamp(m["date"]) for m in MILESTONES]
    keep = ["frame_regulation_governance", "frame_risk_safety"]
    out = {}
    for window in windows:
        lo = df["date"].min() + pd.Timedelta(days=window)
        hi = df["date"].max() - pd.Timedelta(days=window)
        span = (hi - lo).days
        deltas = {k: [] for k in keep}
        draws = 0
        while draws < n_draws:
            piv = lo + pd.Timedelta(days=int(rng.integers(0, span)))
            if any(abs((piv - md).days) < window for md in m_dates):
                continue
            pre = df[(df["date"] >= piv - pd.Timedelta(days=window)) & (df["date"] < piv)]
            post = df[(df["date"] > piv) & (df["date"] <= piv + pd.Timedelta(days=window))]
            if pre.empty or post.empty:
                continue
            for k in keep:
                deltas[k].append((post[k].mean() - pre[k].mean()) * 100)
            draws += 1
        out[window] = {k: (round(float(np.percentile(v, 2.5)), 2),
                           round(float(np.percentile(v, 97.5)), 2)) for k, v in deltas.items()}
    return out


# --------------------------------------------------------------------------- #
# W3 — pruned Regulation frame
# --------------------------------------------------------------------------- #
def pruned_regulation_terms() -> tuple[list[str], list[str]]:
    gov = yaml.safe_load((LEXICONS / "governance.yaml").read_text(encoding="utf-8"))
    gov_flat = {t.lower() for lang in gov["gov_lexicon"].values() for t in lang}
    full = FRAME_DICTS["regulation_governance"]
    kept = [t for t in full if t.lower() not in gov_flat]
    removed = [t for t in full if t.lower() in gov_flat]
    return kept, removed


def count_hits(text: pd.Series, keywords: list[str]) -> np.ndarray:
    pattern = "|".join(
        (r"\b" + re.escape(kw) + r"\b") if " " not in kw else re.escape(kw)
        for kw in keywords
    )
    return text.str.count(pattern).to_numpy()


def run_w3() -> dict:
    kept, removed = pruned_regulation_terms()
    raw = pd.read_parquet(INTERIM / "gdelt_preprocessed.parquet",
                          columns=["DocumentIdentifier", "DATE", *GKG_TEXT_COLS])
    emb = pd.read_parquet(INTERIM / "full_embedding_data.parquet",
                          columns=["regulation_governance"])["regulation_governance"].to_numpy()
    cf = pd.read_parquet(PROCESSED / "ml_frame_confirmed.parquet",
                         columns=["DocumentIdentifier", *FRAME_COLS])
    assert (raw["DocumentIdentifier"].values == cf["DocumentIdentifier"].values).all()

    combined = raw[GKG_TEXT_COLS].fillna("").apply(lambda r: " ".join(r), axis=1)
    kw_pruned = count_hits(combined, kept)
    confirmed_pruned = ((kw_pruned > 0) & (emb > 0)).astype(int)

    n = len(cf)
    orig = cf["frame_regulation_governance"].to_numpy()
    res = {
        "n_terms_full": len(FRAME_DICTS["regulation_governance"]),
        "n_terms_removed": len(removed),
        "n_terms_kept": len(kept),
        "orig_pct": round(orig.sum() / n * 100, 2),
        "pruned_pct": round(confirmed_pruned.sum() / n * 100, 2),
        "orig_count": int(orig.sum()),
        "pruned_count": int(confirmed_pruned.sum()),
    }
    # rank vs other frames (by %-corpus)
    other = {f: cf[f"frame_{f}"].sum() / n * 100 for f in FRAMES
             if f != "regulation_governance"}
    other["regulation_governance(pruned)"] = res["pruned_pct"]
    res["rank_among_frames"] = sorted(other.items(), key=lambda x: -x[1])

    # event-study reg deltas: original vs pruned
    dfo = cf[["DocumentIdentifier"]].copy()
    dfo["date"] = pd.to_datetime(raw["DATE"].values).normalize()
    dfo["orig"] = orig
    dfo["pruned"] = confirmed_pruned
    m_dates = sorted(pd.Timestamp(m["date"]) for m in MILESTONES)
    ds, de = dfo["date"].min(), dfo["date"].max()
    diffs = []
    for m in MILESTONES:
        md = pd.Timestamp(m["date"])
        w = adaptive_window(md, m_dates, ds, de)
        if w < MIN_WINDOW:
            continue
        pre = dfo[(dfo["date"] >= md - pd.Timedelta(days=w)) & (dfo["date"] < md)]
        post = dfo[(dfo["date"] > md) & (dfo["date"] <= md + pd.Timedelta(days=w))]
        do = (post["orig"].mean() - pre["orig"].mean()) * 100
        dp = (post["pruned"].mean() - pre["pruned"].mean()) * 100
        diffs.append((m["name"], round(do, 2), round(dp, 2), round(abs(do - dp), 2)))
    res["delta_changes"] = diffs
    res["max_delta_change"] = round(max(d[3] for d in diffs), 2)
    res["removed_terms_en_sample"] = [t for t in removed if t.isascii()][:20]
    return res


# --------------------------------------------------------------------------- #
def main() -> None:
    print("Loading article-level data ...")
    df = load_article_level()
    print(f"  {len(df):,} articles, {df['date'].min().date()} -> {df['date'].max().date()}\n")

    print("=== W1: event-study significance (permutation, N=%d) ===" % N_PERM)
    sig = run_event_significance(df)
    pd.set_option("display.width", 200, "display.max_columns", 40)
    show = ["milestone", "window_days",
            "d_regulation_governance", "p_regulation_governance",
            "d_risk_safety", "p_risk_safety"]
    print(sig[[c for c in show if c in sig.columns]].to_string(index=False))
    sig.to_parquet(PROCESSED / "event_studies_significance.parquet")
    print(f"\nWrote {PROCESSED / 'event_studies_significance.parquet'}")

    print("\n=== W1b: window-matched placebo (random non-milestone dates) ===")
    placebo = run_placebo(df)
    for w, bands in placebo.items():
        r, k = bands["frame_regulation_governance"], bands["frame_risk_safety"]
        print(f"  window={w:3d}d  Reg 95%[{r[0]:+.2f},{r[1]:+.2f}]  "
              f"Risk 95%[{k[0]:+.2f},{k[1]:+.2f}]")

    print("\n=== W3: pruned Regulation frame ===")
    w3 = run_w3()
    print(f"  terms: full={w3['n_terms_full']}, removed={w3['n_terms_removed']}, kept={w3['n_terms_kept']}")
    print(f"  Regulation %-corpus: original {w3['orig_pct']}% ({w3['orig_count']:,}) "
          f"-> pruned {w3['pruned_pct']}% ({w3['pruned_count']:,})")
    print(f"  removed en terms (sample): {w3['removed_terms_en_sample']}")
    print("  rank by %-corpus (with pruned regulation):")
    for name, pct in w3["rank_among_frames"]:
        print(f"     {pct:5.2f}%  {name}")
    print(f"  max |Δ change| across milestones: {w3['max_delta_change']} pp")
    print("  per-milestone reg delta (orig -> pruned, |diff|):")
    for name, do, dp, dd in w3["delta_changes"]:
        print(f"     {name:24s} {do:+6.2f} -> {dp:+6.2f}  (|{dd:.2f}|)")


if __name__ == "__main__":
    main()
