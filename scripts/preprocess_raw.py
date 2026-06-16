"""
Memory-conscious preprocessing of the raw GDELT export into a slim parquet.

The raw CSV (~3.6 GB, ~888k rows) cannot be loaded whole — run_pipeline()
copies the DataFrame at every step and holds the long AllNames/Quotations/
V2Themes text. So we stream it in chunks, run the full pipeline per chunk,
keep only the columns the figures need, dedup once at the end, and write a
compact parquet to data/interim/gdelt_preprocessed.parquet.

Usage:
    .venv/bin/python scripts/preprocess_raw.py [SRC_CSV] [OUT_PARQUET]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.preprocessing import run_pipeline
from src.dictionaries import FRAME_COLS

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "gdelt_genai_gov.csv"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data" / "interim" / "gdelt_preprocessed.parquet"

CHUNK = 100_000
# Slim output: only what the notebook figures consume (drops the big text fields).
KEEP = [
    "month", "year", "region", "country_code", "tone",
    "dominant_frame", "SourceCommonName", "DocumentIdentifier",
] + FRAME_COLS


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Source CSV not found: {SRC}")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading {SRC} in chunks of {CHUNK:,} rows ...", flush=True)
    t0 = time.time()
    parts: list[pd.DataFrame] = []
    total = 0

    reader = pd.read_csv(SRC, chunksize=CHUNK, dtype=str)
    for i, chunk in enumerate(reader):
        proc = run_pipeline(chunk)
        slim = proc[[c for c in KEEP if c in proc.columns]].copy()
        parts.append(slim)
        total += len(chunk)
        print(f"  chunk {i:>3}: {len(chunk):>7,} rows  (cumulative {total:>9,})  "
              f"[{time.time() - t0:6.1f}s]", flush=True)
        del chunk, proc, slim

    print("Concatenating + deduplicating ...", flush=True)
    df = pd.concat(parts, ignore_index=True)
    del parts
    before = len(df)
    df = df.drop_duplicates(subset=["DocumentIdentifier"]).reset_index(drop=True)
    print(f"  dedup on DocumentIdentifier: {before:,} -> {len(df):,}", flush=True)
    df = df.drop(columns=["DocumentIdentifier"])

    for c in ("region", "country_code", "dominant_frame", "SourceCommonName"):
        if c in df.columns:
            df[c] = df[c].astype("category")

    df.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}  shape={df.shape}  ({time.time() - t0:.1f}s total)", flush=True)
    print("\nRegion counts:\n" + df["region"].value_counts(dropna=False).to_string(), flush=True)


if __name__ == "__main__":
    main()
