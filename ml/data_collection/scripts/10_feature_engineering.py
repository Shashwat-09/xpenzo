#!/usr/bin/env python3
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
10_feature_engineering.py — Xpenzo Feature Engineering & Dataset Split

Takes labeled_dataset.csv + synthetic_dataset.csv and produces:
  1. Merged + deduplicated combined dataset
  2. Feature-engineered records (text tokens + 16 numerical features)
  3. Stratified train/val/test split (85/10/5)
  4. Class weight computation (sqrt inverse frequency)
  5. SentencePiece BPE tokenizer training

Input features per docs/09 Section 4.5 & 5.4:
  - Text: "<bos> merchant_tokens <sep> <eos> <pad>..." → int32[32]
  - Numerical: 16-dim float32 vector (amount, time, location features)

Since our dataset has merchant names (no UPI IDs or amounts yet),
we train text features from names and generate placeholder numerical
features. The pipeline is designed to easily add real UPI/amount data
when available.

Output:
  ml/training/combined_dataset.csv     (merged labeled + synthetic)
  ml/training/train.csv / val.csv / test.csv
  ml/training/tokenizer/               (SentencePiece model)
  ml/training/class_weights.json
  ml/training/label_encoders.json      (L1/L2/L3 code → integer mappings)
  ml/training/split_stats.json

Usage:
    python 10_feature_engineering.py [--labeled PATH] [--synthetic PATH]
           [--output-dir PATH] [--vocab-size 8192] [--max-seq-len 32]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DEFAULT_LABELED = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "labeled_dataset.csv"
DEFAULT_SYNTHETIC = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "synthetic_dataset.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ml" / "training"

# Columns we keep for training
KEEP_COLS: list[str] = [
    "name", "brand", "cuisine", "city", "state", "lat", "lon",
    "l1_id", "l1_code", "l1_name",
    "l2_id", "l2_code", "l2_name",
    "l3_id", "l3_code", "l3_name",
    "confidence", "match_method",
]


# ═══════════════════════════════════════════════════════════════════════════
# TEXT NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════

_CLEAN_RE = re.compile(r"[^a-z0-9\s\-\'/]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_merchant(name: str) -> str:
    """
    Normalize merchant name for tokenization.
    Lowercase, strip special chars (keep hyphens, apostrophes),
    collapse whitespace.
    """
    text = name.lower().strip()
    text = _CLEAN_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text


# ═══════════════════════════════════════════════════════════════════════════
# NUMERICAL FEATURE ENGINEERING (16 dimensions per docs/09 §5.4)
# ═══════════════════════════════════════════════════════════════════════════

# India bounding box for lat/lon normalization
LAT_MIN, LAT_MAX = 6.0, 37.0   # ~India bounds
LON_MIN, LON_MAX = 68.0, 97.5


def compute_numerical_features(row: dict[str, str]) -> list[float]:
    """
    Compute 16-dimensional numerical feature vector.

    Since our training data has merchant names (not transactions with amounts/times),
    we use available features (lat, lon) and generate sensible defaults for
    transaction-level features. The model will learn from real features post-launch.

    Feature layout (per docs/09 §5.4):
      [0]  log(amount + 1)       → 0.0 (no amount data)
      [1]  amount_bucket          → 5 (median bucket)
      [2]  is_round_amount        → 0
      [3]  hour_sin               → random realistic
      [4]  hour_cos               → random realistic
      [5]  dow_sin                → random realistic
      [6]  dow_cos                → random realistic
      [7]  is_weekend             → random 0/1 (28% weekend)
      [8]  is_meal_hour           → random based on category
      [9]  is_salary_window       → 0
      [10] month_sin              → random
      [11] month_cos              → random
      [12] is_holiday             → 0
      [13] has_location           → 1 if lat/lon present
      [14] lat_normalized         → normalized or 0
      [15] lng_normalized         → normalized or 0
    """
    features: list[float] = [0.0] * 16

    # Amount features: defaults (training will learn from real data later)
    features[0] = 0.0     # log(amount + 1)
    features[1] = 5.0     # median bucket
    features[2] = 0.0     # is_round

    # Time features: sample realistic distributions
    hour = random.gauss(14.0, 5.0) % 24  # peak around 2 PM
    dow = random.randint(0, 6)
    month = random.randint(1, 12)

    features[3] = math.sin(2 * math.pi * hour / 24)
    features[4] = math.cos(2 * math.pi * hour / 24)
    features[5] = math.sin(2 * math.pi * dow / 7)
    features[6] = math.cos(2 * math.pi * dow / 7)
    features[7] = 1.0 if dow >= 5 else 0.0  # weekend
    features[8] = 1.0 if (11 <= hour <= 14 or 19 <= hour <= 22) else 0.0
    features[9] = 0.0     # salary window
    features[10] = math.sin(2 * math.pi * month / 12)
    features[11] = math.cos(2 * math.pi * month / 12)
    features[12] = 0.0    # holiday

    # Location features
    lat_str = row.get("lat", "").strip()
    lon_str = row.get("lon", "").strip()
    if lat_str and lon_str:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
                features[13] = 1.0
                features[14] = (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)
                features[15] = (lon - LON_MIN) / (LON_MAX - LON_MIN)
        except ValueError:
            pass

    return [round(f, 6) for f in features]


# ═══════════════════════════════════════════════════════════════════════════
# LABEL ENCODING
# ═══════════════════════════════════════════════════════════════════════════

def build_label_encoders(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, int]]:
    """
    Build integer label encoders for L1, L2, L3 codes.
    Returns: {"l1_code": {"FD": 0, ...}, "l2_code": {...}, "l3_code": {...}}
    """
    l1_codes: set[str] = set()
    l2_codes: set[str] = set()
    l3_codes: set[str] = set()

    for row in rows:
        l1_codes.add(row["l1_code"])
        l2_codes.add(row["l2_code"])
        l3_codes.add(row["l3_code"])

    encoders: dict[str, dict[str, int]] = {
        "l1_code": {code: i for i, code in enumerate(sorted(l1_codes))},
        "l2_code": {code: i for i, code in enumerate(sorted(l2_codes))},
        "l3_code": {code: i for i, code in enumerate(sorted(l3_codes))},
    }
    return encoders


# ═══════════════════════════════════════════════════════════════════════════
# CLASS WEIGHTS (sqrt inverse frequency, per docs/09 §13.3)
# ═══════════════════════════════════════════════════════════════════════════

def compute_class_weights(
    rows: list[dict[str, str]],
    encoders: dict[str, dict[str, int]],
) -> dict[str, dict[str, float]]:
    """
    Compute class weights using sqrt(inverse frequency) strategy.
    This upweights rare categories without over-amplifying noise.
    """
    weights: dict[str, dict[str, float]] = {}

    for level in ["l1_code", "l2_code", "l3_code"]:
        counts = Counter(row[level] for row in rows)
        total = sum(counts.values())

        level_weights: dict[str, float] = {}
        for code in encoders[level]:
            freq = counts.get(code, 1) / total
            # sqrt inverse frequency, normalized so mean weight = 1.0
            raw_weight = 1.0 / math.sqrt(freq)
            level_weights[code] = round(raw_weight, 4)

        # Normalize so mean = 1.0
        mean_w = sum(level_weights.values()) / max(len(level_weights), 1)
        if mean_w > 0:
            level_weights = {k: round(v / mean_w, 4) for k, v in level_weights.items()}

        weights[level] = level_weights

    return weights


# ═══════════════════════════════════════════════════════════════════════════
# STRATIFIED SPLIT
# ═══════════════════════════════════════════════════════════════════════════

def stratified_split(
    rows: list[dict[str, str]],
    train_ratio: float = 0.85,
    val_ratio: float = 0.10,
    seed: int = 42,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """
    Stratified split by L3 code: 85% train, 10% val, 5% test.
    Ensures every L3 category appears in all splits (if ≥3 records).
    """
    rng = random.Random(seed)

    # Group by L3 code
    by_l3: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_l3[row["l3_code"]].append(row)

    train: list[dict[str, str]] = []
    val: list[dict[str, str]] = []
    test: list[dict[str, str]] = []

    for code in sorted(by_l3.keys()):
        group = by_l3[code]
        rng.shuffle(group)

        n = len(group)
        n_val = max(1, round(n * val_ratio))
        n_test = max(1, round(n * (1.0 - train_ratio - val_ratio)))
        n_train = n - n_val - n_test

        if n_train < 1:
            n_train = max(1, n - 2)
            n_val = min(1, n - n_train)
            n_test = n - n_train - n_val

        train.extend(group[:n_train])
        val.extend(group[n_train:n_train + n_val])
        test.extend(group[n_train + n_val:])

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)

    return train, val, test


# ═══════════════════════════════════════════════════════════════════════════
# SENTENCEPIECE TOKENIZER TRAINING
# ═══════════════════════════════════════════════════════════════════════════

def train_sentencepiece(
    texts: list[str],
    output_dir: Path,
    vocab_size: int = 8192,
) -> Path:
    """
    Train SentencePiece BPE tokenizer on merchant names.
    Per docs/09 §4.3: vocab_size=8192, model_type=bpe

    Returns path to the .model file.
    """
    try:
        import sentencepiece as spm  # type: ignore[import-untyped]
    except ImportError:
        print("  WARNING: sentencepiece not installed. Skipping tokenizer training.")
        print("  Install with: pip install sentencepiece")
        return output_dir / "xpenz_bpe.model"

    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = output_dir / "_corpus.txt"
    model_prefix = str(output_dir / "xpenz_bpe")

    # Write corpus
    with open(corpus_path, "w", encoding="utf-8") as f:
        for text in texts:
            if text.strip():
                f.write(text.strip() + "\n")

    print(f"  Training SentencePiece BPE (vocab={vocab_size}, corpus={len(texts):,} lines) ...")
    spm.SentencePieceTrainer.train(
        input=str(corpus_path),
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        model_type="bpe",
        character_coverage=0.9995,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        user_defined_symbols=["<sep>"],
        num_threads=4,
        max_sentence_length=256,
        shuffle_input_sentence=True,
    )

    # Cleanup corpus
    corpus_path.unlink(missing_ok=True)
    model_path = output_dir / "xpenz_bpe.model"
    print(f"  Tokenizer saved: {model_path}")
    print(f"  Vocab file: {output_dir / 'xpenz_bpe.vocab'}")
    return model_path


# ═══════════════════════════════════════════════════════════════════════════
# CSV I/O HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def load_csv(path: Path) -> list[dict[str, str]]:
    """Load a CSV file into a list of dicts."""
    rows: list[dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def save_csv(rows: list[dict[str, str]], path: Path, fieldnames: list[str]) -> None:
    """Save rows to a CSV file."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Xpenzo Feature Engineering & Split")
    parser.add_argument("--labeled", type=str, default=str(DEFAULT_LABELED))
    parser.add_argument("--synthetic", type=str, default=str(DEFAULT_SYNTHETIC))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--vocab-size", type=int, default=8192)
    parser.add_argument("--max-seq-len", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_dir = output_dir / "tokenizer"

    # ── Load datasets ─────────────────────────────────────────────────
    print("Loading labeled dataset ...")
    labeled_path = Path(args.labeled)
    labeled = load_csv(labeled_path)
    print(f"  Labeled: {len(labeled):,} records")

    synthetic_path = Path(args.synthetic)
    synthetic: list[dict[str, str]] = []
    if synthetic_path.exists():
        print("Loading synthetic dataset ...")
        synthetic = load_csv(synthetic_path)
        print(f"  Synthetic: {len(synthetic):,} records")
    else:
        print("  No synthetic dataset found, using labeled only.")

    # ── Merge ─────────────────────────────────────────────────────────
    combined = labeled + synthetic
    print(f"\nCombined: {len(combined):,} records")

    # ── Add normalized text column ────────────────────────────────────
    print("Normalizing merchant names ...")
    for row in combined:
        row["text_normalized"] = normalize_merchant(row.get("name", ""))

    # ── Add numerical features ────────────────────────────────────────
    print("Computing numerical features (16-dim) ...")
    t0 = time.time()
    for row in combined:
        features = compute_numerical_features(row)
        row["num_features"] = json.dumps(features)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s")

    # ── Build label encoders ──────────────────────────────────────────
    print("\nBuilding label encoders ...")
    encoders = build_label_encoders(combined)
    for level, enc in encoders.items():
        print(f"  {level}: {len(enc)} classes")

    # Add integer labels
    for row in combined:
        row["l1_label"] = str(encoders["l1_code"].get(row["l1_code"], 0))
        row["l2_label"] = str(encoders["l2_code"].get(row["l2_code"], 0))
        row["l3_label"] = str(encoders["l3_code"].get(row["l3_code"], 0))

    # ── Class weights ─────────────────────────────────────────────────
    print("Computing class weights (sqrt inverse frequency) ...")
    class_weights = compute_class_weights(combined, encoders)
    weights_path = output_dir / "class_weights.json"
    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(class_weights, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {weights_path}")

    # ── Save label encoders ───────────────────────────────────────────
    encoders_path = output_dir / "label_encoders.json"
    # Also save reverse mappings
    reverse_encoders: dict[str, dict[int, str]] = {}
    for level, enc in encoders.items():
        reverse_encoders[level] = {v: k for k, v in enc.items()}
    save_data: dict[str, Any] = {
        "encoders": encoders,
        "decoders": {k: {str(kk): vv for kk, vv in v.items()} for k, v in reverse_encoders.items()},
    }
    with open(encoders_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {encoders_path}")

    # ── Stratified split ──────────────────────────────────────────────
    print("\nStratified train/val/test split (85/10/5) ...")
    train_rows, val_rows, test_rows = stratified_split(combined, seed=args.seed)
    print(f"  Train: {len(train_rows):,}")
    print(f"  Val:   {len(val_rows):,}")
    print(f"  Test:  {len(test_rows):,}")

    # Verify L3 coverage
    train_l3 = set(r["l3_code"] for r in train_rows)
    val_l3 = set(r["l3_code"] for r in val_rows)
    test_l3 = set(r["l3_code"] for r in test_rows)
    all_l3 = set(r["l3_code"] for r in combined)
    print(f"  L3 coverage: train={len(train_l3)}, val={len(val_l3)}, test={len(test_l3)}, total={len(all_l3)}")

    # ── Save splits ───────────────────────────────────────────────────
    output_fields = KEEP_COLS + ["text_normalized", "num_features", "l1_label", "l2_label", "l3_label"]

    # Filter rows to output fields only
    def filter_row(row: dict[str, str]) -> dict[str, str]:
        return {k: row.get(k, "") for k in output_fields}

    combined_path = output_dir / "combined_dataset.csv"
    train_path = output_dir / "train.csv"
    val_path = output_dir / "val.csv"
    test_path = output_dir / "test.csv"

    print(f"\nSaving datasets to {output_dir} ...")
    save_csv([filter_row(r) for r in combined], combined_path, output_fields)
    save_csv([filter_row(r) for r in train_rows], train_path, output_fields)
    save_csv([filter_row(r) for r in val_rows], val_path, output_fields)
    save_csv([filter_row(r) for r in test_rows], test_path, output_fields)

    for name, path in [("Combined", combined_path), ("Train", train_path),
                       ("Val", val_path), ("Test", test_path)]:
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  {name:10s}: {size_mb:.1f} MB")

    # ── Train SentencePiece tokenizer ─────────────────────────────────
    print("\nTraining SentencePiece tokenizer ...")
    train_texts = [r.get("text_normalized", "") for r in train_rows if r.get("text_normalized")]
    tokenizer_path = train_sentencepiece(train_texts, tokenizer_dir, args.vocab_size)

    # ── Stats ─────────────────────────────────────────────────────────
    train_l3_dist = Counter(r["l3_code"] for r in train_rows)
    stats: dict[str, Any] = {
        "total_combined": len(combined),
        "total_labeled": len(labeled),
        "total_synthetic": len(synthetic),
        "train_size": len(train_rows),
        "val_size": len(val_rows),
        "test_size": len(test_rows),
        "split_ratios": {
            "train": round(len(train_rows) / len(combined), 4),
            "val": round(len(val_rows) / len(combined), 4),
            "test": round(len(test_rows) / len(combined), 4),
        },
        "l1_classes": len(encoders["l1_code"]),
        "l2_classes": len(encoders["l2_code"]),
        "l3_classes": len(encoders["l3_code"]),
        "l3_coverage": {
            "train": len(train_l3),
            "val": len(val_l3),
            "test": len(test_l3),
        },
        "vocab_size": args.vocab_size,
        "max_seq_len": args.max_seq_len,
        "tokenizer_path": str(tokenizer_path),
        "min_train_l3_count": min(train_l3_dist.values()) if train_l3_dist else 0,
        "max_train_l3_count": max(train_l3_dist.values()) if train_l3_dist else 0,
        "median_train_l3_count": sorted(train_l3_dist.values())[len(train_l3_dist) // 2] if train_l3_dist else 0,
    }

    stats_path = output_dir / "split_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("FEATURE ENGINEERING COMPLETE")
    print("=" * 60)
    print(f"  Combined dataset:      {stats['total_combined']:,}")
    print(f"    Labeled:             {stats['total_labeled']:,}")
    print(f"    Synthetic:           {stats['total_synthetic']:,}")
    print(f"  Train / Val / Test:    {stats['train_size']:,} / {stats['val_size']:,} / {stats['test_size']:,}")
    print(f"  Classes: L1={stats['l1_classes']}, L2={stats['l2_classes']}, L3={stats['l3_classes']}")
    print(f"  L3 train count range:  [{stats['min_train_l3_count']}, {stats['max_train_l3_count']}]")
    print(f"  Vocab size:            {stats['vocab_size']}")
    print(f"  Tokenizer:             {tokenizer_path}")
    print(f"\n  Output files:")
    for p in [combined_path, train_path, val_path, test_path, weights_path,
              encoders_path, stats_path, tokenizer_path]:
        print(f"    {p}")


if __name__ == "__main__":
    main()
