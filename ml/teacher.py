"""
teacher.py — Knowledge-distillation teacher wrapper.

Wraps `mitulshah/global-financial-transaction-classifier` (a DistilBERT fine-tuned
on the same 10-category schema we map to Xpenzo's L1). Provides:

  - Batched GPU inference over a DataFrame.
  - On-disk cache keyed by (model_id, text_hash, temperature) so re-runs are free.
  - L1 soft labels aligned to Xpenzo's L1 encoder.
  - Optional L2/L3 prior propagation: each teacher L1 prediction spreads
    uniformly to its children in the taxonomy tree, giving the deeper heads
    a soft prior even though the teacher has no L2/L3 knowledge.

The previous train_cht.py loaded `distilbert-base-uncased` (no classification
head trained on financial data) and ran inference one row at a time — that was
both incorrect and unworkably slow.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

from data_loader import HF_TO_L1


TEACHER_MODEL_ID = "mitulshah/global-financial-transaction-classifier"
DEFAULT_LOCAL_DIR = Path("models/teacher")
CACHE_DIR = Path("outputs/distill_cache")


@dataclass
class TeacherConfig:
    model_id: str = TEACHER_MODEL_ID
    local_dir: Path = DEFAULT_LOCAL_DIR
    batch_size: int = 64
    temperature: float = 4.0
    max_length: int = 64
    device: str | None = None   # None -> auto-detect
    cache_dir: Path = CACHE_DIR


def _load_teacher(cfg: TeacherConfig):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    src = str(cfg.local_dir) if cfg.local_dir.exists() and any(cfg.local_dir.iterdir()) else cfg.model_id
    print(f"[teacher] Loading {src}...")
    tokenizer = AutoTokenizer.from_pretrained(src)
    model = AutoModelForSequenceClassification.from_pretrained(src)
    model.eval()
    device = cfg.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"[teacher] Loaded on {device}. {model.config.num_labels} output classes.")
    return tokenizer, model, device


def _build_teacher_to_l1_matrix(
    teacher_id2label: dict[int, str],
    l1_encoder: LabelEncoder,
) -> tuple[np.ndarray, list[int]]:
    """
    Build a [num_teacher_classes, num_l1] matrix that, when applied to a
    teacher softmax row, produces an L1 distribution over the encoder's classes.
    Mass from teacher classes outside our mapping (e.g. "Income") is dropped.
    """
    num_teacher = len(teacher_id2label)
    num_l1 = len(l1_encoder.classes_)
    mat = np.zeros((num_teacher, num_l1), dtype=np.float32)
    mapped_indices = []
    for tid, tlabel in teacher_id2label.items():
        xpenzo_l1 = HF_TO_L1.get(tlabel)
        if xpenzo_l1 is None:
            continue
        try:
            l1_idx = int(l1_encoder.transform([xpenzo_l1])[0])
        except ValueError:
            continue
        mat[int(tid), l1_idx] = 1.0
        mapped_indices.append(int(tid))
    return mat, mapped_indices


def _cache_key(texts: Sequence[str], cfg: TeacherConfig) -> str:
    h = hashlib.sha256()
    h.update(cfg.model_id.encode())
    h.update(str(cfg.temperature).encode())
    h.update(str(len(texts)).encode())
    # Sample of texts for keying — full hash would be expensive on 4M rows.
    for t in list(texts[:64]) + list(texts[-64:]):
        h.update(str(t).encode())
    return h.hexdigest()[:16]


def compute_soft_l1(
    texts: Sequence[str],
    l1_encoder: LabelEncoder,
    cfg: TeacherConfig | None = None,
) -> np.ndarray:
    """
    Returns float32 array of shape [len(texts), num_l1] giving the teacher's
    temperature-scaled softmax remapped to Xpenzo's L1 label space.

    Cached to disk — second call with the same inputs is a file read.
    """
    cfg = cfg or TeacherConfig()
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)
    key = _cache_key(texts, cfg)
    cache_path = cfg.cache_dir / f"soft_l1_{key}.npz"
    if cache_path.exists():
        print(f"[teacher] Cache hit → {cache_path.name}")
        return np.load(cache_path)["soft_l1"]

    tokenizer, model, device = _load_teacher(cfg)
    mat, _ = _build_teacher_to_l1_matrix(model.config.id2label, l1_encoder)

    num_l1 = len(l1_encoder.classes_)
    out = np.zeros((len(texts), num_l1), dtype=np.float32)

    print(f"[teacher] Running inference: {len(texts):,} rows, batch_size={cfg.batch_size}")
    with torch.no_grad():
        for start in tqdm(range(0, len(texts), cfg.batch_size)):
            batch = [str(t) for t in texts[start:start + cfg.batch_size]]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=cfg.max_length,
                return_tensors="pt",
            ).to(device)
            logits = model(**enc).logits / cfg.temperature
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            mapped = probs @ mat  # [B, num_l1]
            # Renormalize after dropping unmapped teacher classes (e.g. Income).
            row_sums = mapped.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1.0
            mapped = mapped / row_sums
            out[start:start + len(batch)] = mapped.astype(np.float32)

    np.savez_compressed(cache_path, soft_l1=out)
    print(f"[teacher] Cached → {cache_path.name}")
    return out


def propagate_to_l2_l3(
    soft_l1: np.ndarray,
    l1_encoder: LabelEncoder,
    l2_encoder: LabelEncoder,
    l3_encoder: LabelEncoder,
    taxonomy: dict[str, dict[str, list[str]]],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Propagate teacher's L1 distribution down the taxonomy: mass on each L1
    spreads uniformly to its L2 children, then to L3 leaves.

    This is a coarse but cheap prior. It anchors the deeper heads to respect
    the L1 partition the teacher predicts, without claiming the teacher knows
    anything specific about L2/L3 (it doesn't — it only sees 10 classes).
    """
    num_l1 = len(l1_encoder.classes_)
    num_l2 = len(l2_encoder.classes_)
    num_l3 = len(l3_encoder.classes_)

    # Build L1 -> [L2 indices] and L1 -> [L3 indices] from the taxonomy.
    l1_to_l2: dict[int, list[int]] = {i: [] for i in range(num_l1)}
    l1_to_l3: dict[int, list[int]] = {i: [] for i in range(num_l1)}

    for l1_name, subtree in taxonomy.items():
        try:
            l1_idx = int(l1_encoder.transform([l1_name])[0])
        except ValueError:
            continue
        for l2_name, leaves in subtree.items():
            try:
                l2_idx = int(l2_encoder.transform([l2_name])[0])
                l1_to_l2[l1_idx].append(l2_idx)
            except ValueError:
                pass
            for l3_name in leaves:
                try:
                    l3_idx = int(l3_encoder.transform([l3_name])[0])
                    l1_to_l3[l1_idx].append(l3_idx)
                except ValueError:
                    pass

    # Build broadcast matrices.
    l2_mat = np.zeros((num_l1, num_l2), dtype=np.float32)
    l3_mat = np.zeros((num_l1, num_l3), dtype=np.float32)
    for l1_idx in range(num_l1):
        l2_kids = l1_to_l2.get(l1_idx, [])
        l3_kids = l1_to_l3.get(l1_idx, [])
        if l2_kids:
            l2_mat[l1_idx, l2_kids] = 1.0 / len(l2_kids)
        if l3_kids:
            l3_mat[l1_idx, l3_kids] = 1.0 / len(l3_kids)

    soft_l2 = soft_l1 @ l2_mat
    soft_l3 = soft_l1 @ l3_mat

    # Replace empty rows (no taxonomy match for that L1) with uniform.
    def _safe_norm(x: np.ndarray) -> np.ndarray:
        row_sum = x.sum(axis=1, keepdims=True)
        empty = (row_sum == 0).flatten()
        if empty.any():
            x[empty] = 1.0 / x.shape[1]
            row_sum = x.sum(axis=1, keepdims=True)
        return x / row_sum

    return _safe_norm(soft_l2), _safe_norm(soft_l3)


def precompute_soft_labels_for_df(
    df: pd.DataFrame,
    l1_encoder: LabelEncoder,
    l2_encoder: LabelEncoder,
    l3_encoder: LabelEncoder,
    taxonomy: dict[str, dict[str, list[str]]],
    cfg: TeacherConfig | None = None,
) -> dict[str, np.ndarray]:
    """
    Compute soft labels for all three heads on the full training frame.
    Text fed to teacher = "merchant_name upi_id" to match production inputs.
    """
    cfg = cfg or TeacherConfig()
    texts = (df["merchant_name"].astype(str) + " " + df["upi_id"].astype(str)).tolist()
    soft_l1 = compute_soft_l1(texts, l1_encoder, cfg)
    soft_l2, soft_l3 = propagate_to_l2_l3(soft_l1, l1_encoder, l2_encoder, l3_encoder, taxonomy)
    return {"l1": soft_l1, "l2": soft_l2, "l3": soft_l3}
