"""Re-evaluate v3 model on current enriched test set for fair comparison."""
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportReturnType=false, reportUnknownParameterType=false
import json, os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from typing import Any
import numpy as np
import keras  # type: ignore[import-untyped]
import sentencepiece as spm  # type: ignore[import-untyped]

# Load tokenizer and data
TRAIN_DIR = "ml/training"
MODELS_DIR = "ml/models"

sp = spm.SentencePieceProcessor()
sp.Load(f"{TRAIN_DIR}/tokenizer/xpenz_bpe.model")

def tokenize(text: str, max_len: int = 32) -> list[int]:
    ids: list[int] = sp.EncodeAsIds(text)
    if len(ids) > max_len: ids = ids[:max_len]
    else: ids = ids + [0] * (max_len - len(ids))
    return ids

# Load test data
import csv
with open(f"{TRAIN_DIR}/test.csv") as f:
    test_rows = list(csv.DictReader(f))

print(f"Test set: {len(test_rows)} samples")

tokens: list[list[int]] = []
nums: list[list[float]] = []
l1s_list: list[int] = []
l2s_list: list[int] = []
l3s_list: list[int] = []
for row in test_rows:
    tokens.append(tokenize(row.get("text_normalized", "")))
    nf: list[float] = json.loads(row.get("num_features", "[]"))
    if len(nf) < 16: nf += [0.0] * (16 - len(nf))
    nums.append(nf[:16])
    l1s_list.append(int(row.get("l1_label", "0")))
    l2s_list.append(int(row.get("l2_label", "0")))
    l3s_list.append(int(row.get("l3_label", "0")))

tokens_arr = np.array(tokens, dtype=np.int32)
nums_arr = np.array(nums, dtype=np.float32)
l1s = np.array(l1s_list, dtype=np.int32)
l2s = np.array(l2s_list, dtype=np.int32)
l3s = np.array(l3s_list, dtype=np.int32)

# Load v3 model
print("Loading v3 model...")
model: Any = keras.models.load_model(f"{MODELS_DIR}/xpenz_cht_v3_best.keras", compile=False)

# Predict
l1_pred, l2_pred, l3_pred = model.predict([tokens_arr, nums_arr], batch_size=512, verbose=0)

l1_idx = np.argmax(l1_pred, axis=1)
l2_idx = np.argmax(l2_pred, axis=1)
l3_idx = np.argmax(l3_pred, axis=1)

l1_top1 = float(np.mean(l1_idx == l1s))
l2_top1 = float(np.mean(l2_idx == l2s))
l3_top1 = float(np.mean(l3_idx == l3s))

l3_top3_idx = np.argsort(l3_pred, axis=1)[:, -3:]
l3_top3 = float(np.mean([l3s[i] in l3_top3_idx[i] for i in range(len(l3s))]))
l3_top5_idx = np.argsort(l3_pred, axis=1)[:, -5:]
l3_top5 = float(np.mean([l3s[i] in l3_top5_idx[i] for i in range(len(l3s))]))

print(f"\n=== v3 on current enriched test set ({len(test_rows)} samples) ===")
print(f"  L1 Top-1: {l1_top1:.4f}")
print(f"  L2 Top-1: {l2_top1:.4f}")
print(f"  L3 Top-1: {l3_top1:.4f}")
print(f"  L3 Top-3: {l3_top3:.4f}")
print(f"  L3 Top-5: {l3_top5:.4f}")
