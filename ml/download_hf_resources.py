"""
download_hf_resources.py — Fetch the HF dataset + teacher model used by Option-A training.

Downloads:
  - mitulshah/transaction-categorization (4.5M-row parquet) → data/hf_transaction_categorization/
  - mitulshah/global-financial-transaction-classifier (teacher) → models/teacher/

Both are public — no token needed. The previous version of this file assumed
gated access and silently failed; that's why neither was actually downloaded.

Usage:
    python ml/download_hf_resources.py                  # download both
    python ml/download_hf_resources.py --skip-teacher   # dataset only
    python ml/download_hf_resources.py --skip-dataset   # teacher only
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import subprocess

from huggingface_hub import snapshot_download


DATASET_REPO = "mitulshah/transaction-categorization"
TEACHER_REPO = "mitulshah/global-financial-transaction-classifier"

DATASET_DIR = Path("data/hf_transaction_categorization")
TEACHER_DIR = Path("models/teacher")


def _exists_and_nonempty(path: Path) -> bool:
    if not path.exists():
        return False
    # README + hidden dirs (.cache, .git) don't count — we want real data/model files.
    for f in path.rglob("*"):
        if not f.is_file():
            continue
        # Skip files inside any hidden directory (e.g. .cache/huggingface/...)
        if any(part.startswith(".") for part in f.parts):
            continue
        if f.name.startswith(".") or f.name == "README.md":
            continue
        return True
    return False


def download_dataset(force: bool = False, token: str | None = None):
    if not force and _exists_and_nonempty(DATASET_DIR):
        print(f"[dataset] Already present at {DATASET_DIR}/ — skipping. Use --force to re-download.")
        return
    print(f"[dataset] Downloading {DATASET_REPO} -> {DATASET_DIR}/")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        local_dir=str(DATASET_DIR),
        local_dir_use_symlinks=False,
        token=token,
    )
    print(f"[dataset] Saved to {path}")

    # Sanity-check the parquet that data_loader.py expects.
    expected = DATASET_DIR / "default" / "train" / "0000.parquet"
    if expected.exists():
        size_mb = expected.stat().st_size / 1024 / 1024
        print(f"[dataset] Found parquet ({size_mb:.1f} MB) at {expected}")
    else:
        print(f"[dataset] WARNING: expected parquet not at {expected}.")
        print(f"[dataset] Directory contents:")
        for f in sorted(DATASET_DIR.rglob("*"))[:20]:
            if f.is_file():
                print(f"    {f}")


def download_teacher(force: bool = False, token: str | None = None):
    if not force and _exists_and_nonempty(TEACHER_DIR):
        print(f"[teacher] Already present at {TEACHER_DIR}/ — skipping. Use --force to re-download.")
        return
    print(f"[teacher] Downloading {TEACHER_REPO} -> {TEACHER_DIR}/")
    TEACHER_DIR.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(
        repo_id=TEACHER_REPO,
        local_dir=str(TEACHER_DIR),
        local_dir_use_symlinks=False,
        token=token,
    )
    print(f"[teacher] Saved to {path}")

    required = ["config.json", "tokenizer_config.json"]
    missing = [r for r in required if not (TEACHER_DIR / r).exists()]
    if missing:
        print(f"[teacher] WARNING: missing expected files: {missing}")


def _get_token() -> str | None:
    """Read token from hf CLI (same one set by `hf auth login`)."""
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["hf", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        line = result.stdout.strip().splitlines()[0] if result.stdout else ""
        if line.startswith("hf_"):
            return line
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Download HF resources for Xpenzo CHT training.")
    parser.add_argument("--skip-dataset", action="store_true", help="Skip the 71MB dataset download.")
    parser.add_argument("--skip-teacher", action="store_true", help="Skip the teacher model download.")
    parser.add_argument("--force", action="store_true", help="Re-download even if files exist.")
    args = parser.parse_args()

    token = _get_token()
    if token:
        print(f"[auth] Using HF token ({token[:8]}...)")
    else:
        print("[auth] No HF token found — gated repos will fail. Run `hf auth login` first.")

    if not args.skip_dataset:
        download_dataset(force=args.force, token=token)
    if not args.skip_teacher:
        download_teacher(force=args.force, token=token)

    print("\nDone. Next:")
    print("  python ml/generate_data.py --output data/train.csv --n_samples 200000")
    print("  python ml/train_cht.py --mode train_tokenizer --data data/train.csv")
    print("  python ml/train_cht.py --mode train_distill   --data data/train.csv --val data/val.csv")
    print("  python ml/train_cht.py --mode export          --checkpoint outputs/cht_best.keras")


if __name__ == "__main__":
    sys.exit(main() or 0)
