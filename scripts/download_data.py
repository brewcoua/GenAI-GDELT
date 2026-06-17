"""
Download large data files from Google Drive into their expected locations.

Files in data/raw/ and data/processed/ml_frame_scores_embedding_full.parquet are
excluded from git due to size; this script fetches them so the pipeline can run.

Usage:
    python scripts/download_data.py                    # download all missing files
    python scripts/download_data.py --force            # re-download even if present
    python scripts/download_data.py gdelt_genai_gov.csv monthly_genai_total.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import gdown

ROOT = Path(__file__).resolve().parents[1]

# Edit the "id" values below with the Google Drive file IDs for each file.
# The ID is the long alphanumeric string in the sharing URL:
#   https://drive.google.com/file/d/<FILE_ID>/view
MANIFEST: dict[str, dict[str, str]] = {
    "data/raw/gdelt_genai_gov.csv": {
        "id": "TODO_GDRIVE_ID",
        "description": "Main GDELT corpus (~4.7 GB)",
    },
    "data/raw/monthly_genai_total.csv": {
        "id": "1X-iVbqqzwwtheWSBhXajRYF8rnKMmoiE",
        "description": "Monthly generative-AI article totals (~4 KB)",
    },
    "data/processed/ml_frame_scores_embedding_full.parquet": {
        "id": "1CZswBXRDmM6N2zUAKt1QRKZrARiQrRSj",
        "description": "Full ML embeddings + frame scores (~117 MB)",
    },
}


def _fmt_size(path: Path) -> str:
    mb = path.stat().st_size / 1_048_576
    return f"{mb:.1f} MB" if mb >= 1 else f"{path.stat().st_size / 1024:.1f} KB"


def download_file(rel_path: str, entry: dict[str, str], force: bool) -> bool:
    dest = ROOT / rel_path
    file_id = entry["id"]

    if file_id.startswith("TODO"):
        print(f"  SKIP  {rel_path}  (Google Drive ID not set — edit MANIFEST in this script)")
        return True

    if dest.exists() and not force:
        print(f"  skip  {rel_path}  (already exists, {_fmt_size(dest)} — use --force to re-download)")
        return True

    print(f"  {rel_path}  —  {entry['description']}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = gdown.download(id=file_id, output=str(dest), fuzzy=False, quiet=False)
        if result is None:
            print(f"  ERROR  gdown returned None for {rel_path} — check the file ID and sharing permissions")
            return False
        print(f"  done   {dest}  ({_fmt_size(dest)})")
        return True
    except Exception as exc:
        print(f"  ERROR  {rel_path}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILENAME",
        help="Basenames of files to download (default: all). Example: gdelt_genai_gov.csv",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files that already exist locally.",
    )
    args = parser.parse_args()

    targets: dict[str, dict[str, str]]
    if args.files:
        targets = {}
        for name in args.files:
            matches = {k: v for k, v in MANIFEST.items() if Path(k).name == name}
            if not matches:
                print(f"WARNING: '{name}' not found in MANIFEST — skipping")
            targets.update(matches)
        if not targets:
            sys.exit("No matching files found in MANIFEST.")
    else:
        targets = MANIFEST

    print(f"Downloading {len(targets)} file(s) to {ROOT}/")
    failed = []
    for rel_path, entry in targets.items():
        ok = download_file(rel_path, entry, force=args.force)
        if not ok:
            failed.append(rel_path)

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for f in failed:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nAll done.")


if __name__ == "__main__":
    main()
