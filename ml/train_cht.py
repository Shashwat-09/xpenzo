"""
train_cht.py — Compact Hierarchical Transformer (CHT) training for Xpenzo v3.

Option-A pipeline (post-refactor):
  - Real data: mitulshah/transaction-categorization (4.5M rows) mixed with the
    synthetic L2/L3 generator output.
  - Real teacher: mitulshah/global-financial-transaction-classifier (fine-tuned
    DistilBERT), batched on GPU, soft labels cached to disk.
  - Distillation across all three heads (L1 directly from teacher, L2/L3 via
    taxonomy-tree propagation as a soft prior).
  - Architecture: attention pooling instead of average pooling; shared dense
    bumped 256 → 384 to give the 520-class L3 head more representational room.

Usage:
    # 1. Get data + teacher (one-time)
    python ml/download_hf_resources.py
    python ml/generate_data.py --output data/train.csv --n_samples 200000
    python ml/generate_data.py --output data/val.csv   --n_samples 20000 --seed 99

    # 2. Train tokenizer
    python ml/train_cht.py --mode train_tokenizer --data data/train.csv

    # 3. Train (synthetic only) or train_distill (HF + synthetic + teacher)
    python ml/train_cht.py --mode train_distill

    # 4. Export INT8 TFLite
    python ml/train_cht.py --mode export --checkpoint outputs/cht_best.keras

Outputs land in outputs/:
    xpenz_bpe.model            SentencePiece tokenizer (~150 KB)
    label_encoders.pkl         Sklearn LabelEncoders for L1/L2/L3
    cht_best.keras             Best Keras checkpoint
    xpenz_cht_v3.tflite        INT8-quantized model (target < 5 MB)
"""

from __future__ import annotations

import argparse
import math
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Local modules (added in Option-A refactor)
sys.path.insert(0, str(Path(__file__).parent))
from data_loader import LoaderConfig, load_mixed, load_synthetic_only
from teacher import TeacherConfig, precompute_soft_labels_for_df


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

SEQ_LEN = 32          # Max token sequence length
VOCAB_SIZE = 8192     # SentencePiece BPE vocab size
D_MODEL = 128         # Transformer hidden dimension
NUM_HEADS = 4         # Attention heads
D_FF = 256            # FFN inner dimension
NUM_LAYERS = 3        # Transformer blocks
NUM_FEATURES = 16     # Numerical features
SHARED_DIM = 384      # Shared fusion dim (was 256 — bumped for L3's 520 classes)
DROPOUT = 0.1
BATCH_SIZE = 512
EPOCHS = 30
LR = 3e-4
WARMUP_STEPS = 1000

# Distillation hyperparameters
DISTILL_TEMPERATURE = 4.0   # Higher T = softer teacher distribution
DISTILL_ALPHA = 0.5         # Weight on KL vs hard CE. 0=hard only, 1=soft only

SP_MODEL_PATH = "outputs/xpenz_bpe.model"
CHECKPOINT_PATH = "outputs/cht_best.keras"
TFLITE_PATH = "outputs/xpenz_cht_v3.tflite"


# ─────────────────────────────────────────────────────────────────────────────
# TOKENIZER (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def train_tokenizer(data_path: str):
    """Train SentencePiece BPE tokenizer on merchant names + UPI IDs."""
    import sentencepiece as spm

    os.makedirs("outputs", exist_ok=True)

    df = pd.read_csv(data_path)
    corpus_path = "outputs/merchant_corpus.txt"

    print(f"Building corpus from {len(df):,} rows...")
    with open(corpus_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            f.write(str(row["merchant_name"]).lower().strip() + "\n")
            upi_clean = str(row["upi_id"]).split("@")[0].lower().strip()
            f.write(upi_clean + "\n")

    print("Training SentencePiece BPE tokenizer...")
    spm.SentencePieceTrainer.train(
        input=corpus_path,
        model_prefix="outputs/xpenz_bpe",
        vocab_size=VOCAB_SIZE,
        model_type="bpe",
        character_coverage=0.9998,
        max_sentence_length=128,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        user_defined_symbols=["<sep>", "<amt_low>", "<amt_mid>", "<amt_high>",
                              "<time_morning>", "<time_lunch>", "<time_evening>", "<time_night>"],
        num_threads=8,
        byte_fallback=True,
    )
    print(f"Tokenizer saved -> {SP_MODEL_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# PREPROCESSING (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_merchant(name: str) -> str:
    name = str(name).lower().strip()
    return name.replace("'", "").replace('"', "")


def clean_upi(upi: str) -> str:
    return str(upi).split("@")[0].lower().strip()


def prepare_text_input(merchant: str, upi: str, sp_model, subword_sampling: bool = False) -> np.ndarray:
    """
    Returns int32[32] token ID array.
    Format: <bos> merchant_tokens <sep> upi_tokens <eos> <pad>...

    When subword_sampling=True, SentencePiece uses BPE-dropout-style sampling
    for regularization. Used during training; disabled at inference.
    """
    SEP_ID, BOS_ID, EOS_ID, PAD_ID = 4, 2, 3, 0

    if subword_sampling:
        merchant_ids = sp_model.encode(normalize_merchant(merchant), out_type=int,
                                       enable_sampling=True, alpha=0.1, nbest_size=-1)
        upi_ids = sp_model.encode(clean_upi(upi), out_type=int,
                                  enable_sampling=True, alpha=0.1, nbest_size=-1)
    else:
        merchant_ids = sp_model.encode(normalize_merchant(merchant), out_type=int)
        upi_ids = sp_model.encode(clean_upi(upi), out_type=int)

    token_ids = [BOS_ID] + merchant_ids[:20] + [SEP_ID] + upi_ids[:8] + [EOS_ID]
    token_ids = token_ids[:SEQ_LEN]
    token_ids += [PAD_ID] * (SEQ_LEN - len(token_ids))
    return np.array(token_ids, dtype=np.int32)


def prepare_numerical_features(amount: float, timestamp: str) -> np.ndarray:
    """Returns float32[16] numerical feature vector."""
    try:
        dt = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
    except Exception:
        dt = datetime.now()

    hour = dt.hour
    dow = dt.weekday()
    month = dt.month
    day = dt.day

    amount = float(amount) if amount else 0.0
    if amount < 50:       bucket = 0
    elif amount < 100:    bucket = 1
    elif amount < 200:    bucket = 2
    elif amount < 500:    bucket = 3
    elif amount < 1000:   bucket = 4
    elif amount < 2000:   bucket = 5
    elif amount < 5000:   bucket = 6
    elif amount < 10000:  bucket = 7
    elif amount < 25000:  bucket = 8
    elif amount < 50000:  bucket = 9
    else:                 bucket = 10

    is_round = 1.0 if (amount > 0 and amount % 10 == 0) else 0.0
    is_weekend = 1.0 if dow >= 5 else 0.0
    is_meal_hour = 1.0 if (11 <= hour <= 14 or 19 <= hour <= 22) else 0.0
    is_salary_window = 1.0 if (1 <= day <= 5) else 0.0

    feats = [
        math.log(amount + 1),
        float(bucket) / 10.0,
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
        0.0, 0.0, 0.0, 0.0,
    ]
    return np.array(feats, dtype=np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# ATTENTION POOLING (new)
# ─────────────────────────────────────────────────────────────────────────────

class AttentionPooling(layers.Layer):
    """
    Single-head attention pooling: a learnable query vector attends over the
    token sequence and returns one fixed-size vector. Replaces GlobalAvgPool,
    which weighed every token equally and diluted the strong merchant tokens
    that carry most of the categorical signal.
    """

    def __init__(self, d_model: int, **kwargs):
        super().__init__(**kwargs)
        self.d_model = d_model

    def build(self, input_shape):
        # Learnable query of shape [1, d_model]
        self.query = self.add_weight(
            name="pool_query",
            shape=(1, self.d_model),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.scale = float(self.d_model) ** -0.5
        super().build(input_shape)

    def call(self, x, mask=None):
        # x: [B, T, D];  query: [1, D] -> squeeze to [D]
        q = tf.squeeze(self.query, axis=0)              # [D]
        scores = tf.einsum("d,btd->bt", q, x) * self.scale  # [B, T]
        if mask is not None:
            scores = tf.where(mask, scores, tf.fill(tf.shape(scores), -1e9))
        weights = tf.nn.softmax(scores, axis=-1)        # [B, T]
        pooled = tf.einsum("bt,btd->bd", weights, x)    # [B, D]
        return pooled

    def get_config(self):
        return {**super().get_config(), "d_model": self.d_model}


# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORMER BLOCK (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class TransformerBlock(layers.Layer):
    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_ff = d_ff
        self.dropout = dropout
        self.mha = layers.MultiHeadAttention(num_heads=num_heads, key_dim=d_model // num_heads,
                                             dropout=dropout)
        self.ffn1 = layers.Dense(d_ff, activation="gelu")
        self.ffn2 = layers.Dense(d_model)
        self.ln1 = layers.LayerNormalization(epsilon=1e-6)
        self.ln2 = layers.LayerNormalization(epsilon=1e-6)
        self.drop1 = layers.Dropout(dropout)
        self.drop2 = layers.Dropout(dropout)

    def build(self, input_shape):
        # Explicitly build all sublayers so Keras 3 materialises their variables
        # during model loading — without this, they stay "unbuilt" and are missing
        # from tf.saved_model.save() output.
        self.mha.build(input_shape, input_shape)  # self-attention: query == value
        self.drop1.build(input_shape)
        self.ln1.build(input_shape)
        ffn1_out = list(input_shape[:-1]) + [self.d_ff]
        self.ffn1.build(input_shape)
        self.ffn2.build(ffn1_out)
        self.drop2.build(input_shape)
        self.ln2.build(input_shape)
        super().build(input_shape)

    def call(self, x, training=False):
        attn = self.mha(x, x, training=training)
        x = self.ln1(x + self.drop1(attn, training=training))
        ffn = self.ffn2(self.ffn1(x))
        x = self.ln2(x + self.drop2(ffn, training=training))
        return x

    def get_config(self):
        return {**super().get_config(),
                "d_model": self.d_model, "num_heads": self.num_heads,
                "d_ff": self.d_ff, "dropout": self.dropout}


# ─────────────────────────────────────────────────────────────────────────────
# MODEL BUILDER (modified: attention pooling + larger shared dim)
# ─────────────────────────────────────────────────────────────────────────────

def build_cht_model(num_l1: int, num_l2: int, num_l3: int) -> keras.Model:
    token_ids = keras.Input(shape=(SEQ_LEN,), dtype=tf.int32, name="token_ids")
    num_feats = keras.Input(shape=(NUM_FEATURES,), dtype=tf.float32, name="num_features")

    # Text branch
    token_emb = layers.Embedding(VOCAB_SIZE, D_MODEL, name="token_embedding")(token_ids)
    positions = tf.range(start=0, limit=SEQ_LEN, delta=1)
    pos_emb = layers.Embedding(SEQ_LEN, D_MODEL, name="positional_embedding")(positions)
    x = token_emb + pos_emb
    x = layers.Dropout(DROPOUT)(x)

    for i in range(NUM_LAYERS):
        x = TransformerBlock(D_MODEL, NUM_HEADS, D_FF, DROPOUT, name=f"transformer_{i+1}")(x)

    text_repr = AttentionPooling(D_MODEL, name="attn_pool")(x)  # [B, 128]

    # Numerical branch
    n = layers.Dense(64, activation="relu", name="num_dense1")(num_feats)
    n = layers.LayerNormalization(epsilon=1e-6)(n)
    n = layers.Dense(D_MODEL, activation="relu", name="num_dense2")(n)
    num_repr = layers.LayerNormalization(epsilon=1e-6, name="num_repr")(n)

    # Fusion
    fused = layers.Concatenate(name="fused")([text_repr, num_repr])
    shared = layers.Dense(SHARED_DIM, activation="relu", name="shared_dense")(fused)
    shared = layers.Dropout(0.2)(shared)
    shared = layers.LayerNormalization(epsilon=1e-6, name="shared_norm")(shared)

    # L1 head
    l1_logits = layers.Dense(num_l1, name="l1_dense")(shared)
    l1_probs = layers.Softmax(name="l1_probs")(l1_logits)

    # L2 head — conditioned on L1
    l2_input = layers.Concatenate(name="l2_fused")([shared, l1_probs])
    l2 = layers.Dense(SHARED_DIM, activation="relu", name="l2_dense1")(l2_input)
    l2_logits = layers.Dense(num_l2, name="l2_dense2")(l2)
    l2_probs = layers.Softmax(name="l2_probs")(l2_logits)

    # L3 head — conditioned on L2
    l3_input = layers.Concatenate(name="l3_fused")([shared, l2_probs])
    l3 = layers.Dense(512, activation="relu", name="l3_dense1")(l3_input)
    l3 = layers.Dropout(0.15)(l3)
    l3_logits = layers.Dense(num_l3, name="l3_dense2")(l3)
    l3_probs = layers.Softmax(name="l3_probs")(l3_logits)

    return keras.Model(
        inputs={"token_ids": token_ids, "num_features": num_feats},
        outputs={"l1_probs": l1_probs, "l2_probs": l2_probs, "l3_probs": l3_probs},
        name="CHT_v3",
    )


# ─────────────────────────────────────────────────────────────────────────────
# LR SCHEDULE (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class WarmupCosineDecay(keras.optimizers.schedules.LearningRateSchedule):
    def __init__(self, peak_lr: float, warmup_steps: int, total_steps: int):
        super().__init__()
        self.peak_lr = peak_lr
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps

    def __call__(self, step):
        step = tf.cast(step, tf.float32)
        warmup = self.peak_lr * step / self.warmup_steps
        cosine = self.peak_lr * 0.5 * (
            1 + tf.cos(math.pi * (step - self.warmup_steps) / (self.total_steps - self.warmup_steps))
        )
        return tf.where(step < self.warmup_steps, warmup, cosine)

    def get_config(self):
        return {"peak_lr": self.peak_lr, "warmup_steps": self.warmup_steps, "total_steps": self.total_steps}


# ─────────────────────────────────────────────────────────────────────────────
# DISTILLATION MODEL (new — custom train_step that mixes CE + KL with masking)
# ─────────────────────────────────────────────────────────────────────────────

class DistillCHT(keras.Model):
    """
    Wraps the CHT model with a custom train/test step that:
      1. Computes per-head categorical CE against hard one-hot labels.
      2. Computes per-head KL divergence against teacher soft labels,
         scaled by T² (standard Hinton distillation correction).
      3. Combines: loss_head = (1-α)·CE + α·T²·KL
      4. Multiplies L2 and L3 losses by the `has_l2_l3` per-sample mask so HF
         rows (which lack L2/L3 ground truth) don't drag the deeper heads.

    Inputs are passed via the standard fit() signature:
        x  = {"token_ids", "num_features"}
        y  = {"hard_l1", "hard_l2", "hard_l3", "soft_l1", "soft_l2", "soft_l3", "mask"}
    """

    HEAD_WEIGHTS = {"l1": 0.2, "l2": 0.3, "l3": 0.5}

    def __init__(self, inner: keras.Model, temperature: float, alpha: float, **kwargs):
        super().__init__(**kwargs)
        self.inner = inner
        self.temperature = float(temperature)
        self.alpha = float(alpha)
        self._kl = keras.losses.KLDivergence(reduction="none")
        self._ce = keras.losses.CategoricalCrossentropy(label_smoothing=0.1, reduction="none")

        # Track per-head losses + accuracies for logging
        self._loss_trackers = {
            head: keras.metrics.Mean(name=f"{head}_loss") for head in ("l1", "l2", "l3")
        }
        self._acc_trackers = {
            head: keras.metrics.CategoricalAccuracy(name=f"{head}_acc") for head in ("l1", "l2", "l3")
        }
        self._total_tracker = keras.metrics.Mean(name="loss")

    @property
    def metrics(self):
        return [self._total_tracker, *self._loss_trackers.values(), *self._acc_trackers.values()]

    def call(self, inputs, training=False):
        return self.inner(inputs, training=training)

    def _per_head_loss(self, head: str, hard: tf.Tensor, soft: tf.Tensor,
                       preds: tf.Tensor, mask: tf.Tensor) -> tf.Tensor:
        """
        hard:  [B, C] one-hot ground truth (zeros if absent — masked away)
        soft:  [B, C] teacher distribution
        preds: [B, C] student softmax
        mask:  [B] 1.0 if this sample has ground truth for this head, else 0.0
        Returns scalar (mean over batch with mask applied).
        """
        ce = self._ce(hard, preds)                              # [B]
        kl = self._kl(soft, preds) * (self.temperature ** 2)    # [B]
        combined = (1.0 - self.alpha) * ce + self.alpha * kl    # [B]
        # Safely average over the masked subset; if mask sums to 0, return 0.
        denom = tf.reduce_sum(mask) + 1e-6
        return tf.reduce_sum(combined * mask) / denom

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            preds = self.inner(x, training=True)
            # L1 has hard labels for ALL rows (HF + synthetic)
            mask_l1 = tf.ones_like(y["mask"])
            mask_l23 = y["mask"]

            losses = {
                "l1": self._per_head_loss("l1", y["hard_l1"], y["soft_l1"], preds["l1_probs"], mask_l1),
                "l2": self._per_head_loss("l2", y["hard_l2"], y["soft_l2"], preds["l2_probs"], mask_l23),
                "l3": self._per_head_loss("l3", y["hard_l3"], y["soft_l3"], preds["l3_probs"], mask_l23),
            }
            total = sum(self.HEAD_WEIGHTS[h] * losses[h] for h in ("l1", "l2", "l3"))

        grads = tape.gradient(total, self.inner.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.inner.trainable_variables))

        self._total_tracker.update_state(total)
        for h in ("l1", "l2", "l3"):
            self._loss_trackers[h].update_state(losses[h])
            # Accuracy is only meaningful where we have hard labels (mask applies for L2/L3)
            mask = mask_l1 if h == "l1" else mask_l23
            self._acc_trackers[h].update_state(y[f"hard_{h}"], preds[f"{h}_probs"], sample_weight=mask)

        return {m.name: m.result() for m in self.metrics}

    def test_step(self, data):
        x, y = data
        preds = self.inner(x, training=False)
        mask_l1 = tf.ones_like(y["mask"])
        mask_l23 = y["mask"]
        losses = {
            "l1": self._per_head_loss("l1", y["hard_l1"], y["soft_l1"], preds["l1_probs"], mask_l1),
            "l2": self._per_head_loss("l2", y["hard_l2"], y["soft_l2"], preds["l2_probs"], mask_l23),
            "l3": self._per_head_loss("l3", y["hard_l3"], y["soft_l3"], preds["l3_probs"], mask_l23),
        }
        total = sum(self.HEAD_WEIGHTS[h] * losses[h] for h in ("l1", "l2", "l3"))

        self._total_tracker.update_state(total)
        for h in ("l1", "l2", "l3"):
            self._loss_trackers[h].update_state(losses[h])
            mask = mask_l1 if h == "l1" else mask_l23
            self._acc_trackers[h].update_state(y[f"hard_{h}"], preds[f"{h}_probs"], sample_weight=mask)

        return {m.name: m.result() for m in self.metrics}


# ─────────────────────────────────────────────────────────────────────────────
# DATASET BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _featurize_rows(df: pd.DataFrame, sp_model, l1_enc, l2_enc, l3_enc):
    """Convert a DataFrame into the numpy arrays the model expects."""
    n = len(df)
    token_arr = np.zeros((n, SEQ_LEN), dtype=np.int32)
    feat_arr = np.zeros((n, NUM_FEATURES), dtype=np.float32)
    l1_arr = np.full(n, -1, dtype=np.int32)
    l2_arr = np.full(n, -1, dtype=np.int32)
    l3_arr = np.full(n, -1, dtype=np.int32)
    mask_arr = np.zeros(n, dtype=np.float32)

    l1_classes = set(l1_enc.classes_)
    l2_classes = set(l2_enc.classes_)
    l3_classes = set(l3_enc.classes_)

    for i, (_, row) in enumerate(tqdm(df.iterrows(), total=n, desc="featurize")):
        token_arr[i] = prepare_text_input(row["merchant_name"], row["upi_id"], sp_model,
                                          subword_sampling=True)
        feat_arr[i] = prepare_numerical_features(row.get("amount", 0.0), row.get("timestamp", ""))
        if row["l1_label"] in l1_classes:
            l1_arr[i] = int(l1_enc.transform([row["l1_label"]])[0])
        if row.get("has_l2_l3", True):
            if row["l2_label"] in l2_classes:
                l2_arr[i] = int(l2_enc.transform([row["l2_label"]])[0])
            if row["l3_label"] in l3_classes:
                l3_arr[i] = int(l3_enc.transform([row["l3_label"]])[0])
            mask_arr[i] = 1.0 if (l2_arr[i] >= 0 and l3_arr[i] >= 0) else 0.0
    return token_arr, feat_arr, l1_arr, l2_arr, l3_arr, mask_arr


def _to_distill_dataset(df, sp_model, l1_enc, l2_enc, l3_enc,
                        soft_labels: dict[str, np.ndarray], batch_size: int, shuffle: bool):
    """tf.data.Dataset emitting (inputs_dict, targets_dict_with_soft_and_mask)."""
    token_arr, feat_arr, l1_arr, l2_arr, l3_arr, mask_arr = _featurize_rows(
        df, sp_model, l1_enc, l2_enc, l3_enc
    )
    num_l1 = len(l1_enc.classes_)
    num_l2 = len(l2_enc.classes_)
    num_l3 = len(l3_enc.classes_)

    # Zero-out hard label one-hots where index is -1 (absent).
    def safe_one_hot(idx_arr, depth):
        oh = np.zeros((len(idx_arr), depth), dtype=np.float32)
        valid = idx_arr >= 0
        oh[valid, idx_arr[valid]] = 1.0
        return oh

    targets = {
        "hard_l1": safe_one_hot(l1_arr, num_l1),
        "hard_l2": safe_one_hot(l2_arr, num_l2),
        "hard_l3": safe_one_hot(l3_arr, num_l3),
        "soft_l1": soft_labels["l1"].astype(np.float32),
        "soft_l2": soft_labels["l2"].astype(np.float32),
        "soft_l3": soft_labels["l3"].astype(np.float32),
        "mask":    mask_arr,
    }
    inputs = {"token_ids": token_arr, "num_features": feat_arr}

    ds = tf.data.Dataset.from_tensor_slices((inputs, targets))
    if shuffle:
        ds = ds.shuffle(10_000)
    return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)


def _to_plain_dataset(df, sp_model, l1_enc, l2_enc, l3_enc, batch_size: int, shuffle: bool):
    """Non-distillation dataset for the plain `--mode train` path."""
    token_arr, feat_arr, l1_arr, l2_arr, l3_arr, _ = _featurize_rows(df, sp_model, l1_enc, l2_enc, l3_enc)
    num_l1, num_l2, num_l3 = len(l1_enc.classes_), len(l2_enc.classes_), len(l3_enc.classes_)
    inputs = {"token_ids": token_arr, "num_features": feat_arr}
    targets = {
        "l1_probs": tf.one_hot(np.maximum(l1_arr, 0), depth=num_l1),
        "l2_probs": tf.one_hot(np.maximum(l2_arr, 0), depth=num_l2),
        "l3_probs": tf.one_hot(np.maximum(l3_arr, 0), depth=num_l3),
    }
    ds = tf.data.Dataset.from_tensor_slices((inputs, targets))
    if shuffle:
        ds = ds.shuffle(10_000)
    return ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING ENTRY POINTS
# ─────────────────────────────────────────────────────────────────────────────

def _fit_encoders(df: pd.DataFrame) -> tuple[LabelEncoder, LabelEncoder, LabelEncoder]:
    l1_enc = LabelEncoder().fit(df["l1_label"][df["l1_label"].notna() & (df["l1_label"] != "")])
    has_l23 = df["has_l2_l3"] if "has_l2_l3" in df.columns else pd.Series([True] * len(df))
    df_l23 = df[has_l23 & df["l2_label"].notna() & (df["l2_label"] != "")]
    l2_enc = LabelEncoder().fit(df_l23["l2_label"])
    l3_enc = LabelEncoder().fit(df_l23["l3_label"])
    return l1_enc, l2_enc, l3_enc


def _save_encoders(l1, l2, l3):
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/label_encoders.pkl", "wb") as f:
        pickle.dump({"l1": l1, "l2": l2, "l3": l3}, f)
    print("[train] Label encoders saved -> outputs/label_encoders.pkl")


def _load_sp_model():
    import sentencepiece as spm
    sp = spm.SentencePieceProcessor()
    sp.load(SP_MODEL_PATH)
    return sp


def _build_callbacks(monitor: str):
    return [
        keras.callbacks.ModelCheckpoint(CHECKPOINT_PATH, monitor=monitor,
                                        save_best_only=True, mode="max", verbose=1),
        keras.callbacks.EarlyStopping(monitor=monitor, patience=5,
                                      restore_best_weights=True, verbose=1, mode="max"),
        # ReduceLROnPlateau removed — incompatible with LearningRateSchedule optimizer
        keras.callbacks.TensorBoard(log_dir="outputs/logs", histogram_freq=0),
    ]


def train(data_path: str = "data/train.csv", val_path: str | None = "data/val.csv"):
    """Synthetic-only training, no distillation. Fast path for sanity checks."""
    os.makedirs("outputs", exist_ok=True)
    cfg = LoaderConfig(
        synthetic_train_csv=Path(data_path),
        synthetic_val_csv=Path(val_path) if val_path else None,
    )
    train_df, val_df = load_synthetic_only(cfg)
    l1_enc, l2_enc, l3_enc = _fit_encoders(train_df)
    _save_encoders(l1_enc, l2_enc, l3_enc)
    print(f"[train] Labels: L1={len(l1_enc.classes_)}, L2={len(l2_enc.classes_)}, L3={len(l3_enc.classes_)}")

    sp = _load_sp_model()
    train_ds = _to_plain_dataset(train_df, sp, l1_enc, l2_enc, l3_enc, BATCH_SIZE, shuffle=True)
    val_ds = _to_plain_dataset(val_df, sp, l1_enc, l2_enc, l3_enc, BATCH_SIZE, shuffle=False) if val_df is not None else None

    model = build_cht_model(len(l1_enc.classes_), len(l2_enc.classes_), len(l3_enc.classes_))
    model.summary()

    total_steps = max(len(train_df) // BATCH_SIZE * EPOCHS, WARMUP_STEPS + 100)
    lr_schedule = WarmupCosineDecay(LR, WARMUP_STEPS, total_steps)
    model.compile(
        optimizer=keras.optimizers.Adam(lr_schedule, clipnorm=1.0),
        loss={
            "l1_probs": keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
            "l2_probs": keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
            "l3_probs": keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        },
        loss_weights={"l1_probs": 0.2, "l2_probs": 0.3, "l3_probs": 0.5},
        metrics={"l1_probs": "accuracy", "l2_probs": "accuracy", "l3_probs": "accuracy"},
    )

    monitor = "val_l3_probs_accuracy" if val_ds else "l3_probs_accuracy"
    model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS, callbacks=_build_callbacks(monitor))
    print(f"[train] Done. Best checkpoint -> {CHECKPOINT_PATH}")


def train_distill(temperature: float = DISTILL_TEMPERATURE, alpha: float = DISTILL_ALPHA):
    """
    Full Option-A pipeline: mixed HF + synthetic data, real fine-tuned teacher,
    distillation across all three heads with per-sample L2/L3 masking.
    """
    os.makedirs("outputs", exist_ok=True)

    # 1. Load mixed corpus
    cfg = LoaderConfig()
    train_df, val_df = load_mixed(cfg)

    # 2. Fit encoders (L1 covers HF+synth; L2/L3 covers synthetic-labeled rows only)
    l1_enc, l2_enc, l3_enc = _fit_encoders(train_df)
    _save_encoders(l1_enc, l2_enc, l3_enc)
    print(f"[distill] Labels: L1={len(l1_enc.classes_)}, L2={len(l2_enc.classes_)}, L3={len(l3_enc.classes_)}")

    # 3. Compute teacher soft labels (cached on disk after first run)
    from generate_data import TAXONOMY
    print("[distill] Precomputing teacher soft labels for train set...")
    soft_train = precompute_soft_labels_for_df(
        train_df, l1_enc, l2_enc, l3_enc, TAXONOMY,
        TeacherConfig(temperature=temperature),
    )
    print("[distill] Precomputing teacher soft labels for val set...")
    soft_val = precompute_soft_labels_for_df(
        val_df, l1_enc, l2_enc, l3_enc, TAXONOMY,
        TeacherConfig(temperature=temperature),
    )

    # 4. Build tf.data pipelines
    sp = _load_sp_model()
    train_ds = _to_distill_dataset(train_df, sp, l1_enc, l2_enc, l3_enc,
                                    soft_train, BATCH_SIZE, shuffle=True)
    val_ds = _to_distill_dataset(val_df, sp, l1_enc, l2_enc, l3_enc,
                                  soft_val, BATCH_SIZE, shuffle=False)

    # 5. Build & wrap model
    inner = build_cht_model(len(l1_enc.classes_), len(l2_enc.classes_), len(l3_enc.classes_))
    inner.summary()
    model = DistillCHT(inner, temperature=temperature, alpha=alpha)

    total_steps = max(len(train_df) // BATCH_SIZE * EPOCHS, WARMUP_STEPS + 100)
    lr_schedule = WarmupCosineDecay(LR, WARMUP_STEPS, total_steps)
    model.compile(optimizer=keras.optimizers.Adam(lr_schedule, clipnorm=1.0))

    # 6. Train. Monitor val L3 accuracy since it's the hardest head.
    # We deliberately skip ModelCheckpoint here: the DistillCHT wrapper isn't
    # cleanly serializable, and EarlyStopping(restore_best_weights=True)
    # already gives us the best epoch's weights at the end of training.
    monitor = "val_l3_acc"
    callbacks = [
        keras.callbacks.EarlyStopping(monitor=monitor, patience=5,
                                      restore_best_weights=True, verbose=1, mode="max"),
        keras.callbacks.ReduceLROnPlateau(monitor=monitor, factor=0.5, patience=3,
                                          min_lr=1e-6, verbose=1, mode="max"),
        keras.callbacks.TensorBoard(log_dir="outputs/logs_distill", histogram_freq=0),
    ]

    print(f"\n[distill] Training for up to {EPOCHS} epochs "
          f"(batch={BATCH_SIZE}, T={temperature}, α={alpha})...")
    model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS, callbacks=callbacks)

    # Save the inner model — what export_tflite() expects to load.
    inner.save(CHECKPOINT_PATH)
    print(f"[distill] Done. Inner checkpoint (best weights) -> {CHECKPOINT_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# TFLITE EXPORT (preserved with custom-objects update)
# ─────────────────────────────────────────────────────────────────────────────

def export_tflite(checkpoint_path: str):
    """Load saved Keras model and export to FP16-quantized TFLite."""
    import shutil, tempfile

    print(f"Loading checkpoint: {checkpoint_path}")
    model = keras.models.load_model(checkpoint_path, custom_objects={
        "TransformerBlock": TransformerBlock,
        "AttentionPooling": AttentionPooling,
        "WarmupCosineDecay": WarmupCosineDecay,
    })

    # Warmup: forces Keras 3 to materialise all sublayer variables.
    # TransformerBlock now has build(), so tf.saved_model.save() captures all weights.
    dummy_tokens = np.zeros((1, SEQ_LEN), dtype=np.int32)
    dummy_feats = np.zeros((1, NUM_FEATURES), dtype=np.float32)
    _ = model({"token_ids": dummy_tokens, "num_features": dummy_feats}, training=False)
    total_params = sum(v.numpy().size for v in model.variables)
    print(f"Warmup done: {total_params:,} params materialised.")

    # Save as SavedModel, then convert to TFLite.
    saved_model_dir = tempfile.mkdtemp(prefix="cht_saved_model_")
    print(f"Saving to SavedModel: {saved_model_dir}")
    model.export(saved_model_dir)

    # Report saved model size so we can diagnose weight-capture issues.
    sm_bytes = sum(f.stat().st_size for f in __import__('pathlib').Path(saved_model_dir).rglob('*') if f.is_file())
    print(f"SavedModel size on disk: {sm_bytes/1024/1024:.2f} MB")

    print("Converting to TFLite (FP16 quantization)...")
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()

    shutil.rmtree(saved_model_dir, ignore_errors=True)

    os.makedirs(os.path.dirname(TFLITE_PATH), exist_ok=True)
    with open(TFLITE_PATH, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"TFLite model saved -> {TFLITE_PATH}  ({size_mb:.2f} MB)")
    if size_mb > 5.0:
        print(f"WARNING: Model size {size_mb:.2f} MB exceeds 5MB budget!")
    else:
        print(f"Size budget: OK ({size_mb:.2f} MB / 5.0 MB)")

    print("\nVerifying TFLite inference...")
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()
    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()
    print(f"Inputs:  {[inp['name'] for inp in inputs]}")
    print(f"Outputs: {[out['name'] for out in outputs]}")

    token_ids = np.zeros((1, SEQ_LEN), dtype=np.int32)
    num_feats = np.zeros((1, NUM_FEATURES), dtype=np.float32)
    # Match inputs by name — order may vary depending on export method.
    for inp in inputs:
        if inp["dtype"] == np.int32:
            interpreter.set_tensor(inp["index"], token_ids)
        else:
            interpreter.set_tensor(inp["index"], num_feats)

    import time
    t0 = time.perf_counter()
    interpreter.invoke()
    elapsed_ms = (time.perf_counter() - t0) * 1000

    for out in outputs:
        data = interpreter.get_tensor(out["index"])
        print(f"  {out['name']}: shape={data.shape}, top1_idx={data.argmax()}")

    print(f"Inference time: {elapsed_ms:.1f} ms")
    if elapsed_ms > 100:
        print(f"WARNING: Inference {elapsed_ms:.1f} ms exceeds 100ms budget!")
    else:
        print(f"Latency budget: OK ({elapsed_ms:.1f} ms / 100 ms)")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train / Export Xpenzo CHT Model")
    parser.add_argument("--mode", choices=["train_tokenizer", "train", "train_distill", "export"], required=True)
    parser.add_argument("--data", default="data/train.csv",
                        help="Training CSV (synthetic). Used by train_tokenizer and train modes.")
    parser.add_argument("--val", default="data/val.csv", help="Validation CSV.")
    parser.add_argument("--checkpoint", default=CHECKPOINT_PATH)
    parser.add_argument("--temperature", type=float, default=DISTILL_TEMPERATURE,
                        help=f"Distillation temperature (default {DISTILL_TEMPERATURE})")
    parser.add_argument("--alpha", type=float, default=DISTILL_ALPHA,
                        help=f"Weight on KL vs CE (default {DISTILL_ALPHA})")
    args = parser.parse_args()

    if args.mode == "train_tokenizer":
        train_tokenizer(args.data)
    elif args.mode == "train":
        train(args.data, args.val)
    elif args.mode == "train_distill":
        train_distill(temperature=args.temperature, alpha=args.alpha)
    elif args.mode == "export":
        export_tflite(args.checkpoint)


if __name__ == "__main__":
    main()
