# Xpenzo — Full Project Completion Roadmap

> **Purpose:** Self-contained execution plan to take Xpenzo from its current state
> (fixed ML pipeline + partial scaffold) to a shippable app.
> **Audience:** A Claude Code session (any model) picking this up cold.
> **Last updated:** 2026-05-20
>
> Each task lists: **what**, **files**, **commands**, **acceptance criteria (AC)**, and **gotchas**.
> Work phases in order — later phases depend on earlier ones. Within a phase, tasks
> are mostly parallelizable unless a dependency is noted.

---

## 0. Current State (what's already done)

| Area | Status | Location |
|---|---|---|
| ML architecture spec | ✅ Canonical v3 | `docs/09 - ML Architecture Specification.md` |
| Python training pipeline | ✅ Refactored (Option A) | `ml/` |
| — Mixed HF + synthetic data loader | ✅ New | `ml/data_loader.py` |
| — Real teacher + batched distillation | ✅ New | `ml/teacher.py` |
| — CHT training (attn pooling, 3-head distill) | ✅ Rewritten | `ml/train_cht.py` |
| — HF resource downloader | ✅ Fixed | `ml/download_hf_resources.py` |
| — Synthetic data generator | ✅ Exists | `ml/generate_data.py` |
| — Incremental retraining (self-improving) | ✅ Exists | `ml/retrain.py` |
| ML Kotlin layer (classifiers, managers) | ✅ Written, ⚠️ NOT integrated | `app/src/main/kotlin/com/xpenzo/ml/` |
| Android app scaffold | ⚠️ Minimal (Gradle + MainActivity + Theme) | `android_app/` |
| UI/UX designs (HTML + PNG) | ✅ 47 screens designed | `UI-UX/*/` |
| Trained `.tflite` model | ❌ Not yet produced | (Phase 1 output) |
| Room DB, SMS pipeline, ViewModels, screens | ❌ Not built | (Phases 3–6) |
| Firebase project | ❌ Not set up | (Phase 7) |
| Groups & Splits (Splitwise-style) | ❌ Not built — spec'd only | (Phase 10, post-MVP) |

**Critical structural note:** The ML Kotlin layer lives in `app/` but the app scaffold
lives in `android_app/`. **Phase 2 must merge these** — move `app/src/main/kotlin/com/xpenzo/ml/`
into `android_app/app/src/main/kotlin/com/xpenzo/ml/`.

---

## Phase 1 — Train & Validate the ML Model

**Goal:** Produce `xpenz_cht_v3.tflite` (< 5 MB, < 100 ms) with measured accuracy.
**Why first:** Everything in the Android ML integration (Phase 5) depends on having a real model file.

### 1.1 Set up the Python environment
- **Commands:**
  ```bash
  cd ml
  python -m venv .venv
  .venv\Scripts\activate          # Windows
  pip install -r requirements.txt
  pip install pyarrow             # parquet reader for data_loader.py (verify it's in requirements)
  ```
- **AC:** `python -c "import tensorflow, transformers, sentencepiece, datasets, pyarrow"` succeeds.
- **Gotcha:** TensorFlow + PyTorch (for the teacher) both load — needs ~6 GB RAM. On Windows, install the CPU build of torch if no CUDA GPU.

### 1.2 Download HF resources
- **Command:** `python ml/download_hf_resources.py`
- **AC:** `data/hf_transaction_categorization/default/train/0000.parquet` (~71 MB) and `models/teacher/config.json` exist.
- **Gotcha:** Both repos are public (MIT) — no HF token needed. If `snapshot_download` 404s, the repo path changed; check huggingface.co.

### 1.3 Generate synthetic data (for L2/L3 hierarchy)
- **Commands:**
  ```bash
  python ml/generate_data.py --output data/train.csv --n_samples 200000
  python ml/generate_data.py --output data/val.csv   --n_samples 20000 --seed 99
  ```
- **AC:** Both CSVs exist with columns `merchant_name, upi_id, amount, timestamp, l1_label, l2_label, l3_label`.
- **Gotcha:** The generator's `TAXONOMY` (top of `generate_data.py`) is the **source of truth** for the L1/L2/L3 tree and is imported by `ml/teacher.py` for prior propagation. If you expand categories, both stay in sync automatically.

### 1.4 Train the tokenizer
- **Command:** `python ml/train_cht.py --mode train_tokenizer --data data/train.csv`
- **AC:** `outputs/xpenz_bpe.model` (~150 KB) exists.
- **Gotcha:** Train tokenizer on synthetic data only (it has the merchant variety). Don't retrain it per run — it's a one-time artifact.

### 1.5 Run distillation training (the main event)
- **Command:** `python ml/train_cht.py --mode train_distill`
- **What happens:** Loads mixed HF+synthetic data → computes teacher soft labels (cached to `outputs/distill_cache/`) → trains CHT with combined CE+KL loss across all 3 heads, L2/L3 masked for HF rows.
- **AC:** `outputs/cht_best.keras` saved; `val_l3_acc` printed each epoch and trending up.
- **Gotchas:**
  - First run computes teacher soft labels for ~800K rows — slow on CPU (~30–60 min), fast on GPU. Subsequent runs hit the cache.
  - If you OOM, lower `BATCH_SIZE` (currently 512) in `train_cht.py` or `max_hf_rows` in `data_loader.py` (currently 800K).
  - Tune `--temperature` (default 4.0) and `--alpha` (default 0.5, weight on KL). Higher alpha = trust teacher more.

### 1.6 Evaluate
- **Files:** `ml/eval_v3_on_current.py`, `ml/compare_models.py` (existing eval scripts).
- **AC:** Report per-level accuracy. **Targets from spec:** L1 ≥ 80%, L2 ≥ 65%, L3 ≥ 50% cold-start.
- **Gotcha:** Evaluate L1 on a **held-out slice of real HF India data**, not synthetic — synthetic accuracy is optimistically high. The deeper L2/L3 can only be evaluated on synthetic (no real labels exist).

### 1.7 Export to TFLite
- **Command:** `python ml/train_cht.py --mode export --checkpoint outputs/cht_best.keras`
- **AC:** `outputs/xpenz_cht_v3.tflite` < 5 MB AND inference < 100 ms (the script prints both and warns if exceeded).
- **Gotcha:** If size > 5 MB, the `SHARED_DIM=384` bump (in `train_cht.py`) is the first thing to revert to 256. Embeddings dominate size — consider `VOCAB_SIZE` 8192 → 6000 if still over.

### 1.8 Generate label files for Android
- **What:** Convert `outputs/label_encoders.pkl` → `labels_l1.txt`, `labels_l2.txt`, `labels_l3.txt` (one label per line, index order).
- **AC:** Three text files where line N = class name for index N.
- **Gotcha:** The Android `CHTClassifier.kt` maps output indices → category names using these. Order MUST match the encoder's `.classes_` order.

**Phase 1 deliverables to copy into Android (Phase 5):**
`xpenz_cht_v3.tflite`, `xpenz_bpe.model`, `labels_l1.txt`, `labels_l2.txt`, `labels_l3.txt`

---

## Phase 2 — Android Project Setup & Merge

**Goal:** One buildable Android project with the ML Kotlin layer integrated.
**Depends on:** nothing (can run parallel to Phase 1).

### 2.1 Merge the ML Kotlin layer into the app
- **What:** Move `app/src/main/kotlin/com/xpenzo/ml/` → `android_app/app/src/main/kotlin/com/xpenzo/ml/`. Delete the orphan `app/` dir after.
- **AC:** All ML classes resolve under one Gradle module.
- **Gotcha:** Package is already `com.xpenzo.ml.*` — no rename needed, just relocate.

### 2.2 Complete Gradle config
- **Files:** `android_app/build.gradle.kts`, `android_app/app/build.gradle.kts`, `android_app/settings.gradle.kts`, add `gradle/wrapper/`, `gradle.properties`.
- **What to add:** Compose BOM, `WorkManager` dep (`androidx.work:work-runtime-ktx`), navigation-compose, `kotlinx-coroutines`, datastore (for prefs). `build.gradle.kts` already has Hilt/Room/Firebase/TFLite.
- **AC:** `./gradlew :app:assembleDebug` builds (even with empty screens).
- **Gotchas:**
  - `compileSdk`/`targetSdk` are 33 — bump to 34 for current Play requirements.
  - TFLite: add `aaptOptions { noCompress("tflite") }` so the model isn't compressed in the APK.
  - `google-services` plugin is declared but needs `google-services.json` (Phase 7) — stub it or the build fails. Comment out until Firebase is set up.

### 2.3 AndroidManifest + permissions
- **File:** `android_app/app/src/main/AndroidManifest.xml`
- **What:** Declare `RECEIVE_SMS`, `READ_SMS`, `INTERNET`, `ACCESS_NETWORK_STATE`, optional `ACCESS_FINE_LOCATION`. Register the SMS `BroadcastReceiver` (Phase 4) and `XpenzoApplication`.
- **AC:** Manifest merges without errors; runtime perms requested at first launch.
- **Gotcha:** SMS perms trigger Play Store review scrutiny — you need a Permissions Declaration Form justifying `READ_SMS` (financial SMS parsing is an allowed use case).

### 2.4 Hilt application setup
- **File:** `android_app/app/.../XpenzoApplication.kt` (exists — verify `@HiltAndroidApp`).
- **AC:** App launches with Hilt graph initialized; `ModelManager` injectable.

---

## Phase 3 — Data Layer (Room)

**Goal:** Local persistence for transactions, habits, and correction events.
**Depends on:** Phase 2.

### 3.1 Define entities
- **Tables:**
  - `transactions` — id, merchant_raw, merchant_normalized, upi_id, amount, timestamp, l1/l2/l3 category, confidence, source (SMS/manual), is_corrected, synced.
  - `habits` — merchant_normalized (PK), category, confirmation_count, last_seen (feeds `HabitModel.kt`).
  - `corrections` — id, transaction_id, old_category, new_category, timestamp, uploaded (feeds `DataCollectionManager.kt`).
  - `budgets` — id, category, limit, period, family_id (nullable).
- **AC:** Room schema compiles; `@Database` version 1 exported to `schemas/`.
- **Gotcha:** `HabitModel.kt` and `DataCollectionManager.kt` already reference these concepts — read them first and match field names.

### 3.2 DAOs + repository
- **What:** `TransactionDao`, `HabitDao`, `CorrectionDao` + a `TransactionRepository` that wraps Room and exposes Flows.
- **AC:** CRUD + reactive queries (Flow) work in an instrumented test.

---

## Phase 4 — SMS Ingestion Pipeline

**Goal:** Detect bank/UPI SMS → parse → produce a `ClassifierInput`.
**Depends on:** Phase 2, 3.

### 4.1 SMS BroadcastReceiver
- **File:** new `sms/SmsReceiver.kt` registered in manifest.
- **AC:** Receives `SMS_RECEIVED`, filters to known bank senders, hands raw body to the parser.
- **Gotcha:** Use a `WorkManager` job for parsing+classification so the receiver returns fast (BroadcastReceivers have a ~10s limit).

### 4.2 SMS parser
- **File:** new `sms/UpiSmsParser.kt`.
- **What:** Regex/heuristic extraction of amount, merchant/UPI, debit-vs-credit, timestamp from Indian bank SMS formats (HDFC, SBI, ICICI, Axis, Paytm, GPay, PhonePe templates).
- **AC:** Unit tests cover ≥ 10 real SMS formats per major bank; extracts amount + merchant correctly.
- **Gotcha:** This is the **highest-variance, highest-bug-risk** component. Build a fixture file of anonymized real SMS and test-drive it. Skip non-transactional SMS (OTP, promo).

### 4.3 Wire parser → classifier
- **What:** Parsed SMS → `ClassifierInput` → `ModelManager.getInstance(ctx).classify(input)` → persist `Transaction`.
- **AC:** End-to-end: inject a fake SMS, see a categorized transaction in Room.

---

## Phase 5 — ML Integration in Android

**Goal:** The on-device ensemble actually runs.
**Depends on:** Phase 1 (model files), Phase 2 (merged layer).

### 5.1 Drop in model assets
- **What:** Copy Phase 1 outputs into `android_app/app/src/main/assets/`:
  `xpenz_cht_v3.tflite`, `xpenz_bpe.model`, `labels_l1.txt`, `labels_l2.txt`, `labels_l3.txt`.
- **AC:** Assets load at runtime without FileNotFound.

### 5.2 Verify CHTClassifier inference
- **File:** `models/CHTClassifier.kt` (exists).
- **What:** Confirm it (a) loads the TFLite interpreter, (b) tokenizes via SentencePiece (need a Kotlin SP wrapper or precomputed vocab), (c) builds the 16 numerical features identically to `prepare_numerical_features` in `train_cht.py`, (d) maps output indices via the label files.
- **AC:** Same input gives the same top category in Python and Android (parity test).
- **Gotchas:**
  - **Feature parity is critical.** The Kotlin numerical-feature code MUST match `train_cht.py:prepare_numerical_features` exactly (same bucket boundaries, same sin/cos, same order). Any drift silently tanks accuracy.
  - SentencePiece on Android: use the `sentencepiece` Android AAR, or export the vocab and reimplement BPE encode in Kotlin. Match `prepare_text_input` token layout (`<bos> merchant <sep> upi <eos>`).

### 5.3 Wire the ensemble + ModelManager into a ViewModel
- **Files:** `manager/ModelManager.kt`, `ensemble/EnsembleClassifier.kt` (exist).
- **AC:** A `TransactionViewModel` calls `ModelManager.classify()` and the adaptive ensemble weights shift by user maturity (cold→warm→mature) as habits accumulate.

---

## Phase 6 — UI (Jetpack Compose)

**Goal:** Build screens from the existing `UI-UX/` designs.
**Depends on:** Phase 3, 5. Reference HTML/PNG in `UI-UX/<screen>/`.

### Priority order (MVP first)
1. **Onboarding/auth:** `welcome_to_xpenzo`, `phone_login`, `verify_otp`, `user_profile_setup`, `upi_id_setup`, `sms_permission_request`.
2. **Core loop:** `expenses_home` (transaction list), `transaction_details`, `edit_transaction`, `ai_category_suggestion` (the ML result UI), `manual_entry`.
3. **Categorization:** `browse_categories`, `search_transactions`.
4. **Budgets:** `budget_management_overview_1/2`, `create_new_budget`.
5. **Insights:** `monthly_insights_overview`, `habit_analysis_details`.
6. **ML settings:** `ai_model_settings` (model switcher UI), `personal_ai_training`, `help_improve_ai` (opt-in consent — gates `DataCollectionManager`).
7. **Family (post-MVP):** `family_hub_overview`, `create_new_family`, `join_a_family_1/2`, `manage_family_members`, `family_spending_dashboard`, `setup_family_budget`, etc.
8. **Settings:** `settings_home_overview`, `language_and_theme_settings`, `personal_notification_settings`, `app_permissions_review`, `export_data_settings`, `backup_and_sync_settings`, `delete_account_confirmation`.

- **AC per screen:** Matches the design's layout/components; wired to its ViewModel; survives config change.
- **Gotcha:** The HTML designs use a specific color/spacing system — extract tokens into `ui/theme/Theme.kt` (exists) once, reuse everywhere. Don't hardcode colors per screen.

---

## Phase 7 — Backend (Firebase)

**Goal:** Auth, cloud sync, model distribution.
**Depends on:** Phase 2 (re-enable `google-services`).

### 7.1 Firebase project + config
- **What:** Create Firebase project, add Android app (package `com.xpenzo`), download `google-services.json` → `android_app/app/`.
- **AC:** App builds with `google-services` plugin enabled; Firebase initializes.

### 7.2 Phone OTP auth
- **What:** Wire Firebase Auth phone flow to `phone_login` + `verify_otp` screens.
- **AC:** Real OTP round-trip; auth state persists.

### 7.3 Firestore schema
- **Ref:** `docs/04 - Backend Schema Documentation.md`.
- **What:** Collections for users, transactions (synced subset), families, budgets, and `transaction_corrections` (what `retrain.py` reads).
- **AC:** Room ↔ Firestore sync works offline-first; security rules restrict per-user/family access.

### 7.4 Firebase Storage for models
- **Layout (from CLAUDE.md):**
  ```
  gs://xpenzo-app.appspot.com/models/
    latest.json          # version manifest the app polls
    v3.0/xpenz_cht_v3.tflite, xpenz_bpe.model
  ```
- **AC:** `ModelUpdateManager.kt` (exists) reads `latest.json`, downloads new model, calls `ModelManager.switchModel()`.

---

## Phase 8 — Self-Improving Loop

**Goal:** Close the data flywheel (already designed, needs wiring + deploy).
**Depends on:** Phase 5, 6 (consent UI), 7.

### 8.1 Wire DataCollectionManager
- **File:** `data/DataCollectionManager.kt` (exists).
- **What:** On user category correction → update `HabitModel` immediately + save to Room + (if opted-in via `help_improve_ai` screen) upload anonymized sample to Firestore.
- **AC:** Correcting a category updates on-device prediction next time; opted-in samples appear in Firestore (normalized merchant only — NO real merchant/amount/account).
- **Gotcha:** Privacy guarantee is contractual — verify the upload payload contains only normalized merchant (digits→#), UPI domain, amount bucket, category. Audit this.

### 8.2 Schedule ModelUpdateManager
- **What:** Call `ModelUpdateManager.schedulePeriodicChecks()` in `XpenzoApplication.onCreate()` — daily, Wi-Fi only.
- **AC:** WorkManager job runs; hot-swaps model when a new version exists.

### 8.3 Deploy retrain.py
- **File:** `ml/retrain.py` (exists).
- **What:** Deploy to Cloud Run in watch mode: `python ml/retrain.py --mode watch --interval 3600`. Polls Firestore, fine-tunes from checkpoint when ≥ 500 new samples, exports new `.tflite`, uploads to Storage, bumps `latest.json`.
- **AC:** A simulated batch of 500 corrections triggers a retrain → new version in Storage.
- **Gotcha:** `retrain.py` predates the Option-A refactor — verify it imports the new `data_loader`/`teacher` modules and uses the same feature pipeline, or it'll produce models incompatible with `CHTClassifier.kt`.

---

## Phase 9 — Testing, Hardening, Launch

**Depends on:** all prior.

### 9.1 Tests
- Unit: SMS parser (fixture-driven), numerical-feature parity (Python vs Kotlin), ensemble weighting.
- Instrumented: Room migrations, end-to-end SMS→categorized transaction, model hot-swap.
- **AC:** CI green; parity test passes (Python and Android agree on a fixed input set).

### 9.2 Performance & battery
- **AC:** Classification < 100 ms on a mid-range device; SMS receiver doesn't wake-lock; model load is lazy/cached.

### 9.3 Privacy & compliance
- **AC:** Play Store SMS Permissions Declaration filled; privacy policy published; data-deletion (`delete_account_confirmation`) actually purges Room + Firestore.

### 9.4 Beta → Production
- Internal testing track → closed beta (real SMS variety is the real test) → staged production rollout.
- **AC:** Crash-free rate > 99%; cold-start L1 accuracy holds on real devices.

---

## Phase 10 — Groups & Splits (Splitwise-style) [Post-MVP]

**Goal:** Ad-hoc bill splitting with friends/groups + "who owes whom" + settle-up.
**Depends on:** Phase 3 (Room), Phase 5 (transaction model + categories), Phase 7 (Firestore/Auth for sync).
**Design decision:** **Option B — a separate subsystem from Family.** Family = one shared household;
Groups = many overlapping circles you split with. Full spec lives in:
PRD **F8** (`docs/08`) · Backend Schema **§3.8** (`docs/04`) · TRD **Tables 12–17** (`docs/01`) ·
App Flow **§9** (`docs/03`). This phase is the *implementation*; read those first.

### 10.1 Room layer (DB v2 migration)
- **What:** Add entities `GroupEntity`, `GroupMemberEntity`, `SplitExpenseEntity`, `SplitShareEntity`, `SettlementEntity`, `FriendEntity` (TRD Tables 12–17). Add nullable `reimbursable_amount` to `transactions`. Bump DB version 1→2 with `MIGRATION_1_2`.
- **AC:** Migration runs without data loss; DAOs expose reactive (Flow) balances.
- **Gotcha:** Do NOT `fallbackToDestructiveMigration` in production — write the real migration.

### 10.2 Split engine (shared Kotlin)
- **What:** Pure functions for the 4 split types (EQUAL/EXACT/PERCENT/SHARES) with paise-exact rounding (leftover → payer), and the min-cash-flow `simplifyDebts` algorithm. Mirror the Cloud Function logic (Backend Schema §5.3) so on-device == server.
- **AC:** Σ shares == total exactly; simplify produces ≤ N-1 settlements netting to zero. Unit-tested.

### 10.3 UI (Compose) — Splits tab
- **What:** Splits tab, Add-friend, Create-group, Split sheet (incl. "Split this" from transaction detail), Balances view, Settle-up (CASH + `upi://pay` deep link). Flows per App Flow §9.
- **AC:** Each screen wired to a ViewModel; survives config change; offline-first.

### 10.4 Firestore sync + Cloud Functions
- **What:** `/groups/**` + `/users/{uid}/friends/**` collections, security rules, indexes (Backend Schema §3.8, §4, §6). Deploy `createGroup`, `joinGroup`, `addFriend`, `generateGroupInviteCode`, `simplifyGroupDebts`, and triggers `onGroupExpenseWrite` / `onSettlementWrite` (recompute cached balances — clients never write balances).
- **AC:** Real-time balance updates across members' devices; rules block non-members; balances match local compute.

### 10.5 Privacy audit
- **AC:** No split-partner identity / group membership / settlement data ever enters `ml_corrections`. Only the local user's own normalized merchant flows to the ML loop (unchanged). Verify the upload payload.

### Acceptance (phase)
- Create group → add expenses (all split types) → balances correct → simplify → settle via UPI → nets to zero, synced across 2 devices, fully working offline, ML privacy boundary intact.

---

## Suggested Execution Order (critical path)

```
Phase 1 (train model) ──┐
                        ├─→ Phase 5 (ML integration) ──┐
Phase 2 (scaffold) ──┬──┘                              │
                     ├─→ Phase 3 (Room) ──→ Phase 4 (SMS) ──┤
                     │                                       ├─→ Phase 6 (UI) ──→ Phase 9 (test/launch)
                     └─→ Phase 7 (Firebase) ──→ Phase 8 (self-improving loop) ──┘

Phase 10 (Groups & Splits) is POST-MVP — runs after Phase 9 ships.
Depends on Phase 3 (Room) + 5 (transactions) + 7 (Firestore/Auth).
```

Phases 1 and 2 are independent — start both. Phase 1 is mostly "run commands and wait";
Phase 2 unblocks everything Android. The longest-pole risks are **Phase 4 (SMS parsing
variance)** and **Phase 5.2 (Python↔Kotlin feature parity)** — budget extra time there.
**Phase 10 (Groups & Splits)** is a post-launch feature; it is fully spec'd but must not
delay the MVP critical path above.

## Watch-outs carried over from this session
- The ML pipeline was just refactored (Option A). Re-run Phase 1 end-to-end before
  trusting any old `outputs/` artifacts — they were trained with the broken
  `distilbert-base-uncased` teacher and synthetic-only data.
- `retrain.py` has NOT been updated for the Option-A changes (see 8.3).
- `graphify-out/` is empty — the knowledge graph was never actually built this session
  despite earlier claims. Run `/graphify .` fresh if you want it.
