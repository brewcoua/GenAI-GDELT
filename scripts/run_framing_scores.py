"""
CLI to run ML-based frame scoring on a sample of preprocessed articles.

Usage
-----
    python scripts/run_framing_scores.py --method embedding --n 500
    python scripts/run_framing_scores.py --method nli --n 100
    python scripts/run_framing_scores.py --method both --n 200

Reads from data/interim/gdelt_preprocessed.parquet (output of preprocess_raw.py).
Writes results to data/interim/framing_scores_<method>_<n>.parquet.

The output parquet has the same index as the input sample plus 6 score columns
named after the FRAME_DICTS keys (e.g. innovation_opportunity, risk_safety, …).
Compare these soft scores against the dictionary-based frame_* integer columns
to validate the keyword approach.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

INTERIM = Path(__file__).parent.parent / "data" / "interim"
DEFAULT_INPUT = INTERIM / "gdelt_preprocessed.parquet"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ML-based frame scoring on a sample")
    p.add_argument(
        "--method",
        choices=["embedding", "nli", "both"],
        default="embedding",
        help="Scoring method to use (default: embedding)",
    )
    p.add_argument(
        "--n",
        type=int,
        default=500,
        help="Number of articles to sample (default: 500)",
    )
    p.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to preprocessed parquet (default: data/interim/gdelt_preprocessed.parquet)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Loading {args.input} …")
    df = pd.read_parquet(args.input)

    # Sample — stratify by month if possible to get broad temporal coverage
    n = min(args.n, len(df))
    sample = df.sample(n=n, random_state=args.seed).copy()
    print(f"Sampled {n} articles (seed={args.seed})")

    # Use Quotations as the primary text; fall back to headline_text
    texts = (
        sample["Quotations"].fillna("")
        .where(sample["Quotations"].fillna("") != "", sample.get("headline_text", ""))
        .tolist()
    )

    from src.dictionaries import FRAME_DICTS
    from src.framing_scores import assign_frame_scores_embedding, assign_frame_scores_nli

    results = {}

    if args.method in ("embedding", "both"):
        print("Running embedding scoring …")
        emb_scores = assign_frame_scores_embedding(texts, FRAME_DICTS)
        emb_scores.index = sample.index
        results["embedding"] = emb_scores

    if args.method in ("nli", "both"):
        print("Running NLI scoring (this may take a while on CPU) …")
        nli_scores = assign_frame_scores_nli(texts)
        nli_scores.index = sample.index
        results["nli"] = nli_scores

    for method, scores in results.items():
        out_path = INTERIM / f"framing_scores_{method}_{n}.parquet"
        combined = sample[["month", "DocumentIdentifier"] + [c for c in sample.columns if c.startswith("frame_")]].join(scores, rsuffix=f"_{method}")
        combined.to_parquet(out_path)
        print(f"Saved → {out_path}")


if __name__ == "__main__":
    main()
