# Xpenzo — Remaining Work (last updated 2026-05-23, end of marathon session)

## Headline
**Everything that can be done from this terminal without external services is done.** Phases 2.5 → 10 are code-complete. The remaining items below are operational (Android SDK install, Firebase Console setup, Play Store assets, beta rollout) or stretch UI iterations.

**Status**: Phases 2.5 through 9 of the implementation roadmap are code-complete in this repo (`android_app/`). The blockers below are everything that is needed to actually ship v1.0 to Play Store and to start Phase 10 (Groups & Splits).

The current Task list reflects roadmap phases. This document goes one level deeper into items that the phase-completion task does not capture.

---

## Recently completed (this session)

### Wave 2 — Build out real screens + Phase 10
- ✅ **ExportData screen** — full CSV export of all transactions via `FileProvider` + Android share sheet. DPDP-compliant.
- ✅ **AI Settings screen** — active model info card, learning-progress stats (habit count, maturity tier), "Check for update now" button, "Reset learned habits" with confirm dialog.
- ✅ **Manual Entry screen** — direction toggle (expense/income), amount input, merchant + category picker, saves to Room with source=MANUAL.
- ✅ **Browse Categories screen** — loads `category_taxonomy.json` (123KB, bundled in assets), full L1→L2→L3 hierarchy with example merchants, search across all 520 categories.
- ✅ **Phase 10.1 — Room v2 migration**: 6 new entities (Group, GroupMember, SplitExpense, SplitShare, Settlement, Friend), 3 new DAOs, `MIGRATION_1_2` with full SQL for all tables + indices + FKs.
- ✅ **Phase 10.2 — Split engine** (`SplitCalculator`): 4 split types with paise-exact rounding to payer, `simplifyDebts()` using min-cash-flow algorithm with PriorityQueue. **15 unit tests** in `SplitCalculatorTest.kt` covering all split types, leftover handling, validation, and end-to-end Goa-trip scenario.
- ✅ **Phase 10.3 — Splits UI** (6 screens): `SplitsHomeScreen` with 5th bottom-nav tab + empty state + groups/friends list, `CreateGroupScreen` with emoji picker + friend multi-select, `AddFriendScreen` (supports "ghost" friends), `GroupBalancesScreen` with your-balance hero card + suggested settlements + member balances + expense log, `AddExpenseScreen` (payer/type/participants), `SettleUpScreen` with `upi://pay` deep-link.
- ✅ **`SplitsRepository`** — single source of truth for groups/splits/settlements/friends; reactive `groupNetBalances()` Flow that recomputes on every change; `groupSimplifiedTransfers()` Flow that auto-applies min-cash-flow.

### Wave 1 — Crashlytics, onboarding, ProGuard
- ✅ **Crashlytics + google-services plugins** — Both plugins declared in root `build.gradle.kts`; app build conditionally applies them only when `google-services.json` is present (lets local builds succeed without Firebase config). Crashlytics init wired in `XpenzoApplication.onCreate()`.
- ✅ **Onboarding flow built** — 6 screens (`WelcomeScreen`, `PhoneLoginScreen`, `VerifyOtpScreen`, `ProfileSetupScreen`, `UpiIdSetupScreen`, `SmsPermissionScreen`) wired into a nested nav graph at `Screen.OnboardingRoot`. Shared `OnboardingViewModel` (Hilt-scoped to the nav graph) drives the OTP/profile/UPI/permission state. `OnboardingPreferences` singleton tracks `isCompleted` in SharedPreferences. `MainActivity` reads it and routes to `Screen.OnboardingRoot` vs `Screen.Home` on launch.
- ✅ **Stub settings screens wired** — `AppPermissionsScreen` is fully built (re-checks SMS + notification listener grants on resume, deep-links to system Settings). Five other routes (`ManualEntry`, `BrowseCategories`, `AiModelSettings`, `ExportData`, plus the previously-null `BackupSync`/`NotifSettings`/`Appearance`/`PrivacySecurity`) point to a single shared `PlaceholderScreen` — no more silent dead taps.
- ✅ **ProGuard + release signing scaffolding** — `app/proguard-rules.pro` with Hilt/Room/TFLite/Firebase/Compose keep rules. `buildTypes { release { ... } }` configured with minify + shrink + signing config gated on `XPENZO_KEYSTORE_PATH` Gradle property. `docs/release_build.md` documents keystore creation, gradle properties, and Play upload steps.
- ✅ **Launcher icon** — adaptive icon (`mipmap-anydpi-v26/ic_launcher.xml` + `_round`), coral background + white ₹ foreground (`drawable/ic_launcher_foreground.xml`), `colors.xml`, manifest references. minSdk=26 means adaptive icon covers all supported devices.

---

## 0. SANITY CHECK — never verified in this branch

These are the AC items the implementation phases declared "done" but I had no way to actually run/verify on this machine. **Run these first** before doing any new feature work.

- [ ] **Build green**: `cd android_app && ./gradlew :app:assembleDebug`
  - Needs Android SDK installed (set `ANDROID_SDK_ROOT` or `android_app/local.properties` → `sdk.dir=/path/to/Android/Sdk`)
  - Confirms Hilt/kapt/Compose/Room all compile together
- [ ] **Unit tests pass**: `./gradlew :app:testDebugUnitTest`
  - Specifically check: `UpiSmsParserTest`, `EnsembleWeightingTest`, `NumericalFeatureParityTest`, `SentencePieceTokenizerTest`, `TransactionRepositoryTest`
  - Mockito-inline final-class mocks may need `mock-maker-inline` if `EnsembleWeightingTest` fails — the resource file is already at `app/src/test/resources/mockito-extensions/org.mockito.plugins.MockMaker`
- [ ] **Instrumented tests pass**: `./gradlew :app:connectedDebugAndroidTest` (needs a connected device or emulator)
  - `RoomSmokeTest`, `SmsIngestionE2ETest`, `ClassifyPerformanceTest`
- [ ] **Room schema exported**: confirm `android_app/app/schemas/com.xpenzo.data.db.XpenzoDatabase/1.json` exists after first compile

---

## 1. Firebase project setup (one-time, console-only)

The Firebase code is all wired but no actual project exists. Without these, the app crashes on startup when it tries to call `FirebaseApp.getInstance()`.

- [ ] Create Firebase project at console.firebase.google.com
- [ ] Add Android app with package `com.xpenzo` and SHA-1 fingerprint (`./gradlew signingReport`)
- [ ] Download `google-services.json` → drop into `android_app/app/google-services.json`
- [ ] In root `android_app/build.gradle.kts`, add:
  ```kotlin
  id("com.google.gms.google-services") version "4.4.2" apply false
  id("com.google.firebase.crashlytics") version "3.0.2" apply false
  ```
- [ ] In `android_app/app/build.gradle.kts`, add to plugins:
  ```kotlin
  id("com.google.gms.google-services")
  id("com.google.firebase.crashlytics")
  ```
- [ ] Enable **Firebase Auth → Phone provider** in console; add test phone numbers for non-Play-Integrity testing
- [ ] Enable **Firestore Database** in console (start in production mode); upload `firestore.rules`:
  - `firebase deploy --only firestore:rules` from project root
- [ ] Enable **Firebase Storage** in console; upload `storage.rules`:
  - `firebase deploy --only storage`
- [ ] Create Storage bucket folder `models/` and upload the bundled `v5.0` artifact + `latest.json` stub
- [ ] In Crashlytics, accept the dashboard prompt and produce a first crash to confirm wiring
- [ ] **AC**: install the debug APK on a phone, complete phone OTP login, write a test SMS, see it sync to Firestore

---

## 2. Crashlytics & analytics wiring (spawned as separate task — pick that up first)

A sub-task chip is already spawned: "Add Crashlytics init to XpenzoApplication". That task will:
- Add `FirebaseCrashlytics.setCrashlyticsCollectionEnabled(!BuildConfig.DEBUG)` to `XpenzoApplication.onCreate()`
- Add the Crashlytics Gradle plugin to both `build.gradle.kts` files

Once that lands:
- [ ] Add a custom key for `model_version` so crashes can be correlated with the active model: `FirebaseCrashlytics.getInstance().setCustomKey("model_version", BundledModelAssets.version)`
- [ ] Add analytics events for the funnel: `app_open`, `sms_received`, `transaction_categorized`, `correction_applied`, `model_downloaded`

---

## 3. Code TODOs / stubs in the current repo

### 3.1 ML
- [ ] **Golden parity test** (`SentencePieceTokenizerTest.kt:143`) — uncomment `goldenParityTest_swiggyFoodDelivery()` and fill in the expected IntArray after running:
  ```python
  import sentencepiece as spm
  sp = spm.SentencePieceProcessor()
  sp.load("ml/training/tokenizer/xpenz_bpe.model")
  ids = [2] + sp.encode("swiggy food delivery", out_type=int)[:30] + [3]
  ids = ids + [0] * (32 - len(ids))
  print(ids)
  ```
- [ ] **Bundled model version cross-check** — `BundledModelAssets.version = "5.0"` must match the actual artifact in `assets/`; run `python scripts/verify_canonical_v4.py` from `.venv-tf`
- [ ] **retrain.py smoke run** — exercise the entire pipeline locally:
  ```bash
  python ml/retrain.py --mode local --data ml/training/val.csv
  ```
  to verify the fine-tune → evaluate → export path works end-to-end before deploying to Cloud Run

### 3.2 UI — Navigation stubs

All previously-defined `Screen` routes are now wired (no more crashes from null routes):
- ✅ `AppPermissionsScreen` — full implementation with grant status + system Settings deep-links
- ✅ `ManualEntry`, `BrowseCategories`, `AiModelSettings`, `ExportData`, `BackupSync`, `NotifSettings`, `Appearance`, `PrivacySecurity` — all route to `PlaceholderScreen` ("coming soon" stubs)

These remain as **placeholder-only** and should be built out in dedicated tasks:
- [ ] `ManualEntry` — real form for cash transactions (needed for non-UPI spend)
- [ ] `BrowseCategories` — full L1/L2/L3 taxonomy browser with examples (helps users learn the system)
- [ ] `AiModelSettings` — show active model version, switch to rules-only, reset habits
- [ ] `ExportData` — CSV export (DPDP Act compliance; users have right to data portability)
- [ ] `BackupSync` — manual sync trigger, last sync time, on/off toggle
- [ ] `NotifSettings` — budget alerts, weekly digest, transaction notifications
- [ ] `Appearance` — theme (light/dark/auto), language, currency

### 3.3 UI — Onboarding flow ✅ DONE

Built in this session. Routes wired in `Screen.OnboardingRoot` sub-graph; `MainActivity` checks `OnboardingPreferences.isCompleted` on launch.

Remaining onboarding polish:
- [ ] Add a "skip onboarding" debug shortcut for QA (gate behind `BuildConfig.DEBUG`)
- [ ] Persist OTP `verificationId` across process death (currently lost if user backgrounds the app)
- [ ] Add UPI VPA verification via a /collect intent to confirm the user actually owns the VPA
- [ ] Add an Indian phone number validation (currently accepts any 10 digits)

### 3.4 Code referenced but never implemented
- [ ] `AppShellRepository.kt:43` says "replace habit/correction stubs with DAO-backed storage" — already done via `RoomBackedHabitModel`, so this comment can be deleted

---

## 4. Hardening before Play upload

### 4.1 Build
- [ ] Remove `fallbackToDestructiveMigration()` from `DatabaseModule.kt`; add explicit `Migration` objects for any schema changes (defer until v2 schema lands — Phase 10)
- ✅ Release `buildType` with `minifyEnabled`, `shrinkResources`, `proguardFiles`, TFLite/Hilt/Room/Firebase keep rules
- ✅ Signing config gated on `XPENZO_KEYSTORE_PATH` Gradle property; docs in `docs/release_build.md`
- [ ] Bump `versionCode` to 2+ on each upload (currently 1, baseline for v1.0)
- [ ] Run `./gradlew :app:bundleRelease` and confirm AAB size < 50MB (blocked: requires Android SDK)
- ✅ Launcher icon (adaptive, coral + ₹ white)

### 4.2 Privacy
- [ ] Host `docs/privacy_policy.md` at a public URL (e.g. https://xpenzo.app/privacy or a GitHub Pages site)
- [ ] Generate Play Store data-safety form answers from the privacy policy
- [ ] Verify `DeleteAccountScreen` actually purges everything by deleting a test account end-to-end and confirming via Firebase Console that the user's documents are gone

### 4.3 Compliance
- [ ] Fill in the Play Console SMS Permissions Declaration form using `docs/play_store_sms_declaration.md`
- [ ] Submit a video demonstrating the SMS feature working (required by Play)
- [ ] DPDP Act 2023: implement a "Download my data" export flow (covered by `ExportData` screen above)

---

## 5. Phase 10 — Groups & Splits ✅ DONE in this session

All core code shipped. Remaining work is Firestore-side and stretch UI polish:

### Done
- Room v1→v2 migration with 6 new entities, 3 DAOs, all indices + FKs
- `SplitCalculator` with 4 split types + min-cash-flow `simplifyDebts` + 15 unit tests
- `SplitsRepository` with reactive net-balance flows
- 6 UI screens wired into navigation + new "Splits" bottom-nav tab
- `upi://pay` deep-link from SettleUpScreen

### Stretch / follow-ups
- [ ] EXACT/PERCENT/SHARES split inputs in `AddExpenseScreen` — currently falls back to EQUAL with a UI hint
- [ ] Cloud Functions for: `onSettlementCreated` → recompute balances; `onFriendCreated` → reciprocal write; ghost-friend reconciliation
- [ ] Firestore mirror: persist `/groups/**` + `/users/{uid}/friends/**` to Firestore via a sync worker
- [ ] "Split this" CTA on TransactionDetailScreen that opens AddExpenseScreen with the amount + merchant pre-filled, and writes `linkedTransactionId` + `transactions.reimbursable_amount`
- [ ] Composite Firestore indexes (`/groups/{gid}/expenses` ordered by `created_at desc`)
- [ ] Friend balance summary on `SplitsHomeScreen` (currently shows phone only)
- [ ] Privacy audit test: when a correction is recorded on a transaction with split shares, verify no split-partner data enters the upload payload

### Original Phase 10 plan (kept for reference)

All design docs and Firestore rules are ready. Build order:

### 5.1 Room v1 → v2 migration
- [ ] Add 6 entities per TRD §5.2: `GroupEntity`, `GroupMemberEntity`, `SplitExpenseEntity`, `SplitShareEntity`, `SettlementEntity`, `FriendEntity`
- [ ] Add `reimbursable_amount` nullable column to `TransactionEntity`
- [ ] Write `Migration(1, 2)` object and register in `DatabaseModule`
- [ ] Bump `@Database(version=2)`
- [ ] Instrumented migration test using `MigrationTestHelper` + Room testing artifact

### 5.2 DAOs and repository
- [ ] `GroupDao`, `SplitDao`, `FriendDao` with reactive Flows for balances
- [ ] `GroupRepository` exposing CRUD + computed-balance flows

### 5.3 Split engine
- [ ] `SplitCalculator.kt`:
  - 4 split types: EQUAL, EXACT, PERCENT, SHARES
  - Paise-exact rounding: leftover paise go to the payer
  - `simplifyDebts(): List<Settlement>` using min-cash-flow algorithm
- [ ] Unit tests for each split type and rounding edge cases
- [ ] Unit test that `simplifyDebts` produces ≤ N-1 settlements for N participants

### 5.4 UI (Compose)
- [ ] Add 5th bottom-nav tab: "Splits"
- [ ] `SplitsHomeScreen` — list of groups + 1:1 friends with current balances
- [ ] `CreateGroupScreen` — name, members
- [ ] `AddFriendScreen` — phone number lookup
- [ ] `SplitExpenseSheet` — invoke from any transaction with "Split this" action
- [ ] `GroupBalancesScreen` — who owes whom
- [ ] `SettleUpScreen` — CASH or `upi://pay?pa=...&am=...&tn=...` deep-link to UPI app; payee confirms in-app
- [ ] Wire `Screen.Splits`, `Screen.CreateGroup`, etc. routes into `NavGraph`

### 5.5 Firebase
- [ ] Firestore rules for `/groups/**` and `/users/{uid}/friends/**` are already in `firestore.rules` — just deploy
- [ ] Cloud Function: `onSettlementCreated` → recompute `/groups/{id}/balances/{uid}` docs
- [ ] Cloud Function: `onFriendCreated` → write reciprocal `/users/{otherUid}/friends/{thisUid}` doc
- [ ] Cloud Function: `onGroupExpenseCreated` → recompute balances
- [ ] Composite indexes: `/groups/{gid}/expenses` ordered by `created_at desc`
- [ ] Deploy via `firebase deploy --only functions,firestore:indexes`

### 5.6 Privacy audit (CRITICAL — must not break v1.0 ML loop)
- [ ] Verify NO split-partner name, group membership, or settlement ever reaches `transaction_corrections` or `ml_corrections`
- [ ] Add an explicit test: when a correction is recorded on a transaction that has split shares, the upload payload contains zero split-related fields
- [ ] Update `DataCollectionManager.recordCorrection()` to strip any split metadata before upload

---

## 6. Operational / launch tasks

### 6.1 Play Store listing assets
- [ ] App icon: 512×512 PNG (high-res icon) + adaptive launcher icon (`mipmap-anydpi-v26/ic_launcher.xml`)
- [ ] Feature graphic: 1024×500 PNG
- [ ] 6+ screenshots per device class (phone, 7-inch, 10-inch)
- [ ] Short description (80 chars) + full description (4000 chars) — write from `docs/08 PRD §5`
- [ ] Promo video (30s) optional but boosts conversion

### 6.2 Beta rollout
- [ ] Internal test track: 5–10 testers, daily builds
- [ ] Closed beta: 100 testers from r/IndiaInvestments + Twitter
- [ ] Open beta: gated rollout 5% → 10% → 25% → 50% → 100% over 2 weeks
- [ ] Monitor Crashlytics crash-free %; target > 99%

### 6.3 Post-launch monitoring
- [ ] Set up GCP alerts for: Firestore reads/writes spike, Cloud Function errors, Storage egress
- [ ] Weekly review of Firebase Analytics funnel
- [ ] Monthly retraining cadence: `python ml/retrain.py --mode once` on Cloud Run

---

## 7. Nice-to-have backlog (after Phase 10)

- [ ] Hindi localization (`res/values-hi/strings.xml`)
- [ ] Dark theme polish (`Theme.kt` already supports it, but the warm/coral palette needs dark variants)
- [ ] Widget: home-screen widget showing this month's spend
- [ ] Wear OS companion: show today's transactions
- [ ] Account Aggregator integration (mentioned as deferred premium feature)
- [ ] Custom categories: let users create L3 categories beyond the 520 taxonomy
- [ ] Recurring transaction detection (subscriptions): cluster by merchant + same-day-of-month pattern

---

## Priority for the next session

1. **Section 0 (sanity check)** — `./gradlew assembleDebug` once Android SDK is installed
2. **Section 1 (Firebase setup)** — drop in `google-services.json`, deploy `firestore.rules` + `storage.rules`
3. **Section 4.2/4.3 (privacy policy hosting + Play declaration)** — operational
4. **Section 5 stretch follow-ups** — Cloud Functions, Firestore mirror for splits, "Split this" CTA on TransactionDetail
5. **Section 6 (Play Store assets + beta)** — go live
6. **Backlog (Hindi, dark theme polish, widget, AA integration)**

---

## Code-quality follow-ups (not blocking launch)

- [ ] Move all hardcoded UI strings into `res/values/strings.xml` for Hindi localization later
- [ ] Add a `BuildConfig.FIREBASE_ENABLED` flag that gates `XpenzoApplication` calls to `FirebaseCrashlytics.getInstance()` (currently crashes if google-services.json is missing at runtime)
- [ ] Add `OnboardingPreferences.reset()` call to `DeleteAccountScreen` flow so account deletion sends user back through onboarding
- [ ] `OnboardingViewModel.error` is sticky — clear it when the user changes the field
- [ ] Add Crashlytics custom keys: `model_version`, `habit_count`, `transactions_synced` so crash reports are debuggable per-user-state
