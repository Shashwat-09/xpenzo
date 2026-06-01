# Phase 2 Plan — Android Integration + Model Reconciliation

**Created:** 2026-05-21 (Opus session — handoff to Sonnet)
**Audience:** Claude Code (Sonnet) picking this up cold. Read this top-to-bottom before touching code.
**Prereq reading:** `CLAUDE.md`, `docs/09 - ML Architecture Specification.md`, `graphify-out/GRAPH_REPORT.md`.

---

## 0. TL;DR — Where We Actually Are (verified 2026-05-21)

The ML model is **trained and exporting**, but there is a **taxonomy split** that must be resolved before anything ships. The Android side is a **bare scaffold** — the ML Kotlin layer exists but is **not wired into the app project**.

| Area | State | Evidence |
|------|-------|----------|
| Real training data | ✅ Built — 570K rows, full 520-class taxonomy | `ml/training/combined_dataset.csv` (570,300 rows), `ml/training/split_stats.json` (l3_classes: 520) |
| Best real-data model | ✅ v4 — L1 82.6%, L3 top1 67.7%, **4.89 MB** | `ml/models/evaluation_report_v4.json`, `ml/models/xpenz_cht_v4.tflite` (5.13MB on disk pre-quant report) |
| v6 model | ⚠️ Regressed + oversized — L1 79.9%, **5.48 MB (over budget)** | `ml/models/v6_comparison.json` |
| Latest May export | ⚠️ **Synthetic-only, partial taxonomy (217/520 L3)** | `outputs/label_encoders.pkl` → l3=217; `outputs/labels_l3.txt` → 216 lines |
| HF gated dataset (mitulshah) | ❌ Abandoned — never downloaded (gated) | `data/hf_transaction_categorization/default/` empty; `models/teacher/` README only |
| Android app project | ⚠️ Scaffold only | `android_app/app/src/main/` = MainActivity, Theme, XpenzoApplication; `assets/` empty |
| ML Kotlin layer | ⚠️ Exists but in OLD location, not in app project | `app/src/main/kotlin/com/xpenzo/ml/**` (10 files) — NOT under `android_app/` |

**The single most important Phase 2 decision:** the canonical model is the **real-data 520-class lineage** (`ml/models/` v4), NOT the fresher synthetic-only `outputs/` v3. The May run regressed taxonomy coverage. See §1.

---

## 1. Model Reconciliation (DO THIS FIRST — blocks everything)

### The problem
Two parallel lineages exist with **incompatible label spaces**:

- **March lineage (`ml/models/`)** — trained via `ml/data_collection/scripts/12_train_cht_v4_optimized.py` and `13_train_cht_v6.py` on the full `combined_dataset.csv`. Full taxonomy: **15 L1 / 80 L2 / 520 L3**. Best = v4 (4.89 MB INT8, under the 5 MB budget). v6 is bigger AND worse — discard v6.
- **May lineage (`outputs/`)** — trained via the rewritten `ml/train_cht.py` (distillation-capable) but on **synthetic data only**, producing a **partial 217-class L3** encoder. Smaller (4.24 MB) but covers <42% of the taxonomy. Not shippable.

These cannot be A/B compared directly — different label encoders. A model that only knows 217 micro-categories will silently misroute the other 303.

### The decision
**Ship the 520-class taxonomy.** Two viable paths — pick based on a quick eval:

- **Path A (fastest, recommended first):** Adopt `ml/models/xpenz_cht_v4.tflite` + its label encoders as the production model. It already meets the spec (520 classes, 82.6% L1, <5 MB). Verify it loads and infers correctly, copy to Android assets, ship. Defer retraining to Phase 3.
- **Path B (better long-term):** Re-run the **current** `ml/train_cht.py` distillation pipeline against `ml/training/combined_dataset.csv` (the 570K real rows) so the newer training code produces a full-520 model. This unifies the lineages on the maintained script. Do this only if Path A's v4 model fails validation OR after the app is working end-to-end.

### Concrete steps for Path A
1. Locate v4's label encoder. Check `ml/training/label_encoders.json` and `ml/models/v4_round1_3layer/`. Confirm it has 520 L3 classes (NOT the 217-class `outputs/label_encoders.pkl`).
2. Generate `labels_l1.txt` / `labels_l2.txt` / `labels_l3.txt` from the **520-class** encoder (15/80/520 lines respectively). Do NOT reuse `outputs/labels_*.txt` — those are the 216/69/14 partial set.
3. Write a smoke-test script: load `xpenz_cht_v4.tflite`, run 20 hand-picked Indian UPI SMS strings (e.g. "Sent Rs.499 to ZOMATO via UPI", "UPI/OLA/...", "Big Bazaar"), confirm sane L1→L2→L3 output and that argmax indices map to the 520-label files. Print predicted category names.
4. Record the verified model + label files as the canonical artifact set in `CLAUDE.md`.

### Acceptance criteria
- One tflite under 5 MB with a 520-class label space, smoke-tested on real-looking SMS, predictions are human-sane.
- `CLAUDE.md` "ML Architecture (v3 — CANONICAL)" section updated to point at the *actual* shipped file + its true accuracy numbers (it currently claims 3.2 MB / 30 ms — verify and correct).

---

## 2. Consolidate ML Kotlin Layer Into the App Project

Right now the 10 ML Kotlin files live under `app/src/main/kotlin/com/xpenzo/ml/` but the real Gradle project is `android_app/`. They must be unified.

### Files to move (from `app/` → `android_app/app/src/main/kotlin/com/xpenzo/ml/`)
```
core/TransactionClassifier.kt      core/ClassifierInput.kt      core/ClassificationResult.kt
models/CHTClassifier.kt            models/RuleEngine.kt         models/HabitModel.kt
ensemble/EnsembleClassifier.kt
manager/ModelManager.kt            manager/ModelUpdateManager.kt
data/DataCollectionManager.kt
```

### Steps
1. Inspect `android_app/app/build.gradle.kts` and `android_app/settings.gradle.kts` — confirm package, minSdk (must be 26+), Compose + Kotlin versions.
2. Move the 10 ML files into `android_app/app/src/main/kotlin/com/xpenzo/ml/`. Delete the old `app/` tree once moved (confirm no other references).
3. Add required deps to `android_app/app/build.gradle.kts`:
   - `org.tensorflow:tensorflow-lite` (+ `tensorflow-lite-support`)
   - Room (`androidx.room:room-runtime`, `room-ktx`, kapt/ksp compiler)
   - WorkManager (`androidx.work:work-runtime-ktx`)
   - Hilt (`com.google.dagger:hilt-android` + compiler) — DI is planned per CLAUDE.md
   - Firebase BoM + Firestore + Storage + Auth (for the self-improving loop; can stub initially)
4. Read each `CHTClassifier.kt` / `ModelManager.kt` to confirm the asset filenames + label filenames it expects match what §1 produced. Fix mismatches.
5. Place artifacts in `android_app/app/src/main/assets/`:
   - the canonical `.tflite` (rename consistently — pick `xpenz_cht_v3.tflite` to match Kotlin or update Kotlin)
   - `xpenz_bpe.model`
   - `labels_l1.txt`, `labels_l2.txt`, `labels_l3.txt` (the **520-class** set)

### Acceptance criteria
- `android_app` compiles (`./gradlew :app:assembleDebug` from `android_app/`). If no JDK/Android SDK available in this env, say so explicitly and stop at "code complete, build unverified."
- No duplicate/orphaned `com.xpenzo.ml` package outside `android_app/`.

---

## 3. Room Database Schema

Per CLAUDE.md "What's Next" #3. Build under `android_app/app/src/main/kotlin/com/xpenzo/data/db/`.

Tables:
- `transactions` — id, raw_sms, normalized_text, amount, merchant, timestamp, l1/l2/l3 category, confidence, source (rule|cht|habit|ensemble), user_confirmed (bool)
- `habits` — merchant_key → category mapping, confirmation_count (feeds `HabitModel`)
- `corrections` — original_category, corrected_category, txn_ref, uploaded (bool) — feeds `DataCollectionManager`

Wire `HabitModel.kt` and `DataCollectionManager.kt` to read/write these DAOs (they currently likely assume an interface — check and connect).

---

## 4. SMS Ingestion Pipeline

Per CLAUDE.md "What's Next" #4.
- `SmsReceiver : BroadcastReceiver` registered for `RECEIVE_SMS` (permission already in manifest).
- An SMS parser that extracts amount, merchant/VPA, direction (debit/credit) from UPI bank SMS. Reuse the normalization logic from the Python `text_normalized` step (digits→#, lowercase) so on-device features match training.
- Build the 16 numerical features `CHTClassifier` expects (check the Kotlin for the exact feature vector — the Python side encodes them in `combined_dataset.csv` `num_features` column: looks like cyclical time encodings + amount bucket + flags). **Feature parity between training and inference is critical** — mismatch silently destroys accuracy.

---

## 5. Wire It Together (ViewModel + UI)

Per CLAUDE.md "What's Next" #5–8.
- ViewModel: SMS in → parser → `ModelManager.getInstance(context).classify(input)` → persist to Room → expose flow to Compose.
- `XpenzoApplication.onCreate()`: call `ModelUpdateManager.schedulePeriodicChecks()`.
- Transaction list UI from existing Compose designs in `UI-UX/` (HTML mockups in each screen's `code.html`).
- Settings: "Help Improve AI" opt-in toggle (`UI-UX/help_improve_ai/`), model switcher (`UI-UX/ai_model_settings/`).

---

## 6. Backend / Self-Improving Loop (defer unless app works)

Per CLAUDE.md #9–10. Firebase Storage `models/` layout + deploy `ml/retrain.py` to Cloud Run. **Do not start this until the app classifies a real SMS end-to-end** — it's worthless without users.

---

## Suggested Execution Order for Sonnet

1. **§1 model reconciliation** (smoke-test v4, generate 520-class labels) — unblocks everything, no Android build needed.
2. **§2 consolidate Kotlin + assets** — get `android_app` to compile.
3. **§3 Room** → **§4 SMS** → **§5 wire-up**.
4. Stop and demo a single SMS → category before touching §6.

## Things That Will Bite You
- **Don't trust `outputs/`** — it's the partial 217-class synthetic model. The real one is in `ml/models/` (v4).
- **The mitulshah HF dataset in CLAUDE.md is dead** — it's gated and was never downloaded. Real data came from the `ml/data_collection/scripts/01-14` POI pipeline (OSM, PhonePe Pulse, Google Maps, Wikidata, scrapers). Update CLAUDE.md's "Data Strategy" section to reflect this.
- **Feature-vector parity** (§4) between Python training and Kotlin inference is the most likely source of "model works in Python, garbage on device."
- **No JDK/Android SDK may be present** in this environment — if so, do code-complete work and clearly flag builds as unverified rather than claiming success.
- After any code change, run `graphify update .` to keep `graphify-out/` current (AST-only, free).
