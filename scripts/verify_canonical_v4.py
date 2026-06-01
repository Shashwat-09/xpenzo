from __future__ import annotations

import csv
import json
import shutil
import time
from pathlib import Path

import numpy as np
import sentencepiece as spm
import tensorflow as tf


ROOT = Path(__file__).resolve().parents[1]
TOKENIZER_PATH = ROOT / "ml" / "training" / "tokenizer" / "xpenz_bpe.model"
ENCODER_PATH = ROOT / "ml" / "training" / "label_encoders.json"
TAXONOMY_PATH = ROOT / "ml" / "taxonomy" / "category_taxonomy.json"
TEST_CSV_PATH = ROOT / "ml" / "training" / "test.csv"
ASSETS_DIR = ROOT / "android_app" / "app" / "src" / "main" / "assets"
REPORT_DIR = ROOT / "outputs" / "smoke_reports"
REPORT_PATH = REPORT_DIR / "canonical_v4_smoke.json"
CANONICAL_ASSET_MODEL = "xpenz_cht_520.tflite"

SEQ_LEN = 32
BOS_ID = 2
EOS_ID = 3
PAD_ID = 0

CANDIDATE_MODELS = [
    ("v4", ROOT / "ml" / "models" / "xpenz_cht_v4.tflite"),
    ("v4_quick_test", ROOT / "ml" / "models" / "quick_test" / "model.tflite"),
    ("v5_round1", ROOT / "ml" / "models" / "v5_round1_3layer" / "model.tflite"),
    ("v6", ROOT / "ml" / "models" / "xpenz_cht_v6.tflite"),
]

CURATED_SAMPLE_TEXTS = [
    "ptel zomato gold",
    "dominos point impahl",
    "quick uber go",
    "yadav ola auto travels",
    "hegde swiggy",
    "bedi airtel broadband satellite",
    "my airtel fiber visakhapatnam",
    "reddy's airetl xstream",
    "thakur netflix",
    "mukherjee netflix subscription",
    "royal netflix bhubaneswar",
    "irctc i k",
    "oyo 29008 mannat residency",
    "oyo 22756 diksha hotel",
    "treebo tms residency",
    "rajakkamangalam phc",
    "sagar pharmacy",
    "prity pharmacy",
    "shree narayana datta dental clinic",
    "mukherje's rooftop solar",
]


def normalize_text(text: str) -> str:
    return text.lower().replace("'", "").replace('"', "").strip()


def prepare_text_input(text: str, sp_model: spm.SentencePieceProcessor) -> np.ndarray:
    text_ids = sp_model.encode(normalize_text(text), out_type=int)
    token_ids = [BOS_ID] + text_ids[: SEQ_LEN - 2] + [EOS_ID]
    token_ids += [PAD_ID] * (SEQ_LEN - len(token_ids))
    return np.asarray(token_ids, dtype=np.int32)


def build_taxonomy_maps() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    l1 = {}
    l2 = {}
    l3 = {}
    for category in taxonomy["categories"]:
        l1[category["l1_code"]] = category["l1_name"]
        for subcategory in category["subcategories"]:
            l2[subcategory["l2_code"]] = subcategory["l2_name"]
            for micro in subcategory["micro_categories"]:
                l3[micro["l3_code"]] = micro["l3_name"]
    return l1, l2, l3


def generate_label_files() -> dict[str, int]:
    encoders = json.loads(ENCODER_PATH.read_text(encoding="utf-8"))["encoders"]
    l1_map, l2_map, l3_map = build_taxonomy_maps()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    counts = {}
    for encoder_key, output_name, taxonomy_map in [
        ("l1_code", "labels_l1.txt", l1_map),
        ("l2_code", "labels_l2.txt", l2_map),
        ("l3_code", "labels_l3.txt", l3_map),
    ]:
        ordered_codes = [code for code, _ in sorted(encoders[encoder_key].items(), key=lambda item: item[1])]
        labels = [taxonomy_map[code] for code in ordered_codes]
        (ASSETS_DIR / output_name).write_text("\n".join(labels) + "\n", encoding="utf-8")
        counts[output_name] = len(labels)
    return counts


def copy_canonical_assets(model_path: Path) -> None:
    shutil.copy2(model_path, ASSETS_DIR / CANONICAL_ASSET_MODEL)
    shutil.copy2(TOKENIZER_PATH, ASSETS_DIR / TOKENIZER_PATH.name)


def load_labels(filename: str) -> list[str]:
    return (ASSETS_DIR / filename).read_text(encoding="utf-8").splitlines()


def load_test_rows() -> list[dict[str, str]]:
    with open(TEST_CSV_PATH, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def evaluate_candidate(
    interpreter: tf.lite.Interpreter,
    rows: list[dict[str, str]],
    sp_model: spm.SentencePieceProcessor,
) -> dict[str, float]:
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    dims = sorted(int(detail["shape"][-1]) for detail in output_details)
    if dims != [15, 80, 520]:
        return {"usable": 0.0, "l1_top1": 0.0, "l2_top1": 0.0, "l3_top1": 0.0}

    ok1 = ok2 = ok3 = 0
    for row in rows:
        token_ids = prepare_text_input(row["text_normalized"], sp_model)[None, :]
        num_feats = np.asarray(json.loads(row["num_features"])[:16], dtype=np.float32)[None, :]
        for detail in input_details:
            interpreter.set_tensor(detail["index"], token_ids if detail["dtype"] == np.int32 else num_feats)
        interpreter.invoke()
        outputs = {int(detail["shape"][-1]): interpreter.get_tensor(detail["index"])[0] for detail in output_details}
        ok1 += int(int(np.argmax(outputs[15])) == int(row["l1_label"]))
        ok2 += int(int(np.argmax(outputs[80])) == int(row["l2_label"]))
        ok3 += int(int(np.argmax(outputs[520])) == int(row["l3_label"]))

    sample_count = float(len(rows))
    return {
        "usable": 1.0,
        "l1_top1": round(ok1 / sample_count, 4),
        "l2_top1": round(ok2 / sample_count, 4),
        "l3_top1": round(ok3 / sample_count, 4),
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    label_counts = generate_label_files()
    all_rows = load_test_rows()
    rows_by_text = {row["text_normalized"]: row for row in all_rows}
    curated_rows = [rows_by_text[text] for text in CURATED_SAMPLE_TEXTS]

    l1_labels = load_labels("labels_l1.txt")
    l2_labels = load_labels("labels_l2.txt")
    l3_labels = load_labels("labels_l3.txt")

    sp = spm.SentencePieceProcessor()
    sp.load(str(TOKENIZER_PATH))

    candidate_scores = {}
    selected_name = None
    selected_path = None
    best_l3 = -1.0
    for name, model_path in CANDIDATE_MODELS:
        interpreter = tf.lite.Interpreter(model_path=str(model_path))
        interpreter.allocate_tensors()
        score = evaluate_candidate(interpreter, all_rows[:1000], sp)
        score["size_bytes"] = float(model_path.stat().st_size)
        candidate_scores[name] = score
        if score["usable"] and score["l3_top1"] > best_l3:
            selected_name = name
            selected_path = model_path
            best_l3 = score["l3_top1"]

    assert selected_path is not None
    copy_canonical_assets(selected_path)

    interpreter = tf.lite.Interpreter(model_path=str(selected_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    samples = []
    latencies_ms = []
    exact_match_count = 0
    for row in curated_rows:
        token_ids = prepare_text_input(row["text_normalized"], sp)[None, :]
        num_feats = np.asarray(json.loads(row["num_features"])[:16], dtype=np.float32)[None, :]

        for detail in input_details:
            interpreter.set_tensor(detail["index"], token_ids if detail["dtype"] == np.int32 else num_feats)

        start = time.perf_counter()
        interpreter.invoke()
        latency_ms = (time.perf_counter() - start) * 1000.0
        latencies_ms.append(latency_ms)

        outputs = {int(detail["shape"][-1]): interpreter.get_tensor(detail["index"])[0] for detail in output_details}
        l1_probs = outputs[15]
        l2_probs = outputs[80]
        l3_probs = outputs[520]

        l1_idx = int(np.argmax(l1_probs))
        l2_idx = int(np.argmax(l2_probs))
        l3_top = np.argsort(l3_probs)[-3:][::-1]
        exact_match = (
            l1_labels[l1_idx] == row["l1_name"]
            and l2_labels[l2_idx] == row["l2_name"]
            and l3_labels[int(l3_top[0])] == row["l3_name"]
        )
        exact_match_count += int(exact_match)

        samples.append(
            {
                "sms": f"UPI debit to {row['text_normalized']} successful.",
                "merchant_text": row["text_normalized"],
                "expected": {
                    "l1": row["l1_name"],
                    "l2": row["l2_name"],
                    "l3": row["l3_name"],
                },
                "predicted_l1": {"label": l1_labels[l1_idx], "confidence": round(float(l1_probs[l1_idx]), 4)},
                "predicted_l2": {"label": l2_labels[l2_idx], "confidence": round(float(l2_probs[l2_idx]), 4)},
                "predicted_l3": {"label": l3_labels[int(l3_top[0])], "confidence": round(float(l3_probs[int(l3_top[0])]), 4)},
                "top3_l3": [
                    {"label": l3_labels[int(idx)], "confidence": round(float(l3_probs[int(idx)]), 4)}
                    for idx in l3_top
                ],
                "exact_match": exact_match,
                "latency_ms": round(latency_ms, 2),
            }
        )

    report = {
        "candidate_comparison_top1_on_first_1000_test_rows": candidate_scores,
        "canonical_artifacts": {
            "selected_candidate": selected_name,
            "source_model": str(selected_path.relative_to(ROOT)),
            "tokenizer": str(TOKENIZER_PATH.relative_to(ROOT)),
            "bundled_asset_model": str((ASSETS_DIR / CANONICAL_ASSET_MODEL).relative_to(ROOT)),
            "bundled_asset_tokenizer": str((ASSETS_DIR / TOKENIZER_PATH.name).relative_to(ROOT)),
            "labels": [
                str((ASSETS_DIR / "labels_l1.txt").relative_to(ROOT)),
                str((ASSETS_DIR / "labels_l2.txt").relative_to(ROOT)),
                str((ASSETS_DIR / "labels_l3.txt").relative_to(ROOT)),
            ],
        },
        "label_counts": label_counts,
        "input_details": [
            {"name": detail["name"], "shape": detail["shape"].tolist(), "dtype": str(detail["dtype"])}
            for detail in input_details
        ],
        "output_details": [
            {"name": detail["name"], "shape": detail["shape"].tolist(), "dtype": str(detail["dtype"])}
            for detail in output_details
        ],
        "smoke_summary": {
            "sample_count": len(samples),
            "exact_match_count": exact_match_count,
            "mean_latency_ms": round(float(np.mean(latencies_ms)), 2),
            "max_latency_ms": round(float(np.max(latencies_ms)), 2),
        },
        "samples": samples,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
