# Project Context
> This file is the single source of truth for this project.
> Every agent reads this first. Every agent updates this when things change.
> Last updated: 2026-03-10 — CHT v5 Training: Enriched dataset (570K records), fresh training launched (4 rounds, batch=512, 504ms/step)

---

## 📌 Project Overview
- **Name:** Xpenz (also referred to as Xpenzo)
- **Description:** AI-powered UPI-based family expense tracker for the Indian market (Android). Automatically detects transactions from bank SMS, categorizes them with on-device ML (520 categories), tracks family spending in real-time, and provides budget alerts.
- **Status:** SPRINT 0 (Gradle scaffolding + core architecture + Room DB layer + Hilt DI modules + Repository implementations + DataStore + EncryptionService complete — 58 source files created)
- **Started:** February 24, 2026
- **Target Platform:** Android API 26+ (Android 8.0+), Kotlin 100%

---

## 🛠️ Tech Stack
- **Platform:** Android (Kotlin 1.9.21, Jetpack Compose 1.6.0, Material 3)
- **Architecture:** MVVM + Clean Architecture, Hilt DI
- **Local DB:** Room 2.6.1 (11 tables in full product, 6 in MVP)
- **Cloud Backend:** Firebase (Firestore, Auth, Storage, FCM, Cloud Functions, Analytics, Crashlytics, Remote Config) — region: asia-south1 (Mumbai)
- **Auth:** Firebase Phone Auth (OTP)
- **ML:** TensorFlow Lite on-device — Ensemble: Compact Hierarchical Transformer (CHT) + Rule Engine + User Habit Cache + Amount-Time Prior → 520 categories in 3-level hierarchy (15→80→520), 4.0 MB total, <50ms inference. See `docs/09 - ML Architecture Specification.md`
- **Serialization:** Moshi (Retrofit) + kotlinx-serialization (internal) — Gson removed
- **Networking:** Retrofit 2.9.0 + OkHttp 4.12.0
- **Background:** WorkManager 2.9.0, Coroutines 1.7.3
- **Billing:** Google Play Billing 6.1.0
- **Other:** Coil (images), Vico (charts), Lottie (animations), Timber (logging), Apache POI + iText7 (exports)

### Admin Dashboard Stack
- **Framework:** Next.js 14 (App Router), TypeScript 5.3+
- **Styling:** Tailwind CSS 3.4+, shadcn/ui
- **Charts:** Recharts 2.x
- **Tables:** TanStack Table 8.x
- **State:** Zustand 4.x
- **Forms:** React Hook Form 7.x + Zod
- **Auth:** Firebase Admin SDK 12.x + Google Workspace SSO (@xpenz.app domain)
- **Hosting:** Firebase Hosting at `admin.xpenz.app`
- **Tooling:** pnpm 8.x, Node.js 20 LTS
- **Roles:** Super Admin, Ops Manager, ML Engineer, Finance, Support
- **Modules:** 12 modules (A-L), 42 screens, 87 Cloud Function endpoints, 8 new Firestore collections
- **Design Tokens:** Manrope (400-800) + Lora; Primary #1b3fc0; BG Light #f6f6f8; BG Dark #111521; Card Dark #1a1f30; Green #10b981, Amber #f59e0b, Red #ef4444; Material Symbols Outlined; rounded-2xl cards
- **See:** `docs/10 - Admin Dashboard Architecture.md`

---

## 📁 Folder Structure
```
XPENZO/
├── android/                                              (Sprint 0 codebase — 58 files)
│   ├── .gitignore
│   ├── build.gradle.kts                                   (root — plugins apply false)
│   ├── settings.gradle.kts                                (Xpenz, include :app)
│   ├── gradle.properties                                  (JVM, parallel, R8 full mode)
│   ├── gradle/libs.versions.toml                          (108 deps, 52 versions, 5 bundles)
│   ├── gradle/wrapper/gradle-wrapper.properties            (Gradle 8.5)
│   └── app/
│       ├── build.gradle.kts                               (com.xpenz.app, minSdk 26, compileSdk 34)
│       ├── proguard-rules.pro                             (Firebase/Retrofit/Moshi/TFLite/Compose)
│       └── src/main/
│           ├── AndroidManifest.xml                        (9 permissions, single activity)
│           ├── res/values/strings.xml, themes.xml
│           ├── res/values-night/themes.xml
│           ├── res/xml/backup_rules.xml, data_extraction_rules.xml
│           └── kotlin/com/xpenz/app/
│               ├── XpenzApplication.kt                    (@HiltAndroidApp)
│               ├── MainActivity.kt                        (@AndroidEntryPoint, edge-to-edge)
│               ├── navigation/XpenzNavHost.kt              (12 Screen routes)
│               ├── di/                                    (5 modules: Database, Firebase, Repository, DataStore, Coroutine)
│               ├── core/common/                           (XpenzResult, DateTimeUtil, Extensions, AppConstants)
│               ├── core/domain/model/                     (User, Transaction, Family, FamilyMember, Budget, MLCategory)
│               ├── core/domain/repository/                (5 interfaces)
│               ├── core/database/entity/                  (6 Room entities — MVP tables)
│               ├── core/database/dao/                     (6 DAOs)
│               ├── core/database/converter/Converters.kt
│               ├── core/database/XpenzDatabase.kt          (Room DB, version 1, 6 entities)
│               ├── core/data/mapper/EntityMappers.kt       (12 extension fns)
│               ├── core/data/repository/                  (5 impl classes)
│               ├── core/datastore/UserPreferencesDataStore.kt (8 prefs)
│               ├── core/security/EncryptionService.kt      (AES-256-GCM, Android Keystore)
│               └── ui/                                    (theme/ + components/)
├── docs/
│   ├── 01 - Technical Requirements Document (TRD).md      (10,094 lines)
│   ├── 02 - Tech Stack.md                                  (619 lines)
│   ├── 03 - App Flow Documentation.md                     (1,762 lines)
│   ├── 04 - Backend Schema Documentation.md               (2,641 lines)
│   ├── 05 - Visual Diagrams & Authentication Flows.md     (1,251 lines)
│   ├── 06 - Implementation Plan (20-Week Roadmap).md      (1,724 lines)
│   ├── 07 - MVP Definition.md                             (1,689 lines)
│   ├── 08 - Product Requirements Document (PRD).md        (14,861 lines)
│   ├── 09 - ML Architecture Specification.md              (CANONICAL — supersedes ML in TRD & PRD)
│   └── 10 - Admin Dashboard Architecture.md               (~1,800 lines — admin web app spec)
├── UI-UX/
│   ├── [47 mobile screen folders]/                         (each has code.html + screen.png)
│   │   └── All 47 have dark mode CSS injected + toggle button
│   └── admin/
│       ├── admin_login/code.html
│       ├── admin_dashboard_home/code.html
│       ├── admin_user_list/code.html
│       ├── admin_user_detail/code.html
│       ├── admin_ml_dashboard/code.html
│       ├── admin_support_tickets/code.html
│       ├── admin_revenue_dashboard/code.html
│       ├── admin_feature_flags/code.html
│       └── admin_security_audit/code.html
├── scripts/
│   ├── inject-dark-mode.ps1                               (deprecated — parse errors)
│   └── inject_dark_mode.py                                (ran successfully on all 47 screens)
├── XPENZO - UPI Based Expense Tracker.md                  (monolithic source doc)
└── .github/
    ├── agents/
    ├── context/
    │   ├── project-context.md   ← YOU ARE HERE
    │   └── chat-history.md
    └── instructions/
        └── copilot-instructions.md
├── ml/
│   ├── taxonomy/
│   │   └── category_taxonomy.json                          (520 L3 categories, 80 L2, 15 L1)
│   ├── data_collection/
│   │   ├── scripts/
│   │   │   ├── 01_osm_extractor.py                        (OSM India PBF parser, ~280 lines)
│   │   │   ├── 02_phonepe_pulse_parser.py                 (PhonePe Pulse 4-type parser, ~320 lines)
│   │   │   ├── 03_web_scrapers.py                         (Swiggy/Zomato/Practo/JustDial/Sulekha, ~500 lines)
│   │   │   ├── 04_data_gov_downloader.py                  (9 govt datasets + API, ~300 lines)
│   │   │   ├── 05_google_maps_api.py                      (Google Places API, 20 cities, ~280 lines)
│   │   │   ├── 06_wikidata_query.py                       (14 SPARQL queries, ~350 lines)
│   │   │   ├── 07_master_pipeline.py                      (Orchestrator, merge, dedup, stats, ~400 lines)
│   │   │   ├── 08_label_dataset.py                        (5-layer cascade labeler, ~580 lines)
│   │   │   ├── 09_synthetic_generator.py                  (synthetic data for unused/low-count L3, ~535 lines)
│   │   │   ├── 10_feature_engineering.py                  (feature eng + stratified split + tokenizer, ~537 lines)
│   │   │   ├── 11_train_cht_model.py                      (CHT v3 model training + TFLite export, ~715 lines)
│   │   │   ├── 12_train_cht_v4_optimized.py               (CHT v4/v5 optimized multi-round training, ~850 lines)
│   │   │   ├── 13_enhanced_data_generator.py              (Enhanced synthetic v2, domain-specific merchants, ~700 lines)
│   │   │   └── 14_rebuild_dataset.py                      (Merge all sources + rebuild pipeline, ~280 lines)
│   │   ├── raw/
│   │   │   ├── osm/                                       (needs india-latest.osm.pbf download)
│   │   │   ├── phonepe_pulse/                             (9,029 files cloned from PhonePe/pulse)
│   │   │   ├── npci/upi_handles.json                      (95+ PSP handles + SMS regex)
│   │   │   ├── data_gov_in/                               (needs script run)
│   │   │   ├── google_maps/                               (needs GOOGLE_MAPS_API_KEY)
│   │   │   ├── wikidata/                                  (needs script run)
│   │   │   ├── swiggy/ zomato/ practo/ justdial/ indiamart/
│   │   │   └── (all raw/ subdirs empty until scripts run)
│   │   ├── processed/                                     (master_dataset.csv after pipeline)
│   │   └── labeled/                                       (labeled_dataset.csv + synthetic_dataset.csv + label_stats.json)
│   ├── training/                                          (combined_dataset.csv, train/val/test.csv, tokenizer/, label_encoders.json, class_weights.json)
│   └── models/                                            (xpenz_cht_v3.keras, .tflite, training_history.json, evaluation_report.json, training_log.csv)
```

---

## 🗄️ Database Schema

### Firestore Collections (Cloud)
```
/users/{userId}              → Profile, premium status, device count
  /devices/{deviceId}        → FCM tokens, device info
  /preferences               → UI prefs, notification settings, privacy
/families/{familyId}
  /info                      → Family name, invite code, settings (require_approval: true)
  /members/{memberId}        → Role (ADMIN/MEMBER), status, spending counters (FieldValue.increment)
  /transactions/{txnId}      → Amount, category, ML confidence, visibility (FAMILY|PRIVATE), corrected_by, encrypted_data
  /budgets/{budgetId}        → 3 types (FAMILY/CATEGORY/MEMBER), alerts at 50/80/100/120%
  /budget_progress/{id}      → Calculated by Cloud Functions only
  /sync_metadata             → Last sync timestamps, active devices, conflicts
/invitations/{code}          → max_uses: 1 (default single-use), expires 7 days
/ml_corrections/{id}         → Training feedback (write-only from clients)
/notifications/{id}          → FCM + in-app notifications
/subscriptions/{id}          → Google Play purchase verification
/system/config               → Feature flags, pricing, version control
  /ml_models/{version}       → Model URLs, accuracy metrics, rollout %
```

### Room Tables (Local — 11 in full, 6 in MVP)
Users, Transactions, Families, FamilyMembers, Budgets, MLCategories, SMSPatterns, Subscriptions, BudgetProgress, Notifications, SyncQueue

### Key Schema Decisions (from previous review)
- `TransactionDocument.visibility`: `'FAMILY' | 'PRIVATE'` — per-transaction privacy toggle
- `TransactionDocument.corrected_by`: tracks who corrected a category (may differ from owner)
- `FamilyInfoDocument.settings.require_approval`: defaults to `true` (admin must approve joins)
- `InvitationDocument.max_uses`: defaults to `1` (single-use per code)
- Counter fields (`total_transactions`, `total_spending`, etc.): must use `FieldValue.increment()`

---

## 📡 API Contracts (Cloud Functions — Callable)

| Function | Type | Purpose |
|----------|------|---------|
| `createFamily` | Callable | Create family + generate invite code |
| `joinFamily` | Callable | Validate code + add member |
| `generateInvitationCode` | Callable | Regenerate invite code for family |
| `verifyPurchase` | Callable | Verify Google Play purchase token |
| `exportData` | Callable | Premium — generate PDF/Excel export |
| `cancelSubscription` | Callable | Cancel + log reason |
| `restorePurchase` | Callable | Restore premium status |
| `onTransactionCreate` | Trigger | Update budgets, send alerts, notify family |
| `onUserCreate` | Trigger | Initialize new user |
| `onFamilyCreate` | Trigger | Family setup |
| `onMemberAdd` | Trigger | Welcome notification |
| `onSubscriptionChange` | Trigger | Premium activation/deactivation |
| `dailyBudgetCheck` | Scheduled | Daily budget status check |
| `weeklyReports` | Scheduled | Premium email reports |
| `cleanupExpiredInvitations` | Scheduled | Remove expired codes |
| `syncMLCorrections` | Scheduled | Aggregate ML feedback |
| Webhook: `playBilling` | HTTP | Google Play RTDN handler |

---

## 🔒 Encryption
- **Method:** AES-256-GCM, client-side before Firestore write
- **Key Derivation:** HKDF(Firebase UID + server-side salt) → 256-bit key
- **Key Caching:** Android Keystore (hardware-backed on API 28+)
- **Phone Migration:** Same UID → same derived key → seamless
- **Account Deletion:** UID invalidated + salt revoked → key unrecoverable
- **Key Rotation:** Annual server-side salt rotation, re-encryption via Cloud Function

---

## 🔐 Auth & Roles
- **Auth method:** Firebase Phone Auth (OTP, 6-digit, 3 attempts then 15-min lockout)
- **Roles:** ADMIN (family creator + promoted), MEMBER (joined via invite)
- **Security Rules:** Firestore rules enforce: owner-only for users, family-member check for families, privacy (`visibility == 'FAMILY' || user_id == auth.uid`) for transactions

---

## 🎨 UI Conventions
- **Framework:** Jetpack Compose (100% declarative)
- **Design System:** Material 3 (Material You)
- **Navigation:** Compose Navigation + Hilt Navigation
- **Onboarding:** 5 screens (Phone → OTP → Profile → SMS Permission + Historical Import + Notification Listener fallback → Family Setup → Dashboard)
- **Deferred prompts:** Battery optimization (on late SMS), Location (on transaction detail tap), Tutorial (replaced by dashboard tooltips)
- **Category UX:** 3-level hierarchy (15 → 80 → 520), never flat 520-item list, search bar auto-jumps

---

## ⚙️ Environment Variables
> Never store real values here — just variable names and descriptions
```
FIREBASE_APP_ID               → Firebase app identifier
FIREBASE_TOKEN                → CI/CD deployment token
SIGNING_KEY (base64)          → Android release keystore
KEY_ALIAS                     → Keystore alias
KEY_STORE_PASSWORD             → Keystore password
KEY_PASSWORD                   → Key password
SERVICE_ACCOUNT_JSON           → Google Play Console service account
HKDF_SALT                     → Server-side encryption salt (Cloud Functions env only)
GOOGLE_PLAY_DEVELOPER_API_KEY → For purchase verification
```

---

## ✅ Completed Features (Documentation Phase)
- [x] Complete PRD with 14 sections + DPDP compliance + Firebase cost model — Feb 2026
- [x] Tech Stack documented (112 deps after Gson removal) — Feb 2026
- [x] App Flow rewritten: 5-screen onboarding + deferred prompts — Mar 2026
- [x] Backend Schema: privacy fields, encryption key lifecycle, counter annotations — Mar 2026
- [x] Security Rules: privacy-aware transaction reads — Mar 2026
- [x] Implementation Plan: 20-week roadmap (10 sprints) — Feb 2026
- [x] MVP Definition: 12-week plan (6 sprints), 8 core features — Feb 2026
- [x] Visual Diagrams & Auth Flows — Feb 2026
- [x] ML Architecture Specification v3.0 — Mar 2026 (replaces ML sections in TRD & PRD)
- [x] All 13 second-pass doc flaw fixes applied — Mar 2026 (TRD, Tech Stack, App Flow, Backend Schema, Impl Plan, MVP Def, PRD)
- [x] Admin Dashboard Architecture doc (docs/10) — Mar 2026
- [x] 9 Admin UI-UX HTML mockup screens with dark mode — Mar 2026
- [x] Dark mode CSS injected into all 47 mobile UI screens — Mar 2026
- [x] Sprint 0: Android project scaffolded (58 files) — Mar 2026
  - Gradle (version catalog, 108 deps, build variants, ProGuard)
  - MVVM + Clean Architecture (domain/data/database/di/ui layers)
  - Room DB (6 MVP tables, DAOs, TypeConverters)
  - Hilt DI (5 modules: Database, Firebase, Repository, DataStore, Coroutine)
  - DataStore preferences (8 keys)
  - EncryptionService (AES-256-GCM, Android Keystore)
  - Navigation (12 screen routes)
  - Theme (Xpenz brand colors, Manrope+Lora typography, light/dark)
  - Base components (TopBar, Button, Loading, Error)
- [x] ML Data Collection Pipeline (7 scripts) — Mar 2026
  - Script 01: OSM India PBF extractor (osmium-based, 50+ place types)
  - Script 02: PhonePe Pulse parser (4 data types, state/district rollup)
  - Script 03: Web scrapers (Swiggy/Zomato/Practo/JustDial/Sulekha, 25 cities)
  - Script 04: data.gov.in downloader (9 govt datasets, API + direct download)
  - Script 05: Google Maps Places API (20 Indian cities, free tier 28K req/month)
  - Script 06: Wikidata SPARQL (14 queries, 100% free, no API key)
  - Script 07: Master pipeline orchestrator (merge, deduplicate, stats)
  - NPCI UPI handles JSON (95+ PSP handles + SMS regex patterns)
  - PhonePe Pulse data cloned (9,029 files, 100% complete)
- [x] 520-Category Taxonomy JSON — Mar 2026
  - 15 L1 → 80 L2 → 520 L3 hierarchical taxonomy
  - Each L3: id, code, name, keywords[], example_merchants[]
  - India-specific categories (kirana, chai tapri, auto rickshaw, etc.)
  - JSON validated: all 520 unique IDs, proper hierarchy
- [x] Pyright Strict Mode — All 8 Python files pass with 0 errors — Mar 2026
  - `pyrightconfig.json` created (typeCheckingMode: strict, pythonVersion: 3.14)
  - 840 total errors fixed across 8 files (inject_dark_mode.py + 7 ML scripts)
  - Full type annotations on all functions, params, returns
  - `# type: ignore[import-untyped]` for osmium, bs4, tqdm, pandas
  - `cast()` pattern for bs4/JSON isinstance narrowing (prevents Unknown cascade)
  - pyright 1.1.408 installed in venv
- [x] Dataset Labeling Complete — 418,645 records labeled — Mar 2026
  - Script: `08_label_dataset.py` — 5-layer cascade: brand(0.95) → rules(0.85) → cuisine(0.85) → keywords(0.60-0.80) → fallback(0.30)
  - Match methods: rule_cat_sub 93.2%, brand_substring 3.0%, fallback 1.6%, name_keyword 1.5%, brand_exact 0.4%
  - 411 of 520 L3 categories used, avg confidence 0.84
  - 96.4% records labeled at ≥0.80 confidence, only 1.6% at fallback (0.30)
  - L1 distribution: Healthcare 28.6%, Food 15.0%, Shopping 13.6%, Education 10.7%, Family/Social 9.9%
  - Output: `labeled_dataset.csv` (73.1 MB) + `label_stats.json`
  - Pyright strict: 0 errors
- [x] Synthetic Data Generation — 74,437 records for 422 categories — Mar 2026
  - Script: `09_synthetic_generator.py` — fills 109 unused + 313 low-count L3 categories
  - 25 Indian cities with lat/lon, 32 Indian name prefixes, domain-specific business suffixes
  - Augmentation: truncation, abbreviation, typo injection, case variation, Hindi transliteration
  - Target: min 200 records per L3 category, augmentation_factor=5
  - Output: `synthetic_dataset.csv` (13.2 MB, 74,437 records)
- [x] Feature Engineering + Train/Val/Test Split — 493,082 records — Mar 2026
  - Script: `10_feature_engineering.py` — merges labeled + synthetic datasets
  - Text normalization, 16-dim numerical features (per docs/09 §5.4)
  - SentencePiece BPE tokenizer (vocab=8192, character_coverage=0.9995)
  - Label encoding: L1(15), L2(80), L3(520) code → integer mappings
  - Class weights: sqrt inverse frequency, normalized mean=1.0
  - Stratified split: Train 419,120 / Val 49,307 / Test 24,655 (85/10/5)
  - L3 coverage: 520/520 in all splits, min train count 168, max 66,988
  - Output: combined_dataset.csv, train.csv, val.csv, test.csv, tokenizer/, class_weights.json, label_encoders.json, split_stats.json
  - Pyright strict: 0 errors
- [x] CHT Model Training Script — Mar 2026
  - Script: `11_train_cht_model.py` — full training pipeline per docs/09
  - TransformerBlock (MHA + FFN + LayerNorm + Dropout), 3 layers, d=128, heads=4, ff=256
  - Hierarchical heads: L1(15) → L2(80, conditioned on L1) → L3(520, conditioned on L2)
  - Multi-task loss: α=0.15 L1 + β=0.25 L2 + γ=0.60 L3
  - AdamW (lr=3e-4, wd=0.01), cosine warmup (2000 steps), 50 epochs
  - INT8 + FP16 hybrid TFLite quantization, ~3.2 MB target
  - Evaluation: L1/L2/L3 top-1, L3 top-3/top-5, hierarchy consistency
  - Output: xpenz_cht_v3.keras, xpenz_cht_v3.tflite, training_history.json, evaluation_report.json
  - Keras 3 compatibility: uses `keras.ops` (not `tf.*`), standalone `import keras` (not `tf.keras`)
  - Pyright strict: 0 errors
  - Status: TRAINED (5 epochs, CPU, batch 512)
- [x] TensorFlow Installed + CHT Model Trained (5 epochs, CPU) — Mar 2026
  - `.venv-tf/` created with Python 3.11 (TF doesn't support 3.14)
  - TensorFlow 2.21.0 + Keras 3.13.2 + sentencepiece 0.2.1 installed
  - CPU-only (no GPU on native Windows for TF ≥2.11)
  - Training: 33.2 minutes, 5 epochs, batch_size=512
  - **Test set results (24,655 samples):**
    - L1 Top-1: **81.89%**, L2 Top-1: **73.25%**, L3 Top-1: **68.81%**
    - L3 Top-3: **83.03%**, L3 Top-5: **86.45%**
    - Hierarchy consistency: **48.59%**
  - TFLite exported: `xpenz_cht_v3.tflite` (**3.98 MB**, INT8+FP16 hybrid)
  - Keras model: `xpenz_cht_v3.keras` (23.8 MB)
  - Files: training_history.json, evaluation_report.json, training_log.csv, xpenz_cht_v3_best.keras
  - Note: This is a 5-epoch CPU verification run; full 50-epoch GPU training recommended for production
- [x] CHT v4 Quick Test Complete + Full Pipeline Running — Mar 2026
  - Script: `12_train_cht_v4_optimized.py` (~750 lines) — comprehensive multi-round training
  - v3 baseline bugs found: label_smoothing never applied, class_weights unused, only 5 epochs
  - v4 architecture: Pre-LayerNorm Transformer, SpatialDropout1D, deeper residual heads, learned L1/L2 context embeddings, GELU, BatchNorm in numerical branch
  - v4 training: Focal loss (gamma=2.0) with label smoothing (0.05) + baked class weights, data augmentation (token masking 15% + numerical noise std=0.05), SWA, cosine warmup, gradient clipping (clipnorm=1.0), EarlyStopping patience=20
  - Model: 2,526,695 params (9.64 MB), batch_size=256
  - Fixed Keras 3 KeyError: 0 (sample_weight bug → baked class weights into focal loss via tf.gather)
  - **Quick Test Results (10 epochs, 86.4 min, test set):**
    - L1: **82.6%** (+0.7% vs v3), L2: **74.2%** (+0.9%), L3: **67.7%** (-1.1%)
    - L3-Top3: **82.6%**, L3-Top5: **86.4%**
    - **Hierarchy Consistency: 90.8%** (+42.2% vs v3's 48.6%) — massive improvement
    - TFLite: 4.89 MB
    - All outputs: best.keras, final.keras, model.tflite, evaluation_report.json, etc.
  - **Full Pipeline Running** (terminal `ff7d7cf2-4386-4637-9e7f-1ad05bb75c60`):
    - Round 1 (80ep 3-layer) → Round 2 (40ep finetune) → Round 3 (80ep 4-layer) → Round 4 (conditional)
    - Estimated ~25 hours total for all rounds
    - Currently in Round 1, epoch 1
- [x] Data Enrichment + CHT v5 Training Launched — Mar 2026
  - Script: `13_enhanced_data_generator.py` — comprehensive synthetic data v2
  - 130,213 new records for 441 underrepresented L3 categories (target min 500 per category)
  - Real Indian merchant databases per L1 domain (500+ names/domain), UPI-style augmentation
  - Script: `14_rebuild_dataset.py` — combined all 3 sources, deduped, rebuilt features
  - **Enriched dataset: 570,288 total records** (was 493,082) | Train: 484,735 | Val: 57,028 | Test: 28,525
  - L3 min count: 344 (was ~20), L3 median count: 419 (was ~170)
  - SentencePiece tokenizer retrained on enriched data
  - **CHT v5 training launched** (terminal `fa4f7148-d71e-4c69-b009-8e2b2667cf71`):
    - Round 1: 50ep, 3-layer, batch=512, 504ms/step, patience=15
    - Round 2: 25ep fine-tune (lower LR, less augmentation)
    - Round 3: 50ep, 4-layer architecture experiment
    - Round 4: 25ep fine-tune 4-layer (conditional if R3 beats R1)
    - Estimated ~7-8 hours per round (947 steps/epoch)

---

## 🚧 In Progress
- [x] Sprint 0 scaffolding complete (58 files)
- [ ] Add `google-services.json` (requires Firebase project creation)
- [ ] Sprint 1: Phone Auth + OTP verification
- [ ] Sprint 1: SMS BroadcastReceiver + transaction parsing
- [ ] Sprint 1: Dashboard home screen
- [ ] Context files kept up to date

---

## 📌 Key Decisions Made
| Decision | Reason | Date |
|----------|--------|------|
| Gson removed, Moshi + kotlinx-serialization kept | Avoid 3 JSON libs; Moshi for Retrofit, kotlinx for internal | Mar 2026 |
| Onboarding reduced from 9 → 5 screens | Faster time-to-dashboard (≤90s target); battery/location/tutorial deferred | Mar 2026 |
| Per-transaction `PRIVATE` visibility toggle added | Families need some privacy for personal purchases | Mar 2026 |
| `require_approval` defaults to `true` | Prevent unauthorized family joins | Mar 2026 |
| `max_uses` defaults to 1 (single-use invite codes) | Security — prevent code sharing/abuse | Mar 2026 |
| HKDF key derivation (UID + server salt) | Neither Google nor server alone can decrypt; no key at rest | Mar 2026 |
| NotificationListenerService as SMS fallback | Android 13+ may restrict READ_SMS; dual-channel mitigation | Mar 2026 |
| iOS deferred indefinitely | iOS restrictions make similar UPI/SMS tracking infeasible | Mar 2026 |
| Ads strategy deferred | Needs dedicated analysis; excluded from current review | Mar 2026 |
| ML architecture: CHT + Rules + Habits + ATP (v3) | New spec `docs/09` replaces both TRD (LSTM+CNN+Transformer) and PRD (DNN+BERT). 4.0 MB, <50ms, 3-level hierarchy | Mar 2026 |
| Admin Dashboard: Next.js 14 + shadcn/ui + Firebase | Separate web app at admin.xpenz.app for 5 admin roles, 12 modules (42 screens), 87 Cloud Function endpoints | Mar 2026 |
| Dark mode via CSS override injection | All 47 mobile HTML mockups get `<style id="xpenz-dark-mode">` + toggle button. Uses `html.dark` class + CSS overrides rather than per-element `dark:` variants | Mar 2026 |
| Admin design tokens: Manrope + #1b3fc0 primary | Consistent across all 9 admin screens. Mobile screens have varying primaries (#4f46e5, #1D40C0, #1d40bf) — preserved as-is | Mar 2026 |
| Room entities store enums as String (name) not ordinal | Human-readable DB, query-friendly (`WHERE type = 'DEBIT'`), survives enum reordering | Mar 2026 |
| Room schema export enabled + KSP arg for schema dir | Enables migration test JSON generation under `app/schemas/` | Mar 2026 |
| ML data: $0 budget, 29 free sources | OSM, PhonePe Pulse, data.gov.in, Google Maps free tier, Wikidata, web scraping. Labeling via Copilot Pro + Gemini (~30K labels/hr) | Mar 2026 |
| LLM for labeling only, CHT is custom model | LLM never on device; CHT (3.2MB TFLite, 2.05M params) trained by us, runs 100% offline | Mar 2026 |
| Dual venv: `.venv/` (Python 3.14, pyright) + `.venv-tf/` (Python 3.11, TF) | TensorFlow has no Python 3.14 build; separate venv for training | Mar 2026 |
| Keras 3 standalone: `import keras` + `keras.ops` | TF 2.21 ships Keras 3 which disallows `tf.*` ops on KerasTensors; must use `keras.ops` namespace | Mar 2026 |
| 520-category taxonomy: 15 L1 → 80 L2 → 520 L3 | Covers all Indian expense categories (food, transport, shopping, healthcare, etc.) with India-specific granularity | Mar 2026 |
| Pyright strict mode enforced for all Python | Type safety catches bugs early; `pyrightconfig.json` at project root; `cast()` pattern for bs4/JSON narrowing | Mar 2026 |
| Rule-Based Cascade labeling (5 layers) | $0 cost, deterministic, reproducible. Brand→Rules→Cuisine→Keywords→Fallback. 93.2% via rules, 98.4% above fallback | Mar 2026 |
| Synthetic data for 422 categories (109+313) | Min 200 records per L3 — augmented merchant names with Indian-specific patterns. 74,437 synthetic records generated | Mar 2026 |
| 85/10/5 stratified split by L3 code | Ensures all 520 L3 categories present in every split. Total: 493,082 records | Mar 2026 |
| SentencePiece BPE tokenizer (vocab=8192) | Consistent with docs/09 spec. Trained on 493K merchant names. Character coverage 99.95% | Mar 2026 |
| sqrt inverse frequency class weights | Upweights rare categories without over-amplifying noise. Normalized mean=1.0 | Mar 2026 |
| Data enrichment: min 500 per L3 | 441/520 categories were below 500 samples. Generated 130K new records with domain-specific merchants and UPI augmentation | Mar 2026 |
| v5 naming: fresh retrain on enriched data | New tokenizer + new data distribution = must train from scratch. v5 = models trained on 570K enriched dataset | Mar 2026 |
| Batch size 512 for CPU training | 504ms/step on 15.6GB RAM system. 256→512 halved epoch time from ~16min to ~8min with negligible accuracy impact | Mar 2026 |

---

## ⚠️ Known Issues & TODOs
> Found during second-pass review on 2026-03-08 by Context Manager

### Critical
- [x] **ML architecture mismatch:** RESOLVED — New `docs/09` supersedes both. CHT + Rule Engine + Habits + ATP = 4.0MB total.
- [x] **Model size contradiction:** RESOLVED — v3 spec: 4.0MB total (under 5MB limit).
- [x] **Account deletion excluded from MVP:** RESOLVED — Added to MVP Feature 8 as row 9 (MUST, Critical) with full data purge flow.

### High
- [x] **Onboarding "9 screens" in 4+ locations:** RESOLVED — All updated to 5 screens across TRD, App Flow, Impl Plan.
- [x] **"Complete Transparency — No privacy" conflicts with PRIVATE toggle:** RESOLVED — PRD updated to acknowledge PRIVATE toggle.
- [x] **NotificationListenerService missing from TRD, Tech Stack, Sprint plan:** RESOLVED — Added dual-channel Section 6.3 in Tech Stack.
- [x] **No rate limiting on Cloud Functions:** RESOLVED — Added Section 5.4 in Backend Schema with per-function rate limits.

### Medium
- [x] **Invitation example data contradicts max_uses=1:** RESOLVED — Example corrected to current_uses: 1.
- [x] **MVP says "roles = post-MVP" but schema uses roles:** RESOLVED — Roles confirmed as MVP scope.
- [x] **Two competing timelines (12-week MVP vs 20-week full):** RESOLVED — Timeline clarification added to MVP doc.
- [x] **Cloud Functions base URL region wrong:** RESOLVED — Changed to asia-south1.

### Low
- [x] **Dependency count table wrong:** RESOLVED — JSON 4→3, Networking 5→4, Accompanist 6→2, Total 114→108.
- [x] **Stale Accompanist libraries:** RESOLVED — 4 deprecated libs removed (systemuicontroller, navigation-animation, swiperefresh, flowlayout). 2 kept (permissions, placeholder-material).
- [x] **`project-context.md` was unpopulated:** Fixed.
- [x] **`chat-history.md` had no entries:** Fixed.
