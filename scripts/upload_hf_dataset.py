"""
Upload the prepared HuggingFace dataset files to the Hub.

Prerequisites:
    pip install huggingface_hub
    huggingface-cli login   # or set HF_TOKEN env var

Run from repo root:
    python scripts/upload_hf_dataset.py

The dataset will be published at:
    https://huggingface.co/datasets/brewcoua/genai-gdelt-framing
"""

from __future__ import annotations

import os
from pathlib import Path

HF_REPO = "brewcoua/genai-gdelt-framing"
ROOT = Path(__file__).parent.parent
HF_DIR = ROOT / "data" / "huggingface"


def main() -> None:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise SystemExit("Install huggingface_hub first: pip install huggingface_hub")

    if not HF_DIR.exists():
        raise SystemExit(
            "data/huggingface/ not found — run scripts/build_hf_dataset.py first"
        )

    api = HfApi()

    print(f"Creating (or verifying) dataset repo: {HF_REPO}")
    api.create_repo(
        repo_id=HF_REPO,
        repo_type="dataset",
        exist_ok=True,
        private=False,
    )

    # Upload dataset card first so the repo page looks right immediately
    card_path = HF_DIR / "README.md"
    if card_path.exists():
        print("Uploading dataset card (README.md) …")
        api.upload_file(
            path_or_fileobj=str(card_path),
            path_in_repo="README.md",
            repo_id=HF_REPO,
            repo_type="dataset",
        )

    # Upload main files
    for fpath in sorted(HF_DIR.rglob("*.parquet")):
        rel = fpath.relative_to(HF_DIR)
        print(f"Uploading {rel} ({fpath.stat().st_size / 1e6:.1f} MB) …")
        api.upload_file(
            path_or_fileobj=str(fpath),
            path_in_repo=str(rel),
            repo_id=HF_REPO,
            repo_type="dataset",
        )

    print(f"\nDone! Dataset live at https://huggingface.co/datasets/{HF_REPO}")


if __name__ == "__main__":
    main()
