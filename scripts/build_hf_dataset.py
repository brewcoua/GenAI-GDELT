"""
Build the HuggingFace-ready dataset files from processed parquets.

Output: data/huggingface/
  articles.parquet        — 1,116,091 rows, keyword flags + embedding scores
  event_studies.parquet   — 22 rows, pre/post frame prevalence per milestone
  aggregates/             — small summary parquets

Run from repo root:
    python scripts/build_hf_dataset.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "data" / "huggingface"
AGG_OUT = OUT / "aggregates"

OUT.mkdir(parents=True, exist_ok=True)
AGG_OUT.mkdir(parents=True, exist_ok=True)


def build_articles() -> None:
    print("Reading ml_frame_scores_embedding_full.parquet …")
    df = pd.read_parquet(PROCESSED / "ml_frame_scores_embedding_full.parquet")
    print(f"  {len(df):,} rows, columns: {list(df.columns)}")

    df = df.rename(columns={
        "DocumentIdentifier": "document_id",
        "dominant_frame": "dominant_frame",
        "frame_innovation_opportunity":      "kw_innovation_opportunity",
        "frame_risk_safety":                 "kw_risk_safety",
        "frame_regulation_governance":       "kw_regulation_governance",
        "frame_rights_privacy":              "kw_rights_privacy",
        "frame_economic_competition_labour": "kw_economic_competition_labour",
        "frame_misinformation_integrity":    "kw_misinformation_integrity",
        "innovation_opportunity":            "emb_innovation_opportunity",
        "risk_safety":                       "emb_risk_safety",
        "regulation_governance":             "emb_regulation_governance",
        "rights_privacy":                    "emb_rights_privacy",
        "economic_competition_labour":       "emb_economic_competition_labour",
        "misinformation_integrity":          "emb_misinformation_integrity",
    })

    # Period[M] is not supported by HuggingFace — convert to YYYY-MM string
    df["month"] = df["month"].dt.strftime("%Y-%m")

    # Downcast binary flags to int8 to save space
    kw_cols = [c for c in df.columns if c.startswith("kw_")]
    df[kw_cols] = df[kw_cols].astype("int8")

    # Reorder columns for readability
    col_order = (
        ["document_id", "month", "region", "dominant_frame"]
        + kw_cols
        + [c for c in df.columns if c.startswith("emb_")]
    )
    df = df[col_order]

    out_path = OUT / "articles.parquet"
    print(f"  Saving → {out_path}")
    df.to_parquet(out_path, index=False, compression="zstd")
    size_mb = out_path.stat().st_size / 1e6
    print(f"  Done. {size_mb:.1f} MB")


def build_event_studies() -> None:
    print("Building event_studies.parquet …")
    df = pd.read_parquet(PROCESSED / "event_studies_confirmed.parquet")
    df = df.rename(columns={
        "frame_regulation_governance":       "reg_governance",
        "frame_risk_safety":                 "risk_safety",
        "frame_innovation_opportunity":      "innovation_opportunity",
        "frame_economic_competition_labour": "economic_competition_labour",
        "frame_rights_privacy":              "rights_privacy",
        "frame_misinformation_integrity":    "misinformation_integrity",
    })
    out_path = OUT / "event_studies.parquet"
    df.to_parquet(out_path, index=False, compression="zstd")
    print(f"  Saved {len(df)} rows → {out_path}")


def build_aggregates() -> None:
    aggregate_files = [
        "monthly_volume.parquet",
        "monthly_frames.parquet",
        "regional_frames.parquet",
        "regional_frames_quarterly.parquet",
        "tone_monthly.parquet",
        "tone_by_frame.parquet",
        "tone_by_region.parquet",
    ]
    print("Copying aggregate files …")
    for fname in aggregate_files:
        src = PROCESSED / fname
        if src.exists():
            shutil.copy2(src, AGG_OUT / fname)
            print(f"  {fname}")
        else:
            print(f"  SKIP (not found): {fname}")


if __name__ == "__main__":
    build_articles()
    build_event_studies()
    build_aggregates()
    print("\nAll done. Files in data/huggingface/")
    print("Next: run scripts/upload_hf_dataset.py (requires HF token)")
