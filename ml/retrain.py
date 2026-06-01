"""
retrain.py — Incremental fine-tuning pipeline for Xpenzo CHT v5+.

This script runs on a server (Cloud Run or local machine) and:
  1. Monitors Firestore for opted-in correction samples (collection: transaction_corrections)
  2. When enough new samples accumulate (RETRAINING_THRESHOLD), triggers fine-tuning
  3. Fine-tunes from the last checkpoint — NOT from scratch
  4. Exports a new .tflite
  5. Uploads to Firebase Storage and bumps latest.json
  6. Android ModelUpdateManager picks up the new model within 24 h

CANONICAL PIPELINE (must match data_collection/scripts/11_train_cht_model.py):
  Text:     tokenize_text(text_normalized) → <bos> tokens <eos> <pad...>  [no SEP, no upi split]
  Numerics: 16-dim vector per compute_numerical_features() below
  Labels:   integer indices from ml/training/label_encoders.json

Usage:
    # Continuous polling (default Cloud Run mode)
    python ml/retrain.py --mode watch --interval 3600

    # One-shot (download samples and fine-tune immediately)
    python ml/retrain.py --mode once

    # Development: use a local CSV already in training format
    python ml/retrain.py --mode local --data /path/to/samples.csv

Requirements:
    pip install firebase-admin tensorflow sentencepiece pandas tqdm
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf
from tensorflow import keras

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL PATHS  (per CLAUDE.md — do not change these without updating
#                  CHTClassifier.kt and running the parity test)
# ─────────────────────────────────────────────────────────────────────────────

# Paths are relative to the project root (D:/Codify/Xpenzo/)
SP_MODEL_PATH       = "ml/training/tokenizer/xpenz_bpe.model"
LABEL_ENCODERS_PATH = "ml/training/label_encoders.json"
TEST_CSV            = "ml/training/test.csv"
BASE_CHECKPOINT     = "ml/models/v5_round1_3layer/best.keras"
CHECKPOINT_DIR      = "ml/models"          # fine-tuned checkpoints go here
TFLITE_DIR          = "outputs"            # temporary TFLite landing zone
BUNDLED_VERSION     = "5.0"               # version of the assets-bundled model

# Firebase
STORAGE_BUCKET      = "xpenzo-app.appspot.com"
CORRECTIONS_COLL    = "transaction_corrections"  # DataCollectionManager writes here

# Hyperparameters
SEQ_LEN             = 32
NUM_FEATURES        = 16
RETRAINING_THRESHOLD = 500   # minimum new samples before a retrain run
FINE_TUNE_EPOCHS    = 5
FINE_TUNE_LR        = 3e-5   # 10× smaller than initial training LR
BATCH_SIZE          = 128
MIN_ACCURACY_TO_SHIP = 0.60  # don't upload if L3 val accuracy < this


# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL TEXT + FEATURE PIPELINE
# (must stay in sync with 10_feature_engineering.py and 11_train_cht_model.py)
# ─────────────────────────────────────────────────────────────────────────────

def tokenize_text(text: str, sp_model, max_len: int = SEQ_LEN) -> list[int]:
    """
    Canonical tokenizer matching 11_train_cht_model.py::tokenize_text.
    Format: <bos=2> tokens <eos=3> <pad=0>...

    NOTE: this is NOT the merchant+SEP+upi split from the old v3 lineage.
          The canonical v5+ model expects a SINGLE normalized text field.
    """
    BOS_ID, EOS_ID, PAD_ID = 2, 3, 0
    token_ids = sp_model.encode(text, out_type=int)
    sequence = [BOS_ID] + token_ids[: max_len - 2] + [EOS_ID]
    sequence = sequence[:max_len]
    sequence += [PAD_ID] * (max_len - len(sequence))
    return sequence


def compute_numerical_features(
    amount_rupees: float = 0.0,
    timestamp: datetime | None = None,
    has_location: bool = False,
    lat_normalized: float = 0.0,
    lon_normalized: float = 0.0,
) -> list[float]:
    """
    16-dim numerical feature vector matching 10_feature_engineering.py.

    Feature layout (per docs/09 §5.4):
      [0]  log(amount + 1)        — 0.0 when unknown
      [1]  amount_bucket (0–10)   — 5 (median) when unknown
      [2]  is_round_amount        — 0 when unknown
      [3]  hour_sin
      [4]  hour_cos
      [5]  dow_sin
      [6]  dow_cos
      [7]  is_weekend
      [8]  is_meal_hour
      [9]  is_salary_window
      [10] month_sin
      [11] month_cos
      [12] is_holiday              — 0
      [13] has_location
      [14] lat_normalized
      [15] lon_normalized
    """
    if timestamp is None:
        timestamp = datetime.now(tz=timezone.utc)

    hour  = timestamp.hour
    dow   = timestamp.weekday()
    month = timestamp.month
    day   = timestamp.day

    # Amount features
    log_amount  = math.log(amount_rupees + 1.0) if amount_rupees > 0 else 0.0
    if   amount_rupees < 50:     bucket = 0
    elif amount_rupees < 100:    bucket = 1
    elif amount_rupees < 200:    bucket = 2
    elif amount_rupees < 500:    bucket = 3
    elif amount_rupees < 1000:   bucket = 4
    elif amount_rupees < 2000:   bucket = 5
    elif amount_rupees < 5000:   bucket = 6
    elif amount_rupees < 10000:  bucket = 7
    elif amount_rupees < 25000:  bucket = 8
    elif amount_rupees < 50000:  bucket = 9
    else:                        bucket = 10

    is_round = 1.0 if (amount_rupees > 0 and amount_rupees % 10 == 0) else 0.0
    if amount_rupees == 0.0:
        bucket = 5  # canonical default: median bucket, matches training data

    is_weekend      = 1.0 if dow >= 5 else 0.0
    is_meal_hour    = 1.0 if (11 <= hour <= 14 or 19 <= hour <= 22) else 0.0
    is_salary_window = 1.0 if 1 <= day <= 5 else 0.0

    features = [
        log_amount,
        float(bucket),                          # raw bucket (0–10), NOT /10
        is_round,
        math.sin(2 * math.pi * hour / 24),
        math.cos(2 * math.pi * hour / 24),
        math.sin(2 * math.pi * dow / 7),
        math.cos(2 * math.pi * dow / 7),
        is_weekend,
        is_meal_hour,
        is_salary_window,
        math.sin(2 * math.pi * month / 12),
        math.cos(2 * math.pi * month / 12),
        0.0,                                    # is_holiday
        1.0 if has_location else 0.0,           # has_location
        lat_normalized,
        lon_normalized,
    ]
    return [round(f, 6) for f in features]


def bucket_label_to_rupees(bucket: str) -> float:
    """Representative rupee amount for each DataCollectionManager bucket label."""
    return {
        "xs":  30.0,     # < ₹50
        "sm":  100.0,    # ₹50–200
        "md":  300.0,    # ₹200–500
        "lg":  1_000.0,  # ₹500–2,000
        "xl":  5_000.0,  # ₹2,000–10,000
        "xxl": 20_000.0, # ≥ ₹10,000
    }.get(bucket, 300.0)


# ─────────────────────────────────────────────────────────────────────────────
# LABEL ENCODERS  (JSON format — per CLAUDE.md always use .json, not .pkl)
# ─────────────────────────────────────────────────────────────────────────────

def load_label_encoders() -> dict[str, dict[str, int]]:
    """
    Returns {level: {code_string: int_index}} for l1_code, l2_code, l3_code.
    """
    with open(LABEL_ENCODERS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["encoders"]  # keys: "l1_code", "l2_code", "l3_code"


def num_classes(encoders: dict[str, dict[str, int]]) -> tuple[int, int, int]:
    return (
        len(encoders["l1_code"]),
        len(encoders["l2_code"]),
        len(encoders["l3_code"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# FIREBASE
# ─────────────────────────────────────────────────────────────────────────────

def init_firebase():
    import firebase_admin
    from firebase_admin import credentials, firestore, storage as fb_storage

    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"storageBucket": STORAGE_BUCKET})

    return firestore.client(), fb_storage.bucket()


def fetch_new_samples(db, since_date: str | None = None) -> pd.DataFrame:
    """
    Download correction samples from Firestore.
    Returns a DataFrame with columns:
        text_normalized, num_features, l1_label, l2_label, l3_label  (all ints)
    """
    encoders = load_label_encoders()
    print(f"Fetching samples from '{CORRECTIONS_COLL}' (since={since_date or 'all'})...")

    col = db.collection(CORRECTIONS_COLL)
    if since_date:
        col = col.where("timestamp", ">=", since_date)

    rows = []
    for doc in col.stream():
        d = doc.to_dict()

        # Map string codes → int indices (drop unknown codes)
        l1_code = d.get("l1_label", "")
        l2_code = d.get("l2_label", "")
        l3_code = d.get("l3_label", "")

        if l1_code not in encoders["l1_code"]:
            continue  # skip unknown L1 — taxonomy drift
        l1_idx = encoders["l1_code"][l1_code]
        l2_idx = encoders["l2_code"].get(l2_code, 0)
        l3_idx = encoders["l3_code"].get(l3_code, 0)

        # Reconstruct amount from bucket
        amount_rupees = bucket_label_to_rupees(d.get("amount_bucket", "md"))

        # Parse timestamp if present
        ts_str = d.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str)
        except Exception:
            ts = datetime.now(tz=timezone.utc)

        # merchant_norm from Android is already lowercased + digits→#
        # Use it directly as text_normalized — close enough for fine-tuning.
        text = d.get("merchant_norm", "")

        feats = compute_numerical_features(amount_rupees=amount_rupees, timestamp=ts)

        rows.append({
            "text_normalized": text,
            "num_features_raw": feats,
            "l1_label": l1_idx,
            "l2_label": l2_idx,
            "l3_label": l3_idx,
        })

    df = pd.DataFrame(rows)
    print(f"  Fetched {len(df):,} usable correction samples")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FINE-TUNING
# ─────────────────────────────────────────────────────────────────────────────

def fine_tune(df: pd.DataFrame, base_checkpoint: str, new_version: str) -> str:
    """
    Fine-tune the CHT model on new correction samples.
    Returns path to the new Keras checkpoint.
    """
    import sentencepiece as spm

    print(f"\nFine-tuning from:  {base_checkpoint}")
    print(f"New samples:       {len(df):,}")
    print(f"Target version:    v{new_version}")

    encoders = load_label_encoders()
    n1, n2, n3 = num_classes(encoders)
    print(f"Classes: L1={n1} L2={n2} L3={n3}")

    # Load canonical tokenizer
    sp = spm.SentencePieceProcessor()
    sp.load(SP_MODEL_PATH)

    # Preprocess
    n = len(df)
    token_arr = np.zeros((n, SEQ_LEN), dtype=np.int32)
    feat_arr  = np.zeros((n, NUM_FEATURES), dtype=np.float32)
    l1_arr = df["l1_label"].to_numpy(dtype=np.int32)
    l2_arr = df["l2_label"].to_numpy(dtype=np.int32)
    l3_arr = df["l3_label"].to_numpy(dtype=np.int32)

    print("Tokenizing and encoding features...")
    for i, row in df.iterrows():
        token_arr[i] = tokenize_text(row["text_normalized"], sp)
        feats = row["num_features_raw"]
        feat_arr[i, : len(feats)] = feats

    # Build TF dataset
    dataset = tf.data.Dataset.from_tensor_slices((
        {"token_ids": token_arr, "num_features": feat_arr},
        {
            "l1_output": tf.one_hot(l1_arr, depth=n1),
            "l2_output": tf.one_hot(l2_arr, depth=n2),
            "l3_output": tf.one_hot(l3_arr, depth=n3),
        },
    )).shuffle(10_000).batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

    # Load base model (custom layer names from script 11's architecture)
    model = keras.models.load_model(
        base_checkpoint,
        compile=False,
    )

    # Recompile at lower LR with label smoothing (prevents catastrophic forgetting)
    model.compile(
        optimizer=keras.optimizers.Adam(FINE_TUNE_LR, clipnorm=1.0),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
        loss_weights={"l1_output": 0.2, "l2_output": 0.3, "l3_output": 0.5},
        metrics={
            "l1_output": "accuracy",
            "l2_output": "accuracy",
            "l3_output": "accuracy",
        },
    )

    out_dir = Path(CHECKPOINT_DIR) / f"v{new_version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    new_checkpoint = str(out_dir / "best.keras")

    model.fit(
        dataset,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=[
            keras.callbacks.ModelCheckpoint(
                new_checkpoint,
                monitor="val_l3_output_accuracy" if False else "l3_output_accuracy",
                save_best_only=True,
                mode="max",
                verbose=1,
            ),
        ],
    )

    print(f"\nFine-tuned checkpoint → {new_checkpoint}")
    return new_checkpoint


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_on_test_set(checkpoint: str) -> dict[str, float]:
    """
    Evaluate the fine-tuned checkpoint on the canonical held-out test.csv.
    Returns {"l1_acc": ..., "l2_acc": ..., "l3_acc": ...}.
    """
    import sentencepiece as spm
    import ast

    print(f"\nEvaluating {checkpoint} on {TEST_CSV}...")

    sp = spm.SentencePieceProcessor()
    sp.load(SP_MODEL_PATH)

    df = pd.read_csv(TEST_CSV)
    n = len(df)

    token_arr = np.zeros((n, SEQ_LEN), dtype=np.int32)
    feat_arr  = np.zeros((n, NUM_FEATURES), dtype=np.float32)

    for i, row in df.iterrows():
        token_arr[i] = tokenize_text(str(row.get("text_normalized", "")), sp)
        nf = row.get("num_features", "[]")
        feats = ast.literal_eval(nf) if isinstance(nf, str) else nf
        feat_arr[i, : len(feats)] = feats

    l1_true = df["l1_label"].to_numpy(dtype=np.int32)
    l2_true = df["l2_label"].to_numpy(dtype=np.int32)
    l3_true = df["l3_label"].to_numpy(dtype=np.int32)

    model = keras.models.load_model(checkpoint, compile=False)
    preds = model.predict(
        {"token_ids": token_arr, "num_features": feat_arr},
        batch_size=512,
        verbose=0,
    )

    # Output keys depend on the architecture; try both naming conventions
    if isinstance(preds, dict):
        l1_logits = preds.get("l1_output") or preds.get("l1_probs")
        l2_logits = preds.get("l2_output") or preds.get("l2_probs")
        l3_logits = preds.get("l3_output") or preds.get("l3_probs")
    else:
        l1_logits, l2_logits, l3_logits = preds[0], preds[1], preds[2]

    l1_acc = float(np.mean(np.argmax(l1_logits, axis=1) == l1_true))
    l2_acc = float(np.mean(np.argmax(l2_logits, axis=1) == l2_true))
    l3_acc = float(np.mean(np.argmax(l3_logits, axis=1) == l3_true))

    print(f"  L1 acc: {l1_acc:.3f} | L2 acc: {l2_acc:.3f} | L3 acc: {l3_acc:.3f}")
    return {"l1_acc": l1_acc, "l2_acc": l2_acc, "l3_acc": l3_acc}


# ─────────────────────────────────────────────────────────────────────────────
# TFLITE EXPORT + UPLOAD
# ─────────────────────────────────────────────────────────────────────────────

def export_tflite(checkpoint: str, version: str) -> str:
    """Export Keras checkpoint → FP16 TFLite. Returns path to .tflite file."""
    import shutil

    print(f"\nExporting TFLite for v{version}...")
    model = keras.models.load_model(checkpoint, compile=False)

    # Warmup forward pass to materialise all variables
    dummy_tokens = np.zeros((1, SEQ_LEN), dtype=np.int32)
    dummy_feats  = np.zeros((1, NUM_FEATURES), dtype=np.float32)
    _ = model({"token_ids": dummy_tokens, "num_features": dummy_feats}, training=False)

    saved_dir = tempfile.mkdtemp(prefix="cht_export_")
    model.export(saved_dir)

    converter = tf.lite.TFLiteConverter.from_saved_model(saved_dir)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite_bytes = converter.convert()

    shutil.rmtree(saved_dir, ignore_errors=True)

    os.makedirs(TFLITE_DIR, exist_ok=True)
    out_path = os.path.join(TFLITE_DIR, f"xpenz_cht_{version.replace('.', '_')}.tflite")
    with open(out_path, "wb") as f:
        f.write(tflite_bytes)

    size_mb = len(tflite_bytes) / 1_048_576
    print(f"  TFLite → {out_path}  ({size_mb:.2f} MB)")
    if size_mb > 5.0:
        print(f"  WARNING: model {size_mb:.2f} MB exceeds 5 MB budget!")
    return out_path


def upload_to_firebase(tflite_path: str, version: str, bucket, metrics: dict, sample_count: int):
    """
    Upload .tflite to Storage and update latest.json.
    latest.json format matches ModelUpdateManager.kt expectations:
        { "version": "5.1", "path": "models/v5_1/model.tflite", ... }
    """
    v_slug = version.replace(".", "_")
    remote_tflite_path = f"models/v{v_slug}/model.tflite"

    print(f"Uploading → gs://{STORAGE_BUCKET}/{remote_tflite_path}")
    blob = bucket.blob(remote_tflite_path)
    blob.upload_from_filename(tflite_path, content_type="application/octet-stream")
    # NOTE: do NOT make_public() — access via Firebase Storage SDK with Auth

    # Build latest.json — fields consumed by ModelUpdateManager.kt:
    #   getString("version"), getString("path")
    manifest = {
        "version": version,
        "path": remote_tflite_path,       # ← ModelUpdateManager reads this field
        "min_app_version": "1.0",
        "size_bytes": os.path.getsize(tflite_path),
        "l1_acc": round(metrics.get("l1_acc", 0), 4),
        "l2_acc": round(metrics.get("l2_acc", 0), 4),
        "l3_acc": round(metrics.get("l3_acc", 0), 4),
        "trained_on_samples": sample_count,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        "release_notes": (
            f"Auto-retrained on {sample_count} user corrections "
            f"({datetime.now().strftime('%Y-%m-%d')})"
        ),
    }

    manifest_json = json.dumps(manifest, indent=2)
    blob_manifest = bucket.blob("models/latest.json")
    blob_manifest.upload_from_string(manifest_json, content_type="application/json")

    print(f"  latest.json updated: v{version} | "
          f"L3={metrics.get('l3_acc', 0):.1%} | {sample_count:,} samples")
    print(f"  Apps will download the new model in the next 24 h check.")


# ─────────────────────────────────────────────────────────────────────────────
# VERSION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _next_version(state: dict) -> str:
    """Increment minor version from state file. Starts at 5.1 after bundled 5.0."""
    last = state.get("last_version", BUNDLED_VERSION)
    try:
        major, minor = last.split(".")
        return f"{major}.{int(minor) + 1}"
    except Exception:
        return "5.1"


def _find_latest_checkpoint() -> str:
    """Best Keras checkpoint to fine-tune from (newest fine-tuned, else base)."""
    candidates = sorted(Path(CHECKPOINT_DIR).glob("v*/best.keras"))
    if candidates:
        chosen = str(candidates[-1])
        print(f"Resuming from: {chosen}")
        return chosen
    print(f"Starting from base: {BASE_CHECKPOINT}")
    return BASE_CHECKPOINT


def _load_state() -> dict:
    p = "outputs/retrain_state.json"
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"pending_count": 0, "last_timestamp": None, "last_version": BUNDLED_VERSION}


def _save_state(state: dict):
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/retrain_state.json", "w") as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# WATCH MODE
# ─────────────────────────────────────────────────────────────────────────────

def watch_mode(interval_seconds: int):
    db, bucket = init_firebase()
    state = _load_state()
    print(f"Watch mode: polling every {interval_seconds}s | "
          f"threshold={RETRAINING_THRESHOLD} samples")

    while True:
        try:
            df = fetch_new_samples(db, since_date=state.get("last_timestamp"))
            new_count = len(df)
            state["pending_count"] = state.get("pending_count", 0) + new_count

            now_str = datetime.now().strftime("%H:%M:%S")
            print(f"[{now_str}] New: {new_count} | "
                  f"Pending: {state['pending_count']}/{RETRAINING_THRESHOLD}")

            if state["pending_count"] >= RETRAINING_THRESHOLD:
                print(f"\n{'='*60}")
                print(f"THRESHOLD REACHED. Retraining...")
                print(f"{'='*60}\n")
                _run_retrain_cycle(df, bucket, state)

            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
            break
        except Exception as e:
            print(f"Error: {e}. Retrying in 60s...")
            time.sleep(60)


def _run_retrain_cycle(df: pd.DataFrame, bucket, state: dict):
    new_version = _next_version(state)
    base = _find_latest_checkpoint()

    # Fine-tune
    new_checkpoint = fine_tune(df, base, new_version)

    # Evaluate — safety gate before shipping
    metrics = evaluate_on_test_set(new_checkpoint)
    if metrics["l3_acc"] < MIN_ACCURACY_TO_SHIP:
        print(f"L3 accuracy {metrics['l3_acc']:.3f} < {MIN_ACCURACY_TO_SHIP} threshold. "
              f"NOT uploading — check the data quality and retry.")
        return

    # Export + upload
    tflite_path = export_tflite(new_checkpoint, new_version)
    upload_to_firebase(tflite_path, new_version, bucket, metrics, len(df))

    state["pending_count"] = 0
    state["last_timestamp"] = datetime.now().strftime("%Y-%m-%d")
    state["last_version"] = new_version
    _save_state(state)

    print(f"\nDone. v{new_version} shipped.")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Xpenzo CHT Incremental Retraining")
    parser.add_argument(
        "--mode", choices=["once", "watch", "local"], required=True,
        help="once=run immediately, watch=poll continuously, local=use local CSV",
    )
    parser.add_argument("--data", default=None,
                        help="CSV path for local mode (columns: text_normalized, num_features, l1_label..l3_label)")
    parser.add_argument("--interval", type=int, default=3600,
                        help="Polling interval in seconds (watch mode, default 3600)")
    parser.add_argument("--checkpoint", default=None,
                        help="Override base checkpoint path")
    args = parser.parse_args()

    if args.mode == "local":
        assert args.data, "--data is required for local mode"
        df = pd.read_csv(args.data)
        # Expect same format as training CSV (integer labels, num_features as JSON string)
        import ast
        if "num_features" in df.columns and isinstance(df["num_features"].iloc[0], str):
            df["num_features_raw"] = df["num_features"].apply(ast.literal_eval)
        else:
            df["num_features_raw"] = df.apply(
                lambda r: compute_numerical_features(), axis=1
            )
        state  = _load_state()
        version = _next_version(state)
        base   = args.checkpoint or _find_latest_checkpoint()
        ckpt   = fine_tune(df, base, version)
        metrics = evaluate_on_test_set(ckpt)
        print(f"\nLocal fine-tune done → {ckpt}")
        print(f"To export: python ml/retrain.py --mode once --checkpoint {ckpt}")

    elif args.mode == "once":
        db, bucket = init_firebase()
        df = fetch_new_samples(db)
        if len(df) < 50:
            print(f"Only {len(df)} samples (need ≥50). Exiting.")
            return
        state  = _load_state()
        _run_retrain_cycle(df, bucket, state)

    elif args.mode == "watch":
        watch_mode(args.interval)


if __name__ == "__main__":
    main()
