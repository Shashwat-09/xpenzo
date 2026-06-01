# Xpenzo - Codex Memory File

This file is read automatically by Codex at startup.
Last updated: 2026-05-21 (COD-11 canonical 520-class artifact verification)

---

## What Xpenzo Is

Xpenzo is an Android app that reads Indian UPI/bank SMS messages and classifies spend into a 3-level expense taxonomy on-device.

- Platform: Android API 26+, Kotlin, Jetpack Compose
- Core ML constraint: offline inference, bundled artifact under roughly 5 MB, fast enough for SMS ingestion
- Primary specs: `docs/01 - Technical Requirements Document (TRD).md`, `docs/09 - ML Architecture Specification.md`

---

## Canonical ML Bundle

The current full-taxonomy production bundle is:

- Model alias for Android assets: `android_app/app/src/main/assets/xpenz_cht_520.tflite`
- Verified source artifact: `ml/models/v5_round1_3layer/model.tflite`
- Tokenizer: `android_app/app/src/main/assets/xpenz_bpe.model`
- Labels:
  - `android_app/app/src/main/assets/labels_l1.txt`
  - `android_app/app/src/main/assets/labels_l2.txt`
  - `android_app/app/src/main/assets/labels_l3.txt`
- Verification report: `outputs/smoke_reports/canonical_v4_smoke.json`

Canonical tensor contract:

- Inputs: `token_ids` int32 `[1, 32]`, `num_feats` float32 `[1, 16]`
- Outputs: 15 L1, 80 L2, 520 L3

Verification summary from `COD-11`:

- `v5_round1` on first 1,000 held-out test rows: L1 `0.818`, L2 `0.723`, L3 `0.654`
- `v6` is worse and larger: L3 `0.604`, size `5,744,792` bytes
- `v4` and `quick_test` are unusable despite matching tensor shapes:
  - L1 `0.124`, L2 `0.064`, L3 `0.028`
- `outputs/xpenz_cht_v3.tflite` is partial taxonomy only:
  - outputs `15 / 70 / 217`
  - not shippable for the 520-class product

Important preprocessing note:

- The canonical 520-class lineage is verified against one normalized merchant-like text field plus 16 numeric features.
- The Android classifier should not assume the synthetic-only `merchant + upi split` contract from the stale v3 lineage.

---

## Training Lineage Reality

The real 520-class taxonomy in this repo comes from Xpenzo's India business corpus and labeling pipeline, not from the historical HuggingFace plan.

- Taxonomy: `ml/taxonomy/category_taxonomy.json`
- Encoders: `ml/training/label_encoders.json`
- Tokenizer source: `ml/training/tokenizer/xpenz_bpe.model`
- Dataset used for verification: `ml/training/test.csv`
- Full dataset root: `ml/training/combined_dataset.csv`

Historical but not currently verified:

- The `mitulshah` teacher/dataset distillation path described in older notes
- Any claim that `xpenz_cht_v3.tflite` is the canonical Android artifact
- Any claim that `xpenz_cht_v4.tflite` is the best March-lineage model

---

## Android State

The active Android scaffold is under `android_app/`.

Relevant ML code:

- `android_app/app/src/main/kotlin/com/xpenzo/ml/models/CHTClassifier.kt`
- `android_app/app/src/main/kotlin/com/xpenzo/ml/manager/ModelManager.kt`
- `android_app/app/src/main/kotlin/com/xpenzo/ml/manager/ModelUpdateManager.kt`

The canonical bundle is already materialized into `android_app/app/src/main/assets/`.

---

## Self-Improving Loop

The long-term plan is still:

1. bundled on-device model classifies SMS
2. user corrections update local habit signals immediately
3. opted-in anonymized corrections flow to Firestore
4. `ml/retrain.py` fine-tunes and exports a newer artifact
5. Android downloads the newer bundle through `ModelUpdateManager`

That loop is future-facing. The immediate shipping truth is the verified bundled 520-class asset set above.

---

## Practical Rules

- Prefer `android_app/` over older duplicated Kotlin paths when making app changes.
- Treat `outputs/` as experimental unless a task explicitly asks for the synthetic-only lineage.
- If a task touches artifact selection, re-run `python scripts/verify_canonical_v4.py` from `.venv-tf`.
- If a task touches label mapping, regenerate `labels_l1.txt`, `labels_l2.txt`, and `labels_l3.txt` from `ml/training/label_encoders.json`, not `outputs/label_encoders.pkl`.

---

## graphify

This repo has a knowledge graph under `graphify-out/`.

- Read `graphify-out/GRAPH_REPORT.md` before broad codebase exploration.
- If `graphify-out/wiki/index.md` exists, prefer it over raw-file wandering.
- After meaningful code changes, run `graphify update .` when maintaining graph freshness matters.
