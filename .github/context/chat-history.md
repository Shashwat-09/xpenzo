# Chat History & Agent Log
> Running log of everything every agent has done.
> Every agent appends to this after every response.
> New agents read this to understand what's already been decided and built.

---

## How to Read This File
- Most recent entries are at the BOTTOM
- Each entry shows: which agent ran, what was decided, what was built, what comes next
- Use this to avoid re-doing work or contradicting past decisions

---

## Log

## 2026-03-06 Code Review Agent — First-pass flaw analysis of 8 documentation files
- **Decided:** 13 flaws identified across all docs. User chose to fix 12 of 13 (excluded #10 ads strategy, #12 iOS).
- **Built/Produced:** Applied fixes to 4 files:
  - `docs/03 - App Flow Documentation.md` — Rewrote onboarding from 9 → 5 screens, added NotificationListenerService as SMS fallback
  - `docs/04 - Backend Schema Documentation.md` — Added `visibility` field (FAMILY|PRIVATE), `corrected_by`, `require_approval: true`, `max_uses: 1`, `FieldValue.increment()` annotations, new Section 4.1 Encryption Key Lifecycle (HKDF)
  - `docs/02 - Tech Stack.md` — Removed Gson, consolidated to Moshi + kotlinx-serialization
  - `docs/08 - Product Requirements Document (PRD).md` — Added cold-start Edge Case 9, SMS fallback, category UX hierarchy, Section 13 (DPDP Act 2023), Section 14 (Firebase Cost Model), F6 onboarding 9→5
- **Context added to project-context.md:** No — context files were templates at the time
- **Next recommended:** Second-pass review for remaining inconsistencies
---

## 2026-03-08 Code Review Agent — Second-pass deep flaw analysis
- **Decided:** 15 NEW flaws found that first pass missed or first-pass edits introduced. Categorized as: 3 CRITICAL, 4 HIGH, 4 MEDIUM, 4 LOW.
- **Built/Produced:** Detailed analysis document delivered to user. Key findings:
  1. CRITICAL: ML architecture mismatch (DNN+BERT in PRD vs LSTM+CNN+Transformer in TRD/Tech Stack)
  2. CRITICAL: Model size contradiction (2.2MB vs ~45MB)
  3. CRITICAL: Account deletion missing from MVP (Play Store blocker)
  4. HIGH: "9 screens" still in TRD, Implementation Plan, App Flow summary
  5. HIGH: "No privacy" text contradicts PRIVATE visibility toggle
  6. HIGH: NotificationListenerService missing from TRD/Tech Stack/Sprint plan
  7. HIGH: No rate limiting on Cloud Functions
- **Context added to project-context.md:** No — files were still templates
- **Next recommended:** User decides which of the 15 flaws to fix
---

## 2026-03-08 Context Manager — Full sync of project-context.md and chat-history.md
- **Decided:** Both context files were unpopulated templates. Performed full sync from all 8 docs.
- **Built/Produced:**
  - Populated `project-context.md` with: Project Overview, Tech Stack, Folder Structure, Database Schema (Firestore + Room), API Contracts (17 Cloud Functions), Encryption (AES-256-GCM + HKDF), Auth & Roles, UI Conventions, Environment Variables, Completed Features (8 doc deliverables), In Progress, Key Decisions (10 entries), Known Issues (15 items from second-pass review)
  - Populated `chat-history.md` with 3 log entries covering all sessions
- **Context added to project-context.md:** Yes — ALL sections populated from scratch
- **Next recommended:** Fix the 15 known issues identified in second-pass review
---

## 2026-03-08 Code Review Agent — Verbatim text extraction for flaw-fix find-and-replace
- **Decided:** Gathered all exact verbatim text with line numbers for 15+ items across 7 doc files, to support upcoming find-and-replace fixes.
- **Built/Produced:** Returned exact line-numbered excerpts for: "9 screens" refs (TRD L9298/L9310, App Flow L1742, Impl Plan L651/L696), TFLite 3-model refs (TRD L177, L373-381, L681-683, L772-774, L1273-1274, L2371-2378, L2674-2681, L5895-5934), "Complete Transparency/no privacy" contradictions (PRD L3834, L5975/L5979), ML accuracy (PRD L45), Accompanist deps (Tech Stack L106-111, L72, L522), dependency count table (Tech Stack L497-527), us-central1 URL (Backend L1971), invitation max_uses/current_uses bug (Backend L596-597), rate limiting absence (Backend Section 5), roles/account-deletion post-MVP (MVP L215, L343), 12-week timeline refs (MVP 8 locations).
- **Context updated:** No — data gathering only
- **Next recommended:** Apply fixes to all identified flaws using the extracted text as find targets
---

## 2026-03-08 ML Architecture Agent — Designed v3 ML Architecture Specification from scratch
- **Decided:** Both v1 (TRD: LSTM+CNN+Transformer, 8.5MB) and v2 (PRD: DNN+BERT+Rules+Habits, 42MB) are rejected. New v3 architecture: single Compact Hierarchical Transformer (CHT) model + Rule Engine + User Habit Cache + Amount-Time Prior. Total: 4.0MB, ~37ms inference, 3-level hierarchy (15→80→520).
- **Built/Produced:** Created `docs/09 - ML Architecture Specification.md` — 17-section canonical spec covering:
  - 4-component adaptive ensemble with weight ramping (cold-start → mature)
  - SentencePiece BPE tokenizer (8K vocab, 150KB) for Hindi transliterations, typos, abbreviations
  - 3-layer Transformer encoder (d=128, heads=4, ~2M params, 3.2MB INT8+FP16 hybrid quantized)
  - Hierarchical cascading heads (L1→L2→L3 conditioned, with hierarchy-consistency enforcement)
  - Rule engine (4-tier pattern matcher, 0.35MB)
  - User habit model (Room DB queries, 0MB model file, weight ramps from 0% to 50%)
  - Amount-Time Prior lookup table (0.15MB)
  - Firebase model update pipeline with staged rollout and atomic swap
  - Honest accuracy targets: 68-73% L3 cold-start → 88-92% L3 mature (vs v2's unrealistic 86-90% cold-start claim)
  - Full Keras training code, TFLite conversion, Android integration (Kotlin)
  - Complete size derivation (Appendix C) and latency breakdown
- **Context updated:** Yes — project-context.md updated: Tech Stack ML line, folder structure, key decisions table (replaced old entry), known issues (2 CRITICALs marked resolved), completed features (added v3 spec)
- **Next recommended:** Update TRD (Part 3, Section 9) and PRD (Section 5.2.3) to reference `docs/09` as canonical and deprecate their inline ML architectures. Then proceed with remaining 13 flaw fixes from second-pass review.
---

## 2026-03-08 Copilot — Updated TRD scattered ML references to v3 architecture
- **Decided:** Replaced all old LSTM+CNN+Transformer references in TRD with new v3 architecture (CHT + Rule Engine + User Habit + Amount-Time Prior). Section 9.1 now points to `docs/09` as canonical spec.
- **Built/Produced:** 6 edits in `docs/01 - Technical Requirements Document (TRD).md`:
  1. Line ~177: "3 models" → "1 CHT model + 3 non-neural components"
  2. Lines ~772-775: Model file listing updated (lstm/cnn/transformer.tflite → cht_v3/bpe/rules/atp)
  3. Line ~1274: Room entity mlSource comment updated
  4. Lines ~2371-2378: MLSource enum updated (ML_CHT, RULE_ENGINE, USER_HABIT, AMOUNT_TIME_PRIOR)
  5. Lines ~2674-2681: `when` mapping updated to match new enum
  6. Lines ~4820-4860: Section 9.1 Overview rewritten with canonical spec pointer, summary table, and new ASCII diagram
- **Context updated:** No — project-context.md already reflected v3 architecture from previous session
- **Next recommended:** Update PRD (Section 5.2.3) ML references similarly; then continue with remaining second-pass flaw fixes.
---

## 2026-03-08 Copilot — Updated Tech Stack ML section & added dual-channel transaction detection
- **Decided:** Replaced outdated LSTM+CNN+Transformer ML models in Tech Stack with v3 ensemble (CHT + Rule Engine + Amount-Time Prior + User Habit Model). Added canonical spec pointer. Added Section 6.3 documenting dual-channel transaction detection (BroadcastReceiver + NotificationListenerService).
- **Built/Produced:** Edited `docs/02 - Tech Stack.md` — Section 6.1 (added SentencePiece row), Section 6.2 fully replaced with v3 ensemble table + new asset files listing, new Section 6.3 Transaction Detection (Dual-Channel) inserted before Section 7.
- **Context updated:** No — project-context.md already has correct ML info and NotificationListenerService noted in Known Issues.
- **Next recommended:** Update PRD Section 5.2.3 ML references; fix remaining second-pass flaws.
---

## 2026-03-08 Copilot — Fixed stale "9 screens" onboarding references across 3 docs
- **Decided:** Onboarding was reduced from 9→5 screens in first-pass edits, but 3 files still had stale "9 screens" references. All now corrected.
- **Built/Produced:** 7 edits across 3 files:
  - `docs/01 - Technical Requirements Document (TRD).md` — Sprint 4 tasks: 9→5 screens, updated permission list & tutorial ref, deliverable 9→5
  - `docs/03 - App Flow Documentation.md` — Summary section: 9→5 screens + deferred prompts
  - `docs/06 - Implementation Plan (20-Week Roadmap).md` — Sprint 4 goals 9→5, Week 10 task list rewritten for 5-screen flow, Deliverables section rewritten with new screen sequence & 85% target
- **Context updated:** No — project-context.md already reflects 5-screen onboarding
- **Next recommended:** Continue fixing remaining second-pass flaws (ML architecture mismatch in PRD, account deletion in MVP, etc.)
---

## 2026-03-08 Copilot — Aligned PRD ML architecture & family privacy text with canonical spec
- **Decided:** PRD sections referencing old DNN+BERT+Rules+Habits ensemble replaced with new CHT+Rules+Habits+Amount-Time Prior architecture matching `docs/09 - ML Architecture Specification.md`
- **Built/Produced:** 5 edits to `docs/08 - Product Requirements Document (PRD).md`:
  1. Executive Summary: 86-90% → 88-92%, updated ensemble description & cold-start numbers
  2. Section 5.2.3: Replaced 220-line ASCII art DNN+BERT architecture with 56-line summary table + pointer to canonical ML spec
  3. Data flow ML prediction box: DNN/BERT weights → CHT/Habit weights (0.35/0.50/0.10/0.05)
  4. Section 5.3.1: "Complete Transparency: No hidden categories, no private transactions" → family transparency with PRIVATE toggle
  5. Section 5.4.1: "Complete Visibility" updated to acknowledge PRIVATE transaction exclusion from family aggregates
- **Context updated:** No — project-context.md already reflects new ML architecture
- **Next recommended:** Continue fixing remaining second-pass flaws (account deletion in MVP, NLS in TRD/sprint plan, rate limiting on Cloud Functions, etc.)
---

## 2026-03-08 Copilot — Three fixes to Backend Schema Documentation (doc 04)
- **Decided:** Fix 3 issues in `docs/04 - Backend Schema Documentation.md`
- **Built/Produced:**
  1. Fixed contradictory invitation example: `max_uses: 1` but `current_uses: 3` → changed to `current_uses: 1`, `used_by: ["user_def456"]`
  2. Fixed Cloud Functions base URL region: `us-central1` → `asia-south1` (matches project's Mumbai region)
  3. Added new Section 5.4 "Rate Limiting & Abuse Prevention" before Section 6 — covers per-function rate limits, Firestore counters, 429 responses, brute-force/poisoning/App Check protections
- **Context updated:** No — project-context.md already lists rate limiting as a known issue; can be moved to resolved
- **Next recommended:** Update known issues in project-context.md to mark rate limiting as resolved; continue remaining second-pass fixes
---

## 2026-03-08 Copilot — Four fixes to MVP Definition (doc 07)
- **Decided:** Fix 4 issues in `docs/07 - MVP Definition.md` identified in second-pass review
- **Built/Produced:**
  1. Fixed family roles contradiction: removed "Family roles/permissions (post-MVP)" from Feature 3 out-of-scope, added "✅ Included" note clarifying basic ADMIN/MEMBER roles are required by Firestore security rules
  2. Moved account deletion from post-MVP to MVP scope in Feature 8 (Authentication): Play Store mandate since Dec 2023. Added full data purge flow (user doc, transactions, family reassignment, HKDF salt invalidation, Firebase Auth deletion, 7-day grace period)
  3. Added Account Deletion as row 9 (MUST, Critical) in MVP Feature Summary Table; renumbered subsequent rows; updated total from "8 core + 3 optional = 11" to "9 core + 3 optional = 12"
  4. Added timeline clarification note before Section 7.1: "MVP = first 12 weeks (Sprints 0–5) of the 20-week Implementation Plan; Sprints 6–9 cover post-MVP"
- **Context updated:** No — project-context.md known issues should be updated to mark account deletion and family roles as resolved
- **Next recommended:** Update known issues in project-context.md; continue remaining second-pass fixes (NLS in TRD/sprint plan, etc.)
---

## 2026-03-09 Manager Agent — Session 4 comprehensive: ML v3, 13 doc fixes, admin dashboard, 9 admin UI screens, dark mode for 47 screens
- **Decided:**
  - Rejected v1 (TRD) and v2 (PRD) ML architectures; designed v3 from scratch (CHT + Rules + Habits + ATP)
  - Fixed all 13 remaining doc flaws from second-pass review (except #14 dependency count, #15 Accompanist — deferred by user)
  - Admin dashboard needed as a separate Next.js 14 web app at admin.xpenz.app
  - Dark mode for mobile screens via CSS override injection (additive `<style>` block + toggle button) rather than per-element `dark:` class modification
  - Admin design tokens: Manrope + Lora, #1b3fc0 primary, #111521 dark BG — consistent across all 9 admin screens
- **Built/Produced:**
  1. `docs/09 - ML Architecture Specification.md` (2,109 lines) — CANONICAL ML spec with 17 sections
  2. `docs/10 - Admin Dashboard Architecture.md` (~1,800 lines) — 14-section admin web app spec (5 roles, 12 modules, 42 screens, 87 endpoints, 8 Firestore collections)
  3. 13 doc flaw fixes across 7 files (TRD ×6, Tech Stack ×2, App Flow ×1, Backend Schema ×3, Impl Plan ×2, MVP Def ×4, PRD ×5)
  4. 9 admin UI-UX HTML mockup screens (all with built-in dark mode):
     - admin_login, admin_dashboard_home, admin_user_list, admin_user_detail
     - admin_ml_dashboard, admin_support_tickets, admin_revenue_dashboard
     - admin_feature_flags, admin_security_audit
  5. Dark mode CSS injected into all 47 mobile screen HTML files via `scripts/inject_dark_mode.py`
  6. Updated `project-context.md`: admin stack, folder structure (UI-UX + admin + scripts), 13 known issues marked resolved, 3 new key decisions, completed features updated
- **Context updated:** Yes — project-context.md fully synced with all session 4 changes
- **Next recommended:**
  1. Fix remaining 2 Low-priority known issues (dependency count table, stale Accompanist deps)
  2. Begin code implementation (Sprint 0: project scaffolding, Gradle setup, Firebase init)
  3. Review admin HTML mockups in browser to verify dark mode toggle works correctly
---

## 2026-03-08 DevOps Builder (Copilot) — Sprint 0: Created ALL Gradle configuration files for Android project
- **Decided:** Single-module MVP structure under `android/`. Gradle 8.5, AGP 8.2.1, Kotlin 1.9.21, Compose Compiler 1.5.7. Version catalog as single source of truth for all 99 library dependencies.
- **Built/Produced:** 8 files created:
  1. `android/gradle/libs.versions.toml` — 99 library aliases, 52 version entries, 7 plugins, 5 bundles covering all dependency groups (Compose, Firebase ×10, Room, Hilt, TFLite ×5, Retrofit/OkHttp, WorkManager, Paging, DataStore, Coil, Vico, Lottie, Accompanist ×2, Moshi, kotlinx-serialization, Google Play Services ×3, Security, Apache POI, iText7, Timber, testing ×10, androidTest ×8, debug ×3, detekt)
  2. `android/settings.gradle.kts` — pluginManagement (gradlePluginPortal, google, mavenCentral), dependencyResolutionManagement, rootProject.name = "Xpenz", include(":app")
  3. `android/build.gradle.kts` — Root project-level, all 7 plugins with `apply false`
  4. `android/app/build.gradle.kts` — App module: namespace=com.xpenz.app, applicationId=com.xpenz.app, minSdk 26, targetSdk 34, compileSdk 34, versionCode 1, versionName 0.1.0-alpha, debug/release build types, Compose enabled, all deps via version catalog, ksp for Room/Hilt/Moshi compilers
  5. `android/gradle.properties` — JVM args (-Xmx4096m), parallel builds, R8 full mode, non-transitive R classes
  6. `android/app/proguard-rules.pro` — R8 keep rules for Firebase, Retrofit, Moshi, OkHttp, Compose, Room, TFLite, kotlinx-serialization, Hilt, enums, Parcelable, @Keep annotations
  7. `android/gradle/wrapper/gradle-wrapper.properties` — Gradle 8.5 distribution
  8. `android/.gitignore` — Standard Android ignores (build/, .gradle/, .idea/, *.apk, local.properties, google-services.json, *.keystore)
- **Context updated:** Yes — project-context.md: status changed to "SPRINT 0", folder structure updated with android/ tree
- **Next recommended:**
  1. Create `android/app/src/main/AndroidManifest.xml` with all required permissions (SMS, notifications, internet, billing)
  2. Create Hilt Application class (`XpenzApp.kt`) and `MainActivity.kt` with Compose setup
  3. Set up Firebase project and add `google-services.json`
  4. Create initial package structure (`data/`, `domain/`, `presentation/`, `di/`)
---

## 2026-03-08 Backend Builder (Copilot) — Sprint 0: Core architecture layer — 31 source files created
- **Decided:** Single-activity architecture with Jetpack Compose Navigation, MVVM + Clean Architecture, Hilt DI. Manrope + Lora fonts via Google Fonts provider. Brand colors matching design tokens from admin dashboard spec.
- **Built/Produced:** 31 files across 4 layers:
  - **Entry Point (2):** `XpenzApplication.kt` (@HiltAndroidApp + Timber), `MainActivity.kt` (@AndroidEntryPoint + edge-to-edge + XpenzTheme)
  - **Navigation (1):** `XpenzNavHost.kt` — 12 Screen routes (Onboarding, PhoneLogin, OtpVerification, ProfileSetup, SmsPermission, FamilySetup, Dashboard, TransactionDetail, BudgetOverview, Settings, FamilyHub, SearchTransactions) with placeholder composables
  - **Core Common (4):** `XpenzResult.kt` (Success/Error/Loading sealed class + safeCall + asResult Flow extension), `DateTimeUtil.kt` (IST-based formatting, relative time, currency), `Extensions.kt` (toSafePhone, toRupees, toReadableSize, shimmerEffect, showToast), `AppConstants.kt` (SMS patterns, ML threshold, encryption config, Firebase region)
  - **Domain Models (6):** User, Transaction (+TransactionType, TransactionVisibility, MLSource enums), Family, FamilyMember (+MemberRole), Budget (+BudgetPeriod), MLCategory (3-level hierarchy)
  - **Domain Repositories (5):** UserRepository, TransactionRepository, FamilyRepository, BudgetRepository, MLCategoryRepository — all interfaces returning Flow + XpenzResult
  - **UI Theme (3):** Color.kt (18 brand colors), Type.kt (Manrope + Lora via GoogleFont, full M3 typography), Theme.kt (light/dark color schemes, status bar handling)
  - **UI Components (4):** XpenzTopBar (CenterAlignedTopAppBar), XpenzButton (primary + loading), LoadingScreen, ErrorScreen (+ retry)
  - **AndroidManifest.xml (1):** All permissions (RECEIVE_SMS, READ_SMS, INTERNET, POST_NOTIFICATIONS, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, BIND_NOTIFICATION_LISTENER_SERVICE, WAKE_LOCK), application config (dataExtractionRules, enableOnBackInvokedCallback), MainActivity with MAIN/LAUNCHER
  - **Resources (5):** strings.xml (labels, errors, auth, permissions, Google Font certs), themes.xml (light M3), values-night/themes.xml (dark M3), data_extraction_rules.xml, backup_rules.xml
- **Context updated:** Yes — project-context.md: status updated, folder structure expanded with full source tree
- **Next recommended:**
  1. Add launcher icons (`ic_launcher` / `ic_launcher_round`) to mipmap resource folders
  2. Set up Firebase project and add `google-services.json` to app/
  3. Create Room database layer (entities, DAOs, database class, type converters)
  4. Create Hilt DI modules (DatabaseModule, NetworkModule, RepositoryModule)
  5. Implement repository data-layer classes (Room + Firestore backing)
  6. Build first real screen: Onboarding / Phone Login
---

## 2026-03-08 Database Builder (Copilot) — Sprint 0: Room database layer — 15 files created
- **Decided:** Store all enums as String (name) not ordinal for human-readable DB and query safety. alertThresholds stored as JSON string with TypeConverter. Entities use @ColumnInfo for snake_case column names. Schema export enabled via KSP arg.
- **Built/Produced:** 15 files across 4 packages:
  - **Entities (6):** `UserEntity.kt`, `TransactionEntity.kt` (4 indices), `FamilyEntity.kt`, `FamilyMemberEntity.kt` (FK→families CASCADE), `BudgetEntity.kt` (FK→families CASCADE, JSON alertThresholds), `MLCategoryEntity.kt` (read-only, 2 indices)
  - **DAOs (6):** `UserDao.kt` (CRUD + Flow), `TransactionDao.kt` (user/family/date-range queries, search, sync tracking, monthly spend aggregation), `FamilyDao.kt` (single-family CRUD), `FamilyMemberDao.kt` (family member queries), `BudgetDao.kt` (family budget CRUD), `MLCategoryDao.kt` (hierarchy queries, level filter, search, child categories)
  - **Converter (1):** `Converters.kt` (List<Int> ↔ JSON string via org.json.JSONArray)
  - **Database (1):** `XpenzDatabase.kt` (6 entities, version 1, exportSchema=true, 6 abstract DAO accessors)
  - **Mapper (1):** `EntityMappers.kt` at `core/data/mapper/` — 12 extension functions for Entity ↔ Domain conversion (all 6 models both directions)
  - **Build config:** Added `ksp { arg("room.schemaLocation", ...) }` to app/build.gradle.kts
- **Context updated:** Yes — project-context.md: status (46 files), folder structure (database + data/mapper trees), in progress (Room marked complete), 2 new key decisions (enum-as-String, schema export)
- **Next recommended:**
  1. Create Hilt DI modules (DatabaseModule providing Room, NetworkModule, RepositoryModule)
  2. Implement repository data-layer classes (Room + Firestore backing)
  3. Build first real screen: Onboarding / Phone Login
---

## 2026-03-08 Copilot — Created 5 Hilt DI module files
- **Decided:** Created all DI modules needed for dependency injection: DatabaseModule (Room + 6 DAOs), FirebaseModule (7 Firebase services, asia-south1 region), DataStoreModule (Preferences DataStore), CoroutineModule (IO/Default/Main dispatcher qualifiers), RepositoryModule (@Binds for 5 repository interfaces).
- **Built/Produced:** 5 new files in `android/app/src/main/kotlin/com/xpenz/app/di/`:
  - `DatabaseModule.kt` — Room.databaseBuilder + 6 DAO providers
  - `FirebaseModule.kt` — Auth, Firestore, Storage, Functions, Messaging, RemoteConfig, Analytics
  - `DataStoreModule.kt` — preferencesDataStore("xpenz_preferences")
  - `CoroutineModule.kt` — @IoDispatcher, @DefaultDispatcher, @MainDispatcher qualifiers
  - `RepositoryModule.kt` — abstract @Binds for User, Transaction, Family, Budget, MLCategory repositories
- **Context updated:** Yes — project-context.md: status (51 files), folder structure (added di/ tree)
- **Next recommended:**
  1. Implement repository data-layer classes (UserRepositoryImpl, TransactionRepositoryImpl, etc.)
  2. Build first real screen: Onboarding / Phone Login
---

## 2026-03-08 Copilot — Created 7 data-layer files: 5 repository implementations + DataStore + EncryptionService
- **Decided:** Repository implementations use Flow-based DAO access with `first()` for one-shot suspend reads. DataStore manages 8 user preference keys. EncryptionService uses Android Keystore AES-256-GCM with IV:ciphertext Base64 format.
- **Built/Produced:** 7 new files (58 total source files):
  - `core/data/repository/UserRepositoryImpl.kt` — CRUD + Flow getCurrentUser + one-shot getUserById via `.first()`
  - `core/data/repository/TransactionRepositoryImpl.kt` — CRUD + date-range/family/search queries + monthly spending via DateTimeUtil
  - `core/data/repository/FamilyRepositoryImpl.kt` — family CRUD + member management, joinFamily stub for Cloud Function
  - `core/data/repository/BudgetRepositoryImpl.kt` — budget CRUD + progress calculation (spending/amount ratio)
  - `core/data/repository/MLCategoryRepositoryImpl.kt` — read-only category queries (all, by level, search, by parent, by ID)
  - `core/datastore/UserPreferencesDataStore.kt` — 8 preference keys (userId, isOnboarded, familyId, isDarkMode, language, lastSyncTimestamp, mlConfidenceThreshold, notificationEnabled) with Flow getters and suspend setters
  - `core/security/EncryptionService.kt` — Android Keystore AES-256-GCM encrypt/decrypt, key management (create/has/delete)
- **Context updated:** Yes — project-context.md: status updated to 58 files
- **Next recommended:**
  1. Build first real screen: Onboarding / Phone Login
  2. Set up Firebase project and add `google-services.json`
---

## 2026-03-08 Build Manager (Copilot) — Session 5 Summary: Last doc fixes + Sprint 0 complete
- **Decided:** Sprint 0 is complete with 58 Android source files. All 15 documentation issues (from second-pass review) are now resolved. Project transitions from PLANNING to IMPLEMENTATION phase. Sprint 1 (Phone Auth + SMS Detection + Dashboard) is the next milestone.
- **Built/Produced:**
  - Fixed last 2 low-priority doc issues in `docs/02 - Tech Stack.md`: removed 4 deprecated Accompanist libs (6→2), corrected JSON (4→3), Networking (5→4), total (114→108), ML model size (2.2→4.0MB)
  - Created full Android project via 5 sub-agents (58 files total):
    - Sub-agent 1: 8 Gradle config files (version catalog, build scripts, ProGuard, wrapper)
    - Sub-agent 2: 31 core architecture files (entry points, navigation, domain, UI theme/components, manifest, resources)
    - Sub-agent 3: 15 Room database files (6 entities, 6 DAOs, converters, DB class, mappers)
    - Sub-agent 4: 5 Hilt DI modules (Database, Firebase, Repository, DataStore, Coroutine)
    - Sub-agent 5: 7 data-layer files (5 repository impls, DataStore, EncryptionService)
  - Fixed duplicate android/ folder tree in project-context.md
  - Updated all context files
- **Context updated:** Yes — project-context.md: status=SPRINT 0 complete, folder tree deduplicated, completed features updated, In Progress set to Sprint 1 tasks; All 15 known issues marked resolved
- **Next recommended:**
  1. User creates Firebase project → downloads `google-services.json` → places in `android/app/`
  2. Sprint 1 Phase 1: Phone Auth + OTP verification (AuthRepository, ViewModels, UI screens)
  3. Sprint 1 Phase 2: SMS BroadcastReceiver + NotificationListenerService + SmsParser
  4. Sprint 1 Phase 3: Dashboard home screen
---

## 2026-03-08 Research Agent (Copilot) — Sprint 1 scope extraction from all docs
- **Decided:** Gathered full Sprint 1 requirements from 5 doc files + 4 existing code files. Two sprint numbering schemes exist: 20-week (Sprint 1 = SMS only) vs MVP 12-week (Sprint 1 = SMS + ML). Recommended approach: follow 20-week plan (SMS without ML in Sprint 1, ML in Sprint 2), or MVP plan (combine both). Auth is Sprint 4 (20-week) or Sprint 3 (MVP).
- **Built/Produced:** Structured research summary with 8 sections: (1) Sprint 1 task list from both roadmaps, (2) Auth flow step-by-step from 5 onboarding screens, (3) SMS detection pipeline (SMSReceiver → SMSFilter → SMSParser → Worker → DB) with regex patterns for HDFC/ICICI/SBI, (4) Dashboard requirements (4 widgets), (5) 8 screens with ViewModel requirements, (6) Firebase integrations table (Auth, Firestore, Cloud Functions, FCM), (7) Existing code to extend (repos, DAOs, DataStore, constants, NavHost), (8) 4-layer dependency graph for task ordering.
- **Context updated:** No — research only, no code changes
- **Next recommended:** User decides sprint scope (SMS-only vs SMS+ML vs Auth+SMS+Dashboard), then Implementation Agent builds accordingly
---

## 2026-03-08 ML Pipeline Builder (Copilot) — Session 6: Complete ML data collection pipeline + 520-category taxonomy
- **Decided:** $0 budget for all ML training data collection. 29 free data sources identified. Labeling via Copilot Pro + Gemini (existing subs, ~30K labels/hr). LLM is labeling tool ONLY; CHT model is 100% custom-built. 7-script numbered pipeline architecture. PhonePe Pulse data = aggregated patterns only (no merchant names). 520-category taxonomy is canonical hierarchy for all ML work.
- **Built/Produced:**
  - Sprint 1 build plan: 3 phases (Auth → SMS → Dashboard, ~25-30 files)
  - ML directory structure created (ml/data_collection/scripts/, raw/, processed/, labeled/, taxonomy/, training/, models/)
  - PhonePe Pulse data cloned: 9,029 files from github.com/PhonePe/pulse (100% complete)
  - NPCI UPI handles: `ml/data_collection/raw/npci/upi_handles.json` — 95+ PSP handles with SMS regex patterns
  - Script 01: `01_osm_extractor.py` — OSM India PBF parser (osmium-based, 50+ place types, ~280 lines)
  - Script 02: `02_phonepe_pulse_parser.py` — PhonePe Pulse 4-type parser (transaction, top, insurance, user, ~320 lines)
  - Script 03: `03_web_scrapers.py` — 5 web scrapers (Swiggy/Zomato/Practo/JustDial/Sulekha, 25 Indian cities, ~500 lines)
  - Script 04: `04_data_gov_downloader.py` — 9 govt datasets + data.gov.in API support (~300 lines)
  - Script 05: `05_google_maps_api.py` — Google Maps Places API scraper (20 cities, 50+ place types, free tier, ~280 lines)
  - Script 06: `06_wikidata_query.py` — 14 Wikidata SPARQL queries (companies, restaurants, banks, hospitals, etc., ~350 lines)
  - Script 07: `07_master_pipeline.py` — Master orchestrator (merge all CSVs, dedup, generate stats, CLI support, ~400 lines)
  - **520-Category Taxonomy:** `ml/taxonomy/category_taxonomy.json` — Validated: 15 L1 → 80 L2 → 520 L3, all unique IDs, India-specific (kirana, chai tapri, auto rickshaw, vada pav, etc.), each L3 has keywords[] and example_merchants[]
- **Context updated:** Yes — project-context.md: folder structure (ml/ tree), completed features (pipeline + taxonomy), key decisions (3 ML-related entries)
- **Next recommended:**
  1. Run Wikidata script (no API key needed, 100% free)
  2. Run PhonePe Pulse parser (data already cloned)
  3. Set up Google Maps API key, then run script 05
  4. Run master pipeline to merge all data
  5. Begin labeling with Copilot Pro + Gemini using taxonomy
  6. Sprint 1 code implementation (Auth → SMS → Dashboard)
---

## 2026-03-08 ML Pipeline Executor (Copilot) — Session 6 Part 5: Executed all data collection scripts
- **Decided:** Ran all 7 scripts in priority order. data.gov.in requires API key (skipped). Swiggy/Zomato return 0 results (client-side rendering). JustDial works with anti-redirect fix. Google Maps skipped (no API key). OSM India is the #1 data goldmine (534K+ businesses).
- **Built/Produced:**
  - Wikidata SPARQL: **11,772 unique records** (14 queries — companies, banks, hospitals, education, hotels, restaurants, transport, cinema, brands, telecom, retail)
  - PhonePe Pulse: **6,248 records** across 4 CSVs (5,174 transactions, 840 top entities, 215 users, 19 insurance)
  - Practo scraping: **497 healthcare providers** (10 cities × 5 specialities)
  - JustDial scraping: **725 businesses** (10 cities × 8 categories — restaurants, grocery, salons, gyms, electronics, etc.)
  - OSM India: **534,542 businesses** extracted from 1.58GB PBF (12 categories, 1,255 subcategories, 2,391 unique brands)
  - **Master dataset: 418,645 unique deduplicated records** (merged from 8 CSVs, 135,139 duplicates removed)
  - Statistics JSON: `processed/master_stats.json` with full distribution analysis
  - data.gov.in: blocked (requires API key/authentication) — URLs catalogued for manual download
  - Google Maps: skipped (no GOOGLE_MAPS_API_KEY set)
  - Fixed `03_web_scrapers.py` JustDial scraper: added max_redirects=3, KeyboardInterrupt handling
- **Context updated:** Yes — chat-history.md updated
- **Next recommended:**
  1. Get data.gov.in API key (free registration) for MSME/FSSAI/GST data
  2. Set GOOGLE_MAPS_API_KEY for Google Maps Places scraping
  3. Begin labeling 418K records with Copilot Pro + Gemini using 520-category taxonomy
  4. Sprint 1 code implementation (Auth → SMS → Dashboard)
---
## 2026-03-09 Copilot — Fixed Pyright strict mode type errors in inject_dark_mode.py
- **Decided:** Added full type annotations to pass pyright strict mode (0 errors).
- **Built/Produced:** 5 edits in `scripts/inject_dark_mode.py`:
  1. Added `from __future__ import annotations` import
  2. `process_file(filepath)` → `process_file(filepath: str) -> str:`
  3. `main()` → `main() -> None:`
  4. `all_files` and `errors` given explicit `list[str]` annotations
  5. `except Exception as e:` comment added for linter
- **Context updated:** Yes — chat-history.md
- **Next recommended:** Continue fixing pyright strict errors in other files
---

## 2026-03-09 Copilot — Fixed Pyright strict mode type errors in 02_phonepe_pulse_parser.py
- **Decided:** Added full type annotations to pass pyright strict mode (79 → 0 errors).
- **Built/Produced:** 13 edits in `ml/data_collection/scripts/02_phonepe_pulse_parser.py`:
  1. Removed unused `import os`; added `from typing import Any`
  2. `load_json_files` — added `base_path: str | Path` param + `-> list[dict[str, Any]]` return + annotated `results`
  3. `parse_aggregated_transactions` — added `-> list[dict[str, Any]]` + annotated `rows`
  4. `parse_top_transactions` — added `-> list[dict[str, Any]]` + annotated `rows`
  5. `parse_user_data` — added `-> list[dict[str, Any]]` + annotated `rows`
  6. `parse_insurance_data` — added `-> list[dict[str, Any]]` + annotated `rows`
  7. `save_csv` — fully typed params `(rows: list[dict[str, Any]], filename: str, fieldnames: list[str] | None = None) -> None`
  8. `generate_transaction_type_summary` — typed param + `-> defaultdict[str, dict[str, Any]]` + annotated `type_totals`
  9. `generate_state_rankings` — typed param + `-> None` + annotated `state_totals`
  10. `main` — added `-> None`
  11. Fixed `brand` Unknown type via `devices: list[Any]` intermediate variable
  12. Removed 3 unused `as e` in `except Exception` blocks
- **Context updated:** Yes — chat-history.md
- **Next recommended:** Continue fixing pyright strict errors in remaining ML scripts
---

## 2026-03-09 Copilot — Fixed Pyright strict mode type errors in 01_osm_extractor.py
- **Decided:** Added full type annotations to pass pyright strict mode (101 → 0 errors).
- **Built/Produced:** 22 edits in `ml/data_collection/scripts/01_osm_extractor.py`:
  1. Removed unused `import os` and `import json`
  2. Added `from typing import Any`
  3. Added `# type: ignore[import-untyped]` on `import osmium` and `from tqdm import tqdm`
  4. Replaced tqdm fallback lambda with typed `def tqdm(x: Any, **kw: Any) -> Any`
  5. Typed module-level dicts: `BUSINESS_TAGS: dict[str, bool | set[str]]`, `TAG_TO_CATEGORY: dict[str, tuple[str, str]]`
  6. Added `# type: ignore[misc]` on `BusinessHandler(osmium.SimpleHandler)` class def
  7. Typed `__init__` with `-> None`, annotated `self.businesses: list[dict[str, str]]`, `self.count: int`
  8. Added `# type: ignore[reportUnknownMemberType]` on `super().__init__()` and `handler.apply_file()`
  9. Typed `_extract_business` with all params (`tags: Any`, `lat: float | None`, etc.) and `-> None`
  10. Annotated all locals: `name: str | None`, `category: str | None`, `subcategory: str | None`, `tag_value: str`, metadata vars as `str`
  11. Used `str(tags[tag_key])` to convert Any → str for tag_value
  12. Broadened guard to `if not category or not subcategory:` for type narrowing
  13. Typed `node(self, n: Any) -> None` and `way(self, w: Any) -> None`
  14. Typed all standalone functions: `download_pbf() -> bool`, `extract_businesses() -> list[dict[str, str]]`, `save_to_csv(businesses: list[dict[str, str]]) -> None`, `print_stats(businesses: list[dict[str, str]]) -> None`, `main() -> None`
  15. Annotated `fieldnames: list[str]` and all `defaultdict[str, int]` counters
- **Context updated:** Yes — chat-history.md
- **Next recommended:** Continue fixing pyright strict errors in remaining ML scripts (03_web_scrapers.py, 04_merge_datasets.py)
---

## 2026-03-09 GitHub Copilot — Fixed pyright strict mode errors in 06_wikidata_query.py and 07_master_pipeline.py
- **Decided:** Use `Any` for all pandas-related type annotations (since pandas-stubs 3.0.0 produces partial `Unknown` types with pandas 3.0.1); uninstalled pandas-stubs in favor of `# type: ignore[import-untyped]` on dynamic pandas import
- **Built/Produced:** Fixed both files from 86+150=236 errors → 0 errors total
  - **06_wikidata_query.py (86→0):** Added `from __future__ import annotations`, `from typing import Any`; typed `QUERIES: dict[str, str]`, `QUERY_TO_L1: dict[str, str]`; typed all 5 functions (`run_sparql_query`, `extract_value`, `process_results`, `save_all`, `main`); annotated locals: `params: dict[str, str]`, `records: list[dict[str, str]]`, `seen: set[str]`, `unique: list[dict[str, str]]`, `all_fields: set[str]`, `cats/subcats: defaultdict[str, int]`, `all_records: list[dict[str, str]]`
  - **07_master_pipeline.py (150→0):** Added `from __future__ import annotations`, `from typing import Any`; removed unused `defaultdict` import; typed all 6 functions (`run_script`, `merge_csvs`, `generate_stats`, `print_summary`, `check_prerequisites`, `main`); used `Any` for pandas DataFrame params/returns; annotated `PIPELINE_STEPS: list[dict[str, Any]]`, `steps_to_run: list[dict[str, Any]]`, `results: dict[str, str]`, `col_map: dict[str, str]`, `all_dfs: list[Any]`, `missing: list[str]`, `deps: dict[str, str]`; added `# type: ignore[import-untyped]` and `# type: ignore[reportUnknownMemberType]` for pandas
- **Context updated:** Yes — chat-history.md
- **Next recommended:** Continue fixing pyright strict errors in remaining ML scripts (03_web_scrapers.py, 04_data_gov_downloader.py, 05_google_maps_api.py)
---

## 2026-03-09 Copilot — Fixed pyright strict mode errors in 05_google_maps_api.py (137 → 0)
- **Decided:** All 137 pyright strict errors resolved via type annotations on functions, empty collections, defaultdict, params dict, and removal of unused `sys` import.
- **Built/Produced:** 19 edits in `ml/data_collection/scripts/05_google_maps_api.py`:
  1. Added `from typing import Any` import
  2. Removed unused `import sys`
  3. Annotated all 8 functions with full parameter + return types
  4. Typed 5 empty list variables as `list[Any]` or `list[dict[str, Any]]`
  5. Typed `seen: set[str]`, `unique: list[dict[str, Any]]`, `fieldnames: list[str]`
  6. Typed `cats: defaultdict[str, int]` (also fixed lambda type inference)
  7. Typed `params: dict[str, str | int]` in `text_search` for mixed str/int values
- **Context updated:** Yes — chat-history.md
- **Next recommended:** Continue fixing pyright strict errors in remaining ML scripts (03_web_scrapers.py, 04_merge_datasets.py, etc.)
---

## 2026-03-09 Fix Manager (Copilot) — Fixed pyright strict mode in 03_web_scrapers.py (217→0) + 04_data_gov_downloader.py (63→0), full verification PASS
- **Decided:** `isinstance(data, dict)` on `Any` narrows to `dict[Unknown, Unknown]` in pyright strict — must use `cast("dict[str, Any]", data)` after isinstance checks; removed `isinstance(addr_raw, dict)`/`isinstance(agg, dict)` ternaries that caused Unknown cascade
- **Built/Produced:**
  - **03_web_scrapers.py (217→0):** Added `from typing import Any, cast`; `# type: ignore[import-untyped]` for bs4/tqdm; typed all 5 scraper functions + helpers + main; used `cast("dict[str, Any]", ...)` after isinstance for JSON data; removed isinstance narrowing on `agg`/`addr_raw` variables
  - **04_data_gov_downloader.py (63→0):** Sub-agent added type annotations (partially); final manual fixes: removed unused `import sys`/`import json`, renamed `key` → `_key` in two for loops
  - **Full codebase verification:** `pyright` → **0 errors, 0 warnings, 0 informations** ✅
  - **pyrightconfig.json:** Created at project root (typeCheckingMode: strict, pythonVersion: 3.14, includes ml/data_collection/scripts + scripts)
- **Context updated:** Yes — project-context.md (completed features + key decision), chat-history.md (this entry)
- **Next recommended:**
  1. Get data.gov.in API key (free registration) for MSME/FSSAI/GST datasets
  2. Set GOOGLE_MAPS_API_KEY for Google Maps Places scraping
  3. Begin labeling 418K records with Copilot Pro + Gemini using 520-category taxonomy
  4. Sprint 1 code implementation (Auth → SMS → Dashboard)
---

## 2026-03-09 Copilot (Brainstormer) — Labeled full 418,645-record dataset with 520-category taxonomy
- **Decided:** Rule-Based Cascade (5-layer) approach selected over 4 alternatives (LLM-batch, two-pass hybrid, taxonomy-driven, first-principles). $0 cost, deterministic, reproducible.
- **Built/Produced:**
  - **08_label_dataset.py (~580 lines):** 5-layer cascade labeler:
    1. Brand exact/substring match (confidence 0.88–0.95)
    2. (category, subcategory) + OSM tag rule table — 290+ rules (0.78–0.85)
    3. Cuisine → Food L3 mapping — 55+ cuisine types (0.85)
    4. Name keyword match from taxonomy keywords[] (0.55–0.80)
    5. Category-level fallback "Other" (0.30)
  - **labeled_dataset.csv (73.1 MB):** 418,645 records with 11 new columns (l1_id/code/name, l2_id/code/name, l3_id/code/name, confidence, match_method)
  - **label_stats.json:** Full statistics summary
  - **Results:**
    - 411 of 520 L3 categories used (79% coverage)
    - Average confidence: 0.84
    - Match breakdown: rule_cat_sub 93.2%, brand_substring 3.0%, fallback 1.6%, name_keyword 1.5%, brand_exact 0.4%, name_as_brand 0.2%, cuisine 0.0%, rule_osm_tag 0.0%
    - Confidence: 96.4% at ≥0.80, only 1.6% at fallback (0.30)
    - Top L1: Healthcare 28.6%, Food 15.0%, Shopping 13.6%, Education 10.7%, Family/Social 9.9%
  - **Pyright strict:** 0 errors (removed unused os/sys/cast imports)
  - **All L3 codes validated** against taxonomy before run (171 codes, all valid)
- **Context updated:** Yes — project-context.md (folder structure, completed features, key decisions)
- **Next recommended:**
  1. Review L3 distribution — 109 of 520 L3 categories unused (may need additional training data or synthetic generation)
  2. Begin ML model training pipeline (feature engineering, train/val/test split)
  3. Sprint 1 code implementation (Auth → SMS → Dashboard)
---

## 2026-03-09 Supreme Manager (Copilot) — Installed TensorFlow + Trained CHT Model (5 epochs, CPU)
- **Decided:** Created separate `.venv-tf/` (Python 3.11) because TF has no 3.14 build. Migrated `11_train_cht_model.py` to Keras 3 API (`keras.ops` instead of `tf.*` on KerasTensors, standalone `import keras`). Removed `ReduceLROnPlateau` callback (conflicts with custom CosineWarmup schedule). 5-epoch CPU verification run (full 50-epoch GPU run recommended for production).
- **Built/Produced:**
  - `.venv-tf/` — Python 3.11 venv with TensorFlow 2.21.0, Keras 3.13.2, sentencepiece 0.2.1
  - `11_train_cht_model.py` — Keras 3 compatible: `build_cht_model()` uses `keras.ops.cast/not_equal/arange/sum/expand_dims`; `main()` uses standalone `keras.optimizers.AdamW`, `keras.losses.*`, `keras.metrics.*`
  - **Training: 33.2 min, 5 epochs, batch 512, CPU-only**
  - **Test set (24,655 samples):**
    - L1 Top-1: **81.89%** | L2 Top-1: **73.25%** | L3 Top-1: **68.81%**
    - L3 Top-3: **83.03%** | L3 Top-5: **86.45%**
    - Hierarchy consistency: **48.59%**
  - **Output files in `ml/models/`:**
    - `xpenz_cht_v3.tflite` — **3.98 MB** (INT8+FP16 hybrid quantized)
    - `xpenz_cht_v3.keras` — 23.8 MB (full precision)
    - `xpenz_cht_v3_best.keras` — best epoch checkpoint (epoch 5)
    - `training_history.json` — per-epoch metrics (5 epochs)
    - `evaluation_report.json` — test set metrics
    - `training_log.csv` — CSV logger output
  - Pyright strict: 0 errors after Keras 3 migration
- **Context updated:** Yes — project-context.md (completed features, folder structure, key decisions)
- **Next recommended:**
  1. Full 50-epoch GPU training for production accuracy (ideally on CUDA/WSL2)
  2. Improve hierarchy consistency (48.59% → target 85%+, may need hierarchy-constraint loss)
  3. Sprint 1 code implementation (Auth → SMS → Dashboard)
---

## 2026-03-09 ML/AI Builder — Synthetic Data Generation + Feature Engineering + CHT Training Pipeline
- **Decided:** Generate synthetic data for 109 unused + 313 low-count L3 categories; build full ML training pipeline (3 scripts)
- **Built/Produced:**
  - **09_synthetic_generator.py (~535 lines):** Generates synthetic merchant records
    - 25 Indian cities with lat/lon, 32 Indian name prefixes, domain-specific business suffixes
    - Augmentation engine: truncation, abbreviation, typo injection, case variation, Hindi transliteration
    - Generated 74,437 synthetic records for 422 categories (109 unused + 313 low-count) in 0.5s
    - Output: synthetic_dataset.csv (13.2 MB)
  - **10_feature_engineering.py (~537 lines):** Feature engineering + stratified split + tokenizer
    - Merges labeled (418,645) + synthetic (74,437) = 493,082 total records
    - Text normalization, 16-dim numerical features (per docs/09 §5.4)
    - SentencePiece BPE tokenizer (vocab=8192, character_coverage=0.9995)
    - Label encoding: L1(15), L2(80), L3(520) code → integer mappings
    - Stratified split: Train 419,120 / Val 49,307 / Test 24,655 (85/10/5)
    - 520/520 L3 coverage in all splits
    - Output: combined_dataset.csv, train.csv, val.csv, test.csv, tokenizer/, class_weights.json, label_encoders.json
  - **11_train_cht_model.py (~715 lines):** CHT model training + TFLite export (CREATED, NOT YET RUN)
    - TransformerBlock: MHA + FFN(gelu) + LayerNorm + Dropout, 3 layers, d=128, h=4, ff=256
    - Hierarchical heads: L1(15) → L2(80, conditioned on L1) → L3(520, conditioned on L2)
    - Multi-task loss: α=0.15 L1 + β=0.25 L2 + γ=0.60 L3
    - AdamW (lr=3e-4, wd=0.01), cosine warmup (2000 steps), 50 epochs, batch=256
    - INT8 + FP16 hybrid TFLite quantization (~3.2 MB target)
    - Eval metrics: L1/L2/L3 accuracy, L3 top-3/top-5, hierarchy consistency
  - **All 3 scripts pass pyright strict (0 errors)**
  - **Packages installed:** sentencepiece 0.2.1
- **Context updated:** Yes — project-context.md (folder structure, completed features, key decisions, training dir status)
- **Next recommended:**
  1. Install TensorFlow (`pip install tensorflow`) and run 11_train_cht_model.py
  2. Review training results (accuracy, model size, TFLite output)
  3. Sprint 1 code implementation (Auth → SMS → Dashboard)
---

## 2026-03-09 Supreme Manager — Session 6 Parts 7-8: TF Installation + v3 Baseline Training
- **Decided:** Created separate `.venv-tf/` with Python 3.11 for TensorFlow (3.14 unsupported). CPU-only training on Windows (GPU unavailable for TF ≥2.11 on native Windows). Ran v3 baseline for 5 epochs with batch_size=512.
- **Built/Produced:**
  - `.venv-tf/` environment: TF 2.21.0, Keras 3.13.2, sentencepiece 0.2.1
  - Fixed Keras 3 compatibility in `11_train_cht_model.py` (keras.ops, standalone import, KerasTensor issues)
  - v3 Baseline Results (5 epochs, 33.2 min):
    - L1: 81.89%, L2: 73.25%, L3: 68.81%, L3-Top3: 83.03%, L3-Top5: 86.45%
    - Hierarchy Consistency: 48.59%
    - TFLite: 3.98 MB (INT8+FP16 hybrid)
  - Stored in `ml/models/`: xpenz_cht_v3.keras, .tflite, evaluation_report.json, training_history.json
- **Context updated:** Yes — project-context.md (dual venv, training results, completed features)
- **Next recommended:** Optimize model — fix bugs (label smoothing unused, class weights unused), increase epochs, improve architecture
---

## 2026-03-09 Supreme Manager — Session 6 Part 9: CHT v4 Optimized Training Pipeline
- **Decided:** User wants absolute best model regardless of training time. Analyzed v3 baseline, found 3 critical bugs (label smoothing not applied, class weights unused, only 5 epochs). Created comprehensive v4 pipeline with 10+ improvements.
- **Built/Produced:**
  - `12_train_cht_v4_optimized.py` (~750 lines) — full optimized training pipeline
  - Architecture improvements: Pre-LayerNorm Transformer, SpatialDropout1D, deeper residual classification heads, learned L1/L2 context embeddings, BatchNorm in numerical branch, GELU throughout
  - Training improvements: Focal loss (gamma=2.0) + label smoothing (0.05) + class weights baked into loss, data augmentation (token masking 15% + numerical noise), SWA, gradient clipping, EarlyStopping patience=20
  - Fixed Keras 3 KeyError: 0 (sample_weight dict bug → baked class weights into focal loss via tf.gather)
  - Fixed ReduceLROnPlateau + CosineWarmup schedule conflict
  - Multi-round pipeline: Round 1 (80ep 3-layer) → Round 2 (40ep finetune) → Round 3 (80ep 4-layer) → Round 4 (conditional)
  - Quick 10-epoch validation test launched and running:
    - Epoch 1 val: L1=76.5%, L2=64.1%, L3=55.7%, L3-Top3=69.8% (strong after just 1 epoch)
- **Context updated:** Yes — project-context.md (v4 pipeline entry, folder structure, script entry)
- **Next recommended:**
  1. Wait for quick test to complete (10 epochs), verify all outputs
  2. Launch full `--mode full` pipeline (4 rounds, ~25 hours)
  3. Evaluate champion model and compare to v3 baseline
---

## 2026-03-09 Supreme Manager — Session 6 Part 10: Quick Test Complete + Full Pipeline Launched
- **Decided:** v4 quick test (10 epochs) validated entire pipeline. Full 4-round pipeline launched for maximum accuracy.
- **Built/Produced:**
  - **v4 Quick Test Results (10 epochs, 86.4 min, test set 24,655 samples):**
    - L1: 82.6% (+0.7% vs v3), L2: 74.2% (+0.9%), L3: 67.7% (-1.1%), L3-Top3: 82.6% (-0.4%), L3-Top5: 86.4% (-0.1%)
    - **Hierarchy Consistency: 90.8% (+42.2% vs v3's 48.6%)** — massive improvement
    - TFLite: 4.89 MB, 2,526,695 params
    - All outputs verified: best.keras, final.keras, model.tflite, evaluation_report.json, eval_pre_swa.json, training_history.json, training_log.csv
  - **Full pipeline launched** (background terminal `ff7d7cf2-4386-4637-9e7f-1ad05bb75c60`):
    - Command: `--mode full` (Round 1: 80ep 3-layer → Round 2: 40ep finetune → Round 3: 80ep 4-layer → Round 4: conditional finetune)
    - Round 1 training started, step 281/1638 of epoch 1 at ~300ms/step
    - Estimated total: ~25 hours for all 4 rounds
- **Context updated:** Yes — chat-history.md (this entry)
- **Next recommended:**
  1. Periodically check `ml/models/v4_round1_3layer/training_log.csv` for Round 1 progress
  2. After Round 1 completes, verify Round 2 finetune starts automatically
  3. After all rounds, check `ml/models/experiment_comparison_v4.json` and champion model
  4. Final model comparison: v3 baseline vs v4 champion
---

## 2026-03-10 Supreme Manager — Session 6 Part 11+: Data Enrichment + CHT v5 Training
- **Decided:** Enrich dataset with more synthetic data for underrepresented categories, rebuild full pipeline, retrain from scratch (new tokenizer = new vocabulary)
- **Built/Produced:**
  - **Script: `13_enhanced_data_generator.py` (~700 lines):**
    - Comprehensive domain-specific merchant name databases for all 15 L1 domains
    - 500+ real Indian merchant names per domain (restaurants, hospitals, schools, banks, etc.)
    - Domain-specific name templates, UPI-style augmentation (truncation, abbreviation, typos, case, Hindi transliteration)
    - Target: min 500 records per L3 category (augmentation_factor=6)
    - **Output: 130,213 new records for 441 underrepresented categories**
  - **Script: `14_rebuild_dataset.py` (~280 lines):**
    - Merges labeled (418,645) + synthetic (74,437) + enhanced (130,213) datasets
    - Deduplication by (normalized_name, l3_code)
    - Full feature engineering: text normalization, 16-dim numerical features, label encoding, class weights, stratified split (85/10/5)
    - SentencePiece BPE tokenizer retrained (vocab=8192) on enriched data
    - **Output: 570,288 total records** | Train: 484,735 | Val: 57,028 | Test: 28,525
    - L3 min count improved: 344 (was ~20), median: 419 (was ~170)
  - **Modified: `12_train_cht_v4_optimized.py`:**
    - Added `bs_override` from `--batch-size` arg for all modes (was only overnight/finetune)
    - Changed full mode output names to `v5_*` prefix (v5 = enriched data models)
    - Reduced epochs: R1 50ep (was 80), R2 25ep (was 40), R3 50ep (was 80), R4 25ep (was 40)
    - Reduced patience: R1/R3 15 (was 20), R2/R4 10 (was 15)
  - **CHT v5 training launched** (terminal `fa4f7148-d71e-4c69-b009-8e2b2667cf71`):
    - Mode: full, batch=512, 504ms/step, 947 steps/epoch
    - Round 1: 50ep, 3-layer (d=128, h=4, ff=256), lr=3e-4, patience=15
    - Round 2: 25ep fine-tune, lr=5e-5, resume from R1 best
    - Round 3: 50ep, 4-layer (d=128, h=4, ff=384), lr=2.5e-4
    - Round 4: 25ep fine-tune 4-layer (conditional)
    - Monitoring: `ml/monitor_training.py` created for status checks
  - **Monitoring script: `ml/monitor_training.py`** — checks all model dirs for training progress
- **Context updated:** Yes — project-context.md (header, folder structure, completed features, key decisions)
- **Next recommended:**
  1. Monitor Round 1 progress via `ml/monitor_training.py` or `ml/models/v5_round1_3layer/training_log.csv`
  2. After all rounds complete, compare v5 champion vs v4 (68.76%) vs v3 (68.81%)
  3. Export best model as TFLite for Android
  4. If accuracy still below target, consider: more real data (Apify scraping), larger model, curriculum learning
---