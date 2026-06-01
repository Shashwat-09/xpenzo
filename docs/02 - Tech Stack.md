# XPENZ - COMPLETE TECH STACK DOCUMENTATION

## 📱 **TECHNOLOGY STACK OVERVIEW**

---

## 1. PLATFORM & CORE

### 1.1 Development Platform

| Technology | Version | Purpose |
| --- | --- | --- |
| **Android** | API 26+ (Android 8.0+) | Target Platform |
| **Kotlin** | 1.9.21 | Primary Language (100%) |
| **Java** | None | No Java code |
| **Gradle** | 8.2+ | Build System |
| **Android Studio** | Giraffe+ | IDE |

### 1.2 Minimum Requirements

```kotlin
android {
    compileSdk = 34        // Android 14
    minSdk = 26            // Android 8.0 (Covers 85%+ devices)
    targetSdk = 34         // Android 14

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}
```

---

## 2. ARCHITECTURE & DESIGN PATTERNS

### 2.1 Architecture

| Pattern | Implementation |
| --- | --- |
| **Clean Architecture** | Domain → Data → Presentation layers |
| **MVVM** | ViewModel + StateFlow/LiveData |
| **Repository Pattern** | Single source of truth |
| **Use Cases** | Business logic encapsulation |
| **Dependency Injection** | Hilt (Dagger) |

### 2.2 Architectural Components

```
androidx.lifecycle:lifecycle-runtime-ktx:2.7.0
androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0
androidx.lifecycle:lifecycle-livedata-ktx:2.7.0
androidx.lifecycle:lifecycle-runtime-compose:2.7.0
```

---

## 3. UI LAYER (PRESENTATION)

### 3.1 UI Framework

| Technology | Version | Purpose |
| --- | --- | --- |
| **Jetpack Compose** | 1.6.0 | Declarative UI |
| **Material 3** | 1.2.0-rc01 | Design System |
| **Compose Navigation** | 2.7.6 | Navigation |
| **Accompanist** | 0.32.0 | Compose Utilities |

### 3.2 Complete UI Dependencies

```kotlin
// Jetpack Compose (18 dependencies)
implementation("androidx.compose.ui:ui:1.6.0")
implementation("androidx.compose.ui:ui-tooling:1.6.0")
implementation("androidx.compose.ui:ui-tooling-preview:1.6.0")
implementation("androidx.compose.ui:ui-util:1.6.0")
implementation("androidx.compose.ui:ui-graphics:1.6.0")
implementation("androidx.compose.ui:ui-text:1.6.0")

// Material Design
implementation("androidx.compose.material3:material3:1.2.0-rc01")
implementation("androidx.compose.material3:material3-window-size-class:1.2.0-rc01")
implementation("androidx.compose.material:material-icons-extended:1.6.0")

// Foundation & Animation
implementation("androidx.compose.foundation:foundation:1.6.0")
implementation("androidx.compose.foundation:foundation-layout:1.6.0")
implementation("androidx.compose.animation:animation:1.6.0")
implementation("androidx.compose.animation:animation-graphics:1.6.0")

// Integration
implementation("androidx.activity:activity-compose:1.8.2")
implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")

// Navigation
implementation("androidx.navigation:navigation-compose:2.7.6")
implementation("androidx.hilt:hilt-navigation-compose:1.1.0")

// Accompanist Utilities (2 remaining — 4 deprecated in Compose 1.6+)
implementation("com.google.accompanist:accompanist-permissions:0.32.0")      // No first-party replacement yet
implementation("com.google.accompanist:accompanist-placeholder-material:0.32.0") // Shimmer loading
// REMOVED (deprecated, now in Compose/Material 3 core):
//   accompanist-systemuicontroller → use enableEdgeToEdge() + WindowCompat
//   accompanist-navigation-animation → use AnimatedNavHost (navigation-compose 2.7+)
//   accompanist-swiperefresh → use PullToRefreshContainer (Material 3)
//   accompanist-flowlayout → use FlowRow/FlowColumn (Compose Foundation 1.4+)

// Image Loading
implementation("io.coil-kt:coil-compose:2.5.0")
implementation("io.coil-kt:coil-svg:2.5.0")

// Charts & Visualization
implementation("com.patrykandpatrick.vico:compose:1.13.1")
implementation("com.patrykandpatrick.vico:compose-m3:1.13.1")

// Animations
implementation("com.airbnb.android:lottie-compose:6.3.0")

// Paging
implementation("androidx.paging:paging-runtime-ktx:3.2.1")
implementation("androidx.paging:paging-compose:3.2.1")
```

---

## 4. DATA LAYER

### 4.1 Local Database

| Technology | Version | Purpose |
| --- | --- | --- |
| **Room** | 2.6.1 | SQLite ORM |
| **SQLite** | Built-in | Database Engine |

```kotlin
// Room Database (4 dependencies)
implementation("androidx.room:room-runtime:2.6.1")
implementation("androidx.room:room-ktx:2.6.1")
ksp("androidx.room:room-compiler:2.6.1")
implementation("androidx.room:room-paging:2.6.1")

// Database Configuration
@Database(
    entities = [
        UserEntity::class,
        TransactionEntity::class,
        FamilyEntity::class,
        FamilyMemberEntity::class,
        BudgetEntity::class,
        MLCategoryEntity::class,
        SMSPatternEntity::class,
        SubscriptionEntity::class,
        BudgetProgressEntity::class,
        NotificationEntity::class,
        SyncQueueEntity::class
        // + Groups & Splits (Option B), DB v2: GroupEntity, GroupMemberEntity,
        //   SplitExpenseEntity, SplitShareEntity, SettlementEntity, FriendEntity
    ],
    version = 1, // → 2 when Groups & Splits ships (Phase 10); see TRD §5.2–5.3
    exportSchema = true
)
```

> **Groups & Splits (Phase 10, post-MVP) adds NO new dependencies.** It reuses Room
> (6 new tables, DB v1→v2 migration), Firestore/Auth, WorkManager, and Hilt. Settle-up
> via UPI uses a standard Android `Intent` to a `upi://pay?...` deep link — no SDK needed.
> See PRD F8, Backend Schema §3.8, TRD Tables 12–17.

### 4.2 Preferences Storage

| Technology | Version | Purpose |
| --- | --- | --- |
| **DataStore** | 1.0.0 | Preferences |
| **EncryptedSharedPreferences** | 1.1.0-alpha06 | Secure Storage |

```kotlin
// DataStore
implementation("androidx.datastore:datastore-preferences:1.0.0")
implementation("androidx.datastore:datastore-core:1.0.0")

// Security
implementation("androidx.security:security-crypto:1.1.0-alpha06")
implementation("androidx.biometric:biometric:1.1.0")
```

### 4.3 Serialization

> **Decision:** Gson removed. Moshi is used for Retrofit (better Kotlin null-safety).
> kotlinx-serialization is used for all internal data classes (official Kotlin, Coroutines-native).

```kotlin
// JSON Parsing (3 dependencies — Gson removed to avoid duplication)
implementation("com.squareup.moshi:moshi-kotlin:1.15.0")         // Retrofit JSON converter
ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.0")            // Moshi Kotlin codegen
implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2") // Internal serialization
```

---

## 5. NETWORKING & CLOUD

### 5.1 HTTP Client

| Technology | Version | Purpose |
| --- | --- | --- |
| **Retrofit** | 2.9.0 | REST API Client |
| **OkHttp** | 4.12.0 | HTTP Client |

```kotlin
// Networking (4 dependencies — converter-gson removed, Moshi used instead)
implementation("com.squareup.retrofit2:retrofit:2.9.0")
implementation("com.squareup.retrofit2:converter-moshi:2.9.0")
implementation("com.squareup.okhttp3:okhttp:4.12.0")
implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
```

### 5.2 Firebase Services

| Service | Purpose |
| --- | --- |
| **Firebase Firestore** | Cloud Database |
| **Firebase Auth** | Phone Authentication |
| **Firebase Storage** | File Storage (Receipts, ML Models) |
| **Firebase Cloud Messaging** | Push Notifications |
| **Firebase Crashlytics** | Crash Reporting |
| **Firebase Analytics** | Analytics |
| **Firebase Performance** | Performance Monitoring |
| **Firebase Remote Config** | Feature Flags |

```kotlin
// Firebase (10 dependencies via BOM)
implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
implementation("com.google.firebase:firebase-firestore-ktx")
implementation("com.google.firebase:firebase-auth-ktx")
implementation("com.google.firebase:firebase-storage-ktx")
implementation("com.google.firebase:firebase-messaging-ktx")
implementation("com.google.firebase:firebase-crashlytics-ktx")
implementation("com.google.firebase:firebase-analytics-ktx")
implementation("com.google.firebase:firebase-perf-ktx")
implementation("com.google.firebase:firebase-config-ktx")
implementation("com.google.firebase:firebase-functions-ktx")
implementation("com.google.firebase:firebase-installations-ktx")
```

### 5.3 Google Play Services

```kotlin
// Google Play Services (3 dependencies)
implementation("com.google.android.gms:play-services-auth:20.7.0")
implementation("com.google.android.gms:play-services-location:21.1.0")
implementation("com.android.billingclient:billing-ktx:6.1.0")
```

---

## 6. MACHINE LEARNING

> ⚠️ **CANONICAL SPEC:** Full ML architecture in `docs/09 - ML Architecture Specification.md`

### 6.1 ML Framework

| Technology | Version | Purpose |
| --- | --- | --- |
| **TensorFlow Lite** | 2.14.0 | On-Device Inference |
| **TFLite Support** | 0.4.4 | Helper Library |
| **TFLite GPU** | 2.14.0 | GPU Acceleration |
| **SentencePiece** | 0.2.0 | BPE Tokenizer (via TFLite custom ops) |

```kotlin
// TensorFlow Lite (5 dependencies)
implementation("org.tensorflow:tensorflow-lite:2.14.0")
implementation("org.tensorflow:tensorflow-lite-support:0.4.4")
implementation("org.tensorflow:tensorflow-lite-metadata:0.4.4")
implementation("org.tensorflow:tensorflow-lite-gpu:2.14.0")
implementation("org.tensorflow:tensorflow-lite-select-tf-ops:2.14.0")
```

### 6.2 ML Models (v3 Ensemble)

| Component | Type | Size | Purpose |
| --- | --- | --- | --- |
| **Compact Hierarchical Transformer** | 3-layer Transformer (d=128, 4 heads) | 3.2 MB | Primary text classifier (SentencePiece BPE, 8K vocab) |
| **Rule Engine** | Trie-based pattern matcher | 350 KB | Exact-match for known merchants/UPI patterns |
| **Amount-Time Prior** | Lookup table | 150 KB | P(category \| amount_bucket, time_slot) |
| **User Habit Model** | Room DB queries | 0 KB | Personalized merchant→category frequency map |
| **Total** | Adaptive Ensemble | **3.7 MB** | 520-Category Hierarchical Classification (15→80→520) |

**Asset Files:**

```
app/src/main/assets/
├── xpenz_cht_v3.tflite        (3.2 MB)  — Compact Hierarchical Transformer
├── xpenz_bpe.model            (150 KB)  — SentencePiece tokenizer
├── rules_v3.json              (350 KB)  — Rule engine patterns
├── atp_v3.bin                 (150 KB)  — Amount-Time Prior table
└── category_mapping.json      (50 KB)   — 520-category hierarchy
```

### 6.3 Transaction Detection (Dual-Channel)

| Technology | Version | Purpose |
| --- | --- | --- |
| **BroadcastReceiver** | Android SDK | Primary SMS detection (READ_SMS) |
| **NotificationListenerService** | Android SDK | Fallback detection via banking app notifications |

> **Dual-channel strategy:** Primary detection via `SMS_RECEIVED` BroadcastReceiver. Fallback via `NotificationListenerService` for devices where READ_SMS is restricted (Android 13+) or where banks use push notifications instead of SMS. User grants notification access during onboarding if SMS permission is denied.

---

## 7. BACKGROUND PROCESSING

### 7.1 Background Work

| Technology | Version | Purpose |
| --- | --- | --- |
| **WorkManager** | 2.9.0 | Background Tasks |
| **Coroutines** | 1.7.3 | Async Operations |

```kotlin
// WorkManager (3 dependencies)
implementation("androidx.work:work-runtime-ktx:2.9.0")
implementation("androidx.work:work-multiprocess:2.9.0")
implementation("androidx.hilt:hilt-work:1.1.0")

// Coroutines (3 dependencies)
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.7.3")
```

### 7.2 Background Services

| Service | Purpose |
| --- | --- |
| **SMSReceiver** | BroadcastReceiver for SMS |
| **SyncWorker** | Periodic cloud sync |
| **SMSProcessingWorker** | Transaction parsing |
| **BudgetAlertWorker** | Budget monitoring |
| **ModelUpdateWorker** | ML model updates |

---

## 8. DEPENDENCY INJECTION

| Technology | Version | Purpose |
| --- | --- | --- |
| **Hilt** | 2.50 | DI Framework |
| **Dagger** | 2.50 | DI Core |

```kotlin
// Hilt (3 dependencies)
implementation("com.google.dagger:hilt-android:2.50")
ksp("com.google.dagger:hilt-compiler:2.50")
implementation("androidx.hilt:hilt-work:1.1.0")

// Annotation Processing
plugins {
    id("com.google.devtools.ksp") version "1.9.21-1.0.15"
    id("dagger.hilt.android.plugin")
}
```

---

## 9. UTILITIES

### 9.1 Date/Time

```kotlin
implementation("org.jetbrains.kotlinx:kotlinx-datetime:0.5.0")
```

### 9.2 Logging

```kotlin
implementation("com.jakewharton.timber:timber:5.0.1")
```

### 9.3 Document Generation

```kotlin
// Excel/PDF Generation
implementation("org.apache.poi:poi-ooxml:5.2.5")
implementation("com.itextpdf:itext7-core:8.0.2")
```

---

## 10. TESTING

### 10.1 Unit Testing

```kotlin
// Unit Testing (10 dependencies)
testImplementation("junit:junit:4.13.2")
testImplementation("io.mockk:mockk:1.13.8")
testImplementation("io.mockk:mockk-android:1.13.8")
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
testImplementation("app.cash.turbine:turbine:1.0.0")
testImplementation("com.google.truth:truth:1.1.5")
testImplementation("androidx.arch.core:core-testing:2.2.0")
testImplementation("androidx.room:room-testing:2.6.1")
testImplementation("org.robolectric:robolectric:4.11.1")
testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
```

### 10.2 Instrumentation Testing

```kotlin
// Android Instrumentation Tests (8 dependencies)
androidTestImplementation("androidx.test:runner:1.5.2")
androidTestImplementation("androidx.test:rules:1.5.0")
androidTestImplementation("androidx.test.ext:junit:1.1.5")
androidTestImplementation("androidx.test.ext:junit-ktx:1.1.5")
androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
androidTestImplementation("androidx.test.espresso:espresso-intents:3.5.1")
androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.6.0")
debugImplementation("androidx.compose.ui:ui-test-manifest:1.6.0")
```

### 10.3 Code Quality

```kotlin
// Static Analysis (3 dependencies)
detektPlugins("io.gitlab.arturbosch.detekt:detekt-formatting:1.23.4")
implementation("com.pinterest:ktlint:0.50.0")
implementation("org.jacoco:org.jacoco.core:0.8.11")
```

---

## 11. BUILD & DEPLOYMENT

### 11.1 Build Tools

| Tool | Version | Purpose |
| --- | --- | --- |
| **Gradle** | 8.2+ | Build System |
| **Android Gradle Plugin** | 8.2.1 | Android Build |
| **KSP** | 1.9.21-1.0.15 | Kotlin Symbol Processing |

```kotlin
plugins {
    id("com.android.application") version "8.2.1"
    id("org.jetbrains.kotlin.android") version "1.9.21"
    id("com.google.devtools.ksp") version "1.9.21-1.0.15"
    id("dagger.hilt.android.plugin") version "2.50"
    id("com.google.gms.google-services") version "4.4.0"
    id("com.google.firebase.crashlytics") version "2.9.9"
    kotlin("plugin.serialization") version "1.9.21"
}
```

### 11.2 ProGuard/R8

```
# ProGuard Rules
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt

# Retrofit
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}

# TensorFlow Lite
-keep class org.tensorflow.lite.** { *; }
-keep interface org.tensorflow.lite.** { *; }

# Firebase
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }

# Room
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-dontwarn androidx.room.paging.**
```

### 11.3 CI/CD

| Tool | Purpose |
| --- | --- |
| **GitHub Actions** | CI/CD Pipeline |
| **Firebase App Distribution** | Beta Testing |
| **Google Play Console** | Production Deployment |
| **Codecov** | Code Coverage |

---

## 12. DEVELOPMENT TOOLS

### 12.1 IDE & Extensions

| Tool | Version | Purpose |
| --- | --- | --- |
| **Android Studio** | Giraffe+ | IDE |
| **Android Emulator** | Built-in | Testing |
| **ADB** | Built-in | Device Debugging |

### 12.2 Debug Tools

```kotlin
debugImplementation("com.squareup.leakcanary:leakcanary-android:2.12")
debugImplementation("com.facebook.flipper:flipper:0.212.0")
debugImplementation("com.facebook.soloader:soloader:0.10.5")
```

---

## 13. COMPLETE DEPENDENCY COUNT

### Summary by Category

| Category | Count |
| --- | --- |
| **Core Android** | 15 |
| **Jetpack Compose** | 18 |
| **Room Database** | 4 |
| **Coroutines** | 3 |
| **Hilt/DI** | 3 |
| **Networking** | 4 |
| **Firebase** | 10 |
| **Google Play Services** | 3 |
| **TensorFlow Lite** | 5 |
| **WorkManager** | 3 |
| **DataStore** | 2 |
| **Security** | 2 |
| **JSON** | 3 |
| **Image Loading** | 2 |
| **Paging** | 2 |
| **Charts** | 2 |
| **Document Generation** | 2 |
| **Date/Time** | 1 |
| **Logging** | 1 |
| **Accompanist** | 2 |
| **Animations** | 1 |
| **Unit Testing** | 10 |
| **Android Testing** | 8 |
| **Code Quality** | 3 |
| **TOTAL** | **108** |

---

## 14. VERSION CATALOG (libs.versions.toml)

```toml
[versions]
kotlin = "1.9.21"
compose = "1.6.0"
composeCompiler = "1.5.7"
androidGradlePlugin = "8.2.1"
ksp = "1.9.21-1.0.15"
hilt = "2.50"
room = "2.6.1"
coroutines = "1.7.3"
retrofit = "2.9.0"
okhttp = "4.12.0"
firebase = "32.7.0"
tensorflow = "2.14.0"
lifecycle = "2.7.0"
work = "2.9.0"
coil = "2.5.0"

[libraries]
# Kotlin
kotlin-stdlib = { module = "org.jetbrains.kotlin:kotlin-stdlib", version.ref = "kotlin" }
kotlinx-coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
kotlinx-coroutines-android = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-android", version.ref = "coroutines" }

# Android Core
androidx-core-ktx = { module = "androidx.core:core-ktx", version = "1.12.0" }
androidx-lifecycle-runtime-ktx = { module = "androidx.lifecycle:lifecycle-runtime-ktx", version.ref = "lifecycle" }

# Compose
androidx-compose-bom = { module = "androidx.compose:compose-bom", version = "2024.01.00" }
androidx-compose-ui = { module = "androidx.compose.ui:ui", version.ref = "compose" }
androidx-compose-material3 = { module = "androidx.compose.material3:material3", version = "1.2.0-rc01" }

# Hilt
hilt-android = { module = "com.google.dagger:hilt-android", version.ref = "hilt" }
hilt-compiler = { module = "com.google.dagger:hilt-compiler", version.ref = "hilt" }

# Room
androidx-room-runtime = { module = "androidx.room:room-runtime", version.ref = "room" }
androidx-room-ktx = { module = "androidx.room:room-ktx", version.ref = "room" }
androidx-room-compiler = { module = "androidx.room:room-compiler", version.ref = "room" }

# Firebase
firebase-bom = { module = "com.google.firebase:firebase-bom", version.ref = "firebase" }
firebase-firestore = { module = "com.google.firebase:firebase-firestore-ktx" }
firebase-auth = { module = "com.google.firebase:firebase-auth-ktx" }

# TensorFlow Lite
tensorflow-lite = { module = "org.tensorflow:tensorflow-lite", version.ref = "tensorflow" }
tensorflow-lite-support = { module = "org.tensorflow:tensorflow-lite-support", version = "0.4.4" }

# Testing
junit = { module = "junit:junit", version = "4.13.2" }
mockk = { module = "io.mockk:mockk", version = "1.13.8" }
truth = { module = "com.google.truth:truth", version = "1.1.5" }

[plugins]
android-application = { id = "com.android.application", version.ref = "androidGradlePlugin" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
google-services = { id = "com.google.gms.google-services", version = "4.4.0" }
```

---

## 15. APP SIZE ESTIMATES

| Component | Size |
| --- | --- |
| **APK Size (Debug)** | ~45 MB |
| **APK Size (Release)** | ~12 MB |
| **AAB Size** | ~10 MB |
| **Download Size (Play Store)** | ~8 MB |
| **Installed Size** | ~25 MB |
| **ML Models** | 4.0 MB |
| **Assets** | 1 MB |
| **Native Libraries** | 3 MB |
| **Resources** | 2 MB |

---

This is the **COMPLETE TECH STACK** for Xpenz with all 108 dependencies documented.

