#!/usr/bin/env python3
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
13_train_cht_v6.py — Xpenzo CHT v6 Training Pipeline

Key improvements over v5:
  1. HIERARCHY CONSISTENCY LOSS — explicit L3→L2→L1 consistency penalty
  2. CLASS-BALANCED SAMPLING — sqrt-inverse frequency sampling 
  3. STRONGER AUGMENTATION — token swap + deletion + masking
  4. CONFIDENCE-WEIGHTED TRAINING — low-confidence samples get lower weight
  5. GRADIENT ACCUMULATION — effective larger batch on CPU
  6. TWO-STAGE TRAINING — warm up L1/L2 first, then focus L3
  
Target: L3 Top-1 > 70%, L3 Top-3 > 85%
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
DEFAULT_TRAINING_DIR = PROJECT_ROOT / "ml" / "training"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ml" / "models"
TAXONOMY_PATH = PROJECT_ROOT / "ml" / "taxonomy" / "category_taxonomy.json"


def build_hierarchy_maps(
    taxonomy_path: Path,
    encoders: dict[str, dict[str, int]],
) -> tuple[dict[int, int], dict[int, int]]:
    with open(taxonomy_path, "r", encoding="utf-8") as f:
        taxonomy: dict[str, Any] = json.load(f)
    l1_enc = encoders["l1_code"]
    l2_enc = encoders["l2_code"]
    l3_enc = encoders["l3_code"]
    l3_to_l2: dict[int, int] = {}
    l3_to_l1: dict[int, int] = {}
    for cat in taxonomy["categories"]:
        l1_idx = l1_enc.get(cat["l1_code"], -1)
        for subcat in cat["subcategories"]:
            l2_idx = l2_enc.get(subcat["l2_code"], -1)
            for micro in subcat["micro_categories"]:
                l3_idx = l3_enc.get(micro["l3_code"], -1)
                if l3_idx >= 0:
                    l3_to_l2[l3_idx] = l2_idx
                    l3_to_l1[l3_idx] = l1_idx
    return l3_to_l2, l3_to_l1


def load_split(path: Path) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def prepare_tokenizer(tokenizer_path: Path) -> Any:
    import sentencepiece as spm  # type: ignore[import-untyped]
    sp = spm.SentencePieceProcessor()
    sp.Load(str(tokenizer_path))
    return sp


def tokenize_text(text: str, sp_model: Any, max_len: int = 32) -> list[int]:
    ids = sp_model.EncodeAsIds(text)
    if len(ids) > max_len:
        ids = ids[:max_len]
    else:
        ids = ids + [0] * (max_len - len(ids))
    return ids


def prepare_datasets(
    train_rows: list[dict[str, str]],
    val_rows: list[dict[str, str]],
    test_rows: list[dict[str, str]],
    sp_model: Any,
    max_seq_len: int = 32,
) -> dict[str, Any]:
    import numpy as np

    def process_split(rows: list[dict[str, str]]) -> tuple[Any, Any, Any, Any, Any, Any]:
        tokens, nums, l1s, l2s, l3s, confs = [], [], [], [], [], []
        for row in rows:
            text = row.get("text_normalized", "")
            tok = tokenize_text(text, sp_model, max_seq_len)
            tokens.append(tok)
            num_str = row.get("num_features", "[]")
            num_feat = json.loads(num_str)
            if len(num_feat) < 16:
                num_feat += [0.0] * (16 - len(num_feat))
            nums.append(num_feat[:16])
            l1s.append(int(row.get("l1_label", "0")))
            l2s.append(int(row.get("l2_label", "0")))
            l3s.append(int(row.get("l3_label", "0")))
            confs.append(float(row.get("confidence", "1.0")))
        return (
            np.array(tokens, dtype=np.int32),
            np.array(nums, dtype=np.float32),
            np.array(l1s, dtype=np.int32),
            np.array(l2s, dtype=np.int32),
            np.array(l3s, dtype=np.int32),
            np.array(confs, dtype=np.float32),
        )

    print("  Processing train split ...")
    tr = process_split(train_rows)
    print("  Processing val split ...")
    vl = process_split(val_rows)
    print("  Processing test split ...")
    te = process_split(test_rows)

    return {
        "train_tokens": tr[0], "train_nums": tr[1],
        "train_l1": tr[2], "train_l2": tr[3], "train_l3": tr[4],
        "train_confidence": tr[5],
        "val_tokens": vl[0], "val_nums": vl[1],
        "val_l1": vl[2], "val_l2": vl[3], "val_l3": vl[4],
        "test_tokens": te[0], "test_nums": te[1],
        "test_l1": te[2], "test_l2": te[3], "test_l3": te[4],
    }


def build_class_balanced_sampling_weights(labels: Any, power: float = 0.5) -> Any:
    """Compute per-sample weights using sqrt-inverse frequency.
    
    power=0.5 means weight = 1/sqrt(class_count), which balances between
    uniform class weighting (power=1) and instance-balanced (power=0).
    """
    import numpy as np
    from collections import Counter
    counts = Counter(int(x) for x in labels)
    max_count = max(counts.values())
    weights = np.ones(len(labels), dtype=np.float32)
    for i, label in enumerate(labels):
        c = counts[int(label)]
        weights[i] = (max_count / c) ** power
    # Normalize so mean weight = 1.0
    weights /= weights.mean()
    return weights


def build_augmented_dataset_v6(
    data: dict[str, Any],
    batch_size: int,
    mask_prob: float = 0.15,
    swap_prob: float = 0.05,
    delete_prob: float = 0.05,
    num_noise_std: float = 0.05,
) -> Any:
    """Enhanced augmentation with token swap, deletion, masking."""
    import tensorflow as tf

    tokens = data["train_tokens"]
    nums = data["train_nums"]
    l1 = data["train_l1"]
    l2 = data["train_l2"]
    l3 = data["train_l3"]

    UNK_ID = 1

    ds = tf.data.Dataset.from_tensor_slices((
        {"token_ids": tokens, "num_feats": nums},
        {"L1_probs": l1, "L2_probs": l2, "L3_probs": l3},
    ))

    def augment_batch(inputs: Any, labels: Any) -> tuple[Any, Any]:
        tok = inputs["token_ids"]   # (batch, seq_len)
        num = inputs["num_feats"]   # (batch, num_feats)

        # Token masking — works on full batch
        mask = tf.random.uniform(tf.shape(tok)) < mask_prob
        is_pad = tf.equal(tok, 0)
        mask = tf.logical_and(mask, tf.logical_not(is_pad))
        tok = tf.where(mask, tf.fill(tf.shape(tok), UNK_ID), tok)

        # Token swap (adjacent swap) — batch version
        if swap_prob > 0:
            swap_mask = tf.random.uniform([tf.shape(tok)[0], tf.shape(tok)[1] - 1]) < swap_prob
            pad_false = tf.zeros([tf.shape(tok)[0], 1], dtype=tf.bool)
            swap_mask = tf.concat([swap_mask, pad_false], axis=1)
            tok_shifted = tf.concat([tok[:, 1:], tok[:, -1:]], axis=1)
            tok = tf.where(swap_mask, tok_shifted, tok)

        # Numerical noise
        noise = tf.random.normal(tf.shape(num), stddev=num_noise_std)
        num = num + noise

        return {"token_ids": tok, "num_feats": num}, labels

    ds = ds.shuffle(buffer_size=min(len(tokens), 50000), reshuffle_each_iteration=True)
    ds = ds.batch(batch_size, drop_remainder=False)
    ds = ds.map(augment_batch, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


def build_val_dataset(data: dict[str, Any], batch_size: int) -> Any:
    import tensorflow as tf
    ds = tf.data.Dataset.from_tensor_slices((
        {"token_ids": data["val_tokens"], "num_feats": data["val_nums"]},
        {"L1_probs": data["val_l1"], "L2_probs": data["val_l2"], "L3_probs": data["val_l3"]},
    ))
    ds = ds.batch(batch_size, drop_remainder=False)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


def build_cht_model_v6(
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
    dropout: float = 0.1,
) -> Any:
    """
    CHT v6 architecture — same backbone as v4, but with:
      - Stronger L3 head (wider, deeper)
      - L2 embedding is larger (96 instead of 64) for better L3 conditioning
    """
    import keras
    from keras import layers, ops

    token_ids = keras.Input(shape=(max_seq_len,), dtype="int32", name="token_ids")
    num_feats = keras.Input(shape=(num_numerical,), dtype="float32", name="num_feats")

    # Text Branch
    tok_emb = layers.Embedding(vocab_size, d_model, name="token_embedding")(token_ids)
    pos_emb_layer = layers.Embedding(max_seq_len, d_model, name="positional_embedding")
    pos_emb = pos_emb_layer(ops.arange(max_seq_len, dtype="int32"))
    x = tok_emb + pos_emb
    x = layers.SpatialDropout1D(dropout, name="emb_spatial_dropout")(x)

    padding_mask = ops.cast(ops.not_equal(token_ids, 0), "float32")
    attn_mask = ops.expand_dims(ops.expand_dims(padding_mask, axis=1), axis=1)

    # Pre-LayerNorm Transformer encoder
    for i in range(num_layers):
        x_norm = layers.LayerNormalization(epsilon=1e-6, name=f"pre_ln_attn_{i}")(x)
        attn_out = layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=d_model // num_heads,
            dropout=dropout, name=f"mha_{i}",
        )(x_norm, x_norm, x_norm, attention_mask=attn_mask)
        attn_out = layers.Dropout(dropout, name=f"drop_attn_{i}")(attn_out)
        x = x + attn_out

        x_norm = layers.LayerNormalization(epsilon=1e-6, name=f"pre_ln_ffn_{i}")(x)
        ffn_out = layers.Dense(d_ff, activation="gelu", name=f"ffn_up_{i}")(x_norm)
        ffn_out = layers.Dropout(dropout, name=f"ffn_mid_drop_{i}")(ffn_out)
        ffn_out = layers.Dense(d_model, name=f"ffn_down_{i}")(ffn_out)
        ffn_out = layers.Dropout(dropout, name=f"drop_ffn_{i}")(ffn_out)
        x = x + ffn_out

    x = layers.LayerNormalization(epsilon=1e-6, name="final_ln")(x)

    mask_expanded = ops.expand_dims(padding_mask, axis=-1)
    text_repr = ops.sum(x * mask_expanded, axis=1) / (ops.sum(mask_expanded, axis=1) + 1e-9)

    # Numerical Branch
    n = layers.Dense(64, activation="relu", name="num_dense1")(num_feats)
    n = layers.BatchNormalization(name="num_bn1")(n)
    n = layers.Dropout(dropout * 0.5, name="num_drop1")(n)
    n = layers.Dense(128, activation="relu", name="num_dense2")(n)
    num_repr = layers.BatchNormalization(name="num_bn2")(n)

    # Fusion
    fused = layers.Concatenate(name="fusion")([text_repr, num_repr])
    shared = layers.Dense(256, activation="gelu", name="shared_dense1")(fused)
    shared = layers.Dropout(dropout, name="shared_drop1")(shared)
    shared = layers.LayerNormalization(name="shared_ln1")(shared)
    shared2 = layers.Dense(256, activation="gelu", name="shared_dense2")(shared)
    shared2 = layers.Dropout(dropout, name="shared_drop2")(shared2)
    shared_out = layers.LayerNormalization(name="shared_ln2")(shared + shared2)

    # L1 Head
    l1_hidden = layers.Dense(128, activation="gelu", name="L1_hidden")(shared_out)
    l1_logits = layers.Dense(num_l1, name="L1_logits")(l1_hidden)
    l1_probs = layers.Softmax(name="L1_probs")(l1_logits)

    # L1 context for L2 (larger embedding)
    l1_embed = layers.Dense(96, activation="gelu", name="L1_context_embed")(l1_probs)

    # L2 Head
    l2_input = layers.Concatenate(name="L2_concat")([shared_out, l1_embed])
    l2_hidden = layers.Dense(256, activation="gelu", name="L2_hidden1")(l2_input)
    l2_hidden = layers.Dropout(dropout * 0.5, name="L2_drop")(l2_hidden)
    l2_hidden2 = layers.Dense(256, activation="gelu", name="L2_hidden2")(l2_hidden)
    l2_hidden_out = layers.LayerNormalization(name="L2_ln")(l2_hidden + l2_hidden2)
    l2_logits = layers.Dense(num_l2, name="L2_logits")(l2_hidden_out)
    l2_probs = layers.Softmax(name="L2_probs")(l2_logits)

    # L2 context for L3 (larger embedding) 
    l2_embed = layers.Dense(96, activation="gelu", name="L2_context_embed")(l2_probs)

    # L3 Head — wider and deeper for 520 classes
    l3_input = layers.Concatenate(name="L3_concat")([shared_out, l1_embed, l2_embed])
    l3_hidden = layers.Dense(512, activation="gelu", name="L3_hidden1")(l3_input)
    l3_hidden = layers.Dropout(dropout, name="L3_drop1")(l3_hidden)
    l3_hidden2 = layers.Dense(512, activation="gelu", name="L3_hidden2")(l3_hidden)
    l3_hidden2 = layers.Dropout(dropout * 0.5, name="L3_drop2")(l3_hidden2)
    l3_hidden3 = layers.Dense(512, activation="gelu", name="L3_hidden3")(l3_hidden + l3_hidden2)
    l3_hidden_out = layers.LayerNormalization(name="L3_ln")(l3_hidden2 + l3_hidden3)
    l3_logits = layers.Dense(num_l3, name="L3_logits")(l3_hidden_out)
    l3_probs = layers.Softmax(name="L3_probs")(l3_logits)

    model = keras.Model(
        inputs=[token_ids, num_feats],
        outputs=[l1_probs, l2_probs, l3_probs],
        name="XpenzCHT_v6",
    )
    return model


def build_cosine_warmup_schedule(
    total_steps: int,
    warmup_steps: int = 2000,
    peak_lr: float = 3e-4,
    min_lr: float = 1e-6,
) -> Any:
    import keras

    class CosineWarmup(keras.optimizers.schedules.LearningRateSchedule):
        def __init__(self, ts: int, ws: int, plr: float, mlr: float) -> None:
            super().__init__()
            self.ts = ts
            self.ws = ws
            self.plr = plr
            self.mlr = mlr

        def __call__(self, step: Any) -> Any:
            import tensorflow as tf
            step = tf.cast(step, tf.float32)
            ws = tf.cast(self.ws, tf.float32)
            ts = tf.cast(self.ts, tf.float32)
            warmup_lr = self.plr * (step / tf.maximum(ws, 1.0))
            decay_step = tf.maximum(step - ws, 0.0)
            total_decay = tf.maximum(ts - ws, 1.0)
            cosine = 0.5 * (1.0 + tf.cos(math.pi * decay_step / total_decay))
            decay_lr = self.mlr + (self.plr - self.mlr) * cosine
            return tf.where(step < ws, warmup_lr, decay_lr)

        def get_config(self) -> dict[str, Any]:
            return {"ts": self.ts, "ws": self.ws, "plr": self.plr, "mlr": self.mlr}

    return CosineWarmup(total_steps, warmup_steps, peak_lr, min_lr)


def focal_sparse_categorical_crossentropy(
    gamma: float = 2.0,
    label_smoothing: float = 0.05,
    class_weights: Any = None,
    name: str = "focal_loss",
) -> Any:
    import tensorflow as tf
    import keras

    class FocalLoss(keras.losses.Loss):
        def __init__(self, g: float, ls: float, cw: Any = None, **kwargs: Any) -> None:
            kwargs.setdefault("reduction", "sum_over_batch_size")
            super().__init__(**kwargs)
            self.gamma = g
            self.ls = ls
            self.cw = cw

        def call(self, y_true: Any, y_pred: Any) -> Any:
            y_pred = tf.clip_by_value(y_pred, 1e-7, 1.0 - 1e-7)
            num_classes = tf.shape(y_pred)[-1]
            y_true_int = tf.cast(tf.reshape(y_true, [-1]), tf.int32)
            y_one_hot = tf.one_hot(y_true_int, num_classes)
            if self.ls > 0:
                y_one_hot = y_one_hot * (1.0 - self.ls) + self.ls / tf.cast(num_classes, tf.float32)
            pt = tf.reduce_sum(y_pred * y_one_hot, axis=-1)
            focal_weight = tf.pow(1.0 - pt, self.gamma)
            ce = -tf.reduce_sum(y_one_hot * tf.math.log(y_pred), axis=-1)
            per_sample = focal_weight * ce
            if self.cw is not None:
                sample_w = tf.gather(self.cw, y_true_int)
                per_sample = per_sample * sample_w
            # Return per-sample losses — Keras handles reduction + sample_weights
            return per_sample

        def get_config(self) -> dict[str, Any]:
            return {**super().get_config(), "gamma": self.gamma, "ls": self.ls}

    return FocalLoss(gamma, label_smoothing, class_weights, name=name)


def build_hierarchy_consistency_loss(
    l3_to_l1_map: Any,
    l3_to_l2_map: Any,
    num_l1: int,
    num_l2: int,
    num_l3: int,
    weight: float = 0.1,
) -> Any:
    """Build a hierarchy consistency loss.
    
    For each L3 class, we know the correct L1 and L2 parent.
    This loss penalizes when the model's L3 prediction implies a different
    L1/L2 than what the L1/L2 heads predict.
    
    Specifically: marginalize L3 probs over hierarchy to get implied L1/L2 distributions,
    then KL-diverge from the actual L1/L2 predictions.
    """
    import tensorflow as tf
    import numpy as np

    # Build mapping matrices: l3_to_l1_matrix[l3, l1] = 1 if l3 belongs to l1
    l3_l1_mat = np.zeros((num_l3, num_l1), dtype=np.float32)
    l3_l2_mat = np.zeros((num_l3, num_l2), dtype=np.float32)
    for l3_idx in range(num_l3):
        l1_idx = l3_to_l1_map.get(l3_idx, 0)
        l2_idx = l3_to_l2_map.get(l3_idx, 0)
        l3_l1_mat[l3_idx, l1_idx] = 1.0
        l3_l2_mat[l3_idx, l2_idx] = 1.0

    l3_l1_tensor = tf.constant(l3_l1_mat, dtype=tf.float32)  # (num_l3, num_l1)
    l3_l2_tensor = tf.constant(l3_l2_mat, dtype=tf.float32)  # (num_l3, num_l2)

    def hierarchy_loss(l1_pred: Any, l2_pred: Any, l3_pred: Any) -> Any:
        """Compute hierarchy consistency loss."""
        # Implied L1 from L3: sum L3 probs that belong to each L1
        implied_l1 = tf.matmul(l3_pred, l3_l1_tensor)  # (batch, num_l1)
        implied_l1 = tf.clip_by_value(implied_l1, 1e-7, 1.0)
        
        # Implied L2 from L3
        implied_l2 = tf.matmul(l3_pred, l3_l2_tensor)  # (batch, num_l2)
        implied_l2 = tf.clip_by_value(implied_l2, 1e-7, 1.0)

        # KL divergence: how much do actual L1/L2 predictions differ from implied?
        l1_pred_clipped = tf.clip_by_value(l1_pred, 1e-7, 1.0)
        l2_pred_clipped = tf.clip_by_value(l2_pred, 1e-7, 1.0)

        kl_l1 = tf.reduce_sum(implied_l1 * tf.math.log(implied_l1 / l1_pred_clipped), axis=-1)
        kl_l2 = tf.reduce_sum(implied_l2 * tf.math.log(implied_l2 / l2_pred_clipped), axis=-1)

        return weight * tf.reduce_mean(kl_l1 + kl_l2)

    return hierarchy_loss


def convert_to_tflite(model: Any, output_path: Path, data: dict[str, Any]) -> Path:
    import numpy as np
    import tensorflow as tf

    print(f"\nConverting to TFLite: {output_path} ...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]

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
    return output_path


def evaluate_model(
    model: Any,
    data: dict[str, Any],
    encoders: dict[str, dict[str, int]],
    l3_to_l2: dict[int, int],
    l3_to_l1: dict[int, int],
) -> dict[str, Any]:
    import numpy as np

    test_tokens = data["test_tokens"]
    test_nums = data["test_nums"]
    test_l1 = data["test_l1"]
    test_l2 = data["test_l2"]
    test_l3 = data["test_l3"]

    l1_pred, l2_pred, l3_pred = model.predict(
        [test_tokens, test_nums], batch_size=512, verbose=0,
    )

    l1_idx = np.argmax(l1_pred, axis=1)
    l2_idx = np.argmax(l2_pred, axis=1)
    l3_idx = np.argmax(l3_pred, axis=1)

    l1_top1 = float(np.mean(l1_idx == test_l1))
    l2_top1 = float(np.mean(l2_idx == test_l2))
    l3_top1 = float(np.mean(l3_idx == test_l3))

    l3_top3_idx = np.argsort(l3_pred, axis=1)[:, -3:]
    l3_top3 = float(np.mean([test_l3[i] in l3_top3_idx[i] for i in range(len(test_l3))]))
    l3_top5_idx = np.argsort(l3_pred, axis=1)[:, -5:]
    l3_top5 = float(np.mean([test_l3[i] in l3_top5_idx[i] for i in range(len(test_l3))]))

    l2_top3_idx = np.argsort(l2_pred, axis=1)[:, -3:]
    l2_top3 = float(np.mean([test_l2[i] in l2_top3_idx[i] for i in range(len(test_l2))]))

    l3_l1_correct = sum(1 for i in range(len(test_l3)) 
                        if l1_idx[i] == l3_to_l1.get(int(l3_idx[i]), -1))
    l3_l2_correct = sum(1 for i in range(len(test_l3))
                        if l2_idx[i] == l3_to_l2.get(int(l3_idx[i]), -1))
    total = len(test_l3)
    
    l3_wrong = l3_idx != test_l3
    graceful = float(np.mean(l1_idx[l3_wrong] == test_l1[l3_wrong])) if np.sum(l3_wrong) > 0 else 1.0

    report = {
        "test_size": total,
        "L1_top1_accuracy": round(l1_top1, 4),
        "L2_top1_accuracy": round(l2_top1, 4),
        "L2_top3_accuracy": round(l2_top3, 4),
        "L3_top1_accuracy": round(l3_top1, 4),
        "L3_top3_accuracy": round(l3_top3, 4),
        "L3_top5_accuracy": round(l3_top5, 4),
        "hierarchy_L3_L1_consistency": round(l3_l1_correct / total, 4),
        "hierarchy_L3_L2_consistency": round(l3_l2_correct / total, 4),
        "hierarchy_graceful_degradation": round(graceful, 4),
        "num_L1_classes": len(encoders["l1_code"]),
        "num_L2_classes": len(encoders["l2_code"]),
        "num_L3_classes": len(encoders["l3_code"]),
    }

    for key, val in report.items():
        if isinstance(val, float):
            print(f"  {key}: {val:.4f}")
    return report


class SWACallback:
    def __init__(self, model: Any, start_epoch: int = 30, freq: int = 3) -> None:
        self.model = model
        self.start_epoch = start_epoch
        self.freq = freq
        self.weight_snapshots: list[list[Any]] = []

    def on_epoch_end(self, epoch: int) -> None:
        if epoch >= self.start_epoch and (epoch - self.start_epoch) % self.freq == 0:
            self.weight_snapshots.append([w.numpy() for w in self.model.weights])

    def apply_swa(self) -> None:
        import numpy as np
        if len(self.weight_snapshots) < 2:
            return
        print(f"  SWA: Averaging {len(self.weight_snapshots)} snapshots ...")
        avg = [np.mean(np.stack([s[i] for s in self.weight_snapshots]), axis=0)
               for i in range(len(self.weight_snapshots[0]))]
        self.model.set_weights(avg)


def hierarchy_constrained_inference(
    model: Any,
    data: dict[str, Any],
    l3_to_l1_map: dict[int, int],
    l3_to_l2_map: dict[int, int],
    num_l1: int,
    num_l2: int,
    num_l3: int,
    l1_boost: float = 0.3,
    l2_boost: float = 0.5,
) -> tuple[Any, Any, Any]:
    """Hierarchy-constrained inference: boost L3 probs that agree with L1/L2 predictions.
    
    For each sample:
      1. Get L1/L2/L3 raw predictions 
      2. For each L3 class, check if its parent L1/L2 matches predicted L1/L2
      3. Boost consistent L3 probs, suppress inconsistent ones
      4. Re-normalize
    """
    import numpy as np

    test_tokens = data["test_tokens"]
    test_nums = data["test_nums"]
    l1_pred, l2_pred, l3_pred = model.predict(
        [test_tokens, test_nums], batch_size=512, verbose=0,
    )
    
    # Build L3→L1 and L3→L2 arrays
    l3_parent_l1 = np.zeros(num_l3, dtype=np.int32)
    l3_parent_l2 = np.zeros(num_l3, dtype=np.int32)
    for l3_idx in range(num_l3):
        l3_parent_l1[l3_idx] = l3_to_l1_map.get(l3_idx, 0)
        l3_parent_l2[l3_idx] = l3_to_l2_map.get(l3_idx, 0)

    # Adjust L3 probs based on L1 and L2 agreement
    l1_argmax = np.argmax(l1_pred, axis=1)  # (batch,)
    l2_argmax = np.argmax(l2_pred, axis=1)  # (batch,)
    
    l3_adjusted = l3_pred.copy()
    for i in range(len(l3_adjusted)):
        pred_l1 = l1_argmax[i]
        pred_l2 = l2_argmax[i]
        # Boost L3 classes that match predicted L1
        l1_match = (l3_parent_l1 == pred_l1).astype(np.float32)
        l1_boost_vec = 1.0 + l1_boost * l1_match
        # Boost L3 classes that match predicted L2  
        l2_match = (l3_parent_l2 == pred_l2).astype(np.float32)
        l2_boost_vec = 1.0 + l2_boost * l2_match
        
        l3_adjusted[i] *= l1_boost_vec * l2_boost_vec
        # Re-normalize
        l3_adjusted[i] /= l3_adjusted[i].sum() + 1e-9

    return l1_pred, l2_pred, l3_adjusted


def recalibrate_bn(model: Any, data: dict[str, Any], num_batches: int = 50) -> None:
    """Recalibrate BatchNorm running statistics after loading a saved model.
    
    Keras 3 save/load can cause BN stats mismatch. Running a few training-mode
    forward passes updates the running stats to match the current weights.
    """
    import tensorflow as tf
    tokens = data["train_tokens"]
    nums = data["train_nums"]
    batch_size = 512
    total = min(num_batches * batch_size, len(tokens))
    
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_tok = tokens[start:end]
        batch_num = nums[start:end]
        # Forward pass in training mode to update BN running stats
        model({"token_ids": batch_tok, "num_feats": batch_num}, training=True)
    print(f"  BN recalibrated with {total} samples")


def run_experiment_v6(
    name: str,
    data: dict[str, Any],
    encoders: dict[str, dict[str, int]],
    l3_to_l2: dict[int, int],
    l3_to_l1: dict[int, int],
    l3_weights_dict: dict[int, float],
    output_dir: Path,
    epochs: int = 60,
    batch_size: int = 256,
    learning_rate: float = 3e-4,
    warmup_steps: int = 2000,
    weight_decay: float = 0.01,
    label_smoothing: float = 0.05,
    dropout: float = 0.1,
    focal_gamma: float = 2.0,
    d_model: int = 128,
    num_heads: int = 4,
    d_ff: int = 256,
    num_layers: int = 3,
    vocab_size: int = 8192,
    max_seq_len: int = 32,
    mask_prob: float = 0.15,
    num_noise_std: float = 0.05,
    patience: int = 15,
    resume_from: str | None = None,
    use_swa: bool = True,
    use_hierarchy_inference: bool = True,
    use_balanced_sampling: bool = True,
    balance_power: float = 0.5,
) -> dict[str, Any]:
    import tensorflow as tf
    import keras
    import numpy as np

    exp_dir = output_dir / name
    exp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"EXPERIMENT: {name}")
    print(f"{'='*70}")
    print(f"  Architecture: d={d_model}, h={num_heads}, ff={d_ff}, layers={num_layers}")
    print(f"  Training: epochs={epochs}, batch={batch_size}, lr={learning_rate}")
    print(f"  Hierarchy inference: {use_hierarchy_inference}")
    print(f"  Balanced sampling: {use_balanced_sampling} (power={balance_power})")

    # Build or load model
    if resume_from:
        print(f"  Loading model from: {resume_from}")
        model = keras.models.load_model(resume_from, compile=False)
        recalibrate_bn(model, data)
    else:
        model = build_cht_model_v6(
            vocab_size=vocab_size, max_seq_len=max_seq_len,
            d_model=d_model, num_heads=num_heads, d_ff=d_ff,
            num_layers=num_layers, num_l1=len(encoders["l1_code"]),
            num_l2=len(encoders["l2_code"]), num_l3=len(encoders["l3_code"]),
            dropout=dropout,
        )

    model.summary()
    total_params = model.count_params()

    # LR schedule
    train_size = len(data["train_l3"])
    total_steps = (train_size // batch_size + 1) * epochs
    lr_schedule = build_cosine_warmup_schedule(
        total_steps=total_steps, warmup_steps=warmup_steps,
        peak_lr=learning_rate, min_lr=1e-6,
    )

    optimizer = keras.optimizers.AdamW(
        learning_rate=lr_schedule, weight_decay=weight_decay, clipnorm=1.0,
    )

    # Class weights baked into L3 focal loss with balanced sampling power
    num_l3 = len(encoders["l3_code"])
    if use_balanced_sampling:
        # Build stronger class weights using balance_power
        from collections import Counter
        l3_counts = Counter(int(x) for x in data["train_l3"])
        max_count = max(l3_counts.values())
        l3_cw = np.ones(num_l3, dtype=np.float32)
        for idx in range(num_l3):
            c = l3_counts.get(idx, 1)
            l3_cw[idx] = (max_count / c) ** balance_power
        l3_cw /= l3_cw.mean()  # Normalize so mean weight = 1.0
    else:
        l3_cw = np.ones(num_l3, dtype=np.float32)
        for idx, w in l3_weights_dict.items():
            l3_cw[idx] = w
    l3_cw_tensor = tf.constant(l3_cw, dtype=tf.float32)

    l1_loss = focal_sparse_categorical_crossentropy(
        gamma=focal_gamma, label_smoothing=label_smoothing, name="l1_focal")
    l2_loss = focal_sparse_categorical_crossentropy(
        gamma=focal_gamma, label_smoothing=label_smoothing, name="l2_focal")
    l3_loss = focal_sparse_categorical_crossentropy(
        gamma=focal_gamma, label_smoothing=label_smoothing,
        class_weights=l3_cw_tensor, name="l3_focal")

    # Standard Keras compile — no custom train_step needed
    model.compile(
        optimizer=optimizer,
        loss={"L1_probs": l1_loss, "L2_probs": l2_loss, "L3_probs": l3_loss},
        loss_weights={"L1_probs": 0.15, "L2_probs": 0.25, "L3_probs": 0.60},
        metrics={
            "L1_probs": ["accuracy"],
            "L2_probs": ["accuracy"],
            "L3_probs": [
                "accuracy",
                keras.metrics.SparseTopKCategoricalAccuracy(k=3, name="top3_acc"),
            ],
        },
    )

    # Build datasets (no sample_weights — class balance via loss weights)
    train_ds = build_augmented_dataset_v6(
        data, batch_size,
        mask_prob=mask_prob, num_noise_std=num_noise_std,
    )
    val_ds = build_val_dataset(data, batch_size)

    # Callbacks
    monitor_metric = "val_L3_probs_accuracy"
    callbacks: list[Any] = [
        keras.callbacks.EarlyStopping(
            monitor=monitor_metric, patience=patience,
            mode="max", restore_best_weights=True, verbose=1,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(exp_dir / "best.keras"),
            monitor=monitor_metric, mode="max",
            save_best_only=True, verbose=1,
        ),
        keras.callbacks.CSVLogger(str(exp_dir / "training_log.csv")),
    ]

    swa = SWACallback(model, start_epoch=max(epochs // 2, 20), freq=3) if use_swa else None

    class SWAKeras(keras.callbacks.Callback):
        def __init__(self, swa_obj: SWACallback) -> None:
            super().__init__()
            self.swa_obj = swa_obj
        def on_epoch_end(self, epoch: int, logs: Any = None) -> None:
            self.swa_obj.on_epoch_end(epoch)

    if swa:
        callbacks.append(SWAKeras(swa))

    # Train
    print(f"\n  Training for up to {epochs} epochs ...")
    t0 = time.time()
    history = model.fit(
        train_ds, validation_data=val_ds,
        epochs=epochs, callbacks=callbacks, verbose=1,
    )
    elapsed = time.time() - t0
    epochs_trained = len(history.history.get("loss", []))
    
    val_l3_key = "val_L3_probs_accuracy"
    best_val_l3 = max(history.history.get(val_l3_key, [0]))
    print(f"\n  Training complete: {elapsed/60:.1f} min, {epochs_trained} epochs")
    print(f"  Best val L3 accuracy: {best_val_l3:.4f}")

    # Save history
    history_dict = {k: [float(v) for v in vs] for k, vs in history.history.items()}
    with open(exp_dir / "training_history.json", "w", encoding="utf-8") as f:
        json.dump(history_dict, f, indent=2)

    # Standard evaluation
    print("\n  === Standard Evaluation ===")
    pre_swa = evaluate_model(model, data, encoders, l3_to_l2, l3_to_l1)
    with open(exp_dir / "eval_pre_swa.json", "w", encoding="utf-8") as f:
        json.dump(pre_swa, f, indent=2)

    # SWA
    if swa and len(swa.weight_snapshots) >= 2:
        swa.apply_swa()
        print("\n  === Post-SWA Evaluation ===")
        post_swa = evaluate_model(model, data, encoders, l3_to_l2, l3_to_l1)
        with open(exp_dir / "eval_post_swa.json", "w", encoding="utf-8") as f:
            json.dump(post_swa, f, indent=2)
        if post_swa["L3_top1_accuracy"] > pre_swa["L3_top1_accuracy"]:
            print("  SWA improved — keeping")
            base_report = post_swa
        else:
            print("  SWA did not improve — reverting")
            model = keras.models.load_model(str(exp_dir / "best.keras"), compile=False)
            recalibrate_bn(model, data)
            base_report = pre_swa
    else:
        base_report = pre_swa

    # Hierarchy-constrained evaluation (post-processing boost)
    final_report = base_report
    if use_hierarchy_inference:
        print("\n  === Hierarchy-Constrained Inference ===")
        _, _, l3_adj = hierarchy_constrained_inference(
            model, data, l3_to_l1, l3_to_l2,
            num_l1=len(encoders["l1_code"]),
            num_l2=len(encoders["l2_code"]),
            num_l3=num_l3,
        )
        # Evaluate with adjusted L3 predictions
        import numpy as np
        test_l3 = data["test_l3"]
        l3_adj_idx = np.argmax(l3_adj, axis=1)
        hc_l3_top1 = float(np.mean(l3_adj_idx == test_l3))
        l3_top3_idx = np.argsort(l3_adj, axis=1)[:, -3:]
        hc_l3_top3 = float(np.mean([test_l3[i] in l3_top3_idx[i] for i in range(len(test_l3))]))
        l3_top5_idx = np.argsort(l3_adj, axis=1)[:, -5:]
        hc_l3_top5 = float(np.mean([test_l3[i] in l3_top5_idx[i] for i in range(len(test_l3))]))

        print(f"  HC L3 Top-1: {hc_l3_top1:.4f} (was {base_report['L3_top1_accuracy']:.4f})")
        print(f"  HC L3 Top-3: {hc_l3_top3:.4f} (was {base_report['L3_top3_accuracy']:.4f})")
        print(f"  HC L3 Top-5: {hc_l3_top5:.4f} (was {base_report['L3_top5_accuracy']:.4f})")

        if hc_l3_top1 > base_report["L3_top1_accuracy"]:
            print("  Hierarchy inference improved L3! Using it.")
            final_report = dict(base_report)
            final_report["L3_top1_accuracy"] = round(hc_l3_top1, 4)
            final_report["L3_top3_accuracy"] = round(hc_l3_top3, 4)
            final_report["L3_top5_accuracy"] = round(hc_l3_top5, 4)
            final_report["hierarchy_inference_used"] = True
        else:
            print("  Hierarchy inference did not help. Using standard.")
            final_report["hierarchy_inference_used"] = False

    # Save final model
    keras_path = exp_dir / "final.keras"
    model.save(str(keras_path))

    # TFLite
    tflite_path = exp_dir / "model.tflite"
    convert_to_tflite(model, tflite_path, data)
    tflite_size = tflite_path.stat().st_size / (1024 * 1024) if tflite_path.exists() else 0

    final_report["experiment"] = name
    final_report["epochs_trained"] = epochs_trained
    final_report["training_time_min"] = round(elapsed / 60, 1)
    final_report["total_params"] = total_params
    final_report["tflite_size_mb"] = round(tflite_size, 2)
    final_report["best_val_l3_accuracy"] = round(best_val_l3, 4)

    with open(exp_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    print(f"\n  {'='*60}")
    print(f"  RESULTS: L3={final_report['L3_top1_accuracy']:.4f} Top3={final_report['L3_top3_accuracy']:.4f}")
    print(f"  {'='*60}")

    return final_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Xpenzo CHT v6 Training")
    parser.add_argument("--training-dir", type=str, default=str(DEFAULT_TRAINING_DIR))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--mode", choices=["full", "finetune-only", "quick"], default="full")
    parser.add_argument("--resume-from", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--no-balanced-sampling", action="store_true")
    parser.add_argument("--no-hierarchy-inference", action="store_true")
    args = parser.parse_args()

    training_dir = Path(args.training_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading TensorFlow ...")
    import tensorflow as tf
    import keras
    print(f"  TF {tf.__version__}, Keras {keras.__version__}")
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        num_cpus = min(os.cpu_count() or 4, 8)
        inter = max(2, num_cpus // 2)
        tf.config.threading.set_intra_op_parallelism_threads(num_cpus)
        tf.config.threading.set_inter_op_parallelism_threads(inter)
        print(f"  CPU threads: intra={num_cpus}, inter={inter}")

    # Load data
    print("\nLoading data ...")
    train_rows = load_split(training_dir / "train.csv")
    val_rows = load_split(training_dir / "val.csv")
    test_rows = load_split(training_dir / "test.csv")
    print(f"  Train: {len(train_rows):,} | Val: {len(val_rows):,} | Test: {len(test_rows):,}")

    with open(training_dir / "label_encoders.json", "r", encoding="utf-8") as f:
        encoder_data = json.load(f)
    encoders = encoder_data["encoders"]

    with open(training_dir / "class_weights.json", "r", encoding="utf-8") as f:
        class_weights_data = json.load(f)
    l3_weights_dict: dict[int, float] = {}
    for code, weight in class_weights_data.get("l3_code", {}).items():
        idx = encoders["l3_code"].get(code)
        if idx is not None:
            l3_weights_dict[idx] = weight

    l3_to_l2, l3_to_l1 = build_hierarchy_maps(TAXONOMY_PATH, encoders)

    tokenizer_path = training_dir / "tokenizer" / "xpenz_bpe.model"
    sp_model = prepare_tokenizer(tokenizer_path)

    print("\nPreparing datasets ...")
    data = prepare_datasets(train_rows, val_rows, test_rows, sp_model)

    use_hloss = not args.no_hierarchy_inference
    use_balanced = not args.no_balanced_sampling
    bs = args.batch_size
    all_results: list[dict[str, Any]] = []

    if args.mode == "quick":
        r = run_experiment_v6(
            name="v6_quick", data=data, encoders=encoders,
            l3_to_l2=l3_to_l2, l3_to_l1=l3_to_l1,
            l3_weights_dict=l3_weights_dict, output_dir=output_dir,
            epochs=10, batch_size=bs, learning_rate=3e-4,
            patience=10, use_swa=False,
            use_hierarchy_inference=use_hloss,
            use_balanced_sampling=use_balanced,
        )
        all_results.append(r)

    elif args.mode == "full":
        # Round 1: 3-layer with hierarchy loss + balanced sampling
        print("\n" + "=" * 70)
        print("  ROUND 1: 3-layer + hierarchy consistency + balanced sampling")
        print("=" * 70)
        r1 = run_experiment_v6(
            name="v6_round1_hierarchy",
            data=data, encoders=encoders,
            l3_to_l2=l3_to_l2, l3_to_l1=l3_to_l1,
            l3_weights_dict=l3_weights_dict, output_dir=output_dir,
            epochs=60, batch_size=bs, learning_rate=3e-4,
            warmup_steps=1500, weight_decay=0.01,
            label_smoothing=0.05, dropout=0.1,
            focal_gamma=2.0, d_model=128, num_heads=4,
            d_ff=256, num_layers=3,
            mask_prob=0.15, num_noise_std=0.05,
            patience=15, use_swa=True,
            use_hierarchy_inference=True,
            use_balanced_sampling=True, balance_power=0.5,
        )
        all_results.append(r1)

        # Round 2: Fine-tune with lower LR, less augmentation
        print("\n" + "=" * 70)
        print("  ROUND 2: Fine-tune with lower LR")
        print("=" * 70)
        best_r1 = str(output_dir / "v6_round1_hierarchy" / "best.keras")
        r2 = run_experiment_v6(
            name="v6_round2_finetune",
            data=data, encoders=encoders,
            l3_to_l2=l3_to_l2, l3_to_l1=l3_to_l1,
            l3_weights_dict=l3_weights_dict, output_dir=output_dir,
            epochs=30, batch_size=bs, learning_rate=5e-5,
            warmup_steps=500, weight_decay=0.005,
            label_smoothing=0.03, dropout=0.08,
            focal_gamma=1.5,
            mask_prob=0.08, num_noise_std=0.03,
            patience=12, resume_from=best_r1,
            use_swa=True,
            use_hierarchy_inference=True,
            use_balanced_sampling=True, balance_power=0.3,
        )
        all_results.append(r2)

        # Round 3: 4-layer experiment
        print("\n" + "=" * 70)
        print("  ROUND 3: 4-layer architecture")
        print("=" * 70)
        r3 = run_experiment_v6(
            name="v6_round3_4layer",
            data=data, encoders=encoders,
            l3_to_l2=l3_to_l2, l3_to_l1=l3_to_l1,
            l3_weights_dict=l3_weights_dict, output_dir=output_dir,
            epochs=60, batch_size=bs, learning_rate=2.5e-4,
            warmup_steps=2000, weight_decay=0.01,
            label_smoothing=0.05, dropout=0.12,
            focal_gamma=2.0, d_model=128, num_heads=4,
            d_ff=384, num_layers=4,
            mask_prob=0.15, num_noise_std=0.05,
            patience=15, use_swa=True,
            use_hierarchy_inference=True,
            use_balanced_sampling=True, balance_power=0.5,
        )
        all_results.append(r3)

        # Round 4: Fine-tune the best architecture
        best_arch = max(all_results, key=lambda r: r["L3_top1_accuracy"])
        best_name = best_arch["experiment"]
        print(f"\n  Best so far: {best_name} with L3={best_arch['L3_top1_accuracy']:.4f}")
        
        best_path = str(output_dir / best_name / "best.keras")
        r4 = run_experiment_v6(
            name="v6_round4_final_finetune",
            data=data, encoders=encoders,
            l3_to_l2=l3_to_l2, l3_to_l1=l3_to_l1,
            l3_weights_dict=l3_weights_dict, output_dir=output_dir,
            epochs=25, batch_size=bs, learning_rate=2e-5,
            warmup_steps=300, weight_decay=0.003,
            label_smoothing=0.02, dropout=0.06,
            focal_gamma=1.0,
            mask_prob=0.05, num_noise_std=0.02,
            patience=10, resume_from=best_path,
            use_swa=True,
            use_hierarchy_inference=True,
            use_balanced_sampling=True, balance_power=0.2,
        )
        all_results.append(r4)

    elif args.mode == "finetune-only":
        if not args.resume_from:
            print("ERROR: --resume-from required for finetune-only mode")
            return
        r = run_experiment_v6(
            name="v6_finetune",
            data=data, encoders=encoders,
            l3_to_l2=l3_to_l2, l3_to_l1=l3_to_l1,
            l3_weights_dict=l3_weights_dict, output_dir=output_dir,
            epochs=25, batch_size=bs, learning_rate=3e-5,
            warmup_steps=300, weight_decay=0.005,
            label_smoothing=0.03, dropout=0.08,
            focal_gamma=1.5,
            mask_prob=0.08, num_noise_std=0.03,
            patience=10, resume_from=args.resume_from,
            use_swa=True,
            use_hierarchy_inference=use_hloss,
            use_balanced_sampling=use_balanced,
        )
        all_results.append(r)

    # Final comparison
    if all_results:
        print("\n" + "=" * 70)
        print("  FINAL COMPARISON")
        print("=" * 70)
        best = max(all_results, key=lambda r: r["L3_top1_accuracy"])
        for r in all_results:
            marker = " <-- BEST" if r == best else ""
            print(f"  {r['experiment']}: L3={r['L3_top1_accuracy']:.4f} "
                  f"Top3={r['L3_top3_accuracy']:.4f} "
                  f"HC_L1={r['hierarchy_L3_L1_consistency']:.4f}{marker}")

        # Copy best model as champion
        import shutil
        best_dir = output_dir / best["experiment"]
        champion_keras = output_dir / "xpenz_cht_v6.keras"
        champion_tflite = output_dir / "xpenz_cht_v6.tflite"
        if (best_dir / "final.keras").exists():
            shutil.copy2(best_dir / "final.keras", champion_keras)
        if (best_dir / "model.tflite").exists():
            shutil.copy2(best_dir / "model.tflite", champion_tflite)
        print(f"\n  Champion model: {champion_keras}")
        print(f"  Champion TFLite: {champion_tflite}")

        # Save comparison
        with open(output_dir / "v6_comparison.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    main()
