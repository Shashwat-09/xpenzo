"""
data_loader.py — Mixed HF + synthetic data loader for Xpenzo CHT training.

The mitulshah/transaction-categorization dataset (4.5M rows) gives us strong L1
supervision but no L2/L3 labels (it only has 10 broad categories). The synthetic
generator gives us the full L1 -> L2 -> L3 hierarchy but limited merchant variety.

Strategy: train on a mix.
  - HF rows: supervise L1 only; L2/L3 losses masked out per-sample.
  - Synthetic rows: supervise all three levels.
  - Both: numerical features synthesized when amount/timestamp absent.

Output is a (train_df, val_df) pair with columns:
  merchant_name, upi_id, amount, timestamp,
  l1_label, l2_label, l3_label,
  has_l2_l3   (bool — masks the L2/L3 loss for HF rows)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


# Mapping from HF dataset's 10 categories to Xpenzo's L1 labels.
# Both sides must match the actual strings used in the respective sources.
# "Income" is dropped — Xpenzo tracks expenses only.
HF_TO_L1 = {
    "Food & Dining": "Food & Dining",
    "Transportation": "Transport",
    "Shopping & Retail": "Shopping",
    "Entertainment & Recreation": "Entertainment",
    "Healthcare & Medical": "Healthcare",
    "Utilities & Services": "Bills & Utilities",
    "Financial Services": "Finance",
    "Government & Legal": "Others",
    "Charity & Donations": "Social",
}


@dataclass
class LoaderConfig:
    hf_parquet_path: Path = Path("data/hf_transaction_categorization/default/train/0000.parquet")
    synthetic_train_csv: Path = Path("data/train.csv")
    synthetic_val_csv: Path | None = Path("data/val.csv")
    # Mixing ratios. With 4.5M HF + 200K synthetic, downsample HF to keep
    # L2/L3 supervision from being completely drowned.
    max_hf_rows: int = 800_000
    val_fraction_from_hf: float = 0.05
    # India-only filter — the dataset is multi-country; we only ship to Indian users.
    india_only: bool = True
    seed: int = 42
    augment_prob: float = 0.15


def _parse_hf_parquet(path: Path, cfg: LoaderConfig) -> pd.DataFrame:
    """Load HF parquet, filter to India, map categories to L1."""
    if not path.exists():
        raise FileNotFoundError(
            f"HF parquet not found at {path}. "
            f"Run `python ml/download_hf_resources.py` first."
        )

    df = pd.read_parquet(path)
    if cfg.india_only and "country" in df.columns:
        df = df[df["country"].str.upper() == "INDIA"].copy()

    df = df[df["category"].isin(HF_TO_L1.keys())].copy()
    df["l1_label"] = df["category"].map(HF_TO_L1)
    df = df.dropna(subset=["transaction_description", "l1_label"])

    if len(df) > cfg.max_hf_rows:
        df = df.sample(n=cfg.max_hf_rows, random_state=cfg.seed)

    return df


def _split_description(description: str, rng: random.Random) -> tuple[str, str]:
    """
    HF dataset only has `transaction_description` as a single string.
    Synthesize a plausible (merchant_name, upi_id) split.

    UPI IDs are typically `<merchant_slug>@<bank_or_psp>`. We fabricate one
    from the merchant name so the model sees the same input shape as production.
    """
    desc = str(description).strip()
    # Strip trailing transaction-ref tokens (e.g. "McDonald's #1234")
    merchant = desc.split("#")[0].strip().rstrip("-_ ")
    slug = "".join(c for c in merchant.lower() if c.isalnum() or c == " ").strip()
    slug = slug.replace(" ", "")[:18] or "merchant"
    psp = rng.choice(["paytm", "okhdfcbank", "ybl", "okicici", "axisb", "ibl", "upi"])
    upi_id = f"{slug}@{psp}"
    return merchant, upi_id


def _synth_amount_timestamp(rng: random.Random) -> tuple[float, str]:
    """Sample amount and timestamp for HF rows where they're absent."""
    # Log-normal-ish amount distribution centered around small daily spends.
    amount = round(float(np.exp(rng.gauss(5.0, 1.2))), 2)
    amount = min(amount, 50_000.0)
    days_ago = rng.randint(0, 180)
    hours = rng.randint(6, 23)
    minutes = rng.randint(0, 59)
    dt = datetime.now() - timedelta(days=days_ago, hours=-hours, minutes=-minutes)
    return amount, dt.strftime("%Y-%m-%d %H:%M:%S")


def _normalize_hf_frame(df: pd.DataFrame, cfg: LoaderConfig) -> pd.DataFrame:
    """Bring HF rows to Xpenzo's canonical training schema."""
    rng = random.Random(cfg.seed)
    rows = []
    for _, row in df.iterrows():
        merchant, upi = _split_description(row["transaction_description"], rng)
        amount, ts = _synth_amount_timestamp(rng)
        rows.append({
            "merchant_name": merchant,
            "upi_id": upi,
            "amount": amount,
            "timestamp": ts,
            "l1_label": row["l1_label"],
            "l2_label": "",          # unknown — masked at loss time
            "l3_label": "",
            "has_l2_l3": False,
        })
    return pd.DataFrame(rows)


def _normalize_synth_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Synthetic CSVs already have the full schema; just add the mask column."""
    df = df.copy()
    df["has_l2_l3"] = True
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Lightweight augmentation for Indian merchant names.
# Real SMS sees enormous spelling variance — these tiny perturbations help the
# model become robust to it without needing a heavyweight library.
# ──────────────────────────────────────────────────────────────────────────────

_TRANSLIT_PAIRS = [
    ("z", "j"), ("j", "z"),    # Hindi-English: zomato/jomato, jio/zio
    ("v", "w"), ("w", "v"),
    ("ph", "f"), ("f", "ph"),  # phlipkart/flipkart
    ("ee", "i"), ("oo", "u"),
    ("c", "k"), ("k", "c"),
    ("y", "i"), ("i", "y"),
]

def _augment_merchant(name: str, rng: random.Random, prob: float) -> str:
    if not name or rng.random() > prob:
        return name
    op = rng.choice(["transliterate", "drop_space", "double_letter", "drop_char"])
    s = name
    if op == "transliterate":
        old, new = rng.choice(_TRANSLIT_PAIRS)
        idx = s.lower().find(old)
        if idx >= 0:
            s = s[:idx] + new + s[idx + len(old):]
    elif op == "drop_space" and " " in s:
        idx = s.index(" ")
        s = s[:idx] + s[idx + 1:]
    elif op == "double_letter" and len(s) > 2:
        idx = rng.randint(1, len(s) - 2)
        if s[idx].isalpha():
            s = s[:idx] + s[idx] + s[idx:]
    elif op == "drop_char" and len(s) > 4:
        idx = rng.randint(1, len(s) - 2)
        s = s[:idx] + s[idx + 1:]
    return s


def apply_augmentation(df: pd.DataFrame, cfg: LoaderConfig) -> pd.DataFrame:
    """In-place merchant-name perturbation. Cheap, applied at load time."""
    rng = random.Random(cfg.seed + 1)
    df = df.copy()
    df["merchant_name"] = df["merchant_name"].apply(
        lambda n: _augment_merchant(str(n), rng, cfg.augment_prob)
    )
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def load_mixed(cfg: LoaderConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (train_df, val_df), each with columns:
        merchant_name, upi_id, amount, timestamp,
        l1_label, l2_label, l3_label, has_l2_l3
    """
    cfg = cfg or LoaderConfig()

    print(f"[data_loader] Loading HF parquet from {cfg.hf_parquet_path}...")
    hf_raw = _parse_hf_parquet(cfg.hf_parquet_path, cfg)
    print(f"[data_loader]   {len(hf_raw):,} HF rows after India + category filter")
    hf_norm = _normalize_hf_frame(hf_raw, cfg)

    print(f"[data_loader] Loading synthetic CSV from {cfg.synthetic_train_csv}...")
    if not cfg.synthetic_train_csv.exists():
        raise FileNotFoundError(
            f"Synthetic training CSV not found at {cfg.synthetic_train_csv}. "
            f"Run `python ml/generate_data.py --output {cfg.synthetic_train_csv} --n_samples 200000` first."
        )
    synth_train = _normalize_synth_frame(pd.read_csv(cfg.synthetic_train_csv))
    print(f"[data_loader]   {len(synth_train):,} synthetic train rows")

    # Carve a small val slice out of HF for diversity, combined with synthetic val.
    val_n = int(len(hf_norm) * cfg.val_fraction_from_hf)
    hf_val = hf_norm.iloc[:val_n].reset_index(drop=True)
    hf_train = hf_norm.iloc[val_n:].reset_index(drop=True)

    train = pd.concat([hf_train, synth_train], ignore_index=True)
    train = train.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)
    train = apply_augmentation(train, cfg)

    if cfg.synthetic_val_csv and cfg.synthetic_val_csv.exists():
        synth_val = _normalize_synth_frame(pd.read_csv(cfg.synthetic_val_csv))
        val = pd.concat([hf_val, synth_val], ignore_index=True)
    else:
        val = hf_val

    val = val.reset_index(drop=True)

    l1_counts = train["l1_label"].value_counts()
    print(f"[data_loader] Train: {len(train):,} rows ({train['has_l2_l3'].sum():,} with L2/L3)")
    print(f"[data_loader] Val:   {len(val):,} rows ({val['has_l2_l3'].sum():,} with L2/L3)")
    print(f"[data_loader] L1 distribution (top 5): {dict(l1_counts.head().items())}")
    return train, val


def load_synthetic_only(cfg: LoaderConfig | None = None) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Fallback path when the HF dataset isn't available locally."""
    cfg = cfg or LoaderConfig()
    train = _normalize_synth_frame(pd.read_csv(cfg.synthetic_train_csv))
    val = _normalize_synth_frame(pd.read_csv(cfg.synthetic_val_csv)) if cfg.synthetic_val_csv and cfg.synthetic_val_csv.exists() else None
    train = apply_augmentation(train, cfg)
    return train, val
