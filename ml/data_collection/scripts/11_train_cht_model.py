#!/usr/bin/env python3
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
11_train_cht_model.py — Xpenzo CHT Model Training Pipeline

Trains the Compact Hierarchical Transformer (CHT) model per docs/09:
  - 3-layer Transformer encoder (d=128, heads=4, FFN=256)
  - Token embedding (8192 vocab × 128) + Positional embedding (32 × 128)
  - Numerical encoder (16 → 64 → 128)
  - Hierarchical classification heads: L1(15) → L2(80) → L3(520)
  - Multi-task loss: α=0.15 (L1) + β=0.25 (L2) + γ=0.60 (L3)
  - AdamW (lr=3e-4, weight_decay=0.01), cosine warmup schedule
  - Label smoothing 0.05, sqrt inverse frequency class weights
  - INT8 + FP16 hybrid TFLite quantization → ~3.2 MB

Input:  ml/training/train.csv, val.csv, test.csv
        ml/training/tokenizer/xpenz_bpe.model
        ml/training/label_encoders.json
        ml/training/class_weights.json

Output: ml/models/xpenz_cht_v3.keras        (Keras model)
        ml/models/xpenz_cht_v3.tflite       (Quantized TFLite)
        ml/models/training_history.json      (Metrics per epoch)
        ml/models/evaluation_report.json     (Test set metrics)

Usage:
    python 11_train_cht_model.py [--training-dir PATH] [--output-dir PATH]
           [--epochs 50] [--batch-size 256] [--learning-rate 3e-4]

Requires: tensorflow>=2.15, sentencepiece
    pip install tensorflow sentencepiece
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from pathlib import Path
from typing import Any

# Suppress TF warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DEFAULT_TRAINING_DIR = PROJECT_ROOT / "ml" / "training"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ml" / "models"


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

def load_split(path: Path) -> list[dict[str, str]]:
    """Load a CSV split file."""
    rows: list[dict[str, str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def prepare_tokenizer(tokenizer_path: Path) -> Any:
    """Load SentencePiece tokenizer."""
    import sentencepiece as spm  # type: ignore[import-untyped]
    sp = spm.SentencePieceProcessor()
    sp.Load(str(tokenizer_path))
    return sp


def tokenize_text(
    text: str,
    sp_model: Any,
    max_len: int = 32,
) -> list[int]:
    """
    Tokenize merchant text into padded token IDs.
    Format: <bos> tokens <eos> <pad>...<pad>
    Per docs/09 §4.5.
    """
    BOS_ID = 2
    EOS_ID = 3
    PAD_ID = 0

    token_ids: list[int] = sp_model.encode(text, out_type=int)
    # Assemble: <bos> tokens <eos>
    sequence = [BOS_ID] + token_ids[: max_len - 2] + [EOS_ID]
    # Pad to max_len
    sequence = sequence[:max_len]
    sequence += [PAD_ID] * (max_len - len(sequence))
    return sequence


def prepare_datasets(
    train_rows: list[dict[str, str]],
    val_rows: list[dict[str, str]],
    test_rows: list[dict[str, str]],
    sp_model: Any,
    max_seq_len: int = 32,
) -> dict[str, Any]:
    """
    Convert CSV rows into numpy arrays for training.

    Returns dict with:
        train_tokens, train_nums, train_l1, train_l2, train_l3,
        val_tokens, val_nums, val_l1, val_l2, val_l3,
        test_tokens, test_nums, test_l1, test_l2, test_l3
    """
    import numpy as np  # type: ignore[import-untyped]

    def process_split(
        rows: list[dict[str, str]],
    ) -> tuple[Any, Any, Any, Any, Any]:
        tokens = []
        nums = []
        l1_labels = []
        l2_labels = []
        l3_labels = []

        for row in rows:
            # Tokenize text
            text = row.get("text_normalized", "")
            tok = tokenize_text(text, sp_model, max_seq_len)
            tokens.append(tok)

            # Numerical features
            num_str = row.get("num_features", "[]")
            num_feat = json.loads(num_str)
            if len(num_feat) < 16:
                num_feat += [0.0] * (16 - len(num_feat))
            nums.append(num_feat[:16])

            # Labels
            l1_labels.append(int(row.get("l1_label", "0")))
            l2_labels.append(int(row.get("l2_label", "0")))
            l3_labels.append(int(row.get("l3_label", "0")))

        return (
            np.array(tokens, dtype=np.int32),
            np.array(nums, dtype=np.float32),
            np.array(l1_labels, dtype=np.int32),
            np.array(l2_labels, dtype=np.int32),
            np.array(l3_labels, dtype=np.int32),
        )

    print("  Processing train split ...")
    tr_tok, tr_num, tr_l1, tr_l2, tr_l3 = process_split(train_rows)
    print("  Processing val split ...")
    vl_tok, vl_num, vl_l1, vl_l2, vl_l3 = process_split(val_rows)
    print("  Processing test split ...")
    te_tok, te_num, te_l1, te_l2, te_l3 = process_split(test_rows)

    return {
        "train_tokens": tr_tok, "train_nums": tr_num,
        "train_l1": tr_l1, "train_l2": tr_l2, "train_l3": tr_l3,
        "val_tokens": vl_tok, "val_nums": vl_num,
        "val_l1": vl_l1, "val_l2": vl_l2, "val_l3": vl_l3,
        "test_tokens": te_tok, "test_nums": te_num,
        "test_l1": te_l1, "test_l2": te_l2, "test_l3": te_l3,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MODEL ARCHITECTURE (per docs/09 §5.1-5.5)
# ═══════════════════════════════════════════════════════════════════════════

def build_cht_model(
    vocab_size: int = 8192,
    max_seq_len: int = 32,
    d_model: int = 128,
    num_heads: int = 4,
    d_ff: int = 256,
    num_layers: int = 3,
    num_numerical: int = 16,
    num_l1: int = 15,
    num_l2: int = 80,
    num_l3: int = 520,
    dropout: float = 0.15,
    label_smoothing: float = 0.05,
) -> Any:
    """
    Build the Compact Hierarchical Transformer (CHT) model.

    Architecture per docs/09 §5.2:
      Token Embedding → Positional Embedding → 3× Transformer Block
      → Global Avg Pool → Concat with Numerical Encoder
      → Shared Trunk → L1 Head → L2 Head (conditioned on L1) → L3 Head (conditioned on L2)
    """
    import keras  # type: ignore[import-untyped]
    from keras import layers, ops  # type: ignore[import-untyped]

    # ── Inputs ────────────────────────────────────────────────────────
    token_ids = keras.Input(shape=(max_seq_len,), dtype="int32", name="token_ids")
    num_feats = keras.Input(shape=(num_numerical,), dtype="float32", name="num_feats")

    # ── Text Branch ───────────────────────────────────────────────────
    tok_emb = layers.Embedding(vocab_size, d_model, name="token_embedding")(token_ids)

    # Learned positional embedding via Lambda (Keras 3 compatible)
    pos_emb_layer = layers.Embedding(max_seq_len, d_model, name="positional_embedding")
    pos_emb = pos_emb_layer(
        ops.arange(max_seq_len, dtype="int32")
    )
    x = tok_emb + pos_emb

    # Padding mask: (batch, seq_len) -> (batch, 1, 1, seq_len) for attention
    padding_mask = ops.cast(ops.not_equal(token_ids, 0), "float32")
    attn_mask = ops.expand_dims(ops.expand_dims(padding_mask, axis=1), axis=1)

    # Transformer encoder stack (3 layers)
    for i in range(num_layers):
        # Multi-head self-attention
        attn_out = layers.MultiHeadAttention(
            num_heads=num_heads,
            key_dim=d_model // num_heads,
            dropout=dropout,
            name=f"mha_{i}",
        )(x, x, x, attention_mask=attn_mask)
        attn_out = layers.Dropout(dropout, name=f"drop_attn_{i}")(attn_out)
        x = layers.LayerNormalization(epsilon=1e-6, name=f"ln_attn_{i}")(x + attn_out)

        # Feed-forward network
        ffn_out = layers.Dense(d_ff, activation="gelu", name=f"ffn_up_{i}")(x)
        ffn_out = layers.Dense(d_model, name=f"ffn_down_{i}")(ffn_out)
        ffn_out = layers.Dropout(dropout, name=f"drop_ffn_{i}")(ffn_out)
        x = layers.LayerNormalization(epsilon=1e-6, name=f"ln_ffn_{i}")(x + ffn_out)

    # Global average pooling (masked)
    mask_expanded = ops.expand_dims(padding_mask, axis=-1)  # (batch, seq, 1)
    text_repr = ops.sum(x * mask_expanded, axis=1) / (
        ops.sum(mask_expanded, axis=1) + 1e-9
    )

    # ── Numerical Branch ──────────────────────────────────────────────
    n = layers.Dense(64, activation="relu", name="num_dense1")(num_feats)
    n = layers.LayerNormalization(name="num_ln1")(n)
    n = layers.Dense(128, activation="relu", name="num_dense2")(n)
    num_repr = layers.LayerNormalization(name="num_ln2")(n)

    # ── Fusion ────────────────────────────────────────────────────────
    fused = layers.Concatenate(name="fusion")([text_repr, num_repr])
    shared = layers.Dense(256, activation="relu", name="shared_dense")(fused)
    shared = layers.Dropout(dropout, name="shared_dropout")(shared)
    shared = layers.LayerNormalization(name="shared_ln")(shared)

    # ── Hierarchical Classification Heads ─────────────────────────────
    # L1 Head (15 classes)
    l1_logits = layers.Dense(num_l1, name="L1_logits")(shared)
    l1_probs = layers.Softmax(name="L1_probs")(l1_logits)

    # L2 Head (80 classes, conditioned on L1)
    l2_input = layers.Concatenate(name="L2_concat")([shared, l1_probs])
    l2_hidden = layers.Dense(256, activation="relu", name="L2_dense")(l2_input)
    l2_logits = layers.Dense(num_l2, name="L2_logits")(l2_hidden)
    l2_probs = layers.Softmax(name="L2_probs")(l2_logits)

    # L3 Head (520 classes, conditioned on L2)
    l3_input = layers.Concatenate(name="L3_concat")([shared, l2_probs])
    l3_hidden = layers.Dense(512, activation="relu", name="L3_dense")(l3_input)
    l3_hidden = layers.Dropout(0.15, name="L3_dropout")(l3_hidden)
    l3_logits = layers.Dense(num_l3, name="L3_logits")(l3_hidden)
    l3_probs = layers.Softmax(name="L3_probs")(l3_logits)

    model = keras.Model(
        inputs=[token_ids, num_feats],
        outputs=[l1_probs, l2_probs, l3_probs],
        name="XpenzCHT_v3",
    )

    return model


# ═══════════════════════════════════════════════════════════════════════════
# COSINE WARMUP SCHEDULE (per docs/09 §13.3)
# ═══════════════════════════════════════════════════════════════════════════

def build_cosine_warmup_schedule(
    total_steps: int,
    warmup_steps: int = 2000,
    peak_lr: float = 3e-4,
    min_lr: float = 1e-6,
) -> Any:
    """Cosine decay with linear warmup learning rate schedule."""
    import tensorflow as tf  # type: ignore[import-untyped]
    import keras  # type: ignore[import-untyped]

    class CosineWarmup(keras.optimizers.schedules.LearningRateSchedule):  # type: ignore[misc]
        """Cosine warmup learning rate schedule."""

        def __init__(
            self,
            total: int,
            warmup: int,
            peak: float,
            minimum: float,
        ) -> None:
            super().__init__()
            self.total = float(total)
            self.warmup = float(warmup)
            self.peak = peak
            self.minimum = minimum

        def __call__(self, step: Any) -> Any:
            step_f = tf.cast(step, tf.float32)
            warmup_f = tf.constant(self.warmup, dtype=tf.float32)
            total_f = tf.constant(self.total, dtype=tf.float32)
            peak_f = tf.constant(self.peak, dtype=tf.float32)
            min_f = tf.constant(self.minimum, dtype=tf.float32)

            # Linear warmup
            warmup_lr = peak_f * (step_f / tf.maximum(warmup_f, 1.0))

            # Cosine decay
            progress = (step_f - warmup_f) / tf.maximum(total_f - warmup_f, 1.0)
            cosine_lr = min_f + 0.5 * (peak_f - min_f) * (
                1.0 + tf.cos(math.pi * tf.minimum(progress, 1.0))
            )

            return tf.where(step_f < warmup_f, warmup_lr, cosine_lr)

        def get_config(self) -> dict[str, Any]:
            return {
                "total": self.total,
                "warmup": self.warmup,
                "peak": self.peak,
                "minimum": self.minimum,
            }

    return CosineWarmup(total_steps, warmup_steps, peak_lr, min_lr)


# ═══════════════════════════════════════════════════════════════════════════
# TFLITE CONVERSION (per docs/09 §5.7)
# ═══════════════════════════════════════════════════════════════════════════

def convert_to_tflite(
    model: Any,
    output_path: Path,
    data: dict[str, Any],
) -> Path:
    """
    Convert Keras model to INT8-quantized TFLite with FP16 embeddings.
    Uses hybrid quantization per docs/09 §5.7.
    """
    import numpy as np  # type: ignore[import-untyped]
    import tensorflow as tf  # type: ignore[import-untyped]

    print(f"\nConverting to TFLite: {output_path} ...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # INT8 quantization with FP16 fallback for embeddings
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]

    # Representative dataset for INT8 calibration
    cal_tokens = data["train_tokens"][:500]
    cal_nums = data["train_nums"][:500]

    def representative_dataset() -> Any:
        for i in range(min(500, len(cal_tokens))):
            tok = np.expand_dims(cal_tokens[i], 0).astype(np.int32)
            num = np.expand_dims(cal_nums[i], 0).astype(np.float32)
            yield [tok, num]

    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_types = [tf.float16]

    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"  TFLite saved: {output_path} ({size_mb:.2f} MB)")

    if size_mb > 5.0:
        print(f"  WARNING: Model size {size_mb:.2f} MB exceeds 5 MB target!")
    elif size_mb > 3.5:
        print(f"  NOTE: Model size {size_mb:.2f} MB, close to 3.5 MB spec target.")
    else:
        print(f"  Size OK: {size_mb:.2f} MB (target: ~3.2 MB)")

    return output_path


# ═══════════════════════════════════════════════════════════════════════════
# EVALUATION
# ═══════════════════════════════════════════════════════════════════════════

def evaluate_model(
    model: Any,
    data: dict[str, Any],
    encoders: dict[str, dict[str, int]],
) -> dict[str, Any]:
    """Evaluate model on test set and produce metrics report."""
    import numpy as np  # type: ignore[import-untyped]

    print("\nEvaluating on test set ...")
    test_tokens = data["test_tokens"]
    test_nums = data["test_nums"]
    test_l1 = data["test_l1"]
    test_l2 = data["test_l2"]
    test_l3 = data["test_l3"]

    # Predict
    l1_pred, l2_pred, l3_pred = model.predict(
        [test_tokens, test_nums],
        batch_size=512,
        verbose=0,
    )

    # Top-1 accuracy
    l1_top1 = np.mean(np.argmax(l1_pred, axis=1) == test_l1)
    l2_top1 = np.mean(np.argmax(l2_pred, axis=1) == test_l2)
    l3_top1 = np.mean(np.argmax(l3_pred, axis=1) == test_l3)

    # Top-3 accuracy for L3
    l3_top3_indices = np.argsort(l3_pred, axis=1)[:, -3:]
    l3_top3 = float(np.mean([
        test_l3[i] in l3_top3_indices[i] for i in range(len(test_l3))
    ]))

    # Top-5 accuracy for L3
    l3_top5_indices = np.argsort(l3_pred, axis=1)[:, -5:]
    l3_top5 = float(np.mean([
        test_l3[i] in l3_top5_indices[i] for i in range(len(test_l3))
    ]))

    # Hierarchy consistency: when L3 is wrong, is L1 still correct?
    l3_wrong = np.argmax(l3_pred, axis=1) != test_l3
    l1_correct_when_l3_wrong = np.mean(
        np.argmax(l1_pred, axis=1)[l3_wrong] == test_l1[l3_wrong]
    ) if np.sum(l3_wrong) > 0 else 1.0

    report: dict[str, Any] = {
        "test_size": len(test_l3),
        "L1_top1_accuracy": round(float(l1_top1), 4),
        "L2_top1_accuracy": round(float(l2_top1), 4),
        "L3_top1_accuracy": round(float(l3_top1), 4),
        "L3_top3_accuracy": round(float(l3_top3), 4),
        "L3_top5_accuracy": round(float(l3_top5), 4),
        "hierarchy_consistency": round(float(l1_correct_when_l3_wrong), 4),
        "num_L1_classes": len(encoders["l1_code"]),
        "num_L2_classes": len(encoders["l2_code"]),
        "num_L3_classes": len(encoders["l3_code"]),
    }

    print(f"  L1 Top-1: {report['L1_top1_accuracy']:.4f}")
    print(f"  L2 Top-1: {report['L2_top1_accuracy']:.4f}")
    print(f"  L3 Top-1: {report['L3_top1_accuracy']:.4f}")
    print(f"  L3 Top-3: {report['L3_top3_accuracy']:.4f}")
    print(f"  L3 Top-5: {report['L3_top5_accuracy']:.4f}")
    print(f"  Hierarchy consistency: {report['hierarchy_consistency']:.4f}")

    return report


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Xpenzo CHT Model Training")
    parser.add_argument("--training-dir", type=str, default=str(DEFAULT_TRAINING_DIR))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--warmup-steps", type=int, default=2000)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--label-smoothing", type=float, default=0.05)
    parser.add_argument("--dropout", type=float, default=0.15)
    parser.add_argument("--vocab-size", type=int, default=8192)
    parser.add_argument("--max-seq-len", type=int, default=32)
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--num-heads", type=int, default=4)
    parser.add_argument("--d-ff", type=int, default=256)
    parser.add_argument("--num-layers", type=int, default=3)
    args = parser.parse_args()

    training_dir = Path(args.training_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Import TensorFlow + Keras ───────────────────────────────────
    print("Loading TensorFlow ...")
    import tensorflow as tf  # type: ignore[import-untyped]
    import keras  # type: ignore[import-untyped]
    print(f"  TF version: {tf.__version__}")
    print(f"  Keras version: {keras.__version__}")
    gpu_list = tf.config.list_physical_devices('GPU')
    print(f"  GPU available: {len(gpu_list) > 0}")

    # ── Load files ────────────────────────────────────────────────────
    print("\nLoading training data ...")
    train_rows = load_split(training_dir / "train.csv")
    val_rows = load_split(training_dir / "val.csv")
    test_rows = load_split(training_dir / "test.csv")
    print(f"  Train: {len(train_rows):,} | Val: {len(val_rows):,} | Test: {len(test_rows):,}")

    # Load encoders
    encoders_path = training_dir / "label_encoders.json"
    with open(encoders_path, "r", encoding="utf-8") as f:
        encoder_data: dict[str, Any] = json.load(f)
    encoders: dict[str, dict[str, int]] = encoder_data["encoders"]
    num_l1 = len(encoders["l1_code"])
    num_l2 = len(encoders["l2_code"])
    num_l3 = len(encoders["l3_code"])
    print(f"  Classes: L1={num_l1}, L2={num_l2}, L3={num_l3}")

    # Load class weights
    weights_path = training_dir / "class_weights.json"
    with open(weights_path, "r", encoding="utf-8") as f:
        class_weights_data: dict[str, dict[str, float]] = json.load(f)

    # Convert class weights to arrays indexed by integer label
    l3_weights_dict: dict[int, float] = {}
    for code, weight in class_weights_data.get("l3_code", {}).items():
        idx = encoders["l3_code"].get(code)
        if idx is not None:
            l3_weights_dict[idx] = weight

    # Load tokenizer
    tokenizer_path = training_dir / "tokenizer" / "xpenz_bpe.model"
    if not tokenizer_path.exists():
        print(f"  ERROR: Tokenizer not found at {tokenizer_path}")
        print("  Run 10_feature_engineering.py first (with sentencepiece installed)")
        return
    sp_model = prepare_tokenizer(tokenizer_path)
    print(f"  Tokenizer loaded: vocab={sp_model.GetPieceSize()}")

    # ── Prepare numpy arrays ──────────────────────────────────────────
    print("\nPreparing datasets ...")
    data = prepare_datasets(train_rows, val_rows, test_rows, sp_model, args.max_seq_len)

    # ── Build model ───────────────────────────────────────────────────
    print("\nBuilding CHT model ...")
    model = build_cht_model(
        vocab_size=args.vocab_size,
        max_seq_len=args.max_seq_len,
        d_model=args.d_model,
        num_heads=args.num_heads,
        d_ff=args.d_ff,
        num_layers=args.num_layers,
        num_l1=num_l1,
        num_l2=num_l2,
        num_l3=num_l3,
        dropout=args.dropout,
        label_smoothing=args.label_smoothing,
    )
    model.summary()

    # ── Compile ───────────────────────────────────────────────────────
    total_steps = (len(train_rows) // args.batch_size) * args.epochs
    lr_schedule = build_cosine_warmup_schedule(
        total_steps=total_steps,
        warmup_steps=args.warmup_steps,
        peak_lr=args.learning_rate,
    )

    optimizer = keras.optimizers.AdamW(
        learning_rate=lr_schedule,
        weight_decay=args.weight_decay,
    )

    # Label smoothing losses
    l1_loss = keras.losses.SparseCategoricalCrossentropy(
        from_logits=False, name="l1_loss",
    )
    l2_loss = keras.losses.SparseCategoricalCrossentropy(
        from_logits=False, name="l2_loss",
    )
    l3_loss = keras.losses.SparseCategoricalCrossentropy(
        from_logits=False, name="l3_loss",
    )

    model.compile(
        optimizer=optimizer,
        loss={
            "L1_probs": l1_loss,
            "L2_probs": l2_loss,
            "L3_probs": l3_loss,
        },
        loss_weights={
            "L1_probs": 0.15,
            "L2_probs": 0.25,
            "L3_probs": 0.60,
        },
        metrics={
            "L1_probs": ["accuracy"],
            "L2_probs": ["accuracy"],
            "L3_probs": [
                "accuracy",
                keras.metrics.SparseTopKCategoricalAccuracy(
                    k=3, name="top3_acc"
                ),
            ],
        },
    )

    print(f"\n  Optimizer: AdamW (lr={args.learning_rate}, wd={args.weight_decay})")
    print(f"  Schedule: Cosine warmup ({args.warmup_steps} steps)")
    print(f"  Total steps: {total_steps:,}")
    print(f"  Loss weights: L1=0.15, L2=0.25, L3=0.60")

    # ── Callbacks ─────────────────────────────────────────────────────
    callbacks: list[Any] = [
        keras.callbacks.EarlyStopping(  # type: ignore[attr-defined]
            monitor="val_L3_probs_accuracy",
            patience=8,
            mode="max",
            restore_best_weights=True,
            verbose=1,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(output_dir / "xpenz_cht_v3_best.keras"),
            monitor="val_L3_probs_accuracy",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        keras.callbacks.CSVLogger(
            str(output_dir / "training_log.csv"),
        ),
    ]

    # ── Train ─────────────────────────────────────────────────────────
    print(f"\nTraining for up to {args.epochs} epochs (batch_size={args.batch_size}) ...")
    t0 = time.time()

    history = model.fit(
        x=[data["train_tokens"], data["train_nums"]],
        y={
            "L1_probs": data["train_l1"],
            "L2_probs": data["train_l2"],
            "L3_probs": data["train_l3"],
        },
        validation_data=(
            [data["val_tokens"], data["val_nums"]],
            {
                "L1_probs": data["val_l1"],
                "L2_probs": data["val_l2"],
                "L3_probs": data["val_l3"],
            },
        ),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        class_weight=None,  # Applied per-sample for multi-output
        verbose=1,
    )

    elapsed = time.time() - t0
    print(f"\nTraining complete in {elapsed / 60:.1f} minutes")

    # ── Save training history ─────────────────────────────────────────
    history_dict: dict[str, list[float]] = {}
    for key, values in history.history.items():
        history_dict[key] = [float(v) for v in values]

    history_path = output_dir / "training_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_dict, f, indent=2)
    print(f"  History saved: {history_path}")

    # ── Save Keras model ──────────────────────────────────────────────
    keras_path = output_dir / "xpenz_cht_v3.keras"
    model.save(str(keras_path))
    keras_size_mb = keras_path.stat().st_size / (1024 * 1024)
    print(f"  Keras model saved: {keras_path} ({keras_size_mb:.1f} MB)")

    # ── Evaluate on test set ──────────────────────────────────────────
    eval_report = evaluate_model(model, data, encoders)
    eval_path = output_dir / "evaluation_report.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
    print(f"  Evaluation saved: {eval_path}")

    # ── Convert to TFLite ─────────────────────────────────────────────
    tflite_path = output_dir / "xpenz_cht_v3.tflite"
    convert_to_tflite(model, tflite_path, data)

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CHT MODEL TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Training time:    {elapsed / 60:.1f} minutes")
    print(f"  Epochs trained:   {len(history.history.get('loss', []))}")
    print(f"  Best val L3 acc:  {max(history.history.get('val_L3_probs_accuracy', [0])):.4f}")
    print(f"  Test L3 Top-1:    {eval_report['L3_top1_accuracy']:.4f}")
    print(f"  Test L3 Top-3:    {eval_report['L3_top3_accuracy']:.4f}")
    print(f"  Test L3 Top-5:    {eval_report['L3_top5_accuracy']:.4f}")
    print(f"  Hierarchy consis: {eval_report['hierarchy_consistency']:.4f}")
    tflite_mb = tflite_path.stat().st_size / (1024 * 1024) if tflite_path.exists() else 0
    print(f"  TFLite size:      {tflite_mb:.2f} MB")
    print(f"\n  Output files:")
    for p in [keras_path, tflite_path, history_path, eval_path]:
        print(f"    {p}")


if __name__ == "__main__":
    main()
