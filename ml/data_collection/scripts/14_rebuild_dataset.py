#!/usr/bin/env python3
"""
14_rebuild_dataset.py — Merge all data sources and rebuild the training pipeline.

Combines:
  1. labeled_dataset.csv (real data: OSM, PhonePe, Wikidata, scraped)
  2. synthetic_dataset.csv (original synthetic)
  3. enhanced_synthetic.csv (new enhanced synthetic v2)

Then runs the full feature engineering pipeline:
  - Text normalization
  - Numerical features (16-dim)
  - Label encoding
  - Class weight computation
  - Stratified split (85/10/5)
  - SentencePiece tokenizer training

Usage:
    python 14_rebuild_dataset.py
"""
from __future__ import annotations

import csv
import json
import math
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
LABELED = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "labeled_dataset.csv"
SYNTHETIC = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "synthetic_dataset.csv"
ENHANCED = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "enhanced_synthetic.csv"
OUTPUT_DIR = PROJECT_ROOT / "ml" / "training"

# Output columns
KEEP_COLS = [
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
    text = name.lower().strip()
    text = _CLEAN_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text

# ═══════════════════════════════════════════════════════════════════════════
# NUMERICAL FEATURES (16 dimensions)
# ═══════════════════════════════════════════════════════════════════════════
LAT_MIN, LAT_MAX = 6.0, 37.0
LON_MIN, LON_MAX = 68.0, 97.5

def compute_numerical_features(row: dict[str, str]) -> list[float]:
    features = [0.0] * 16
    features[0] = 0.0     # log(amount + 1)
    features[1] = 5.0     # median bucket
    features[2] = 0.0     # is_round

    hour = random.gauss(14.0, 5.0) % 24
    dow = random.randint(0, 6)
    month = random.randint(1, 12)

    features[3] = math.sin(2 * math.pi * hour / 24)
    features[4] = math.cos(2 * math.pi * hour / 24)
    features[5] = math.sin(2 * math.pi * dow / 7)
    features[6] = math.cos(2 * math.pi * dow / 7)
    features[7] = 1.0 if dow >= 5 else 0.0
    features[8] = 1.0 if (11 <= hour <= 14 or 19 <= hour <= 22) else 0.0
    features[9] = 0.0
    features[10] = math.sin(2 * math.pi * month / 12)
    features[11] = math.cos(2 * math.pi * month / 12)
    features[12] = 0.0

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
# LABEL ENCODING & CLASS WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════

def build_label_encoders(rows):
    l1_codes, l2_codes, l3_codes = set(), set(), set()
    for row in rows:
        l1_codes.add(row["l1_code"])
        l2_codes.add(row["l2_code"])
        l3_codes.add(row["l3_code"])
    return {
        "l1_code": {c: i for i, c in enumerate(sorted(l1_codes))},
        "l2_code": {c: i for i, c in enumerate(sorted(l2_codes))},
        "l3_code": {c: i for i, c in enumerate(sorted(l3_codes))},
    }

def compute_class_weights(rows, encoders):
    weights = {}
    for level in ["l1_code", "l2_code", "l3_code"]:
        counts = Counter(row[level] for row in rows)
        total = sum(counts.values())
        level_weights = {}
        for code in encoders[level]:
            freq = counts.get(code, 1) / total
            level_weights[code] = round(1.0 / math.sqrt(freq), 4)
        mean_w = sum(level_weights.values()) / max(len(level_weights), 1)
        if mean_w > 0:
            level_weights = {k: round(v / mean_w, 4) for k, v in level_weights.items()}
        weights[level] = level_weights
    return weights


# ═══════════════════════════════════════════════════════════════════════════
# STRATIFIED SPLIT
# ═══════════════════════════════════════════════════════════════════════════

def stratified_split(rows, train_ratio=0.85, val_ratio=0.10, seed=42):
    rng = random.Random(seed)
    by_l3 = defaultdict(list)
    for row in rows:
        by_l3[row["l3_code"]].append(row)
    
    train, val, test = [], [], []
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
# SENTENCEPIECE TOKENIZER
# ═══════════════════════════════════════════════════════════════════════════

def train_sentencepiece(texts, output_dir, vocab_size=8192):
    try:
        import sentencepiece as spm
    except ImportError:
        print("  WARNING: sentencepiece not installed")
        return output_dir / "xpenz_bpe.model"

    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = output_dir / "_corpus.txt"
    model_prefix = str(output_dir / "xpenz_bpe")

    with open(corpus_path, "w", encoding="utf-8") as f:
        for text in texts:
            if text.strip():
                f.write(text.strip() + "\n")

    print(f"  Training SentencePiece BPE (vocab={vocab_size}, corpus={len(texts):,}) ...")
    spm.SentencePieceTrainer.train(
        input=str(corpus_path),
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        model_type="bpe",
        character_coverage=0.9995,
        pad_id=0, unk_id=1, bos_id=2, eos_id=3,
        user_defined_symbols=["<sep>"],
        num_threads=4,
        max_sentence_length=256,
        shuffle_input_sentence=True,
    )
    corpus_path.unlink(missing_ok=True)
    return output_dir / "xpenz_bpe.model"


# ═══════════════════════════════════════════════════════════════════════════
# CSV HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def save_csv(rows, path, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    random.seed(42)
    
    print("=" * 60)
    print("DATASET REBUILD PIPELINE (v2 with Enhanced Data)")
    print("=" * 60)

    # Load all data sources
    print("\n[1/8] Loading data sources...")
    labeled = load_csv(LABELED)
    print(f"  Labeled:          {len(labeled):>8,} records")
    
    synthetic = load_csv(SYNTHETIC) if SYNTHETIC.exists() else []
    print(f"  Synthetic:        {len(synthetic):>8,} records")
    
    enhanced = load_csv(ENHANCED) if ENHANCED.exists() else []
    print(f"  Enhanced v2:      {len(enhanced):>8,} records")

    # Merge all sources
    print("\n[2/8] Merging datasets...")
    combined = labeled + synthetic + enhanced
    print(f"  Raw combined:     {len(combined):>8,} records")

    # Deduplicate by (text_normalized, l3_code)
    print("\n[3/8] Deduplicating...")
    seen = set()
    deduped = []
    for row in combined:
        norm = normalize_merchant(row.get("name", ""))
        key = (norm, row.get("l3_code", ""))
        if key not in seen and norm:
            seen.add(key)
            deduped.append(row)
    combined = deduped
    print(f"  After dedup:      {len(combined):>8,} records")

    # Count L3 distribution
    l3_counts = Counter(r["l3_code"] for r in combined)
    print(f"  L3 categories:    {len(l3_counts):>8}")
    vals = sorted(l3_counts.values())
    print(f"  Min/Med/Max:      {vals[0]}/{vals[len(vals)//2]}/{vals[-1]}")

    # Normalize and add features
    print("\n[4/8] Normalizing merchant names...")
    for row in combined:
        row["text_normalized"] = normalize_merchant(row.get("name", ""))

    print("[5/8] Computing numerical features (16-dim)...")
    t0 = time.time()
    for row in combined:
        features = compute_numerical_features(row)
        row["num_features"] = json.dumps(features)
    print(f"  Done in {time.time()-t0:.1f}s")

    # Label encoding
    print("\n[6/8] Building label encoders...")
    encoders = build_label_encoders(combined)
    for level, enc in encoders.items():
        print(f"  {level}: {len(enc)} classes")
    
    for row in combined:
        row["l1_label"] = str(encoders["l1_code"].get(row["l1_code"], 0))
        row["l2_label"] = str(encoders["l2_code"].get(row["l2_code"], 0))
        row["l3_label"] = str(encoders["l3_code"].get(row["l3_code"], 0))

    # Class weights
    class_weights = compute_class_weights(combined, encoders)
    weights_path = OUTPUT_DIR / "class_weights.json"
    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(class_weights, f, indent=2)
    
    # Save encoders
    encoders_path = OUTPUT_DIR / "label_encoders.json"
    reverse_encoders = {}
    for level, enc in encoders.items():
        reverse_encoders[level] = {v: k for k, v in enc.items()}
    save_data = {
        "encoders": encoders,
        "decoders": {k: {str(kk): vv for kk, vv in v.items()} for k, v in reverse_encoders.items()},
    }
    with open(encoders_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    # Stratified split
    print("\n[7/8] Stratified split (85/10/5)...")
    train_rows, val_rows, test_rows = stratified_split(combined)
    print(f"  Train:   {len(train_rows):>8,}")
    print(f"  Val:     {len(val_rows):>8,}")
    print(f"  Test:    {len(test_rows):>8,}")

    # Verify coverage
    train_l3 = set(r["l3_code"] for r in train_rows)
    print(f"  L3 in train: {len(train_l3)}/{len(l3_counts)}")

    # Save
    output_fields = KEEP_COLS + ["text_normalized", "num_features", "l1_label", "l2_label", "l3_label"]
    
    def filter_row(row):
        return {k: row.get(k, "") for k in output_fields}

    print("\n[8/8] Saving datasets...")
    save_csv([filter_row(r) for r in combined], OUTPUT_DIR / "combined_dataset.csv", output_fields)
    save_csv([filter_row(r) for r in train_rows], OUTPUT_DIR / "train.csv", output_fields)
    save_csv([filter_row(r) for r in val_rows], OUTPUT_DIR / "val.csv", output_fields)
    save_csv([filter_row(r) for r in test_rows], OUTPUT_DIR / "test.csv", output_fields)

    for name, path_name in [("Combined", "combined_dataset.csv"), ("Train", "train.csv"),
                            ("Val", "val.csv"), ("Test", "test.csv")]:
        p = OUTPUT_DIR / path_name
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"  {name:10s}: {size_mb:.1f} MB")

    # Retrain tokenizer on enriched data
    print("\nTraining SentencePiece tokenizer on enriched dataset...")
    train_texts = [r.get("text_normalized", "") for r in train_rows if r.get("text_normalized")]
    tokenizer_dir = OUTPUT_DIR / "tokenizer"
    train_sentencepiece(train_texts, tokenizer_dir, vocab_size=8192)

    # Save stats
    stats = {
        "total_combined": len(combined),
        "labeled_records": len(labeled),
        "synthetic_records": len(synthetic),
        "enhanced_records": len(enhanced),
        "train_size": len(train_rows),
        "val_size": len(val_rows),
        "test_size": len(test_rows),
        "l1_classes": len(encoders["l1_code"]),
        "l2_classes": len(encoders["l2_code"]),
        "l3_classes": len(encoders["l3_code"]),
        "l3_min_count": vals[0],
        "l3_median_count": vals[len(vals) // 2],
        "l3_max_count": vals[-1],
    }
    with open(OUTPUT_DIR / "split_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'='*60}")
    print(f"DATASET REBUILD COMPLETE!")
    print(f"Total: {len(combined):,} records | Train: {len(train_rows):,} | Val: {len(val_rows):,} | Test: {len(test_rows):,}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
