"""Re-evaluate v4_round1 on current test set."""
# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportReturnType=false, reportUnknownParameterType=false
import json, os, csv
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
from typing import Any
import numpy as np
import keras  # type: ignore[import-untyped]
import sentencepiece as spm  # type: ignore[import-untyped]

TRAIN_DIR = "ml/training"
sp = spm.SentencePieceProcessor()
sp.Load(f"{TRAIN_DIR}/tokenizer/xpenz_bpe.model")

def tokenize(text: str, max_len: int = 32) -> list[int]:
    ids: list[int] = sp.EncodeAsIds(text)
    if len(ids) > max_len: ids = ids[:max_len]
    else: ids = ids + [0] * (max_len - len(ids))
    return ids

with open(f"{TRAIN_DIR}/test.csv") as f:
    test_rows = list(csv.DictReader(f))

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

for model_name in ["v4_round1_3layer/best.keras", "quick_test/best.keras", "v5_round1_3layer/best.keras"]:
    path = f"ml/models/{model_name}"
    if not os.path.exists(path):
        print(f"\n{model_name}: NOT FOUND")
        continue
    print(f"\nLoading {model_name}...")
    model: Any = keras.models.load_model(path, compile=False)
    l1p, l2p, l3p = model.predict([tokens_arr, nums_arr], batch_size=512, verbose=0)
    
    l1_idx = np.argmax(l1p, axis=1)
    l2_idx = np.argmax(l2p, axis=1)
    l3_idx = np.argmax(l3p, axis=1)
    
    print(f"=== {model_name} on current test ({len(test_rows)} samples) ===")
    print(f"  L1={np.mean(l1_idx==l1s):.4f}  L2={np.mean(l2_idx==l2s):.4f}  L3={np.mean(l3_idx==l3s):.4f}")
    top3 = np.argsort(l3p, axis=1)[:, -3:]
    print(f"  L3 Top3={np.mean([l3s[i] in top3[i] for i in range(len(l3s))]):.4f}")
