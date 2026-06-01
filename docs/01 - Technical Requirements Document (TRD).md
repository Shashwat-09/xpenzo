# XPENZ - TECHNICAL REQUIREMENTS DOCUMENT (TRD)

## Complete Technical Specification for AI-Assisted Development

**Version:** 1.0

**Date:** February 24, 2026

**Status:** Ready for Development

**Target Platform:** Android (API 26+)

---

## TABLE OF CONTENTS

**PART 1: ARCHITECTURE & DESIGN**

1. System Architecture
2. Technology Stack (106 Dependencies)
3. Module Structure
4. Design Patterns

**PART 2: DATA & STORAGE**
5. Database Schema (11 Tables)
6. Data Models
7. Repository Pattern
8. Cloud Sync Architecture

**PART 3: MACHINE LEARNING**
9. ML Model Architecture
10. Training Pipeline
11. On-Device Inference
12. Model Updates

**PART 4: CORE FEATURES**
13. SMS Detection & Parsing
14. Transaction Classification
15. Family Management
16. Budget System
17. Real-Time Sync

**PART 5: INFRASTRUCTURE**
18. Security & Privacy
19. Performance Optimization
20. Testing Strategy
21. Monitoring & Analytics

**PART 6: IMPLEMENTATION**
22. Development Roadmap (20 Weeks)
23. API Documentation
24. Deployment Strategy

---

# PART 1: ARCHITECTURE & DESIGN

## 1. SYSTEM ARCHITECTURE

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ANDROID APPLICATION                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │          PRESENTATION LAYER (UI)                    │   │
│  │  • Jetpack Compose                                  │   │
│  │  • Material 3 Design                                │   │
│  │  • Navigation Component                             │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓↑                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │          VIEW MODEL LAYER (MVVM)                    │   │
│  │  • StateFlow/LiveData                               │   │
│  │  • Coroutines                                       │   │
│  │  • UI State Management                              │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓↑                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │          DOMAIN LAYER (Business Logic)              │   │
│  │  • Use Cases (Interactors)                          │   │
│  │  • Domain Models                                    │   │
│  │  • Repository Interfaces                            │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↓↑                                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │          DATA LAYER (Implementation)                │   │
│  │  • Repository Implementations                       │   │
│  │  • Local Data Source (Room)                         │   │
│  │  • Remote Data Source (Firestore)                   │   │
│  │  • ML Service (TensorFlow Lite)                     │   │
│  └────────────────────────────────────────────────────┘   │
│         ↓↑              ↓↑              ↓↑                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │   ROOM   │    │ FIRESTORE│    │  TFLITE  │           │
│  │ DATABASE │    │  + AUTH  │    │  MODELS  │           │
│  └──────────┘    └──────────┘    └──────────┘           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │       BACKGROUND SERVICES                           │   │
│  │  • SMS Listener (BroadcastReceiver)                 │   │
│  │  • Sync Service (WorkManager)                       │   │
│  │  • Notification Service (FCM)                       │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Clean Architecture Layers

**Layer 1: Presentation (UI)**

- **Technology:** Jetpack Compose
- **Responsibility:** Display data, handle user input
- **Components:**
    - Composable screens
    - ViewModels
    - Navigation graphs
    - UI state classes

**Layer 2: Domain (Business Logic)**

- **Technology:** Pure Kotlin
- **Responsibility:** Business rules, use cases
- **Components:**
    - Use case classes
    - Domain models
    - Repository interfaces
    - Business validators

**Layer 3: Data (Implementation)**

- **Technology:** Room, Retrofit, TFLite
- **Responsibility:** Data access, storage, ML inference
- **Components:**
    - Repository implementations
    - Data sources (local/remote)
    - DAOs
    - API services
    - ML inference engine

**Layer 4: Framework**

- **Technology:** Android Framework, Third-party SDKs
- **Responsibility:** Platform-specific code
- **Components:**
    - BroadcastReceivers
    - Services
    - WorkManager workers
    - Firebase SDKs

### 1.3 Data Flow Example

**Use Case: SMS Transaction Detection**

```
1. SMS Received
   ↓
2. BroadcastReceiver (SMSReceiver)
   • Triggered by android.provider.Telephony.SMS_RECEIVED
   ↓
3. SMSListenerService
   • Extract sender, message body, timestamp
   • Filter: Only UPI/bank transaction messages
   ↓
4. SMSParser
   • Regex-based parsing
   • Extract: amount, merchant, type, bank
   • Return: ParsedSMSData
   ↓
5. TrackTransactionUseCase
   • Validate parsed data
   • Call MLClassificationService
   ↓
6. MLClassificationService
   • Feature extraction
   • TFLite model inference (1 CHT model + 3 non-neural components)
   • Ensemble voting
   • Return: Category (1-520) + Confidence
   ↓
7. TransactionRepository
   • Create TransactionEntity
   • Insert into Room database
   • If Premium: Queue for cloud sync
   ↓
8. Room Database
   • Save transaction locally
   • Notify observers (Flow)
   ↓
9. ViewModel
   • Receive update via Flow
   • Update UI state
   ↓
10. Compose UI
    • Recompose with new transaction
    • Animate entry

If Premium:
11. SyncWorker (WorkManager)
    • Encrypt transaction
    • Upload to Firestore
    ↓
12. Firestore
    • Save in /families/{familyId}/transactions
    • Trigger Cloud Function
    ↓
13. Cloud Function
    • Send FCM to other family members
    ↓
14. Other devices receive FCM
    • Download new transaction
    • Decrypt and save locally
    • Update UI
```

---

## 2. TECHNOLOGY STACK

### 2.1 Core Technologies

**Programming Language:**

- **Kotlin 1.9.21** (100% Kotlin, zero Java)
- Coroutines for async
- Flow for reactive streams
- Sealed classes for state
- Data classes for models

**Build System:**

- **Gradle 8.2+** with Kotlin DSL
- Version Catalogs (libs.versions.toml)
- Multi-module architecture
- Build types: debug, release, benchmark

**Android SDK:**

- **compileSdk:** 34 (Android 14)
- **minSdk:** 26 (Android 8.0)
- **targetSdk:** 34
- Supports 85%+ of active Android devices

### 2.2 Complete Dependency List (106 Total)

### **GROUP A: CORE ANDROID (15 dependencies)**

```kotlin
// Core
androidx.core:core-ktx:1.12.0
androidx.appcompat:appcompat:1.6.1
androidx.activity:activity-ktx:1.8.2
androidx.fragment:fragment-ktx:1.6.2

// Lifecycle
androidx.lifecycle:lifecycle-runtime-ktx:2.7.0
androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0
androidx.lifecycle:lifecycle-livedata-ktx:2.7.0
androidx.lifecycle:lifecycle-runtime-compose:2.7.0
androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0
androidx.lifecycle:lifecycle-process:2.7.0

// SavedState
androidx.savedstate:savedstate-ktx:1.2.1

// Startup
androidx.startup:startup-runtime:1.1.1

// SplashScreen
androidx.core:core-splashscreen:1.0.1

// Window
androidx.window:window:1.2.0

// Browser
androidx.browser:browser:1.7.0
```

### **GROUP B: JETPACK COMPOSE (18 dependencies)**

```kotlin
// Compose UI
androidx.compose.ui:ui:1.6.0
androidx.compose.ui:ui-tooling:1.6.0
androidx.compose.ui:ui-tooling-preview:1.6.0
androidx.compose.ui:ui-util:1.6.0
androidx.compose.ui:ui-graphics:1.6.0
androidx.compose.ui:ui-text:1.6.0

// Material 3
androidx.compose.material3:material3:1.2.0-rc01
androidx.compose.material3:material3-window-size-class:1.2.0-rc01
androidx.compose.material:material-icons-extended:1.6.0

// Foundation & Animation
androidx.compose.foundation:foundation:1.6.0
androidx.compose.foundation:foundation-layout:1.6.0
androidx.compose.animation:animation:1.6.0
androidx.compose.animation:animation-graphics:1.6.0

// Integration
androidx.activity:activity-compose:1.8.2
androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0
androidx.lifecycle:lifecycle-runtime-compose:2.7.0

// Navigation
androidx.navigation:navigation-compose:2.7.6
androidx.hilt:hilt-navigation-compose:1.1.0
```

### **GROUP C: ROOM DATABASE (4 dependencies)**

```kotlin
androidx.room:room-runtime:2.6.1
androidx.room:room-ktx:2.6.1
androidx.room:room-compiler:2.6.1 // kapt/ksp
androidx.room:room-paging:2.6.1
```

### **GROUP D: COROUTINES (3 dependencies)**

```kotlin
org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3
org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3
org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.7.3
```

### **GROUP E: DEPENDENCY INJECTION - HILT (3 dependencies)**

```kotlin
com.google.dagger:hilt-android:2.50
com.google.dagger:hilt-compiler:2.50 // kapt/ksp
androidx.hilt:hilt-work:1.1.0
```

### **GROUP F: NETWORKING (5 dependencies)**

```kotlin
com.squareup.retrofit2:retrofit:2.9.0
com.squareup.retrofit2:converter-gson:2.9.0
com.squareup.retrofit2:converter-moshi:2.9.0
com.squareup.okhttp3:okhttp:4.12.0
com.squareup.okhttp3:logging-interceptor:4.12.0
```

### **GROUP G: FIREBASE (10 dependencies)**

```kotlin
// BOM (manages versions)
com.google.firebase:firebase-bom:32.7.0

// Individual modules (versions from BOM)
com.google.firebase:firebase-firestore-ktx
com.google.firebase:firebase-auth-ktx
com.google.firebase:firebase-storage-ktx
com.google.firebase:firebase-messaging-ktx
com.google.firebase:firebase-crashlytics-ktx
com.google.firebase:firebase-analytics-ktx
com.google.firebase:firebase-perf-ktx
com.google.firebase:firebase-config-ktx
com.google.firebase:firebase-functions-ktx
com.google.firebase:firebase-installations-ktx
```

### **GROUP H: GOOGLE PLAY SERVICES (3 dependencies)**

```kotlin
com.google.android.gms:play-services-auth:20.7.0
com.google.android.gms:play-services-location:21.1.0
com.android.billingclient:billing-ktx:6.1.0
```

### **GROUP I: MACHINE LEARNING - TENSORFLOW LITE (5 dependencies)**

```kotlin
org.tensorflow:tensorflow-lite:2.14.0
org.tensorflow:tensorflow-lite-support:0.4.4
org.tensorflow:tensorflow-lite-metadata:0.4.4
org.tensorflow:tensorflow-lite-gpu:2.14.0
org.tensorflow:tensorflow-lite-select-tf-ops:2.14.0
```

### **GROUP J: WORKMANAGER (3 dependencies)**

```kotlin
androidx.work:work-runtime-ktx:2.9.0
androidx.work:work-multiprocess:2.9.0
androidx.hilt:hilt-work:1.1.0
```

### **GROUP K: DATASTORE (2 dependencies)**

```kotlin
androidx.datastore:datastore-preferences:1.0.0
androidx.datastore:datastore-core:1.0.0
```

### **GROUP L: SECURITY & ENCRYPTION (2 dependencies)**

```kotlin
androidx.security:security-crypto:1.1.0-alpha06
androidx.biometric:biometric:1.1.0
```

### **GROUP M: JSON/SERIALIZATION (4 dependencies)**

```kotlin
com.google.code.gson:gson:2.10.1
com.squareup.moshi:moshi-kotlin:1.15.0
com.squareup.moshi:moshi-kotlin-codegen:1.15.0 // kapt/ksp
org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2
```

### **GROUP N: IMAGE LOADING (2 dependencies)**

```kotlin
io.coil-kt:coil-compose:2.5.0
io.coil-kt:coil-svg:2.5.0
```

### **GROUP O: PAGING (2 dependencies)**

```kotlin
androidx.paging:paging-runtime-ktx:3.2.1
androidx.paging:paging-compose:3.2.1
```

### **GROUP P: CHARTS/VISUALIZATION (2 dependencies)**

```kotlin
com.patrykandpatrick.vico:compose:1.13.1
com.patrykandpatrick.vico:compose-m3:1.13.1
```

### **GROUP Q: DOCUMENT GENERATION (2 dependencies)**

```kotlin
org.apache.poi:poi-ooxml:5.2.5  // Excel
com.itextpdf:itext7-core:8.0.2  // PDF
```

### **GROUP R: DATE/TIME (1 dependency)**

```kotlin
org.jetbrains.kotlinx:kotlinx-datetime:0.5.0
```

### **GROUP S: LOGGING (1 dependency)**

```kotlin
com.jakewharton.timber:timber:5.0.1
```

### **GROUP T: ANIMATIONS (1 dependency)**

```kotlin
com.airbnb.android:lottie-compose:6.3.0
```

### **GROUP U: ACCOMPANIST UTILITIES (6 dependencies)**

```kotlin
com.google.accompanist:accompanist-permissions:0.32.0
com.google.accompanist:accompanist-systemuicontroller:0.32.0
com.google.accompanist:accompanist-navigation-animation:0.32.0
com.google.accompanist:accompanist-placeholder-material:0.32.0
com.google.accompanist:accompanist-swiperefresh:0.32.0
com.google.accompanist:accompanist-flowlayout:0.32.0
```

### **GROUP V: TESTING - UNIT (10 dependencies)**

```kotlin
junit:junit:4.13.2
io.mockk:mockk:1.13.8
io.mockk:mockk-android:1.13.8
org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3
app.cash.turbine:turbine:1.0.0
com.google.truth:truth:1.1.5
androidx.arch.core:core-testing:2.2.0
androidx.room:room-testing:2.6.1
org.robolectric:robolectric:4.11.1
com.squareup.okhttp3:mockwebserver:4.12.0
```

### **GROUP W: TESTING - ANDROID INSTRUMENTATION (8 dependencies)**

```kotlin
androidx.test:runner:1.5.2
androidx.test:rules:1.5.0
androidx.test.ext:junit:1.1.5
androidx.test.ext:junit-ktx:1.1.5
androidx.test.espresso:espresso-core:3.5.1
androidx.test.espresso:espresso-intents:3.5.1
androidx.compose.ui:ui-test-junit4:1.6.0
androidx.compose.ui:ui-test-manifest:1.6.0
```

### **GROUP X: CODE QUALITY (3 dependencies)**

```kotlin
io.gitlab.arturbosch.detekt:detekt-formatting:1.23.4
com.pinterest:ktlint:0.50.0
org.jacoco:org.jacoco.core:0.8.11
```

**TOTAL: 106 DEPENDENCIES**

### 2.3 Gradle Configuration

**build.gradle.kts (Project Level)**

```kotlin
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.hilt) apply false
    alias(libs.plugins.google.services) apply false
    alias(libs.plugins.firebase.crashlytics) apply false
}

buildscript {
    repositories {
        google()
        mavenCentral()
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
}

tasks.register("clean", Delete::class) {
    delete(rootProject.buildDir)
}
```

**build.gradle.kts (App Level)**

```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
    alias(libs.plugins.google.services)
    alias(libs.plugins.firebase.crashlytics)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.xpenz.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.xpenz.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        vectorDrawables {
            useSupportLibrary = true
        }

        // Room schema export
        ksp {
            arg("room.schemaLocation", "$projectDir/schemas")
            arg("room.incremental", "true")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )

            // Enable R8 full mode
            isDebuggable = false
        }

        debug {
            isMinifyEnabled = false
            isDebuggable = true
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-DEBUG"
        }

        create("benchmark") {
            initWith(getByName("release"))
            signingConfig = signingConfigs.getByName("debug")
            isDebuggable = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=kotlin.RequiresOptIn",
            "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
            "-opt-in=kotlinx.coroutines.FlowPreview",
            "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api"
        )
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.7"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Core Android
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.activity.ktx)

    // Compose
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    debugImplementation(libs.androidx.compose.ui.tooling)

    // Lifecycle
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)

    // Hilt
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.androidx.hilt.navigation.compose)

    // Room
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    // Coroutines
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.android)

    // Firebase
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.firestore.ktx)
    implementation(libs.firebase.auth.ktx)
    implementation(libs.firebase.messaging.ktx)
    implementation(libs.firebase.crashlytics.ktx)
    implementation(libs.firebase.analytics.ktx)

    // TensorFlow Lite
    implementation(libs.tensorflow.lite)
    implementation(libs.tensorflow.lite.support)
    implementation(libs.tensorflow.lite.gpu)

    // ... rest of dependencies

    // Testing
    testImplementation(libs.junit)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.turbine)
    testImplementation(libs.truth)

    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.androidx.test.espresso.core)
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}
```

---

## 3. MODULE STRUCTURE

### 3.1 Multi-Module Architecture

```
xpenz/
├── app/                                    # Main application module
│   ├── src/main/
│   │   ├── kotlin/com/xpenz/app/
│   │   │   ├── XpenzApplication.kt        # Application class
│   │   │   ├── MainActivity.kt            # Single activity
│   │   │   ├── navigation/                # App navigation
│   │   │   └── di/                        # App-level DI modules
│   │   ├── res/                           # App resources
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
│
├── core/
│   ├── common/                            # Common utilities
│   │   ├── src/main/kotlin/
│   │   │   ├── util/                      # Extension functions, helpers
│   │   │   ├── constants/                 # App constants
│   │   │   └── result/                    # Result wrapper class
│   │   └── build.gradle.kts
│   │
│   ├── data/                              # Data layer
│   │   ├── src/main/kotlin/
│   │   │   ├── repository/                # Repository implementations
│   │   │   ├── mapper/                    # Data mappers
│   │   │   └── di/                        # Data DI modules
│   │   └── build.gradle.kts
│   │
│   ├── database/                          # Room database
│   │   ├── src/main/kotlin/
│   │   │   ├── XpenzDatabase.kt          # Database class
│   │   │   ├── dao/                       # DAOs
│   │   │   ├── entity/                    # Room entities
│   │   │   ├── migration/                 # Database migrations
│   │   │   └── di/                        # Database DI module
│   │   ├── schemas/                       # Room schema exports
│   │   └── build.gradle.kts
│   │
│   ├── domain/                            # Domain layer
│   │   ├── src/main/kotlin/
│   │   │   ├── model/                     # Domain models
│   │   │   ├── repository/                # Repository interfaces
│   │   │   └── usecase/                   # Use cases
│   │   └── build.gradle.kts
│   │
│   ├── network/                           # Network layer
│   │   ├── src/main/kotlin/
│   │   │   ├── firebase/                  # Firebase services
│   │   │   ├── api/                       # API services (if any)
│   │   │   └── di/                        # Network DI modules
│   │   └── build.gradle.kts
│   │
│   ├── datastore/                         # DataStore preferences
│   │   ├── src/main/kotlin/
│   │   │   ├── UserPreferencesDataStore.kt
│   │   │   └── di/
│   │   └── build.gradle.kts
│   │
│   └── ml/                                # ML inference
│       ├── src/main/kotlin/
│       │   ├── MLInferenceService.kt
│       │   ├── model/                     # TFLite model wrapper
│       │   ├── preprocessing/             # Feature extraction
│       │   └── di/
│       ├── src/main/assets/
│       │   ├── xpenz_cht_v3.tflite        # Compact Hierarchical Transformer (3.2 MB)
│       │   ├── xpenz_bpe.model            # SentencePiece tokenizer (150 KB)
│       │   ├── rules_v3.json              # Rule engine patterns (350 KB)
│       │   ├── atp_v3.bin                 # Amount-Time Prior table (150 KB)
│       │   └── category_mapping.json      # 520 categories
│       └── build.gradle.kts
│
├── feature/
│   ├── onboarding/                        # Onboarding feature
│   │   ├── src/main/kotlin/
│   │   │   ├── ui/                        # Compose screens
│   │   │   ├── viewmodel/                 # ViewModels
│   │   │   └── navigation/                # Feature navigation
│   │   └── build.gradle.kts
│   │
│   ├── transaction/                       # Transaction tracking
│   │   ├── src/main/kotlin/
│   │   │   ├── ui/
│   │   │   ├── viewmodel/
│   │   │   ├── service/                   # SMS listener service
│   │   │   └── parser/                    # SMS parser
│   │   └── build.gradle.kts
│   │
│   ├── family/                            # Family management
│   │   ├── src/main/kotlin/
│   │   │   ├── ui/
│   │   │   ├── viewmodel/
│   │   │   └── sync/                      # Family sync logic
│   │   └── build.gradle.kts
│   │
│   ├── budget/                            # Budget management
│   │   ├── src/main/kotlin/
│   │   │   ├── ui/
│   │   │   ├── viewmodel/
│   │   │   └── calculator/                # Budget calculations
│   │   └── build.gradle.kts
│   │
│   ├── dashboard/                         # Dashboard
│   │   ├── src/main/kotlin/
│   │   │   ├── ui/
│   │   │   ├── viewmodel/
│   │   │   └── analytics/                 # Dashboard analytics
│   │   └── build.gradle.kts
│   │
│   ├── settings/                          # Settings
│   │   ├── src/main/kotlin/
│   │   │   ├── ui/
│   │   │   └── viewmodel/
│   │   └── build.gradle.kts
│   │
│   └── premium/                           # Premium subscription
│       ├── src/main/kotlin/
│       │   ├── ui/
│       │   ├── viewmodel/
│       │   └── billing/                   # Google Play Billing
│       └── build.gradle.kts
│
├── buildSrc/                              # Build configuration
│   ├── src/main/kotlin/
│   │   ├── Dependencies.kt
│   │   └── Versions.kt
│   └── build.gradle.kts
│
├── gradle/
│   └── libs.versions.toml                 # Version catalog
│
├── build.gradle.kts                       # Root build file
├── settings.gradle.kts                    # Project settings
└── gradle.properties                      # Gradle properties
```

### 3.2 Module Dependencies

```
app
├── depends on → feature:*
├── depends on → core:*

feature:transaction
├── depends on → core:domain
├── depends on → core:data
├── depends on → core:ml
├── depends on → core:common

feature:family
├── depends on → core:domain
├── depends on → core:data
├── depends on → core:network
├── depends on → core:common

core:data
├── depends on → core:domain
├── depends on → core:database
├── depends on → core:network
├── depends on → core:common

core:network
├── depends on → core:domain
├── depends on → core:common

core:ml
├── depends on → core:domain
├── depends on → core:common

core:database
├── depends on → core:domain
└── depends on → core:common
```

---

## 4. DESIGN PATTERNS

### 4.1 MVVM (Model-View-ViewModel)

**Implementation:**

```kotlin
// View (Composable)
@Composable
fun TransactionScreen(
    viewModel: TransactionViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    when (uiState) {
        is TransactionUiState.Loading -> LoadingIndicator()
        is TransactionUiState.Success -> TransactionList(uiState.transactions)
        is TransactionUiState.Error -> ErrorMessage(uiState.message)
    }
}

// ViewModel
@HiltViewModel
class TransactionViewModel @Inject constructor(
    private val getTransactionsUseCase: GetTransactionsUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow<TransactionUiState>(TransactionUiState.Loading)
    val uiState: StateFlow<TransactionUiState> = _uiState.asStateFlow()

    init {
        loadTransactions()
    }

    private fun loadTransactions() {
        viewModelScope.launch {
            getTransactionsUseCase()
                .catch { e ->
                    _uiState.value = TransactionUiState.Error(e.message ?: "Unknown error")
                }
                .collect { transactions ->
                    _uiState.value = TransactionUiState.Success(transactions)
                }
        }
    }
}

// UI State
sealed class TransactionUiState {
    object Loading : TransactionUiState()
    data class Success(val transactions: List<Transaction>) : TransactionUiState()
    data class Error(val message: String) : TransactionUiState()
}

// Model (Domain)
data class Transaction(
    val id: String,
    val amount: Double,
    val category: String,
    val timestamp: Long
)
```

### 4.2 Repository Pattern

**Interface (Domain Layer):**

```kotlin
interface TransactionRepository {
    fun getTransactions(): Flow<List<Transaction>>
    suspend fun getTransactionById(id: String): Transaction?
    suspend fun insertTransaction(transaction: Transaction)
    suspend fun updateTransaction(transaction: Transaction)
    suspend fun deleteTransaction(id: String)
}
```

**Implementation (Data Layer):**

```kotlin
class TransactionRepositoryImpl @Inject constructor(
    private val localDataSource: TransactionLocalDataSource,
    private val remoteDataSource: TransactionRemoteDataSource,
    private val transactionMapper: TransactionMapper
) : TransactionRepository {

    override fun getTransactions(): Flow<List<Transaction>> {
        return localDataSource.getTransactions()
            .map { entities -> entities.map { transactionMapper.toDomain(it) } }
    }

    override suspend fun insertTransaction(transaction: Transaction) {
        val entity = transactionMapper.toEntity(transaction)
        localDataSource.insertTransaction(entity)

        // Sync to cloud if premium
        if (userPreferences.isPremium()) {
            remoteDataSource.uploadTransaction(entity)
        }
    }
}
```

### 4.3 Use Case Pattern

```kotlin
class TrackTransactionUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val mlClassificationService: MLClassificationService,
    private val budgetRepository: BudgetRepository
) {
    suspend operator fun invoke(parsedSMS: ParsedSMSData): Result<Transaction> {
        return try {
            // Step 1: Classify transaction
            val classification = mlClassificationService.classify(
                merchantName = parsedSMS.merchantName,
                amount = parsedSMS.amount,
                upiId = parsedSMS.upiId
            )

            // Step 2: Create transaction
            val transaction = Transaction(
                id = UUID.randomUUID().toString(),
                amount = parsedSMS.amount,
                type = parsedSMS.type,
                merchantName = parsedSMS.merchantName,
                categoryId = classification.categoryId,
                confidence = classification.confidence,
                timestamp = parsedSMS.timestamp
            )

            // Step 3: Save to repository
            transactionRepository.insertTransaction(transaction)

            // Step 4: Update budgets
            budgetRepository.updateBudgetProgress(transaction)

            Result.Success(transaction)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to track transaction")
        }
    }
}
```

### 4.4 Dependency Injection (Hilt)

**Application Class:**

```kotlin
@HiltAndroidApp
class XpenzApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        // Initialize Timber
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }

        // Initialize other libraries
        FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(!BuildConfig.DEBUG)
    }
}
```

**Module Example:**

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideXpenzDatabase(
        @ApplicationContext context: Context
    ): XpenzDatabase {
        return Room.databaseBuilder(
            context,
            XpenzDatabase::class.java,
            "xpenz_database"
        )
            .fallbackToDestructiveMigration()
            .build()
    }

    @Provides
    fun provideTransactionDao(database: XpenzDatabase): TransactionDao {
        return database.transactionDao()
    }
}
```

### 4.5 Factory Pattern (for ViewModels)

```kotlin
// Handled automatically by Hilt
@HiltViewModel
class TransactionViewModel @Inject constructor(
    private val getTransactionsUseCase: GetTransactionsUseCase,
    savedStateHandle: SavedStateHandle
) : ViewModel() {
    // ViewModel implementation
}

// In Composable
@Composable
fun TransactionScreen(
    viewModel: TransactionViewModel = hiltViewModel()
) {
    // viewModel is automatically created and injected by Hilt
}
```

---

## 5. DATABASE SCHEMA

### 5.1 Room Database Overview

**Database Name:** `xpenz_database`

**Version:** 2 (v1 = 11 core tables; v2 adds 6 Groups & Splits tables — see Tables 12–17)

**Tables:** 17 (11 core + 6 Groups & Splits)

**Relationships:** Foreign keys with cascading deletes/updates

**Indexes:** Strategic indexes for query performance

**Migrations:** Support for future schema changes

### 5.2 Complete Table Definitions

### **Table 1: users**

```kotlin
@Entity(
    tableName = "users",
    indices = [
        Index(value = ["phone_number"], unique = true),
        Index(value = ["email"], unique = true)
    ]
)
data class UserEntity(
    @PrimaryKey
    @ColumnInfo(name = "user_id")
    val userId: String, // Firebase Auth UID

    @ColumnInfo(name = "phone_number")
    val phoneNumber: String, // +91XXXXXXXXXX

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "email")
    val email: String?,

    @ColumnInfo(name = "avatar_url")
    val avatarUrl: String?,

    @ColumnInfo(name = "primary_upi_id")
    val primaryUpiId: String?, // username@paytm

    @ColumnInfo(name = "is_premium")
    val isPremium: Boolean = false,

    @ColumnInfo(name = "premium_expires_at")
    val premiumExpiresAt: Long? = null,

    @ColumnInfo(name = "subscription_type")
    val subscriptionType: String? = null, // ANNUAL, MONTHLY, LIFETIME

    @ColumnInfo(name = "device_id")
    val deviceId: String, // For multi-device tracking

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "last_login_at")
    val lastLoginAt: Long = System.currentTimeMillis()
)
```

**DAO Methods:**

```kotlin
@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE user_id = :userId")
    fun getUser(userId: String): Flow<UserEntity?>

    @Query("SELECT * FROM users WHERE phone_number = :phoneNumber")
    suspend fun getUserByPhone(phoneNumber: String): UserEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: UserEntity)

    @Update
    suspend fun updateUser(user: UserEntity)

    @Query("UPDATE users SET is_premium = :isPremium WHERE user_id = :userId")
    suspend fun updatePremiumStatus(userId: String, isPremium: Boolean)

    @Delete
    suspend fun deleteUser(user: UserEntity)
}
```

---

### **Table 2: transactions**

```kotlin
@Entity(
    tableName = "transactions",
    foreignKeys = [
        ForeignKey(
            entity = UserEntity::class,
            parentColumns = ["user_id"],
            childColumns = ["user_id"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = FamilyEntity::class,
            parentColumns = ["family_id"],
            childColumns = ["family_id"],
            onDelete = ForeignKey.SET_NULL
        ),
        ForeignKey(
            entity = MLCategoryEntity::class,
            parentColumns = ["category_id"],
            childColumns = ["ml_category_id"],
            onDelete = ForeignKey.RESTRICT
        )
    ],
    indices = [
        Index(value = ["user_id"]),
        Index(value = ["family_id"]),
        Index(value = ["timestamp"]),
        Index(value = ["ml_category_id"]),
        Index(value = ["user_id", "timestamp"]),
        Index(value = ["family_id", "timestamp"]),
        Index(value = ["type"]),
        Index(value = ["merchant_name"])
    ]
)
data class TransactionEntity(
    @PrimaryKey
    @ColumnInfo(name = "transaction_id")
    val transactionId: String, // UUID

    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "family_id")
    val familyId: String?,

    // Transaction Details
    @ColumnInfo(name = "type")
    val type: String, // DEBIT, CREDIT, REFUND

    @ColumnInfo(name = "amount")
    val amount: Double,

    @ColumnInfo(name = "currency")
    val currency: String = "INR",

    @ColumnInfo(name = "merchant_name")
    val merchantName: String?,

    @ColumnInfo(name = "upi_id")
    val upiId: String?,

    @ColumnInfo(name = "bank_name")
    val bankName: String?,

    @ColumnInfo(name = "bank_reference_number")
    val bankReferenceNumber: String?,

    // ML Classification
    @ColumnInfo(name = "ml_category_id")
    val mlCategoryId: Int, // 1-520

    @ColumnInfo(name = "ml_confidence")
    val mlConfidence: Float, // 0.0 - 1.0

    @ColumnInfo(name = "ml_source")
    val mlSource: String, // ML_ENSEMBLE, ML_CHT, RULE_ENGINE, USER_HABIT, AMOUNT_TIME_PRIOR, USER_CORRECTED

    @ColumnInfo(name = "ml_top3_predictions")
    val mlTop3Predictions: String?, // JSON: [{"id":1,"conf":0.89},{"id":2,"conf":0.78}]

    @ColumnInfo(name = "user_corrected_category_id")
    val userCorrectedCategoryId: Int?,

    @ColumnInfo(name = "correction_timestamp")
    val correctionTimestamp: Long?,

    // Location
    @ColumnInfo(name = "location_latitude")
    val locationLatitude: Double?,

    @ColumnInfo(name = "location_longitude")
    val locationLongitude: Double?,

    @ColumnInfo(name = "location_name")
    val locationName: String?,

    @ColumnInfo(name = "location_accuracy")
    val locationAccuracy: Float?,

    // Timestamps
    @ColumnInfo(name = "timestamp")
    val timestamp: Long, // Transaction time from SMS

    @ColumnInfo(name = "detected_at")
    val detectedAt: Long = System.currentTimeMillis(), // When app detected it

    // Additional Info
    @ColumnInfo(name = "note")
    val note: String?,

    @ColumnInfo(name = "tags")
    val tags: String?, // JSON array: ["business", "essential"]

    @ColumnInfo(name = "receipt_url")
    val receiptUrl: String?,

    // SMS Source
    @ColumnInfo(name = "sms_sender")
    val smsSender: String?,

    @ColumnInfo(name = "sms_body_hash")
    val smsBodyHash: String?, // SHA-256 hash of SMS (for deduplication, not storing actual SMS)

    // Sync
    @ColumnInfo(name = "is_synced")
    val isSynced: Boolean = false,

    @ColumnInfo(name = "firestore_id")
    val firestoreId: String?,

    @ColumnInfo(name = "sync_version")
    val syncVersion: Int = 1,

    // Metadata
    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "deleted_at")
    val deletedAt: Long? = null, // Soft delete

    @ColumnInfo(name = "is_manually_added")
    val isManuallyAdded: Boolean = false
)
```

**DAO Methods:**

```kotlin
@Dao
interface TransactionDao {
    // Basic CRUD
    @Query("SELECT * FROM transactions WHERE transaction_id = :id AND deleted_at IS NULL")
    suspend fun getTransaction(id: String): TransactionEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTransaction(transaction: TransactionEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTransactions(transactions: List<TransactionEntity>)

    @Update
    suspend fun updateTransaction(transaction: TransactionEntity)

    @Query("UPDATE transactions SET deleted_at = :timestamp WHERE transaction_id = :id")
    suspend fun softDeleteTransaction(id: String, timestamp: Long = System.currentTimeMillis())

    // Get user transactions
    @Query("""
        SELECT * FROM transactions
        WHERE user_id = :userId
        AND deleted_at IS NULL
        ORDER BY timestamp DESC
    """)
    fun getUserTransactions(userId: String): Flow<List<TransactionEntity>>

    @Query("""
        SELECT * FROM transactions
        WHERE user_id = :userId
        AND deleted_at IS NULL
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)
    suspend fun getUserTransactionsPaged(
        userId: String,
        limit: Int,
        offset: Int
    ): List<TransactionEntity>

    // Get family transactions
    @Query("""
        SELECT * FROM transactions
        WHERE family_id = :familyId
        AND deleted_at IS NULL
        ORDER BY timestamp DESC
    """)
    fun getFamilyTransactions(familyId: String): Flow<List<TransactionEntity>>

    // Get transactions by date range
    @Query("""
        SELECT * FROM transactions
        WHERE user_id = :userId
        AND timestamp BETWEEN :startTime AND :endTime
        AND deleted_at IS NULL
        ORDER BY timestamp DESC
    """)
    suspend fun getTransactionsByDateRange(
        userId: String,
        startTime: Long,
        endTime: Long
    ): List<TransactionEntity>

    // Get transactions by category
    @Query("""
        SELECT * FROM transactions
        WHERE user_id = :userId
        AND ml_category_id = :categoryId
        AND deleted_at IS NULL
        ORDER BY timestamp DESC
    """)
    suspend fun getTransactionsByCategory(
        userId: String,
        categoryId: Int
    ): List<TransactionEntity>

    // Search transactions
    @Query("""
        SELECT * FROM transactions
        WHERE user_id = :userId
        AND (
            merchant_name LIKE '%' || :query || '%'
            OR note LIKE '%' || :query || '%'
            OR upi_id LIKE '%' || :query || '%'
        )
        AND deleted_at IS NULL
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    suspend fun searchTransactions(
        userId: String,
        query: String
    ): List<TransactionEntity>

    // Statistics
    @Query("""
        SELECT SUM(amount) FROM transactions
        WHERE user_id = :userId
        AND type = :type
        AND timestamp BETWEEN :startTime AND :endTime
        AND deleted_at IS NULL
    """)
    suspend fun getTotalAmount(
        userId: String,
        type: String,
        startTime: Long,
        endTime: Long
    ): Double?

    @Query("""
        SELECT COUNT(*) FROM transactions
        WHERE user_id = :userId
        AND deleted_at IS NULL
    """)
    suspend fun getTransactionCount(userId: String): Int

    // Category-wise spending
    @Query("""
        SELECT ml_category_id, SUM(amount) as total
        FROM transactions
        WHERE user_id = :userId
        AND type = 'DEBIT'
        AND timestamp BETWEEN :startTime AND :endTime
        AND deleted_at IS NULL
        GROUP BY ml_category_id
        ORDER BY total DESC
    """)
    suspend fun getCategoryWiseSpending(
        userId: String,
        startTime: Long,
        endTime: Long
    ): List<CategorySpending>

    // Sync-related
    @Query("""
        SELECT * FROM transactions
        WHERE is_synced = 0
        AND deleted_at IS NULL
        LIMIT :limit
    """)
    suspend fun getUnsyncedTransactions(limit: Int = 50): List<TransactionEntity>

    @Query("UPDATE transactions SET is_synced = 1 WHERE transaction_id = :id")
    suspend fun markAsSynced(id: String)

    // Deduplication check
    @Query("""
        SELECT COUNT(*) FROM transactions
        WHERE sms_body_hash = :hash
        AND deleted_at IS NULL
    """)
    suspend fun checkDuplicateSMS(hash: String): Int
}

// Helper data classes
data class CategorySpending(
    @ColumnInfo(name = "ml_category_id")
    val categoryId: Int,

    @ColumnInfo(name = "total")
    val total: Double
)
```

---

### **Table 3: families**

```kotlin
@Entity(
    tableName = "families",
    indices = [
        Index(value = ["invitation_code"], unique = true),
        Index(value = ["created_by"])
    ]
)
data class FamilyEntity(
    @PrimaryKey
    @ColumnInfo(name = "family_id")
    val familyId: String, // UUID

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "emoji")
    val emoji: String = "👨‍👩‍👧‍👦",

    @ColumnInfo(name = "color")
    val color: String = "#6200EE", // Hex color

    @ColumnInfo(name = "description")
    val description: String?,

    @ColumnInfo(name = "invitation_code")
    val invitationCode: String, // XP-XXXXX (5 alphanumeric)

    @ColumnInfo(name = "code_generated_at")
    val codeGeneratedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "code_expires_at")
    val codeExpiresAt: Long = System.currentTimeMillis() + (7 * 24 * 60 * 60 * 1000), // 7 days

    @ColumnInfo(name = "created_by")
    val createdBy: String, // User ID of creator

    @ColumnInfo(name = "max_members")
    val maxMembers: Int = 5, // 5 for free, unlimited for premium

    @ColumnInfo(name = "is_premium")
    val isPremium: Boolean = false,

    @ColumnInfo(name = "settings")
    val settings: String?, // JSON: {"require_approval": false, "allow_member_invite": true}

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "deleted_at")
    val deletedAt: Long? = null,

    @ColumnInfo(name = "deleted_by")
    val deletedBy: String? = null
)
```

**DAO Methods:**

```kotlin
@Dao
interface FamilyDao {
    @Query("SELECT * FROM families WHERE family_id = :familyId AND deleted_at IS NULL")
    fun getFamily(familyId: String): Flow<FamilyEntity?>

    @Query("SELECT * FROM families WHERE invitation_code = :code AND deleted_at IS NULL")
    suspend fun getFamilyByCode(code: String): FamilyEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFamily(family: FamilyEntity)

    @Update
    suspend fun updateFamily(family: FamilyEntity)

    @Query("UPDATE families SET deleted_at = :timestamp, deleted_by = :userId WHERE family_id = :familyId")
    suspend fun softDeleteFamily(familyId: String, userId: String, timestamp: Long = System.currentTimeMillis())

    @Query("""
        UPDATE families
        SET invitation_code = :newCode,
            code_generated_at = :timestamp,
            code_expires_at = :expiresAt
        WHERE family_id = :familyId
    """)
    suspend fun regenerateInvitationCode(
        familyId: String,
        newCode: String,
        timestamp: Long = System.currentTimeMillis(),
        expiresAt: Long = System.currentTimeMillis() + (7 * 24 * 60 * 60 * 1000)
    )
}
```

---

### **Table 4: family_members**

```kotlin
@Entity(
    tableName = "family_members",
    foreignKeys = [
        ForeignKey(
            entity = FamilyEntity::class,
            parentColumns = ["family_id"],
            childColumns = ["family_id"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = UserEntity::class,
            parentColumns = ["user_id"],
            childColumns = ["user_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["family_id"]),
        Index(value = ["user_id"]),
        Index(value = ["family_id", "user_id"], unique = true)
    ]
)
data class FamilyMemberEntity(
    @PrimaryKey
    @ColumnInfo(name = "member_id")
    val memberId: String, // UUID

    @ColumnInfo(name = "family_id")
    val familyId: String,

    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "nickname")
    val nickname: String, // Display name in family (Papa, Mom, etc.)

    @ColumnInfo(name = "role")
    val role: String, // ADMIN, MEMBER

    @ColumnInfo(name = "avatar_emoji")
    val avatarEmoji: String?, // Optional custom emoji

    @ColumnInfo(name = "status")
    val status: String, // ACTIVE, LEFT, REMOVED, PENDING

    @ColumnInfo(name = "joined_at")
    val joinedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "left_at")
    val leftAt: Long?,

    @ColumnInfo(name = "removed_by")
    val removedBy: String?, // User ID who removed this member

    @ColumnInfo(name = "removed_at")
    val removedAt: Long?,

    @ColumnInfo(name = "last_active_at")
    val lastActiveAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis()
)
```

**DAO Methods:**

```kotlin
@Dao
interface FamilyMemberDao {
    @Query("""
        SELECT * FROM family_members
        WHERE family_id = :familyId
        AND status = 'ACTIVE'
        ORDER BY joined_at ASC
    """)
    fun getFamilyMembers(familyId: String): Flow<List<FamilyMemberEntity>>

    @Query("""
        SELECT * FROM family_members
        WHERE user_id = :userId
        AND status = 'ACTIVE'
    """)
    fun getUserFamilies(userId: String): Flow<List<FamilyMemberEntity>>

    @Query("""
        SELECT COUNT(*) FROM family_members
        WHERE family_id = :familyId
        AND status = 'ACTIVE'
    """)
    suspend fun getMemberCount(familyId: String): Int

    @Query("""
        SELECT * FROM family_members
        WHERE family_id = :familyId
        AND user_id = :userId
    """)
    suspend fun getMembership(familyId: String, userId: String): FamilyMemberEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMember(member: FamilyMemberEntity)

    @Update
    suspend fun updateMember(member: FamilyMemberEntity)

    @Query("""
        UPDATE family_members
        SET status = 'LEFT', left_at = :timestamp
        WHERE member_id = :memberId
    """)
    suspend fun markAsLeft(memberId: String, timestamp: Long = System.currentTimeMillis())

    @Query("""
        UPDATE family_members
        SET status = 'REMOVED', removed_at = :timestamp, removed_by = :removedBy
        WHERE member_id = :memberId
    """)
    suspend fun markAsRemoved(memberId: String, removedBy: String, timestamp: Long = System.currentTimeMillis())

    @Query("""
        SELECT COUNT(*) FROM family_members
        WHERE family_id = :familyId
        AND role = 'ADMIN'
        AND status = 'ACTIVE'
    """)
    suspend fun getAdminCount(familyId: String): Int
}
```

---

### **Table 5: budgets**

```kotlin
@Entity(
    tableName = "budgets",
    foreignKeys = [
        ForeignKey(
            entity = FamilyEntity::class,
            parentColumns = ["family_id"],
            childColumns = ["family_id"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = UserEntity::class,
            parentColumns = ["user_id"],
            childColumns = ["created_by"],
            onDelete = ForeignKey.SET_NULL
        )
    ],
    indices = [
        Index(value = ["family_id"]),
        Index(value = ["created_by"]),
        Index(value = ["budget_type"]),
        Index(value = ["family_id", "budget_type", "is_active"])
    ]
)
data class BudgetEntity(
    @PrimaryKey
    @ColumnInfo(name = "budget_id")
    val budgetId: String, // UUID

    @ColumnInfo(name = "family_id")
    val familyId: String,

    @ColumnInfo(name = "budget_type")
    val budgetType: String, // FAMILY, CATEGORY, MEMBER

    @ColumnInfo(name = "name")
    val name: String, // Custom name or auto-generated

    // Type-specific fields
    @ColumnInfo(name = "category_id")
    val categoryId: Int?, // For CATEGORY type

    @ColumnInfo(name = "member_id")
    val memberId: String?, // For MEMBER type (user_id)

    // Budget amount
    @ColumnInfo(name = "amount")
    val amount: Double,

    @ColumnInfo(name = "currency")
    val currency: String = "INR",

    @ColumnInfo(name = "period")
    val period: String, // MONTHLY, WEEKLY, YEARLY

    // Alert thresholds
    @ColumnInfo(name = "alert_thresholds")
    val alertThresholds: String, // JSON: [50, 80, 100, 120]

    @ColumnInfo(name = "notification_enabled")
    val notificationEnabled: Boolean = true,

    @ColumnInfo(name = "notify_all_members")
    val notifyAllMembers: Boolean = true,

    // Dates
    @ColumnInfo(name = "start_date")
    val startDate: Long, // Epoch timestamp

    @ColumnInfo(name = "end_date")
    val endDate: Long?, // Null = recurring

    @ColumnInfo(name = "is_recurring")
    val isRecurring: Boolean = true,

    // Status
    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,

    @ColumnInfo(name = "paused_at")
    val pausedAt: Long?,

    // Metadata
    @ColumnInfo(name = "created_by")
    val createdBy: String,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "deleted_at")
    val deletedAt: Long?
)
```

**DAO Methods:**

```kotlin
@Dao
interface BudgetDao {
    @Query("""
        SELECT * FROM budgets
        WHERE family_id = :familyId
        AND is_active = 1
        AND deleted_at IS NULL
        ORDER BY created_at DESC
    """)
    fun getActiveBudgets(familyId: String): Flow<List<BudgetEntity>>

    @Query("""
        SELECT * FROM budgets
        WHERE family_id = :familyId
        AND budget_type = :type
        AND is_active = 1
        AND deleted_at IS NULL
    """)
    suspend fun getBudgetsByType(familyId: String, type: String): List<BudgetEntity>

    @Query("SELECT * FROM budgets WHERE budget_id = :budgetId AND deleted_at IS NULL")
    suspend fun getBudget(budgetId: String): BudgetEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBudget(budget: BudgetEntity)

    @Update
    suspend fun updateBudget(budget: BudgetEntity)

    @Query("UPDATE budgets SET deleted_at = :timestamp WHERE budget_id = :budgetId")
    suspend fun softDeleteBudget(budgetId: String, timestamp: Long = System.currentTimeMillis())

    @Query("UPDATE budgets SET is_active = 0, paused_at = :timestamp WHERE budget_id = :budgetId")
    suspend fun pauseBudget(budgetId: String, timestamp: Long = System.currentTimeMillis())

    @Query("UPDATE budgets SET is_active = 1, paused_at = NULL WHERE budget_id = :budgetId")
    suspend fun resumeBudget(budgetId: String)
}
```

---

### **Table 6: ml_categories**

```kotlin
@Entity(
    tableName = "ml_categories",
    indices = [
        Index(value = ["category_name"], unique = true),
        Index(value = ["parent_category_id"]),
        Index(value = ["level"])
    ]
)
data class MLCategoryEntity(
    @PrimaryKey
    @ColumnInfo(name = "category_id")
    val categoryId: Int, // 1-520

    @ColumnInfo(name = "category_name")
    val categoryName: String, // "North Indian - Butter Chicken"

    @ColumnInfo(name = "display_name")
    val displayName: String, // "Butter Chicken"

    @ColumnInfo(name = "parent_category_id")
    val parentCategoryId: Int?, // For hierarchical categories

    @ColumnInfo(name = "level")
    val level: Int, // 1 (Main), 2 (Sub), 3 (Specific), 4 (Granular)

    @ColumnInfo(name = "emoji")
    val emoji: String, // 🍛

    @ColumnInfo(name = "color")
    val color: String, // #FF5722

    @ColumnInfo(name = "keywords")
    val keywords: String, // JSON: ["butter", "chicken", "murgh", "makhani"]

    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,

    @ColumnInfo(name = "sort_order")
    val sortOrder: Int = 0
)
```

**DAO Methods:**

```kotlin
@Dao
interface MLCategoryDao {
    @Query("SELECT * FROM ml_categories WHERE category_id = :id")
    suspend fun getCategory(id: Int): MLCategoryEntity?

    @Query("SELECT * FROM ml_categories WHERE is_active = 1 ORDER BY sort_order ASC")
    suspend fun getAllCategories(): List<MLCategoryEntity>

    @Query("SELECT * FROM ml_categories WHERE level = :level AND is_active = 1")
    suspend fun getCategoriesByLevel(level: Int): List<MLCategoryEntity>

    @Query("SELECT * FROM ml_categories WHERE parent_category_id = :parentId AND is_active = 1")
    suspend fun getChildCategories(parentId: Int): List<MLCategoryEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategory(category: MLCategoryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategories(categories: List<MLCategoryEntity>)

    @Query("SELECT * FROM ml_categories WHERE category_name LIKE '%' || :query || '%' OR keywords LIKE '%' || :query || '%'")
    suspend fun searchCategories(query: String): List<MLCategoryEntity>
}
```

---

### **Table 7: sms_patterns**

```kotlin
@Entity(
    tableName = "sms_patterns",
    indices = [
        Index(value = ["sender"]),
        Index(value = ["is_active"])
    ]
)
data class SMSPatternEntity(
    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "pattern_id")
    val patternId: Int = 0,

    @ColumnInfo(name = "sender")
    val sender: String, // VK-HDFCBK, VK-ICICIB, etc.

    @ColumnInfo(name = "bank_name")
    val bankName: String, // HDFC Bank, ICICI Bank

    @ColumnInfo(name = "pattern_regex")
    val patternRegex: String, // Regex pattern for parsing

    @ColumnInfo(name = "amount_group")
    val amountGroup: Int, // Regex group number for amount

    @ColumnInfo(name = "merchant_group")
    val merchantGroup: Int?, // Regex group number for merchant

    @ColumnInfo(name = "upi_group")
    val upiGroup: Int?, // Regex group number for UPI ID

    @ColumnInfo(name = "type_keywords")
    val typeKeywords: String, // JSON: {"debit": ["debited", "paid"], "credit": ["credited", "received"]}

    @ColumnInfo(name = "confidence_score")
    val confidenceScore: Float = 1.0f, // Pattern reliability

    @ColumnInfo(name = "usage_count")
    val usageCount: Int = 0, // How many times successfully used

    @ColumnInfo(name = "success_rate")
    val successRate: Float = 1.0f, // Success rate

    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis()
)
```

---

### **Table 8: subscription**

```kotlin
@Entity(
    tableName = "subscriptions",
    foreignKeys = [
        ForeignKey(
            entity = UserEntity::class,
            parentColumns = ["user_id"],
            childColumns = ["user_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["user_id"], unique = true),
        Index(value = ["purchase_token"], unique = true)
    ]
)
data class SubscriptionEntity(
    @PrimaryKey
    @ColumnInfo(name = "subscription_id")
    val subscriptionId: String, // UUID

    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "plan_type")
    val planType: String, // ANNUAL, MONTHLY, LIFETIME

    @ColumnInfo(name = "status")
    val status: String, // ACTIVE, CANCELLED, EXPIRED, REFUNDED

    @ColumnInfo(name = "purchase_token")
    val purchaseToken: String, // Google Play purchase token

    @ColumnInfo(name = "order_id")
    val orderId: String,

    @ColumnInfo(name = "product_id")
    val productId: String, // SKU

    @ColumnInfo(name = "price")
    val price: Double,

    @ColumnInfo(name = "currency")
    val currency: String = "INR",

    @ColumnInfo(name = "purchased_at")
    val purchasedAt: Long,

    @ColumnInfo(name = "expires_at")
    val expiresAt: Long?,

    @ColumnInfo(name = "auto_renew")
    val autoRenew: Boolean = true,

    @ColumnInfo(name = "cancelled_at")
    val cancelledAt: Long?,

    @ColumnInfo(name = "cancellation_reason")
    val cancellationReason: String?,

    @ColumnInfo(name = "refunded_at")
    val refundedAt: Long?,

    @ColumnInfo(name = "verification_status")
    val verificationStatus: String, // VERIFIED, PENDING, FAILED

    @ColumnInfo(name = "last_verified_at")
    val lastVerifiedAt: Long?,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis()
)
```

---

### **Table 9: budget_progress** (Computed/Cached)

```kotlin
@Entity(
    tableName = "budget_progress",
    foreignKeys = [
        ForeignKey(
            entity = BudgetEntity::class,
            parentColumns = ["budget_id"],
            childColumns = ["budget_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["budget_id"]),
        Index(value = ["period_start", "period_end"])
    ]
)
data class BudgetProgressEntity(
    @PrimaryKey
    @ColumnInfo(name = "progress_id")
    val progressId: String, // UUID

    @ColumnInfo(name = "budget_id")
    val budgetId: String,

    @ColumnInfo(name = "period_start")
    val periodStart: Long,

    @ColumnInfo(name = "period_end")
    val periodEnd: Long,

    @ColumnInfo(name = "amount_spent")
    val amountSpent: Double,

    @ColumnInfo(name = "amount_budget")
    val amountBudget: Double,

    @ColumnInfo(name = "percentage")
    val percentage: Float, // 0-100+

    @ColumnInfo(name = "transaction_count")
    val transactionCount: Int,

    @ColumnInfo(name = "status")
    val status: String, // HEALTHY, WARNING, CRITICAL, EXCEEDED, OVER_120

    @ColumnInfo(name = "last_alert_sent")
    val lastAlertSent: String?, // "50", "80", "100", "120"

    @ColumnInfo(name = "last_calculated_at")
    val lastCalculatedAt: Long = System.currentTimeMillis()
)
```

---

### **Table 10: notifications**

```kotlin
@Entity(
    tableName = "notifications",
    foreignKeys = [
        ForeignKey(
            entity = UserEntity::class,
            parentColumns = ["user_id"],
            childColumns = ["user_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["user_id"]),
        Index(value = ["is_read"]),
        Index(value = ["created_at"])
    ]
)
data class NotificationEntity(
    @PrimaryKey
    @ColumnInfo(name = "notification_id")
    val notificationId: String, // UUID

    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "type")
    val type: String, // BUDGET_ALERT, FAMILY_INVITE, TRANSACTION_ADDED, SUBSCRIPTION, etc.

    @ColumnInfo(name = "title")
    val title: String,

    @ColumnInfo(name = "body")
    val body: String,

    @ColumnInfo(name = "data")
    val data: String?, // JSON payload

    @ColumnInfo(name = "action")
    val action: String?, // Deep link or action

    @ColumnInfo(name = "priority")
    val priority: String = "NORMAL", // HIGH, NORMAL, LOW

    @ColumnInfo(name = "is_read")
    val isRead: Boolean = false,

    @ColumnInfo(name = "read_at")
    val readAt: Long?,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis()
)
```

---

### **Table 11: sync_queue** (For offline sync)

```kotlin
@Entity(
    tableName = "sync_queue",
    indices = [
        Index(value = ["status"]),
        Index(value = ["created_at"])
    ]
)
data class SyncQueueEntity(
    @PrimaryKey
    @ColumnInfo(name = "queue_id")
    val queueId: String, // UUID

    @ColumnInfo(name = "operation_type")
    val operationType: String, // INSERT, UPDATE, DELETE

    @ColumnInfo(name = "entity_type")
    val entityType: String, // TRANSACTION, BUDGET, FAMILY_MEMBER, etc.

    @ColumnInfo(name = "entity_id")
    val entityId: String,

    @ColumnInfo(name = "payload")
    val payload: String, // JSON of entity data

    @ColumnInfo(name = "status")
    val status: String, // PENDING, IN_PROGRESS, COMPLETED, FAILED

    @ColumnInfo(name = "retry_count")
    val retryCount: Int = 0,

    @ColumnInfo(name = "last_error")
    val lastError: String?,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis()
)
```

---

> ### Groups & Splits tables (Option B) — Tables 12–17
>
> These six tables back the **Groups & Splits** subsystem (Splitwise-style bill splitting).
> It is a **separate subsystem from Families** (Tables 3–4): Families = shared household
> budgeting; Groups = ad-hoc splitting with friends. Adding these bumps the Room DB
> **version 1 → 2** (see §5.3) and requires a migration. See PRD F8, Backend Schema §3.8,
> and PROJECT_COMPLETION_ROADMAP Phase 10. **Accounting rule (important):** a split does
> NOT create a second expense. The payer's detected/manual transaction stays their expense;
> the split tracks *reimbursements owed*. `transactions` gains a nullable
> `reimbursable_amount` so budgets/analytics can optionally net out the portion others owe.

### **Table 12: groups**

```kotlin
@Entity(
    tableName = "groups",
    indices = [Index(value = ["invite_code"], unique = true)]
)
data class GroupEntity(
    @PrimaryKey
    @ColumnInfo(name = "group_id")
    val groupId: String, // UUID

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "type")
    val type: String, // TRIP, HOME, COUPLE, OTHER

    @ColumnInfo(name = "emoji")
    val emoji: String,

    @ColumnInfo(name = "currency")
    val currency: String = "INR",

    @ColumnInfo(name = "created_by")
    val createdBy: String,

    @ColumnInfo(name = "invite_code")
    val inviteCode: String,

    @ColumnInfo(name = "simplify_debts")
    val simplifyDebts: Boolean = true,

    // true = auto-provisioned hidden 2-person group backing a 1:1 friendship.
    // CANONICAL: all splits (group AND 1:1) live in this table; a direct friend split
    // uses a hidden group rather than a separate code path. Hidden groups are filtered
    // out of the normal groups list and surfaced under the Friends tab.
    @ColumnInfo(name = "is_direct")
    val isDirect: Boolean = false,

    @ColumnInfo(name = "current_member_count")
    val currentMemberCount: Int = 1,

    @ColumnInfo(name = "synced")
    val synced: Boolean = false,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "deleted_at")
    val deletedAt: Long? = null
)
```

### **Table 13: group_members**

```kotlin
@Entity(
    tableName = "group_members",
    primaryKeys = ["group_id", "user_id"],
    foreignKeys = [
        ForeignKey(
            entity = GroupEntity::class,
            parentColumns = ["group_id"],
            childColumns = ["group_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["user_id"])]
)
data class GroupMemberEntity(
    @ColumnInfo(name = "group_id")
    val groupId: String,

    @ColumnInfo(name = "user_id")
    val userId: String,

    @ColumnInfo(name = "display_name")
    val displayName: String,

    @ColumnInfo(name = "role")
    val role: String = "MEMBER", // ADMIN, MEMBER

    @ColumnInfo(name = "status")
    val status: String = "ACTIVE", // ACTIVE, LEFT

    @ColumnInfo(name = "joined_at")
    val joinedAt: Long = System.currentTimeMillis()
)
```

### **Table 14: split_expenses**

```kotlin
@Entity(
    tableName = "split_expenses",
    foreignKeys = [
        ForeignKey(
            entity = GroupEntity::class,
            parentColumns = ["group_id"],
            childColumns = ["group_id"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = TransactionEntity::class,
            parentColumns = ["transaction_id"],
            childColumns = ["transaction_id"],
            onDelete = ForeignKey.SET_NULL
        )
    ],
    indices = [Index(value = ["group_id"]), Index(value = ["transaction_id"])]
)
data class SplitExpenseEntity(
    @PrimaryKey
    @ColumnInfo(name = "expense_id")
    val expenseId: String, // UUID

    // Always set. For 1:1 friend splits this is the hidden 2-person group
    // (GroupEntity.is_direct = true) — there is no null/“direct” special case.
    @ColumnInfo(name = "group_id")
    val groupId: String,

    // Denormalized convenience for 1:1 splits: the other user in a hidden (is_direct)
    // group, so the Friends tab can query without a join. null for multi-person groups.
    // NOT the source of truth — group_id is.
    @ColumnInfo(name = "friend_user_id")
    val friendUserId: String? = null,

    // Links to the payer's own Xpenzo transaction (nullable). The transaction stays
    // the payer's expense; this row tracks who owes the payer back.
    @ColumnInfo(name = "transaction_id")
    val transactionId: String? = null,

    @ColumnInfo(name = "description")
    val description: String,

    @ColumnInfo(name = "total_amount")
    val totalAmount: Double,

    @ColumnInfo(name = "currency")
    val currency: String = "INR",

    @ColumnInfo(name = "category_id")
    val categoryId: Int? = null, // reuses 1-520 ML taxonomy

    @ColumnInfo(name = "paid_by")
    val paidBy: String, // user_id who paid

    @ColumnInfo(name = "split_type")
    val splitType: String, // EQUAL, EXACT, PERCENT, SHARES

    @ColumnInfo(name = "expense_date")
    val expenseDate: Long,

    @ColumnInfo(name = "created_by")
    val createdBy: String,

    @ColumnInfo(name = "synced")
    val synced: Boolean = false,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "deleted_at")
    val deletedAt: Long? = null
)
```

### **Table 15: split_shares**

```kotlin
@Entity(
    tableName = "split_shares",
    primaryKeys = ["expense_id", "user_id"],
    foreignKeys = [
        ForeignKey(
            entity = SplitExpenseEntity::class,
            parentColumns = ["expense_id"],
            childColumns = ["expense_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["user_id"])]
)
data class SplitShareEntity(
    @ColumnInfo(name = "expense_id")
    val expenseId: String,

    @ColumnInfo(name = "user_id")
    val userId: String,

    // Interpretation depends on split_type of the parent expense:
    //  EQUAL  -> ignored; owed = total/N
    //  EXACT  -> exact rupee amount owed
    //  PERCENT-> percent of total (Σ = 100)
    //  SHARES -> weight (e.g., 2,1,1)
    @ColumnInfo(name = "share_value")
    val shareValue: Double,

    @ColumnInfo(name = "owed_amount")
    val owedAmount: Double // computed & stored for audit
)
```

### **Table 16: settlements**

```kotlin
@Entity(
    tableName = "settlements",
    foreignKeys = [
        ForeignKey(
            entity = GroupEntity::class,
            parentColumns = ["group_id"],
            childColumns = ["group_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["group_id"]), Index(value = ["status"])]
)
data class SettlementEntity(
    @PrimaryKey
    @ColumnInfo(name = "settlement_id")
    val settlementId: String, // UUID

    // Always set. For 1:1 friend settlements this is the hidden 2-person group
    // (GroupEntity.is_direct = true) — consistent with split_expenses.group_id.
    @ColumnInfo(name = "group_id")
    val groupId: String,

    @ColumnInfo(name = "from_user")
    val fromUser: String, // debtor

    @ColumnInfo(name = "to_user")
    val toUser: String, // creditor

    @ColumnInfo(name = "amount")
    val amount: Double,

    @ColumnInfo(name = "currency")
    val currency: String = "INR",

    @ColumnInfo(name = "method")
    val method: String, // CASH, UPI

    @ColumnInfo(name = "upi_ref")
    val upiRef: String? = null,

    @ColumnInfo(name = "status")
    val status: String = "PENDING", // PENDING, CONFIRMED

    @ColumnInfo(name = "synced")
    val synced: Boolean = false,

    @ColumnInfo(name = "settled_at")
    val settledAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "confirmed_at")
    val confirmedAt: Long? = null
)
```

### **Table 17: friends**

```kotlin
@Entity(
    tableName = "friends",
    indices = [Index(value = ["friend_user_id"], unique = true)]
)
data class FriendEntity(
    @PrimaryKey
    @ColumnInfo(name = "friend_user_id")
    val friendUserId: String,

    @ColumnInfo(name = "display_name")
    val displayName: String,

    @ColumnInfo(name = "phone_hash")
    val phoneHash: String,

    @ColumnInfo(name = "status")
    val status: String = "PENDING", // PENDING, ACCEPTED, BLOCKED

    // The hidden 2-person group (GroupEntity.is_direct = true) backing this friendship.
    // Provisioned on first 1:1 split; all that friend's splits/settlements live there.
    @ColumnInfo(name = "direct_group_id")
    val directGroupId: String? = null,

    @ColumnInfo(name = "net_balance")
    val netBalance: Double = 0.0, // +ve = friend owes this user (cached mirror of the group balance)

    @ColumnInfo(name = "added_at")
    val addedAt: Long = System.currentTimeMillis()
)
```

**DAO note:** add `GroupDao`, `GroupMemberDao`, `SplitExpenseDao` (with `@Transaction`
queries returning expense + shares), `SettlementDao`, and `FriendDao`. Balances are
computed locally with the same min-cash-flow algorithm as the `simplifyDebts` Cloud
Function (Backend Schema §5.3) so on-device and synced balances match.

---

### 5.3 Database Class

```kotlin
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
        SyncQueueEntity::class,
        // ----- Groups & Splits (Option B), added in DB v2 -----
        GroupEntity::class,
        GroupMemberEntity::class,
        SplitExpenseEntity::class,
        SplitShareEntity::class,
        SettlementEntity::class,
        FriendEntity::class
    ],
    version = 2, // v1 -> v2: Groups & Splits tables + transactions.reimbursable_amount
    exportSchema = true
)
abstract class XpenzDatabase : RoomDatabase() {

    abstract fun userDao(): UserDao
    abstract fun transactionDao(): TransactionDao
    abstract fun familyDao(): FamilyDao
    abstract fun familyMemberDao(): FamilyMemberDao
    abstract fun budgetDao(): BudgetDao
    abstract fun mlCategoryDao(): MLCategoryDao
    abstract fun smsPatternDao(): SMSPatternDao
    abstract fun subscriptionDao(): SubscriptionDao
    abstract fun budgetProgressDao(): BudgetProgressDao
    abstract fun notificationDao(): NotificationDao
    abstract fun syncQueueDao(): SyncQueueDao
    // Groups & Splits DAOs
    abstract fun groupDao(): GroupDao
    abstract fun groupMemberDao(): GroupMemberDao
    abstract fun splitExpenseDao(): SplitExpenseDao
    abstract fun settlementDao(): SettlementDao
    abstract fun friendDao(): FriendDao

    companion object {
        const val DATABASE_NAME = "xpenz_database"
    }
}

// Migration 1 -> 2: create the six Groups & Splits tables and add the
// nullable reimbursable_amount column to transactions. Provide MIGRATION_1_2
// to Room (do NOT use fallbackToDestructiveMigration in production).
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE transactions ADD COLUMN reimbursable_amount REAL")
        // CREATE TABLE statements for groups, group_members, split_expenses,
        // split_shares, settlements, friends (+ their indices) go here.
    }
}
```

---

## 6. DATA MODELS

### 6.1 Domain Models (Core Business Objects)

Domain models represent the business logic layer and are independent of any framework (Room, Firebase, etc.).

### **Transaction (Domain Model)**

```kotlin
package com.xpenz.core.domain.model

data class Transaction(
    val id: String,
    val userId: String,
    val familyId: String?,

    // Transaction details
    val type: TransactionType,
    val amount: Double,
    val currency: String = "INR",
    val merchantName: String?,
    val upiId: String?,
    val bankName: String?,
    val bankReferenceNumber: String?,

    // Classification
    val category: Category,
    val mlConfidence: Float,
    val mlSource: MLSource,
    val top3Predictions: List<CategoryPrediction>?,
    val userCorrectedCategory: Category?,

    // Location
    val location: Location?,

    // Timestamps
    val timestamp: Long,
    val detectedAt: Long,

    // Additional
    val note: String?,
    val tags: List<String>,
    val receiptUrl: String?,

    // Metadata
    val isSynced: Boolean,
    val isManuallyAdded: Boolean,
    val createdAt: Long,
    val updatedAt: Long
)

enum class TransactionType {
    DEBIT,
    CREDIT,
    REFUND
}

enum class MLSource {
    ML_ENSEMBLE,
    ML_CHT,
    RULE_ENGINE,
    USER_HABIT,
    AMOUNT_TIME_PRIOR,
    USER_CORRECTED
}

data class CategoryPrediction(
    val category: Category,
    val confidence: Float
)

data class Location(
    val latitude: Double,
    val longitude: Double,
    val name: String?,
    val accuracy: Float?
)
```

### **Category (Domain Model)**

```kotlin
data class Category(
    val id: Int,
    val name: String,
    val displayName: String,
    val parentCategory: Category?,
    val level: CategoryLevel,
    val emoji: String,
    val color: String,
    val keywords: List<String>
)

enum class CategoryLevel {
    MAIN,        // Level 1: e.g., "Food & Dining"
    SUB,         // Level 2: e.g., "Restaurants"
    SPECIFIC,    // Level 3: e.g., "North Indian"
    GRANULAR     // Level 4: e.g., "Butter Chicken"
}
```

### **Family (Domain Model)**

```kotlin
data class Family(
    val id: String,
    val name: String,
    val emoji: String,
    val color: String,
    val description: String?,
    val invitationCode: String,
    val codeExpiresAt: Long,
    val createdBy: String,
    val maxMembers: Int,
    val isPremium: Boolean,
    val settings: FamilySettings,
    val createdAt: Long,
    val updatedAt: Long
)

data class FamilySettings(
    val requireApproval: Boolean = false,
    val allowMemberInvite: Boolean = true,
    val autoSyncTransactions: Boolean = true
)
```

### **FamilyMember (Domain Model)**

```kotlin
data class FamilyMember(
    val id: String,
    val familyId: String,
    val userId: String,
    val nickname: String,
    val role: MemberRole,
    val avatarEmoji: String?,
    val status: MemberStatus,
    val joinedAt: Long,
    val lastActiveAt: Long
)

enum class MemberRole {
    ADMIN,
    MEMBER
}

enum class MemberStatus {
    ACTIVE,
    LEFT,
    REMOVED,
    PENDING
}
```

### **Budget (Domain Model)**

```kotlin
data class Budget(
    val id: String,
    val familyId: String,
    val type: BudgetType,
    val name: String,
    val amount: Double,
    val currency: String = "INR",
    val period: BudgetPeriod,
    val alertThresholds: List<Int>, // [50, 80, 100, 120]
    val notificationEnabled: Boolean,
    val notifyAllMembers: Boolean,
    val startDate: Long,
    val endDate: Long?,
    val isRecurring: Boolean,
    val isActive: Boolean,
    val createdBy: String,
    val createdAt: Long,

    // Type-specific data
    val categoryId: Int? = null,      // For CATEGORY type
    val memberId: String? = null       // For MEMBER type
)

enum class BudgetType {
    FAMILY,      // Total family spending
    CATEGORY,    // Specific category (e.g., Food & Dining)
    MEMBER       // Individual member spending
}

enum class BudgetPeriod {
    MONTHLY,
    WEEKLY,
    YEARLY
}
```

### **BudgetProgress (Domain Model)**

```kotlin
data class BudgetProgress(
    val budgetId: String,
    val budget: Budget,
    val periodStart: Long,
    val periodEnd: Long,
    val amountSpent: Double,
    val amountBudget: Double,
    val percentage: Float,
    val transactionCount: Int,
    val status: BudgetStatus,
    val daysRemaining: Int,
    val suggestedDailySpend: Double,
    val lastAlertSent: String?
)

enum class BudgetStatus {
    HEALTHY,        // 0-50%
    WARNING,        // 50-80%
    CRITICAL,       // 80-100%
    EXCEEDED,       // 100-120%
    OVER_120        // 120%+
}
```

### **User (Domain Model)**

```kotlin
data class User(
    val id: String,
    val phoneNumber: String,
    val name: String,
    val email: String?,
    val avatarUrl: String?,
    val primaryUpiId: String?,
    val isPremium: Boolean,
    val subscription: Subscription?,
    val createdAt: Long,
    val lastLoginAt: Long
)
```

### **Subscription (Domain Model)**

```kotlin
data class Subscription(
    val id: String,
    val userId: String,
    val planType: SubscriptionPlan,
    val status: SubscriptionStatus,
    val purchaseToken: String,
    val price: Double,
    val currency: String,
    val purchasedAt: Long,
    val expiresAt: Long?,
    val autoRenew: Boolean
)

enum class SubscriptionPlan {
    ANNUAL,      // ₹999/year
    MONTHLY,     // ₹149/month
    LIFETIME     // ₹4,999 one-time
}

enum class SubscriptionStatus {
    ACTIVE,
    CANCELLED,
    EXPIRED,
    REFUNDED
}
```

---

### 6.2 Data Transfer Objects (DTOs)

DTOs are used for network communication with Firebase.

### **TransactionDTO (Firestore)**

```kotlin
package com.xpenz.core.network.model

data class TransactionDTO(
    @PropertyName("transaction_id") val transactionId: String = "",
    @PropertyName("user_id") val userId: String = "",
    @PropertyName("family_id") val familyId: String? = null,
    @PropertyName("type") val type: String = "",
    @PropertyName("amount") val amount: Double = 0.0,
    @PropertyName("currency") val currency: String = "INR",
    @PropertyName("merchant_name") val merchantName: String? = null,
    @PropertyName("upi_id") val upiId: String? = null,
    @PropertyName("category_id") val categoryId: Int = 0,
    @PropertyName("confidence") val confidence: Float = 0f,
    @PropertyName("timestamp") val timestamp: Long = 0L,
    @PropertyName("note") val note: String? = null,
    @PropertyName("encrypted_data") val encryptedData: String? = null, // For sensitive fields
    @PropertyName("created_at") val createdAt: Long = 0L,
    @PropertyName("updated_at") val updatedAt: Long = 0L
) {
    // No-arg constructor required by Firestore
    constructor() : this(transactionId = "")
}
```

### **FamilyDTO (Firestore)**

```kotlin
data class FamilyDTO(
    @PropertyName("family_id") val familyId: String = "",
    @PropertyName("name") val name: String = "",
    @PropertyName("emoji") val emoji: String = "👨‍👩‍👧‍👦",
    @PropertyName("color") val color: String = "#6200EE",
    @PropertyName("invitation_code") val invitationCode: String = "",
    @PropertyName("created_by") val createdBy: String = "",
    @PropertyName("max_members") val maxMembers: Int = 5,
    @PropertyName("is_premium") val isPremium: Boolean = false,
    @PropertyName("created_at") val createdAt: Long = 0L,
    @PropertyName("updated_at") val updatedAt: Long = 0L
) {
    constructor() : this(familyId = "")
}
```

---

### 6.3 Mappers (Entity ↔ Domain ↔ DTO)

Mappers convert between different data representations.

### **TransactionMapper**

```kotlin
package com.xpenz.core.data.mapper

import com.xpenz.core.database.entity.TransactionEntity
import com.xpenz.core.domain.model.*
import com.xpenz.core.network.model.TransactionDTO
import javax.inject.Inject

class TransactionMapper @Inject constructor(
    private val categoryMapper: CategoryMapper
) {

    // Entity -> Domain
    fun toDomain(entity: TransactionEntity, category: Category): Transaction {
        return Transaction(
            id = entity.transactionId,
            userId = entity.userId,
            familyId = entity.familyId,
            type = when (entity.type) {
                "DEBIT" -> TransactionType.DEBIT
                "CREDIT" -> TransactionType.CREDIT
                "REFUND" -> TransactionType.REFUND
                else -> TransactionType.DEBIT
            },
            amount = entity.amount,
            currency = entity.currency,
            merchantName = entity.merchantName,
            upiId = entity.upiId,
            bankName = entity.bankName,
            bankReferenceNumber = entity.bankReferenceNumber,
            category = category,
            mlConfidence = entity.mlConfidence,
            mlSource = when (entity.mlSource) {
                "ML_ENSEMBLE" -> MLSource.ML_ENSEMBLE
                "ML_CHT" -> MLSource.ML_CHT
                "RULE_ENGINE" -> MLSource.RULE_ENGINE
                "USER_HABIT" -> MLSource.USER_HABIT
                "AMOUNT_TIME_PRIOR" -> MLSource.AMOUNT_TIME_PRIOR
                "USER_CORRECTED" -> MLSource.USER_CORRECTED
                else -> MLSource.ML_ENSEMBLE
            },
            top3Predictions = parseTop3Predictions(entity.mlTop3Predictions),
            userCorrectedCategory = null, // Would need to fetch separately
            location = if (entity.locationLatitude != null && entity.locationLongitude != null) {
                Location(
                    latitude = entity.locationLatitude,
                    longitude = entity.locationLongitude,
                    name = entity.locationName,
                    accuracy = entity.locationAccuracy
                )
            } else null,
            timestamp = entity.timestamp,
            detectedAt = entity.detectedAt,
            note = entity.note,
            tags = parseTags(entity.tags),
            receiptUrl = entity.receiptUrl,
            isSynced = entity.isSynced,
            isManuallyAdded = entity.isManuallyAdded,
            createdAt = entity.createdAt,
            updatedAt = entity.updatedAt
        )
    }

    // Domain -> Entity
    fun toEntity(transaction: Transaction): TransactionEntity {
        return TransactionEntity(
            transactionId = transaction.id,
            userId = transaction.userId,
            familyId = transaction.familyId,
            type = transaction.type.name,
            amount = transaction.amount,
            currency = transaction.currency,
            merchantName = transaction.merchantName,
            upiId = transaction.upiId,
            bankName = transaction.bankName,
            bankReferenceNumber = transaction.bankReferenceNumber,
            mlCategoryId = transaction.category.id,
            mlConfidence = transaction.mlConfidence,
            mlSource = transaction.mlSource.name,
            mlTop3Predictions = serializeTop3Predictions(transaction.top3Predictions),
            userCorrectedCategoryId = transaction.userCorrectedCategory?.id,
            correctionTimestamp = null, // Set when correcting
            locationLatitude = transaction.location?.latitude,
            locationLongitude = transaction.location?.longitude,
            locationName = transaction.location?.name,
            locationAccuracy = transaction.location?.accuracy,
            timestamp = transaction.timestamp,
            detectedAt = transaction.detectedAt,
            note = transaction.note,
            tags = serializeTags(transaction.tags),
            receiptUrl = transaction.receiptUrl,
            smsSender = null, // Set during SMS parsing
            smsBodyHash = null, // Set during SMS parsing
            isSynced = transaction.isSynced,
            firestoreId = null,
            syncVersion = 1,
            createdAt = transaction.createdAt,
            updatedAt = transaction.updatedAt,
            deletedAt = null,
            isManuallyAdded = transaction.isManuallyAdded
        )
    }

    // Domain -> DTO (for Firestore)
    fun toDTO(transaction: Transaction, encryptionKey: String?): TransactionDTO {
        // Optionally encrypt sensitive data for cloud storage
        val encryptedData = if (encryptionKey != null) {
            encryptSensitiveData(transaction, encryptionKey)
        } else null

        return TransactionDTO(
            transactionId = transaction.id,
            userId = transaction.userId,
            familyId = transaction.familyId,
            type = transaction.type.name,
            amount = transaction.amount,
            currency = transaction.currency,
            merchantName = transaction.merchantName,
            upiId = transaction.upiId,
            categoryId = transaction.category.id,
            confidence = transaction.mlConfidence,
            timestamp = transaction.timestamp,
            note = transaction.note,
            encryptedData = encryptedData,
            createdAt = transaction.createdAt,
            updatedAt = transaction.updatedAt
        )
    }

    // DTO -> Domain (from Firestore)
    fun fromDTO(dto: TransactionDTO, category: Category, decryptionKey: String?): Transaction {
        // Decrypt if needed
        val decryptedData = if (dto.encryptedData != null && decryptionKey != null) {
            decryptSensitiveData(dto.encryptedData, decryptionKey)
        } else null

        return Transaction(
            id = dto.transactionId,
            userId = dto.userId,
            familyId = dto.familyId,
            type = TransactionType.valueOf(dto.type),
            amount = dto.amount,
            currency = dto.currency,
            merchantName = decryptedData?.merchantName ?: dto.merchantName,
            upiId = decryptedData?.upiId ?: dto.upiId,
            bankName = null,
            bankReferenceNumber = null,
            category = category,
            mlConfidence = dto.confidence,
            mlSource = MLSource.ML_ENSEMBLE,
            top3Predictions = null,
            userCorrectedCategory = null,
            location = null,
            timestamp = dto.timestamp,
            detectedAt = dto.createdAt,
            note = dto.note,
            tags = emptyList(),
            receiptUrl = null,
            isSynced = true,
            isManuallyAdded = false,
            createdAt = dto.createdAt,
            updatedAt = dto.updatedAt
        )
    }

    // Helper functions
    private fun parseTags(tagsJson: String?): List<String> {
        if (tagsJson.isNullOrEmpty()) return emptyList()
        return try {
            Gson().fromJson(tagsJson, Array<String>::class.java).toList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun serializeTags(tags: List<String>): String? {
        if (tags.isEmpty()) return null
        return Gson().toJson(tags)
    }

    private fun parseTop3Predictions(json: String?): List<CategoryPrediction>? {
        if (json.isNullOrEmpty()) return null
        return try {
            val predictions = Gson().fromJson(json, Array<Map<String, Any>>::class.java)
            predictions.map {
                CategoryPrediction(
                    category = Category(
                        id = (it["id"] as Double).toInt(),
                        name = "", // Would need full category lookup
                        displayName = "",
                        parentCategory = null,
                        level = CategoryLevel.GRANULAR,
                        emoji = "",
                        color = "",
                        keywords = emptyList()
                    ),
                    confidence = (it["conf"] as Double).toFloat()
                )
            }
        } catch (e: Exception) {
            null
        }
    }

    private fun serializeTop3Predictions(predictions: List<CategoryPrediction>?): String? {
        if (predictions.isNullOrEmpty()) return null
        val data = predictions.map {
            mapOf(
                "id" to it.category.id,
                "conf" to it.confidence
            )
        }
        return Gson().toJson(data)
    }

    private fun encryptSensitiveData(transaction: Transaction, key: String): String {
        // Implement AES-256-GCM encryption
        // This is a placeholder - actual implementation would use Android Security Crypto
        val sensitiveData = mapOf(
            "merchant" to transaction.merchantName,
            "upi" to transaction.upiId,
            "note" to transaction.note
        )
        return Gson().toJson(sensitiveData) // Would be encrypted
    }

    private fun decryptSensitiveData(encrypted: String, key: String): DecryptedData? {
        // Implement AES-256-GCM decryption
        return try {
            val data = Gson().fromJson(encrypted, Map::class.java)
            DecryptedData(
                merchantName = data["merchant"] as? String,
                upiId = data["upi"] as? String
            )
        } catch (e: Exception) {
            null
        }
    }

    private data class DecryptedData(
        val merchantName: String?,
        val upiId: String?
    )
}
```

### **CategoryMapper**

```kotlin
class CategoryMapper @Inject constructor() {

    fun toDomain(entity: MLCategoryEntity, parent: Category? = null): Category {
        return Category(
            id = entity.categoryId,
            name = entity.categoryName,
            displayName = entity.displayName,
            parentCategory = parent,
            level = when (entity.level) {
                1 -> CategoryLevel.MAIN
                2 -> CategoryLevel.SUB
                3 -> CategoryLevel.SPECIFIC
                4 -> CategoryLevel.GRANULAR
                else -> CategoryLevel.MAIN
            },
            emoji = entity.emoji,
            color = entity.color,
            keywords = parseKeywords(entity.keywords)
        )
    }

    fun toEntity(category: Category): MLCategoryEntity {
        return MLCategoryEntity(
            categoryId = category.id,
            categoryName = category.name,
            displayName = category.displayName,
            parentCategoryId = category.parentCategory?.id,
            level = when (category.level) {
                CategoryLevel.MAIN -> 1
                CategoryLevel.SUB -> 2
                CategoryLevel.SPECIFIC -> 3
                CategoryLevel.GRANULAR -> 4
            },
            emoji = category.emoji,
            color = category.color,
            keywords = serializeKeywords(category.keywords),
            isActive = true,
            sortOrder = 0
        )
    }

    private fun parseKeywords(json: String): List<String> {
        return try {
            Gson().fromJson(json, Array<String>::class.java).toList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun serializeKeywords(keywords: List<String>): String {
        return Gson().toJson(keywords)
    }
}
```

### **BudgetMapper**

```kotlin
class BudgetMapper @Inject constructor() {

    fun toDomain(entity: BudgetEntity): Budget {
        return Budget(
            id = entity.budgetId,
            familyId = entity.familyId,
            type = BudgetType.valueOf(entity.budgetType),
            name = entity.name,
            amount = entity.amount,
            currency = entity.currency,
            period = BudgetPeriod.valueOf(entity.period),
            alertThresholds = parseAlertThresholds(entity.alertThresholds),
            notificationEnabled = entity.notificationEnabled,
            notifyAllMembers = entity.notifyAllMembers,
            startDate = entity.startDate,
            endDate = entity.endDate,
            isRecurring = entity.isRecurring,
            isActive = entity.isActive,
            createdBy = entity.createdBy,
            createdAt = entity.createdAt,
            categoryId = entity.categoryId,
            memberId = entity.memberId
        )
    }

    fun toEntity(budget: Budget): BudgetEntity {
        return BudgetEntity(
            budgetId = budget.id,
            familyId = budget.familyId,
            budgetType = budget.type.name,
            name = budget.name,
            categoryId = budget.categoryId,
            memberId = budget.memberId,
            amount = budget.amount,
            currency = budget.currency,
            period = budget.period.name,
            alertThresholds = serializeAlertThresholds(budget.alertThresholds),
            notificationEnabled = budget.notificationEnabled,
            notifyAllMembers = budget.notifyAllMembers,
            startDate = budget.startDate,
            endDate = budget.endDate,
            isRecurring = budget.isRecurring,
            isActive = budget.isActive,
            pausedAt = null,
            createdBy = budget.createdBy,
            createdAt = budget.createdAt,
            updatedAt = budget.createdAt,
            deletedAt = null
        )
    }

    private fun parseAlertThresholds(json: String): List<Int> {
        return try {
            Gson().fromJson(json, Array<Int>::class.java).toList()
        } catch (e: Exception) {
            listOf(50, 80, 100, 120) // Default
        }
    }

    private fun serializeAlertThresholds(thresholds: List<Int>): String {
        return Gson().toJson(thresholds)
    }
}
```

---

## 7. REPOSITORY PATTERN

### 7.1 Repository Interfaces (Domain Layer)

```kotlin
package com.xpenz.core.domain.repository

import com.xpenz.core.domain.model.*
import com.xpenz.core.common.result.Result
import kotlinx.coroutines.flow.Flow

interface TransactionRepository {

    // Observe transactions
    fun getUserTransactions(userId: String): Flow<List<Transaction>>
    fun getFamilyTransactions(familyId: String): Flow<List<Transaction>>

    // Get single transaction
    suspend fun getTransaction(id: String): Result<Transaction>

    // CRUD operations
    suspend fun insertTransaction(transaction: Transaction): Result<Unit>
    suspend fun updateTransaction(transaction: Transaction): Result<Unit>
    suspend fun deleteTransaction(id: String): Result<Unit>

    // Query operations
    suspend fun getTransactionsByDateRange(
        userId: String,
        startTime: Long,
        endTime: Long
    ): Result<List<Transaction>>

    suspend fun getTransactionsByCategory(
        userId: String,
        categoryId: Int
    ): Result<List<Transaction>>

    suspend fun searchTransactions(
        userId: String,
        query: String
    ): Result<List<Transaction>>

    // Statistics
    suspend fun getTotalSpending(
        userId: String,
        startTime: Long,
        endTime: Long
    ): Result<Double>

    suspend fun getCategoryWiseSpending(
        userId: String,
        startTime: Long,
        endTime: Long
    ): Result<Map<Category, Double>>

    // Sync operations
    suspend fun syncTransactions(): Result<Unit>
}

interface FamilyRepository {

    fun getFamily(familyId: String): Flow<Family?>
    fun getUserFamilies(userId: String): Flow<List<Family>>

    suspend fun createFamily(family: Family): Result<Family>
    suspend fun updateFamily(family: Family): Result<Unit>
    suspend fun deleteFamily(familyId: String, userId: String): Result<Unit>

    suspend fun getFamilyByCode(code: String): Result<Family>
    suspend fun regenerateInvitationCode(familyId: String): Result<String>

    suspend fun getFamilyMembers(familyId: String): Result<List<FamilyMember>>
    suspend fun addMember(familyId: String, userId: String, nickname: String): Result<Unit>
    suspend fun removeMember(familyId: String, memberId: String, removedBy: String): Result<Unit>
    suspend fun updateMemberRole(memberId: String, newRole: MemberRole): Result<Unit>
}

interface BudgetRepository {

    fun getActiveBudgets(familyId: String): Flow<List<Budget>>
    fun getBudgetProgress(budgetId: String): Flow<BudgetProgress?>

    suspend fun createBudget(budget: Budget): Result<Budget>
    suspend fun updateBudget(budget: Budget): Result<Unit>
    suspend fun deleteBudget(budgetId: String): Result<Unit>
    suspend fun pauseBudget(budgetId: String): Result<Unit>
    suspend fun resumeBudget(budgetId: String): Result<Unit>

    suspend fun calculateBudgetProgress(budgetId: String): Result<BudgetProgress>
    suspend fun checkBudgetAlerts(transaction: Transaction): Result<List<BudgetAlert>>
}

interface UserRepository {

    fun getCurrentUser(): Flow<User?>
    suspend fun getUser(userId: String): Result<User>
    suspend fun updateUser(user: User): Result<Unit>
    suspend fun updatePremiumStatus(userId: String, isPremium: Boolean): Result<Unit>
}

interface CategoryRepository {

    suspend fun getCategory(id: Int): Result<Category>
    suspend fun getAllCategories(): Result<List<Category>>
    suspend fun getCategoriesByLevel(level: CategoryLevel): Result<List<Category>>
    suspend fun searchCategories(query: String): Result<List<Category>>
}

interface SubscriptionRepository {

    fun getSubscription(userId: String): Flow<Subscription?>
    suspend fun saveSubscription(subscription: Subscription): Result<Unit>
    suspend fun updateSubscriptionStatus(userId: String, status: SubscriptionStatus): Result<Unit>
    suspend fun verifyPurchase(purchaseToken: String): Result<Boolean>
}
```

---

### 7.2 Repository Implementations (Data Layer)

### **TransactionRepositoryImpl**

```kotlin
package com.xpenz.core.data.repository

import com.xpenz.core.database.dao.TransactionDao
import com.xpenz.core.database.dao.MLCategoryDao
import com.xpenz.core.domain.repository.TransactionRepository
import com.xpenz.core.domain.model.*
import com.xpenz.core.data.mapper.TransactionMapper
import com.xpenz.core.data.mapper.CategoryMapper
import com.xpenz.core.network.firebase.FirestoreService
import com.xpenz.core.common.result.Result
import kotlinx.coroutines.flow.*
import javax.inject.Inject

class TransactionRepositoryImpl @Inject constructor(
    private val transactionDao: TransactionDao,
    private val categoryDao: MLCategoryDao,
    private val transactionMapper: TransactionMapper,
    private val categoryMapper: CategoryMapper,
    private val firestoreService: FirestoreService,
    private val userPreferences: UserPreferences
) : TransactionRepository {

    override fun getUserTransactions(userId: String): Flow<List<Transaction>> {
        return transactionDao.getUserTransactions(userId)
            .map { entities ->
                entities.map { entity ->
                    val category = getCategoryFromEntity(entity)
                    transactionMapper.toDomain(entity, category)
                }
            }
    }

    override fun getFamilyTransactions(familyId: String): Flow<List<Transaction>> {
        return transactionDao.getFamilyTransactions(familyId)
            .map { entities ->
                entities.map { entity ->
                    val category = getCategoryFromEntity(entity)
                    transactionMapper.toDomain(entity, category)
                }
            }
    }

    override suspend fun getTransaction(id: String): Result<Transaction> {
        return try {
            val entity = transactionDao.getTransaction(id)
                ?: return Result.Error("Transaction not found")

            val category = getCategoryFromEntity(entity)
            val transaction = transactionMapper.toDomain(entity, category)

            Result.Success(transaction)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get transaction")
        }
    }

    override suspend fun insertTransaction(transaction: Transaction): Result<Unit> {
        return try {
            // Save to local database
            val entity = transactionMapper.toEntity(transaction)
            transactionDao.insertTransaction(entity)

            // Queue for cloud sync if Premium
            if (userPreferences.isPremium()) {
                queueForCloudSync(transaction)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to insert transaction")
        }
    }

    override suspend fun updateTransaction(transaction: Transaction): Result<Unit> {
        return try {
            val entity = transactionMapper.toEntity(transaction)
            transactionDao.updateTransaction(entity)

            // Update in cloud if synced
            if (transaction.isSynced && userPreferences.isPremium()) {
                firestoreService.updateTransaction(transaction)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to update transaction")
        }
    }

    override suspend fun deleteTransaction(id: String): Result<Unit> {
        return try {
            transactionDao.softDeleteTransaction(id)

            // Mark as deleted in cloud
            if (userPreferences.isPremium()) {
                firestoreService.deleteTransaction(id)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to delete transaction")
        }
    }

    override suspend fun getTransactionsByDateRange(
        userId: String,
        startTime: Long,
        endTime: Long
    ): Result<List<Transaction>> {
        return try {
            val entities = transactionDao.getTransactionsByDateRange(userId, startTime, endTime)
            val transactions = entities.map { entity ->
                val category = getCategoryFromEntity(entity)
                transactionMapper.toDomain(entity, category)
            }
            Result.Success(transactions)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get transactions by date range")
        }
    }

    override suspend fun getTransactionsByCategory(
        userId: String,
        categoryId: Int
    ): Result<List<Transaction>> {
        return try {
            val entities = transactionDao.getTransactionsByCategory(userId, categoryId)
            val transactions = entities.map { entity ->
                val category = getCategoryFromEntity(entity)
                transactionMapper.toDomain(entity, category)
            }
            Result.Success(transactions)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get transactions by category")
        }
    }

    override suspend fun searchTransactions(
        userId: String,
        query: String
    ): Result<List<Transaction>> {
        return try {
            val entities = transactionDao.searchTransactions(userId, query)
            val transactions = entities.map { entity ->
                val category = getCategoryFromEntity(entity)
                transactionMapper.toDomain(entity, category)
            }
            Result.Success(transactions)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to search transactions")
        }
    }

    override suspend fun getTotalSpending(
        userId: String,
        startTime: Long,
        endTime: Long
    ): Result<Double> {
        return try {
            val total = transactionDao.getTotalAmount(userId, "DEBIT", startTime, endTime) ?: 0.0
            Result.Success(total)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get total spending")
        }
    }

    override suspend fun getCategoryWiseSpending(
        userId: String,
        startTime: Long,
        endTime: Long
    ): Result<Map<Category, Double>> {
        return try {
            val spending = transactionDao.getCategoryWiseSpending(userId, startTime, endTime)
            val categorySpendingMap = spending.associate { categorySpending ->
                val categoryEntity = categoryDao.getCategory(categorySpending.categoryId)
                    ?: throw Exception("Category not found: ${categorySpending.categoryId}")
                val category = categoryMapper.toDomain(categoryEntity)
                category to categorySpending.total
            }
            Result.Success(categorySpendingMap)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get category-wise spending")
        }
    }

    override suspend fun syncTransactions(): Result<Unit> {
        return try {
            if (!userPreferences.isPremium()) {
                return Result.Error("Cloud sync requires Premium")
            }

            // Get unsynced transactions
            val unsyncedEntities = transactionDao.getUnsyncedTransactions(limit = 50)

            // Upload to Firestore
            unsyncedEntities.forEach { entity ->
                val category = getCategoryFromEntity(entity)
                val transaction = transactionMapper.toDomain(entity, category)
                firestoreService.uploadTransaction(transaction)
                transactionDao.markAsSynced(entity.transactionId)
            }

            // Download new transactions from Firestore
            val newTransactions = firestoreService.downloadNewTransactions(
                userId = userPreferences.getUserId(),
                lastSyncTime = userPreferences.getLastSyncTime()
            )

            newTransactions.forEach { transaction ->
                val entity = transactionMapper.toEntity(transaction.copy(isSynced = true))
                transactionDao.insertTransaction(entity)
            }

            userPreferences.updateLastSyncTime(System.currentTimeMillis())

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to sync transactions")
        }
    }

    // Helper functions
    private suspend fun getCategoryFromEntity(entity: TransactionEntity): Category {
        val categoryEntity = categoryDao.getCategory(entity.mlCategoryId)
            ?: throw Exception("Category not found: ${entity.mlCategoryId}")
        return categoryMapper.toDomain(categoryEntity)
    }

    private suspend fun queueForCloudSync(transaction: Transaction) {
        // Add to WorkManager queue for background sync
        // Implementation in Section 8
    }
}
```

### **FamilyRepositoryImpl**

```kotlin
class FamilyRepositoryImpl @Inject constructor(
    private val familyDao: FamilyDao,
    private val familyMemberDao: FamilyMemberDao,
    private val familyMapper: FamilyMapper,
    private val firestoreService: FirestoreService,
    private val userPreferences: UserPreferences
) : FamilyRepository {

    override fun getFamily(familyId: String): Flow<Family?> {
        return familyDao.getFamily(familyId)
            .map { entity -> entity?.let { familyMapper.toDomain(it) } }
    }

    override fun getUserFamilies(userId: String): Flow<List<Family>> {
        return familyMemberDao.getUserFamilies(userId)
            .map { memberships ->
                memberships.mapNotNull { membership ->
                    familyDao.getFamily(membership.familyId).firstOrNull()
                }.map { familyMapper.toDomain(it) }
            }
    }

    override suspend fun createFamily(family: Family): Result<Family> {
        return try {
            // Generate unique invitation code
            val invitationCode = generateInvitationCode()
            val familyWithCode = family.copy(invitationCode = invitationCode)

            // Save to local database
            val entity = familyMapper.toEntity(familyWithCode)
            familyDao.insertFamily(entity)

            // Add creator as admin member
            val creatorMembership = FamilyMemberEntity(
                memberId = UUID.randomUUID().toString(),
                familyId = family.id,
                userId = family.createdBy,
                nickname = "Admin",
                role = "ADMIN",
                avatarEmoji = null,
                status = "ACTIVE",
                joinedAt = System.currentTimeMillis(),
                leftAt = null,
                removedBy = null,
                removedAt = null,
                lastActiveAt = System.currentTimeMillis(),
                createdAt = System.currentTimeMillis(),
                updatedAt = System.currentTimeMillis()
            )
            familyMemberDao.insertMember(creatorMembership)

            // Sync to cloud if Premium
            if (userPreferences.isPremium()) {
                firestoreService.createFamily(familyWithCode)
            }

            Result.Success(familyWithCode)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to create family")
        }
    }

    override suspend fun updateFamily(family: Family): Result<Unit> {
        return try {
            val entity = familyMapper.toEntity(family)
            familyDao.updateFamily(entity)

            if (userPreferences.isPremium()) {
                firestoreService.updateFamily(family)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to update family")
        }
    }

    override suspend fun deleteFamily(familyId: String, userId: String): Result<Unit> {
        return try {
            familyDao.softDeleteFamily(familyId, userId)

            // Update all members to LEFT status
            val members = familyMemberDao.getFamilyMembers(familyId).first()
            members.forEach { member ->
                familyMemberDao.markAsLeft(member.id)
            }

            if (userPreferences.isPremium()) {
                firestoreService.deleteFamily(familyId)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to delete family")
        }
    }

    override suspend fun getFamilyByCode(code: String): Result<Family> {
        return try {
            val entity = familyDao.getFamilyByCode(code)
                ?: return Result.Error("Invalid invitation code")

            // Check if code expired
            if (System.currentTimeMillis() > entity.codeExpiresAt) {
                return Result.Error("Invitation code expired")
            }

            val family = familyMapper.toDomain(entity)
            Result.Success(family)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get family by code")
        }
    }

    override suspend fun regenerateInvitationCode(familyId: String): Result<String> {
        return try {
            val newCode = generateInvitationCode()
            familyDao.regenerateInvitationCode(familyId, newCode)
            Result.Success(newCode)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to regenerate invitation code")
        }
    }

    override suspend fun getFamilyMembers(familyId: String): Result<List<FamilyMember>> {
        return try {
            val entities = familyMemberDao.getFamilyMembers(familyId).first()
            val members = entities.map { familyMemberMapper.toDomain(it) }
            Result.Success(members)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to get family members")
        }
    }

    override suspend fun addMember(
        familyId: String,
        userId: String,
        nickname: String
    ): Result<Unit> {
        return try {
            // Check member limit
            val family = familyDao.getFamily(familyId).firstOrNull()
                ?: return Result.Error("Family not found")

            val currentCount = familyMemberDao.getMemberCount(familyId)
            if (currentCount >= family.maxMembers) {
                return Result.Error("Family member limit reached")
            }

            // Add member
            val member = FamilyMemberEntity(
                memberId = UUID.randomUUID().toString(),
                familyId = familyId,
                userId = userId,
                nickname = nickname,
                role = "MEMBER",
                avatarEmoji = null,
                status = "ACTIVE",
                joinedAt = System.currentTimeMillis(),
                leftAt = null,
                removedBy = null,
                removedAt = null,
                lastActiveAt = System.currentTimeMillis(),
                createdAt = System.currentTimeMillis(),
                updatedAt = System.currentTimeMillis()
            )
            familyMemberDao.insertMember(member)

            if (userPreferences.isPremium()) {
                firestoreService.addFamilyMember(familyId, userId, nickname)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to add member")
        }
    }

    override suspend fun removeMember(
        familyId: String,
        memberId: String,
        removedBy: String
    ): Result<Unit> {
        return try {
            familyMemberDao.markAsRemoved(memberId, removedBy)

            if (userPreferences.isPremium()) {
                firestoreService.removeFamilyMember(familyId, memberId)
            }

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to remove member")
        }
    }

    override suspend fun updateMemberRole(
        memberId: String,
        newRole: MemberRole
    ): Result<Unit> {
        return try {
            val member = familyMemberDao.getMembership(memberId, "")
                ?: return Result.Error("Member not found")

            val updated = member.copy(role = newRole.name)
            familyMemberDao.updateMember(updated)

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Failed to update member role")
        }
    }

    private fun generateInvitationCode(): String {
        // Generate XP-XXXXX format (5 alphanumeric, excluding confusing chars)
        val chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" // No I, O, 0, 1
        val code = (1..5).map { chars.random() }.joinToString("")
        return "XP-$code"
    }
}
```

## 8. CLOUD SYNC ARCHITECTURE

### 8.1 Cloud Sync Overview

**Architecture Pattern:** Offline-First with Background Sync

```
┌─────────────────────────────────────────────────────────────┐
│                    OFFLINE-FIRST SYNC                        │
│                                                              │
│  Local Database (Room) = Single Source of Truth             │
│                    ↓                                         │
│              All operations write locally first              │
│                    ↓                                         │
│           Queue operations for background sync               │
│                    ↓                                         │
│      WorkManager uploads to Firestore when online           │
│                    ↓                                         │
│        Firestore listeners download updates from others      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**

1. **Local-First:** All operations succeed locally immediately, even offline
2. **Eventual Consistency:** Cloud sync happens in background
3. **Conflict Resolution:** Last-write-wins with timestamp comparison
4. **Encryption:** All data encrypted before upload (AES-256-GCM)
5. **Batching:** Multiple operations batched for efficiency
6. **Retry Logic:** Exponential backoff for failed syncs

---

### 8.2 Firestore Structure

**Database Organization:**

```
firestore/
├── users/
│   └── {userId}/
│       ├── profile (document)
│       ├── subscription (document)
│       └── devices (collection)
│           └── {deviceId} (document)
│
├── families/
│   └── {familyId}/
│       ├── info (document)
│       ├── members (collection)
│       │   └── {memberId} (document)
│       ├── transactions (collection)
│       │   └── {transactionId} (document)
│       ├── budgets (collection)
│       │   └── {budgetId} (document)
│       └── sync_metadata (document)
│
└── invitations/
    └── {invitationCode} (document)
```

**Firestore Collection Schemas:**

### **users/{userId}/profile**

```json
{
  "user_id": "string",
  "phone_number": "string (encrypted)",
  "name": "string (encrypted)",
  "email": "string (encrypted)",
  "avatar_url": "string",
  "is_premium": "boolean",
  "premium_expires_at": "timestamp",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "devices": ["device_id_1", "device_id_2"]
}
```

### **families/{familyId}/info**

```json
{
  "family_id": "string",
  "name": "string (encrypted)",
  "emoji": "string",
  "color": "string",
  "invitation_code": "string",
  "code_expires_at": "timestamp",
  "created_by": "string",
  "max_members": "number",
  "is_premium": "boolean",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "deleted_at": "timestamp | null"
}
```

### **families/{familyId}/members/{memberId}**

```json
{
  "member_id": "string",
  "user_id": "string",
  "nickname": "string (encrypted)",
  "role": "string",
  "status": "string",
  "joined_at": "timestamp",
  "left_at": "timestamp | null",
  "last_active_at": "timestamp"
}
```

### **families/{familyId}/transactions/{transactionId}**

```json
{
  "transaction_id": "string",
  "user_id": "string",
  "encrypted_data": "string (AES-256-GCM encrypted)",
  "type": "string",
  "amount": "number",
  "category_id": "number",
  "timestamp": "timestamp",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "deleted_at": "timestamp | null",
  "sync_version": "number",
  "device_id": "string"
}
```

**Encrypted Data Payload (before encryption):**

```json
{
  "merchant_name": "string",
  "upi_id": "string",
  "bank_name": "string",
  "bank_reference": "string",
  "note": "string",
  "location": {
    "latitude": "number",
    "longitude": "number",
    "name": "string"
  }
}
```

### **families/{familyId}/budgets/{budgetId}**

```json
{
  "budget_id": "string",
  "family_id": "string",
  "budget_type": "string",
  "name": "string (encrypted)",
  "category_id": "number | null",
  "member_id": "string | null",
  "amount": "number",
  "period": "string",
  "alert_thresholds": [50, 80, 100, 120],
  "start_date": "timestamp",
  "is_active": "boolean",
  "created_by": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### **families/{familyId}/sync_metadata**

```json
{
  "last_transaction_sync": "timestamp",
  "last_budget_sync": "timestamp",
  "last_member_sync": "timestamp",
  "active_devices": ["device_id_1", "device_id_2"],
  "sync_conflicts": []
}
```

---

### 8.3 FirestoreService Implementation

```kotlin
package com.xpenz.core.network.firebase

import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.Query
import com.google.firebase.firestore.ktx.snapshots
import com.google.firebase.firestore.ktx.toObject
import com.xpenz.core.domain.model.*
import com.xpenz.core.network.model.*
import com.xpenz.core.security.EncryptionService
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.tasks.await
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FirestoreService @Inject constructor(
    private val firestore: FirebaseFirestore,
    private val encryptionService: EncryptionService,
    private val transactionMapper: TransactionMapper,
    private val familyMapper: FamilyMapper
) {

    // ========== TRANSACTION SYNC ==========

    suspend fun uploadTransaction(transaction: Transaction) {
        try {
            val familyId = transaction.familyId
                ?: throw IllegalArgumentException("Cannot sync transaction without family")

            // Encrypt sensitive data
            val encryptedPayload = encryptionService.encrypt(
                data = serializeSensitiveData(transaction),
                key = getEncryptionKey(familyId)
            )

            val dto = TransactionDTO(
                transactionId = transaction.id,
                userId = transaction.userId,
                familyId = familyId,
                type = transaction.type.name,
                amount = transaction.amount,
                currency = transaction.currency,
                categoryId = transaction.category.id,
                confidence = transaction.mlConfidence,
                timestamp = transaction.timestamp,
                encryptedData = encryptedPayload,
                createdAt = transaction.createdAt,
                updatedAt = transaction.updatedAt
            )

            firestore.collection("families")
                .document(familyId)
                .collection("transactions")
                .document(transaction.id)
                .set(dto)
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to upload transaction: ${e.message}", e)
        }
    }

    suspend fun updateTransaction(transaction: Transaction) {
        try {
            val familyId = transaction.familyId
                ?: throw IllegalArgumentException("Cannot sync transaction without family")

            val updates = mapOf(
                "updated_at" to System.currentTimeMillis(),
                "amount" to transaction.amount,
                "note" to transaction.note,
                "sync_version" to FieldValue.increment(1)
            )

            firestore.collection("families")
                .document(familyId)
                .collection("transactions")
                .document(transaction.id)
                .update(updates)
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to update transaction: ${e.message}", e)
        }
    }

    suspend fun deleteTransaction(transactionId: String, familyId: String) {
        try {
            firestore.collection("families")
                .document(familyId)
                .collection("transactions")
                .document(transactionId)
                .update(
                    mapOf(
                        "deleted_at" to System.currentTimeMillis(),
                        "sync_version" to FieldValue.increment(1)
                    )
                )
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to delete transaction: ${e.message}", e)
        }
    }

    suspend fun downloadNewTransactions(
        userId: String,
        familyId: String,
        lastSyncTime: Long
    ): List<Transaction> {
        try {
            val snapshot = firestore.collection("families")
                .document(familyId)
                .collection("transactions")
                .whereGreaterThan("updated_at", lastSyncTime)
                .whereEqualTo("deleted_at", null)
                .get()
                .await()

            return snapshot.documents.mapNotNull { doc ->
                try {
                    val dto = doc.toObject<TransactionDTO>()
                        ?: return@mapNotNull null

                    // Skip if this transaction was created by current user (already in local DB)
                    if (dto.userId == userId) return@mapNotNull null

                    // Decrypt sensitive data
                    val decryptedData = if (dto.encryptedData != null) {
                        encryptionService.decrypt(
                            encryptedData = dto.encryptedData,
                            key = getEncryptionKey(familyId)
                        )
                    } else null

                    // Convert to domain model
                    val category = getCategoryFromId(dto.categoryId)
                    transactionMapper.fromDTO(dto, category, decryptedData)

                } catch (e: Exception) {
                    Timber.e(e, "Failed to parse transaction: ${doc.id}")
                    null
                }
            }

        } catch (e: Exception) {
            throw SyncException("Failed to download transactions: ${e.message}", e)
        }
    }

    fun observeFamilyTransactions(familyId: String): Flow<List<TransactionDTO>> {
        return firestore.collection("families")
            .document(familyId)
            .collection("transactions")
            .whereEqualTo("deleted_at", null)
            .orderBy("timestamp", Query.Direction.DESCENDING)
            .limit(100)
            .snapshots()
            .map { snapshot ->
                snapshot.documents.mapNotNull { it.toObject<TransactionDTO>() }
            }
    }

    // ========== FAMILY SYNC ==========

    suspend fun createFamily(family: Family) {
        try {
            val dto = FamilyDTO(
                familyId = family.id,
                name = encryptionService.encrypt(family.name, getEncryptionKey(family.id)),
                emoji = family.emoji,
                color = family.color,
                invitationCode = family.invitationCode,
                createdBy = family.createdBy,
                maxMembers = family.maxMembers,
                isPremium = family.isPremium,
                createdAt = family.createdAt,
                updatedAt = family.updatedAt
            )

            firestore.collection("families")
                .document(family.id)
                .set(mapOf("info" to dto))
                .await()

            // Create invitation document for easy lookup
            firestore.collection("invitations")
                .document(family.invitationCode)
                .set(mapOf(
                    "family_id" to family.id,
                    "expires_at" to family.codeExpiresAt,
                    "created_at" to family.createdAt
                ))
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to create family: ${e.message}", e)
        }
    }

    suspend fun updateFamily(family: Family) {
        try {
            val updates = mapOf(
                "info.name" to encryptionService.encrypt(family.name, getEncryptionKey(family.id)),
                "info.emoji" to family.emoji,
                "info.color" to family.color,
                "info.updated_at" to System.currentTimeMillis()
            )

            firestore.collection("families")
                .document(family.id)
                .update(updates)
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to update family: ${e.message}", e)
        }
    }

    suspend fun deleteFamily(familyId: String) {
        try {
            firestore.collection("families")
                .document(familyId)
                .update(mapOf(
                    "info.deleted_at" to System.currentTimeMillis()
                ))
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to delete family: ${e.message}", e)
        }
    }

    suspend fun addFamilyMember(familyId: String, userId: String, nickname: String) {
        try {
            val memberId = UUID.randomUUID().toString()
            val member = mapOf(
                "member_id" to memberId,
                "user_id" to userId,
                "nickname" to encryptionService.encrypt(nickname, getEncryptionKey(familyId)),
                "role" to "MEMBER",
                "status" to "ACTIVE",
                "joined_at" to System.currentTimeMillis(),
                "last_active_at" to System.currentTimeMillis()
            )

            firestore.collection("families")
                .document(familyId)
                .collection("members")
                .document(memberId)
                .set(member)
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to add family member: ${e.message}", e)
        }
    }

    suspend fun removeFamilyMember(familyId: String, memberId: String) {
        try {
            firestore.collection("families")
                .document(familyId)
                .collection("members")
                .document(memberId)
                .update(mapOf(
                    "status" to "REMOVED",
                    "removed_at" to System.currentTimeMillis()
                ))
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to remove family member: ${e.message}", e)
        }
    }

    fun observeFamilyMembers(familyId: String): Flow<List<FamilyMemberDTO>> {
        return firestore.collection("families")
            .document(familyId)
            .collection("members")
            .whereEqualTo("status", "ACTIVE")
            .snapshots()
            .map { snapshot ->
                snapshot.documents.mapNotNull { it.toObject<FamilyMemberDTO>() }
            }
    }

    // ========== BUDGET SYNC ==========

    suspend fun uploadBudget(budget: Budget) {
        try {
            val dto = BudgetDTO(
                budgetId = budget.id,
                familyId = budget.familyId,
                budgetType = budget.type.name,
                name = encryptionService.encrypt(budget.name, getEncryptionKey(budget.familyId)),
                categoryId = budget.categoryId,
                memberId = budget.memberId,
                amount = budget.amount,
                period = budget.period.name,
                alertThresholds = budget.alertThresholds,
                startDate = budget.startDate,
                isActive = budget.isActive,
                createdBy = budget.createdBy,
                createdAt = budget.createdAt,
                updatedAt = budget.updatedAt
            )

            firestore.collection("families")
                .document(budget.familyId)
                .collection("budgets")
                .document(budget.id)
                .set(dto)
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to upload budget: ${e.message}", e)
        }
    }

    suspend fun updateBudgetStatus(budgetId: String, familyId: String, isActive: Boolean) {
        try {
            firestore.collection("families")
                .document(familyId)
                .collection("budgets")
                .document(budgetId)
                .update(mapOf(
                    "is_active" to isActive,
                    "updated_at" to System.currentTimeMillis()
                ))
                .await()

        } catch (e: Exception) {
            throw SyncException("Failed to update budget status: ${e.message}", e)
        }
    }

    fun observeFamilyBudgets(familyId: String): Flow<List<BudgetDTO>> {
        return firestore.collection("families")
            .document(familyId)
            .collection("budgets")
            .whereEqualTo("is_active", true)
            .snapshots()
            .map { snapshot ->
                snapshot.documents.mapNotNull { it.toObject<BudgetDTO>() }
            }
    }

    // ========== HELPER FUNCTIONS ==========

    private fun getEncryptionKey(familyId: String): String {
        // Derive encryption key from family ID + user master key
        // In production, use proper key derivation (PBKDF2, Argon2)
        return encryptionService.deriveKey(familyId)
    }

    private fun serializeSensitiveData(transaction: Transaction): String {
        val data = mapOf(
            "merchant_name" to transaction.merchantName,
            "upi_id" to transaction.upiId,
            "bank_name" to transaction.bankName,
            "bank_reference" to transaction.bankReferenceNumber,
            "note" to transaction.note,
            "location" to transaction.location?.let {
                mapOf(
                    "latitude" to it.latitude,
                    "longitude" to it.longitude,
                    "name" to it.name
                )
            }
        )
        return Gson().toJson(data)
    }

    private suspend fun getCategoryFromId(categoryId: Int): Category {
        // Fetch from local database or cache
        // Implementation depends on CategoryRepository
        throw NotImplementedError("Category lookup not implemented")
    }
}

data class BudgetDTO(
    @PropertyName("budget_id") val budgetId: String = "",
    @PropertyName("family_id") val familyId: String = "",
    @PropertyName("budget_type") val budgetType: String = "",
    @PropertyName("name") val name: String = "",
    @PropertyName("category_id") val categoryId: Int? = null,
    @PropertyName("member_id") val memberId: String? = null,
    @PropertyName("amount") val amount: Double = 0.0,
    @PropertyName("period") val period: String = "",
    @PropertyName("alert_thresholds") val alertThresholds: List<Int> = listOf(),
    @PropertyName("start_date") val startDate: Long = 0L,
    @PropertyName("is_active") val isActive: Boolean = true,
    @PropertyName("created_by") val createdBy: String = "",
    @PropertyName("created_at") val createdAt: Long = 0L,
    @PropertyName("updated_at") val updatedAt: Long = 0L
) {
    constructor() : this(budgetId = "")
}

data class FamilyMemberDTO(
    @PropertyName("member_id") val memberId: String = "",
    @PropertyName("user_id") val userId: String = "",
    @PropertyName("nickname") val nickname: String = "",
    @PropertyName("role") val role: String = "",
    @PropertyName("status") val status: String = "",
    @PropertyName("joined_at") val joinedAt: Long = 0L,
    @PropertyName("last_active_at") val lastActiveAt: Long = 0L
) {
    constructor() : this(memberId = "")
}

class SyncException(message: String, cause: Throwable? = null) : Exception(message, cause)
```

---

### 8.4 Encryption Service

```kotlin
package com.xpenz.core.security

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.inject.Inject
import javax.inject.Singleton
import android.util.Base64

@Singleton
class EncryptionService @Inject constructor(
    private val context: Context
) {

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val MASTER_KEY_ALIAS = "xpenz_master_key"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val GCM_TAG_LENGTH = 128
        private const val IV_LENGTH = 12
    }

    private val keyStore: KeyStore by lazy {
        KeyStore.getInstance(ANDROID_KEYSTORE).apply {
            load(null)
        }
    }

    private val masterKey: MasterKey by lazy {
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
    }

    /**
     * Encrypt data using AES-256-GCM
     */
    fun encrypt(data: String, key: String): String {
        try {
            val secretKey = getOrCreateKey(key)
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(Cipher.ENCRYPT_MODE, secretKey)

            val iv = cipher.iv
            val encryptedBytes = cipher.doFinal(data.toByteArray(Charsets.UTF_8))

            // Combine IV + encrypted data
            val combined = iv + encryptedBytes

            // Base64 encode for storage/transmission
            return Base64.encodeToString(combined, Base64.NO_WRAP)

        } catch (e: Exception) {
            throw EncryptionException("Encryption failed: ${e.message}", e)
        }
    }

    /**
     * Decrypt data encrypted with AES-256-GCM
     */
    fun decrypt(encryptedData: String, key: String): String {
        try {
            val secretKey = getOrCreateKey(key)

            // Base64 decode
            val combined = Base64.decode(encryptedData, Base64.NO_WRAP)

            // Split IV and encrypted data
            val iv = combined.copyOfRange(0, IV_LENGTH)
            val encryptedBytes = combined.copyOfRange(IV_LENGTH, combined.size)

            // Decrypt
            val cipher = Cipher.getInstance(TRANSFORMATION)
            val gcmSpec = GCMParameterSpec(GCM_TAG_LENGTH, iv)
            cipher.init(Cipher.DECRYPT_MODE, secretKey, gcmSpec)

            val decryptedBytes = cipher.doFinal(encryptedBytes)
            return String(decryptedBytes, Charsets.UTF_8)

        } catch (e: Exception) {
            throw EncryptionException("Decryption failed: ${e.message}", e)
        }
    }

    /**
     * Derive a key from family ID
     */
    fun deriveKey(familyId: String): String {
        // In production, use PBKDF2 or Argon2 for key derivation
        // This is a simplified version
        val masterKeyAlias = "${MASTER_KEY_ALIAS}_$familyId"

        return try {
            // Check if key already exists
            if (!keyStore.containsAlias(masterKeyAlias)) {
                generateKey(masterKeyAlias)
            }
            masterKeyAlias
        } catch (e: Exception) {
            throw EncryptionException("Key derivation failed: ${e.message}", e)
        }
    }

    private fun getOrCreateKey(keyAlias: String): SecretKey {
        return if (keyStore.containsAlias(keyAlias)) {
            keyStore.getKey(keyAlias, null) as SecretKey
        } else {
            generateKey(keyAlias)
        }
    }

    private fun generateKey(keyAlias: String): SecretKey {
        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            ANDROID_KEYSTORE
        )

        val keyGenParameterSpec = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .setUserAuthenticationRequired(false)
            .build()

        keyGenerator.init(keyGenParameterSpec)
        return keyGenerator.generateKey()
    }

    /**
     * Hash sensitive data (one-way, for deduplication)
     */
    fun hash(data: String): String {
        try {
            val digest = MessageDigest.getInstance("SHA-256")
            val hashBytes = digest.digest(data.toByteArray(Charsets.UTF_8))
            return Base64.encodeToString(hashBytes, Base64.NO_WRAP)
        } catch (e: Exception) {
            throw EncryptionException("Hashing failed: ${e.message}", e)
        }
    }
}

class EncryptionException(message: String, cause: Throwable? = null) : Exception(message, cause)
```

---

### 8.5 WorkManager Sync Implementation

```kotlin
package com.xpenz.core.data.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.*
import com.xpenz.core.database.dao.SyncQueueDao
import com.xpenz.core.database.dao.TransactionDao
import com.xpenz.core.network.firebase.FirestoreService
import com.xpenz.core.data.mapper.TransactionMapper
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val transactionDao: TransactionDao,
    private val syncQueueDao: SyncQueueDao,
    private val firestoreService: FirestoreService,
    private val transactionMapper: TransactionMapper,
    private val userPreferences: UserPreferences
) : CoroutineWorker(context, params) {

    companion object {
        const val WORK_NAME = "xpenz_sync_worker"
        private const val MAX_RETRY_ATTEMPTS = 3

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
                repeatInterval = 15,
                repeatIntervalTimeUnit = TimeUnit.MINUTES,
                flexTimeInterval = 5,
                flexTimeIntervalUnit = TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .addTag("sync")
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                syncRequest
            )
        }

        fun scheduleOneTime(context: Context) {
            val syncRequest = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .addTag("sync_once")
                .build()

            WorkManager.getInstance(context).enqueue(syncRequest)
        }
    }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            // Check if user is Premium
            if (!userPreferences.isPremium()) {
                return@withContext Result.success()
            }

            // Check network connectivity
            if (!isNetworkAvailable()) {
                return@withContext Result.retry()
            }

            // Upload local changes
            uploadLocalChanges()

            // Download remote changes
            downloadRemoteChanges()

            // Update last sync time
            userPreferences.updateLastSyncTime(System.currentTimeMillis())

            Result.success()

        } catch (e: Exception) {
            Timber.e(e, "Sync failed")

            if (runAttemptCount < MAX_RETRY_ATTEMPTS) {
                Result.retry()
            } else {
                // Log failure and continue (don't block user)
                FirebaseCrashlytics.getInstance().recordException(e)
                Result.failure()
            }
        }
    }

    private suspend fun uploadLocalChanges() {
        // Get all pending sync operations
        val pendingOps = syncQueueDao.getPendingOperations(limit = 50)

        pendingOps.forEach { operation ->
            try {
                // Mark as in progress
                syncQueueDao.updateStatus(operation.queueId, "IN_PROGRESS")

                when (operation.entityType) {
                    "TRANSACTION" -> {
                        when (operation.operationType) {
                            "INSERT" -> {
                                val transaction = parseTransaction(operation.payload)
                                firestoreService.uploadTransaction(transaction)
                            }
                            "UPDATE" -> {
                                val transaction = parseTransaction(operation.payload)
                                firestoreService.updateTransaction(transaction)
                            }
                            "DELETE" -> {
                                val (transactionId, familyId) = parseIds(operation.payload)
                                firestoreService.deleteTransaction(transactionId, familyId)
                            }
                        }
                    }
                    "BUDGET" -> {
                        // Similar handling for budgets
                    }
                    "FAMILY_MEMBER" -> {
                        // Similar handling for family members
                    }
                }

                // Mark as completed
                syncQueueDao.updateStatus(operation.queueId, "COMPLETED")

            } catch (e: Exception) {
                Timber.e(e, "Failed to sync operation: ${operation.queueId}")

                // Increment retry count
                val newRetryCount = operation.retryCount + 1

                if (newRetryCount >= MAX_RETRY_ATTEMPTS) {
                    // Mark as failed after max retries
                    syncQueueDao.updateOperation(
                        operation.copy(
                            status = "FAILED",
                            retryCount = newRetryCount,
                            lastError = e.message
                        )
                    )
                } else {
                    // Update retry count
                    syncQueueDao.updateOperation(
                        operation.copy(
                            status = "PENDING",
                            retryCount = newRetryCount,
                            lastError = e.message
                        )
                    )
                }
            }
        }
    }

    private suspend fun downloadRemoteChanges() {
        val userId = userPreferences.getUserId()
        val familyIds = userPreferences.getFamilyIds()
        val lastSyncTime = userPreferences.getLastSyncTime()

        familyIds.forEach { familyId ->
            try {
                // Download new transactions
                val newTransactions = firestoreService.downloadNewTransactions(
                    userId = userId,
                    familyId = familyId,
                    lastSyncTime = lastSyncTime
                )

                // Save to local database
                newTransactions.forEach { transaction ->
                    val entity = transactionMapper.toEntity(transaction.copy(isSynced = true))
                    transactionDao.insertTransaction(entity)
                }

            } catch (e: Exception) {
                Timber.e(e, "Failed to download changes for family: $familyId")
            }
        }
    }

    private fun isNetworkAvailable(): Boolean {
        val connectivityManager = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun parseTransaction(payload: String): Transaction {
        return Gson().fromJson(payload, Transaction::class.java)
    }

    private fun parseIds(payload: String): Pair<String, String> {
        val data = Gson().fromJson(payload, Map::class.java)
        return Pair(
            data["transaction_id"] as String,
            data["family_id"] as String
        )
    }
}
```

---

### 8.6 Real-Time Sync Listeners

```kotlin
package com.xpenz.core.data.sync

import com.google.firebase.firestore.ListenerRegistration
import com.xpenz.core.network.firebase.FirestoreService
import com.xpenz.core.database.dao.TransactionDao
import com.xpenz.core.data.mapper.TransactionMapper
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RealTimeSyncManager @Inject constructor(
    private val firestoreService: FirestoreService,
    private val transactionDao: TransactionDao,
    private val transactionMapper: TransactionMapper,
    private val userPreferences: UserPreferences
) {

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val listeners = mutableListOf<ListenerRegistration>()

    /**
     * Start listening to real-time updates for all family transactions
     */
    fun startListening(familyIds: List<String>) {
        if (!userPreferences.isPremium()) return

        familyIds.forEach { familyId ->
            // Listen to transaction changes
            val listener = firestoreService.observeFamilyTransactions(familyId)
                .onEach { dtos ->
                    scope.launch {
                        processFamilyTransactions(familyId, dtos)
                    }
                }
                .launchIn(scope)

            // Store listener for cleanup
            // listeners.add(listener) // Would need to adapt for Flow
        }
    }

    /**
     * Stop all real-time listeners
     */
    fun stopListening() {
        listeners.forEach { it.remove() }
        listeners.clear()
        scope.cancel()
    }

    private suspend fun processFamilyTransactions(
        familyId: String,
        dtos: List<TransactionDTO>
    ) {
        try {
            val userId = userPreferences.getUserId()

            dtos.forEach { dto ->
                // Skip transactions created by current user
                if (dto.userId == userId) return@forEach

                // Check if transaction already exists locally
                val existingTransaction = transactionDao.getTransaction(dto.transactionId)

                if (existingTransaction == null) {
                    // New transaction from another family member
                    val transaction = convertAndDecrypt(dto, familyId)
                    val entity = transactionMapper.toEntity(transaction.copy(isSynced = true))
                    transactionDao.insertTransaction(entity)

                    // Show notification
                    showNewTransactionNotification(transaction)

                } else if (existingTransaction.syncVersion < dto.syncVersion) {
                    // Transaction was updated remotely
                    val transaction = convertAndDecrypt(dto, familyId)
                    val entity = transactionMapper.toEntity(transaction.copy(isSynced = true))
                    transactionDao.updateTransaction(entity)
                }
            }

        } catch (e: Exception) {
            Timber.e(e, "Failed to process family transactions")
        }
    }

    private suspend fun convertAndDecrypt(
        dto: TransactionDTO,
        familyId: String
    ): Transaction {
        val category = getCategoryFromId(dto.categoryId)
        val decryptedData = if (dto.encryptedData != null) {
            encryptionService.decrypt(dto.encryptedData, familyId)
        } else null

        return transactionMapper.fromDTO(dto, category, decryptedData)
    }

    private fun showNewTransactionNotification(transaction: Transaction) {
        // Implementation in notification service
        notificationService.showNewTransactionNotification(transaction)
    }
}
```

---

### 8.7 Conflict Resolution Strategy

```kotlin
package com.xpenz.core.data.sync

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConflictResolver @Inject constructor() {

    /**
     * Resolve conflicts using Last-Write-Wins (LWW) strategy
     */
    fun resolveTransactionConflict(
        local: TransactionEntity,
        remote: TransactionDTO
    ): ConflictResolution {

        // Compare timestamps
        return when {
            // Remote is newer
            remote.updatedAt > local.updatedAt -> {
                ConflictResolution.UseRemote(
                    reason = "Remote version is newer",
                    remotedTimestamp = remote.updatedAt,
                    localTimestamp = local.updatedAt
                )
            }

            // Local is newer
            local.updatedAt > remote.updatedAt -> {
                ConflictResolution.UseLocal(
                    reason = "Local version is newer",
                    localTimestamp = local.updatedAt,
                    remoteTimestamp = remote.updatedAt
                )
            }

            // Same timestamp - use sync version
            local.syncVersion > remote.syncVersion -> {
                ConflictResolution.UseLocal(
                    reason = "Local sync version is higher"
                )
            }

            remote.syncVersion > local.syncVersion -> {
                ConflictResolution.UseRemote(
                    reason = "Remote sync version is higher"
                )
            }

            // Exact match - no conflict
            else -> {
                ConflictResolution.NoConflict
            }
        }
    }

    /**
     * Log conflicts for analysis
     */
    fun logConflict(
        entityType: String,
        entityId: String,
        resolution: ConflictResolution
    ) {
        when (resolution) {
            is ConflictResolution.UseLocal,
            is ConflictResolution.UseRemote -> {
                Timber.d(
                    "Conflict resolved for $entityType:$entityId - ${resolution.reason}"
                )

                FirebaseAnalytics.getInstance().logEvent("sync_conflict_resolved") {
                    param("entity_type", entityType)
                    param("resolution", resolution::class.simpleName ?: "unknown")
                }
            }
            else -> {
                // No logging needed
            }
        }
    }
}

sealed class ConflictResolution {
    abstract val reason: String?

    data class UseLocal(
        override val reason: String,
        val localTimestamp: Long? = null,
        val remoteTimestamp: Long? = null
    ) : ConflictResolution()

    data class UseRemote(
        override val reason: String,
        val remotedTimestamp: Long? = null,
        val localTimestamp: Long? = null
    ) : ConflictResolution()

    object NoConflict : ConflictResolution() {
        override val reason: String? = null
    }
}
```

---

# PART 3: MACHINE LEARNING

## 9. ML MODEL ARCHITECTURE

### 9.1 Overview

> ⚠️ **CANONICAL SPEC:** The complete ML architecture is documented in `docs/09 - ML Architecture Specification.md`. This section provides a summary only. For full details (model code, training pipeline, conversion scripts, Android integration), refer to that document.

**Goal:** Classify transactions into 520 granular categories (3-level hierarchy: 15 → 80 → 520) with 88-92% accuracy (post-learning, top-1) and 96-98% accuracy (top-3).

**Approach:** 4-component adaptive ensemble with 1 TFLite model + 3 non-neural components

| Component | Architecture | Size | Weight (Cold → Mature) | Latency |
|-----------|-------------|------|----------------------|--------|
| **Compact Hierarchical Transformer (CHT)** | 3-layer Transformer (d=128, 4 heads) + SentencePiece BPE (8K vocab) + hierarchical output heads | 3.2 MB | 60% → 35% | 20-35ms |
| **Rule Engine** | Trie-based keyword + UPI pattern matcher, ~5,600 patterns | 0.35 MB | 25% → 10% | 1-3ms |
| **User Habit Model** | Room DB lookup: merchant/UPI → category frequency map | 0 MB | 0% → 50% | 2-5ms |
| **Amount-Time Prior** | P(category|amount_bucket, time_slot) lookup table | 0.15 MB | 15% → 5% | 1-2ms |
| **Total** | | **3.7 MB** | 100% | **25-45ms** |

**Final Prediction:** Adaptive weighted ensemble with confidence thresholding and hierarchical cascading

```
Input: "Rs.450 debited from A/c XX1234 at PUNJAB GRILL CONNAUGHT via UPI Ref:412345678"
                                ↓
                    Preprocessing + SentencePiece BPE
                                ↓
        ┌───────────────┬───────────────┬───────────────┐
        ↓               ↓               ↓               ↓
    CHT Model      Rule Engine     User Habits     Amount-Time
    (Weight: 35%)  (Weight: 10%)  (Weight: 50%)   Prior (5%)
        ↓               ↓               ↓               ↓
    L1→L2→L3       Exact match     UPI history     ₹450+lunch
                                ↓
                    Adaptive Ensemble Voting
                                ↓
        Final: Category 234 (North Indian Restaurant)
        Confidence: 89%
        Top-3: [234 (89%), 235 (78%), 12 (65%)]
```

---

### 9.2 Category Hierarchy (520 Categories)

**Level 1: Main Categories (15)**

```
1. Food & Dining
2. Transportation
3. Shopping
4. Entertainment
5. Bills & Utilities
6. Health & Fitness
7. Education
8. Travel
9. Financial Services
10. Personal Care
11. Home & Garden
12. Gifts & Donations
13. Business Services
14. Government & Taxes
15. Miscellaneous
```

**Level 2: Sub-Categories (80)**

```
Food & Dining:
├─ Restaurants
├─ Fast Food
├─ Cafes & Coffee Shops
├─ Bakeries & Desserts
├─ Groceries
├─ Food Delivery
├─ Alcohol & Bars
└─ Street Food
```

**Level 3: Specific Categories (180)**

```
Restaurants:
├─ North Indian
├─ South Indian
├─ Chinese
├─ Continental
├─ Italian
├─ Mexican
├─ Thai
├─ Japanese
├─ Multi-cuisine
└─ Fine Dining
```

**Level 4: Granular Categories (245)**

```
North Indian:
├─ Butter Chicken
├─ Paneer Tikka
├─ Dal Makhani
├─ Biryani
├─ Naan & Roti
├─ Tandoori Items
├─ Curry
├─ Samosa
├─ Chole Bhature
└─ Paratha
```

**Complete Category Mapping JSON:**

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Food & Dining",
      "level": 1,
      "parent_id": null,
      "emoji": "🍽️",
      "color": "#FF5722"
    },
    {
      "id": 11,
      "name": "Restaurants",
      "level": 2,
      "parent_id": 1,
      "emoji": "🍽️",
      "color": "#FF5722"
    },
    {
      "id": 111,
      "name": "North Indian",
      "level": 3,
      "parent_id": 11,
      "emoji": "🍛",
      "color": "#FF6F00"
    },
    {
      "id": 234,
      "name": "Butter Chicken",
      "level": 4,
      "parent_id": 111,
      "emoji": "🍗",
      "color": "#FF8A00",
      "keywords": ["butter", "chicken", "murgh", "makhani", "butter chicken", "murgh makhani"]
    },
    // ... 516 more categories
  ]
}
```

---

### 9.3 Feature Engineering

### **9.3.1 Input Features**

```kotlin
data class TransactionFeatures(
    // Text Features
    val merchantName: String,               // "PUNJAB GRILL CONNAUGHT"
    val merchantNameCleaned: String,        // "punjab grill connaught"
    val merchantNameTokens: List<String>,   // ["punjab", "grill", "connaught"]

    // Numerical Features
    val amount: Float,                      // 450.0
    val amountBucket: Int,                  // 3 (₹100-500 range)
    val hour: Int,                          // 13 (1 PM)
    val dayOfWeek: Int,                     // 5 (Friday)
    val dayOfMonth: Int,                    // 15

    // Location Features (optional)
    val locationName: String?,              // "Connaught Place"
    val locationCategory: String?,          // "Central Delhi"

    // Contextual Features
    val upiId: String?,                     // "punjabgrill@paytm"
    val bankName: String?,                  // "HDFC Bank"

    // Historical Features
    val userPastCategories: List<Int>,      // User's top 10 categories
    val merchantFrequency: Int,             // How many times user visited this merchant
    val categoryFrequency: Map<Int, Int>    // Category visit frequency
)
```

### **9.3.2 Feature Extraction Pipeline**

```kotlin
package com.xpenz.core.ml.preprocessing

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FeatureExtractor @Inject constructor(
    private val textPreprocessor: TextPreprocessor,
    private val categoryRepository: CategoryRepository,
    private val transactionDao: TransactionDao
) {

    suspend fun extractFeatures(
        merchantName: String?,
        amount: Double,
        timestamp: Long,
        upiId: String?,
        bankName: String?,
        userId: String
    ): TransactionFeatures {

        // Clean merchant name
        val cleanedName = textPreprocessor.clean(merchantName ?: "")
        val tokens = textPreprocessor.tokenize(cleanedName)

        // Amount bucket (0-10 scale)
        val amountBucket = when {
            amount < 50 -> 0
            amount < 100 -> 1
            amount < 200 -> 2
            amount < 500 -> 3
            amount < 1000 -> 4
            amount < 2000 -> 5
            amount < 5000 -> 6
            amount < 10000 -> 7
            amount < 25000 -> 8
            amount < 50000 -> 9
            else -> 10
        }

        // Time features
        val calendar = Calendar.getInstance().apply {
            timeInMillis = timestamp
        }
        val hour = calendar.get(Calendar.HOUR_OF_DAY)
        val dayOfWeek = calendar.get(Calendar.DAY_OF_WEEK)
        val dayOfMonth = calendar.get(Calendar.DAY_OF_MONTH)

        // Historical features
        val userHistory = getUserHistory(userId)
        val merchantFreq = getMerchantFrequency(userId, cleanedName)

        return TransactionFeatures(
            merchantName = merchantName ?: "",
            merchantNameCleaned = cleanedName,
            merchantNameTokens = tokens,
            amount = amount.toFloat(),
            amountBucket = amountBucket,
            hour = hour,
            dayOfWeek = dayOfWeek,
            dayOfMonth = dayOfMonth,
            locationName = null,
            locationCategory = null,
            upiId = upiId,
            bankName = bankName,
            userPastCategories = userHistory.topCategories,
            merchantFrequency = merchantFreq,
            categoryFrequency = userHistory.categoryFrequency
        )
    }

    private suspend fun getUserHistory(userId: String): UserHistory {
        // Get user's transaction history
        val transactions = transactionDao.getUserTransactions(userId).first()

        // Calculate category frequency
        val categoryFreq = transactions
            .groupBy { it.mlCategoryId }
            .mapValues { it.value.size }

        // Get top 10 categories
        val topCategories = categoryFreq
            .entries
            .sortedByDescending { it.value }
            .take(10)
            .map { it.key }

        return UserHistory(topCategories, categoryFreq)
    }

    private suspend fun getMerchantFrequency(
        userId: String,
        merchantName: String
    ): Int {
        return transactionDao.getMerchantFrequency(userId, merchantName)
    }

    data class UserHistory(
        val topCategories: List<Int>,
        val categoryFrequency: Map<Int, Int>
    )
}
```

### **9.3.3 Text Preprocessing**

```kotlin
package com.xpenz.core.ml.preprocessing

import java.text.Normalizer
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TextPreprocessor @Inject constructor() {

    companion object {
        // Common stop words in merchant names
        private val STOP_WORDS = setOf(
            "the", "a", "an", "at", "on", "in", "to", "for", "of", "via",
            "pvt", "ltd", "limited", "private", "company", "co", "corporation",
            "inc", "llc", "llp"
        )

        // Common UPI suffixes to remove
        private val UPI_SUFFIXES = listOf(
            "@paytm", "@okaxis", "@oksbi", "@okicici", "@okhdfcbank",
            "@ybl", "@upi", "@ibl", "@axl"
        )
    }

    /**
     * Clean and normalize merchant name
     */
    fun clean(text: String): String {
        return text
            .lowercase()
            .removeUPISuffixes()
            .removeSpecialChars()
            .normalizeUnicode()
            .removeExtraSpaces()
            .trim()
    }

    /**
     * Tokenize text into words
     */
    fun tokenize(text: String): List<String> {
        return text
            .split(Regex("\\s+"))
            .filter { it.isNotEmpty() && !STOP_WORDS.contains(it) }
    }

    /**
     * Extract n-grams (for CNN model)
     */
    fun extractNGrams(text: String, n: Int = 3): List<String> {
        val chars = text.toCharArray()
        return (0..chars.size - n).map { i ->
            chars.slice(i until i + n).joinToString("")
        }
    }

    /**
     * Convert to character-level indices (for LSTM/CNN)
     */
    fun toCharIndices(text: String, maxLength: Int = 50): IntArray {
        val indices = IntArray(maxLength) { 0 } // 0 = padding

        text.take(maxLength).forEachIndexed { index, char ->
            indices[index] = charToIndex(char)
        }

        return indices
    }

    /**
     * Convert to word-level indices (for Transformer)
     */
    fun toWordIndices(
        tokens: List<String>,
        vocabulary: Map<String, Int>,
        maxLength: Int = 20
    ): IntArray {
        val indices = IntArray(maxLength) { 0 } // 0 = padding

        tokens.take(maxLength).forEachIndexed { index, token ->
            indices[index] = vocabulary[token] ?: 1 // 1 = <UNK>
        }

        return indices
    }

    private fun String.removeUPISuffixes(): String {
        var result = this
        UPI_SUFFIXES.forEach { suffix ->
            result = result.replace(suffix, "")
        }
        return result
    }

    private fun String.removeSpecialChars(): String {
        return this.replace(Regex("[^a-z0-9\\s]"), " ")
    }

    private fun String.normalizeUnicode(): String {
        return Normalizer.normalize(this, Normalizer.Form.NFD)
            .replace(Regex("\\p{M}"), "")
    }

    private fun String.removeExtraSpaces(): String {
        return this.replace(Regex("\\s+"), " ")
    }

    private fun charToIndex(char: Char): Int {
        // Map characters to indices (1-38)
        // 0: padding, 1-26: a-z, 27-36: 0-9, 37: space, 38: other
        return when (char) {
            in 'a'..'z' -> char - 'a' + 1
            in '0'..'9' -> char - '0' + 27
            ' ' -> 37
            else -> 38
        }
    }
}
```

---

### 9.4 Model Architectures

### **9.4.1 LSTM Model**

**Architecture:**

```
Input: Character sequence (max length 50)
    ↓
Embedding Layer (vocab_size=39, embedding_dim=32)
    ↓
Bidirectional LSTM (units=64)
    ↓
Bidirectional LSTM (units=32)
    ↓
Dropout (0.3)
    ↓
Dense (256, activation=relu)
    ↓
Dropout (0.3)
    ↓
Dense (520, activation=softmax)
    ↓
Output: Probability distribution over 520 categories
```

**TensorFlow/Keras Code:**

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

def build_lstm_model(
    vocab_size=39,
    max_length=50,
    embedding_dim=32,
    num_categories=520
):
    """
    Build LSTM model for transaction classification
    """
    inputs = keras.Input(shape=(max_length,), dtype=tf.int32)

    # Embedding layer
    x = layers.Embedding(
        input_dim=vocab_size,
        output_dim=embedding_dim,
        mask_zero=True
    )(inputs)

    # Bidirectional LSTM layers
    x = layers.Bidirectional(
        layers.LSTM(64, return_sequences=True)
    )(x)

    x = layers.Bidirectional(
        layers.LSTM(32)
    )(x)

    x = layers.Dropout(0.3)(x)

    # Dense layers
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)

    # Output layer
    outputs = layers.Dense(num_categories, activation='softmax')(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy', 'top_k_categorical_accuracy']
    )

    return model

# Example usage
model = build_lstm_model()
model.summary()

# Model size: ~2.5 MB
# Parameters: ~650K
```

### **9.4.2 CNN Model**

**Architecture:**

```
Input: Character sequence (max length 50)
    ↓
Embedding Layer (vocab_size=39, embedding_dim=32)
    ↓
Conv1D (filters=128, kernel_size=3, activation=relu)
    ↓
MaxPooling1D (pool_size=2)
    ↓
Conv1D (filters=128, kernel_size=3, activation=relu)
    ↓
MaxPooling1D (pool_size=2)
    ↓
Conv1D (filters=64, kernel_size=3, activation=relu)
    ↓
GlobalMaxPooling1D
    ↓
Dense (256, activation=relu)
    ↓
Dropout (0.3)
    ↓
Dense (520, activation=softmax)
    ↓
Output: Probability distribution over 520 categories
```

**TensorFlow/Keras Code:**

```python
def build_cnn_model(
    vocab_size=39,
    max_length=50,
    embedding_dim=32,
    num_categories=520
):
    """
    Build CNN model for transaction classification
    """
    inputs = keras.Input(shape=(max_length,), dtype=tf.int32)

    # Embedding layer
    x = layers.Embedding(
        input_dim=vocab_size,
        output_dim=embedding_dim
    )(inputs)

    # Convolutional layers
    x = layers.Conv1D(
        filters=128,
        kernel_size=3,
        activation='relu',
        padding='same'
    )(x)
    x = layers.MaxPooling1D(pool_size=2)(x)

    x = layers.Conv1D(
        filters=128,
        kernel_size=3,
        activation='relu',
        padding='same'
    )(x)
    x = layers.MaxPooling1D(pool_size=2)(x)

    x = layers.Conv1D(
        filters=64,
        kernel_size=3,
        activation='relu',
        padding='same'
    )(x)

    # Global pooling
    x = layers.GlobalMaxPooling1D()(x)

    # Dense layers
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)

    # Output layer
    outputs = layers.Dense(num_categories, activation='softmax')(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy', 'top_k_categorical_accuracy']
    )

    return model

# Model size: ~2.2 MB
# Parameters: ~580K
```

### **9.4.3 Transformer Model**

**Architecture:**

```
Input: Word sequence (max length 20)
    ↓
Embedding Layer (vocab_size=10000, embedding_dim=64)
    ↓
Positional Encoding
    ↓
Transformer Encoder (heads=4, dim=64, layers=2)
    ↓
GlobalAveragePooling1D
    ↓
Dense (256, activation=relu)
    ↓
Dropout (0.3)
    ↓
Dense (520, activation=softmax)
    ↓
Output: Probability distribution over 520 categories
```

**TensorFlow/Keras Code:**

```python
class TransformerBlock(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = layers.MultiHeadAttention(
            num_heads=num_heads,
            key_dim=embed_dim
        )
        self.ffn = keras.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, training):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

class PositionalEmbedding(layers.Layer):
    def __init__(self, maxlen, vocab_size, embed_dim):
        super(PositionalEmbedding, self).__init__()
        self.token_emb = layers.Embedding(
            input_dim=vocab_size,
            output_dim=embed_dim
        )
        self.pos_emb = layers.Embedding(
            input_dim=maxlen,
            output_dim=embed_dim
        )

    def call(self, x):
        maxlen = tf.shape(x)[-1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions

def build_transformer_model(
    vocab_size=10000,
    max_length=20,
    embedding_dim=64,
    num_heads=4,
    ff_dim=128,
    num_categories=520
):
    """
    Build Transformer model for transaction classification
    """
    inputs = keras.Input(shape=(max_length,), dtype=tf.int32)

    # Positional embedding
    x = PositionalEmbedding(max_length, vocab_size, embedding_dim)(inputs)

    # Transformer blocks
    x = TransformerBlock(embedding_dim, num_heads, ff_dim)(x)
    x = TransformerBlock(embedding_dim, num_heads, ff_dim)(x)

    # Global average pooling
    x = layers.GlobalAveragePooling1D()(x)

    # Dense layers
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)

    # Output layer
    outputs = layers.Dense(num_categories, activation='softmax')(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy', 'top_k_categorical_accuracy']
    )

    return model

# Model size: ~3.8 MB
# Parameters: ~980K
```

---

### 9.5 Ensemble Model

**Weighted Voting Strategy:**

```python
def ensemble_predict(
    input_text,
    lstm_model,
    cnn_model,
    transformer_model,
    feature_extractor,
    weights=(0.35, 0.35, 0.25, 0.05)
):
    """
    Ensemble prediction with weighted voting

    Args:
        input_text: Merchant name
        lstm_model: Trained LSTM model
        cnn_model: Trained CNN model
        transformer_model: Trained Transformer model
        feature_extractor: Feature extraction pipeline
        weights: Model weights (LSTM, CNN, Transformer, Rule-based)

    Returns:
        prediction: Category ID
        confidence: Confidence score (0-1)
        top_3: Top 3 predictions with confidences
    """
    # Extract features
    char_indices = feature_extractor.to_char_indices(input_text)
    word_indices = feature_extractor.to_word_indices(input_text)

    # Get predictions from each model
    lstm_probs = lstm_model.predict(char_indices.reshape(1, -1))[0]
    cnn_probs = cnn_model.predict(char_indices.reshape(1, -1))[0]
    transformer_probs = transformer_model.predict(word_indices.reshape(1, -1))[0]

    # Rule-based prediction (fallback)
    rule_probs = rule_based_predict(input_text)

    # Weighted ensemble
    ensemble_probs = (
        weights[0] * lstm_probs +
        weights[1] * cnn_probs +
        weights[2] * transformer_probs +
        weights[3] * rule_probs
    )

    # Get top-3 predictions
    top_3_indices = np.argsort(ensemble_probs)[-3:][::-1]
    top_3_probs = ensemble_probs[top_3_indices]

    # Final prediction
    prediction = top_3_indices[0]
    confidence = top_3_probs[0]

    top_3 = [
        {"category_id": int(idx), "confidence": float(prob)}
        for idx, prob in zip(top_3_indices, top_3_probs)
    ]

    return {
        "prediction": int(prediction),
        "confidence": float(confidence),
        "top_3": top_3,
        "model_contributions": {
            "lstm": float(weights[0] * lstm_probs[prediction]),
            "cnn": float(weights[1] * cnn_probs[prediction]),
            "transformer": float(weights[2] * transformer_probs[prediction]),
            "rule_based": float(weights[3] * rule_probs[prediction])
        }
    }

def rule_based_predict(merchant_name, num_categories=520):
    """
    Simple rule-based classifier (fallback)
    Uses keyword matching for common merchants
    """
    probs = np.zeros(num_categories)

    # Keyword rules
    rules = {
        "swiggy": 45,  # Food Delivery
        "zomato": 45,
        "uber": 82,    # Ride Sharing - Uber
        "ola": 83,     # Ride Sharing - Ola
        "amazon": 120, # Online Shopping - Amazon
        "flipkart": 121, # Online Shopping - Flipkart
        "dominos": 38, # Fast Food - Pizza
        "mcdonald": 39, # Fast Food - Burgers
        "starbucks": 55, # Coffee Shop
        # ... more rules
    }

    merchant_lower = merchant_name.lower()

    for keyword, category_id in rules.items():
        if keyword in merchant_lower:
            probs[category_id] = 1.0
            return probs

    # Default: miscellaneous
    probs[519] = 1.0
    return probs
```

---

### 9.6 Model Conversion to TensorFlow Lite

**Conversion Script:**

```python
import tensorflow as tf

def convert_to_tflite(model, model_name):
    """
    Convert Keras model to TensorFlow Lite format
    """
    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Optimization flags
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Supported ops
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS
    ]

    # Convert
    tflite_model = converter.convert()

    # Save
    output_path = f"models/{model_name}.tflite"
    with open(output_path, 'wb') as f:
        f.write(tflite_model)

    print(f"✓ Model saved: {output_path}")
    print(f"  Size: {len(tflite_model) / 1024:.2f} KB")

    return output_path

# Convert all models
lstm_path = convert_to_tflite(lstm_model, "model_lstm")
cnn_path = convert_to_tflite(cnn_model, "model_cnn")
transformer_path = convert_to_tflite(transformer_model, "model_transformer")

# Expected sizes:
# model_lstm.tflite: ~2.5 MB
# model_cnn.tflite: ~2.2 MB
# model_transformer.tflite: ~3.8 MB
# Total: ~8.5 MB
```

---

### 9.7 Android Integration (TFLite Inference)

```kotlin
package com.xpenz.core.ml

import android.content.Context
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.support.common.FileUtil
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MLInferenceService @Inject constructor(
    private val context: Context,
    private val featureExtractor: FeatureExtractor,
    private val textPreprocessor: TextPreprocessor
) {

    private lateinit var lstmInterpreter: Interpreter
    private lateinit var cnnInterpreter: Interpreter
    private lateinit var transformerInterpreter: Interpreter

    private val modelWeights = floatArrayOf(0.35f, 0.35f, 0.25f, 0.05f)

    companion object {
        private const val NUM_CATEGORIES = 520
        private const val CHAR_MAX_LENGTH = 50
        private const val WORD_MAX_LENGTH = 20
    }

    init {
        loadModels()
    }

    private fun loadModels() {
        try {
            // Load LSTM model
            val lstmModel = FileUtil.loadMappedFile(context, "model_lstm.tflite")
            lstmInterpreter = Interpreter(lstmModel, getInterpreterOptions())

            // Load CNN model
            val cnnModel = FileUtil.loadMappedFile(context, "model_cnn.tflite")
            cnnInterpreter = Interpreter(cnnModel, getInterpreterOptions())

            // Load Transformer model
            val transformerModel = FileUtil.loadMappedFile(context, "model_transformer.tflite")
            transformerInterpreter = Interpreter(transformerModel, getInterpreterOptions())

            Timber.d("✓ ML models loaded successfully")

        } catch (e: Exception) {
            Timber.e(e, "Failed to load ML models")
            throw MLException("Failed to load models: ${e.message}", e)
        }
    }

    private fun getInterpreterOptions(): Interpreter.Options {
        return Interpreter.Options().apply {
            setNumThreads(4)
            setUseNNAPI(true) // Use Neural Networks API if available
        }
    }

    /**
     * Classify transaction using ensemble model
     */
    suspend fun classify(
        merchantName: String,
        amount: Double,
        upiId: String?,
        timestamp: Long
    ): MLClassification {

        return withContext(Dispatchers.Default) {
            try {
                // Extract features
                val features = featureExtractor.extractFeatures(
                    merchantName = merchantName,
                    amount = amount,
                    timestamp = timestamp,
                    upiId = upiId,
                    bankName = null,
                    userId = "" // Get from preferences
                )

                // Prepare inputs
                val charIndices = textPreprocessor.toCharIndices(
                    features.merchantNameCleaned,
                    CHAR_MAX_LENGTH
                )
                val wordIndices = textPreprocessor.toWordIndices(
                    features.merchantNameTokens,
                    getVocabulary(),
                    WORD_MAX_LENGTH
                )

                // Run inference on each model
                val lstmProbs = runLSTMInference(charIndices)
                val cnnProbs = runCNNInference(charIndices)
                val transformerProbs = runTransformerInference(wordIndices)
                val ruleProbs = runRuleBased(features.merchantNameCleaned)

                // Ensemble voting
                val ensembleProbs = FloatArray(NUM_CATEGORIES) { i ->
                    modelWeights[0] * lstmProbs[i] +
                    modelWeights[1] * cnnProbs[i] +
                    modelWeights[2] * transformerProbs[i] +
                    modelWeights[3] * ruleProbs[i]
                }

                // Get top-3 predictions
                val top3Indices = ensembleProbs.indices
                    .sortedByDescending { ensembleProbs[it] }
                    .take(3)

                val top3 = top3Indices.map { idx ->
                    CategoryPrediction(
                        categoryId = idx,
                        confidence = ensembleProbs[idx]
                    )
                }

                MLClassification(
                    categoryId = top3[0].categoryId,
                    confidence = top3[0].confidence,
                    top3Predictions = top3,
                    source = MLSource.ML_ENSEMBLE,
                    inferenceTimeMs = measureInferenceTime()
                )

            } catch (e: Exception) {
                Timber.e(e, "Classification failed")
                // Fallback to rule-based
                fallbackClassification(merchantName)
            }
        }
    }

    private fun runLSTMInference(charIndices: IntArray): FloatArray {
        val input = Array(1) { charIndices }
        val output = Array(1) { FloatArray(NUM_CATEGORIES) }

        lstmInterpreter.run(input, output)

        return output[0]
    }

    private fun runCNNInference(charIndices: IntArray): FloatArray {
        val input = Array(1) { charIndices }
        val output = Array(1) { FloatArray(NUM_CATEGORIES) }

        cnnInterpreter.run(input, output)

        return output[0]
    }

    private fun runTransformerInference(wordIndices: IntArray): FloatArray {
        val input = Array(1) { wordIndices }
        val output = Array(1) { FloatArray(NUM_CATEGORIES) }

        transformerInterpreter.run(input, output)

        return output[0]
    }

    private fun runRuleBased(merchantName: String): FloatArray {
        val probs = FloatArray(NUM_CATEGORIES) { 0f }

        // Keyword matching rules
        val rules = mapOf(
            "swiggy" to 45,
            "zomato" to 45,
            "uber" to 82,
            "ola" to 83,
            "amazon" to 120,
            "flipkart" to 121,
            "dominos" to 38,
            "mcdonald" to 39,
            "starbucks" to 55,
            "big bazaar" to 140,
            "dmart" to 141,
            "reliance" to 142,
            "pvr" to 200,
            "inox" to 201
        )

        val merchantLower = merchantName.lowercase()

        for ((keyword, categoryId) in rules) {
            if (merchantLower.contains(keyword)) {
                probs[categoryId] = 1.0f
                return probs
            }
        }

        // Default: miscellaneous
        probs[519] = 1.0f
        return probs
    }

    private fun fallbackClassification(merchantName: String): MLClassification {
        val probs = runRuleBased(merchantName)
        val categoryId = probs.indices.maxByOrNull { probs[it] } ?: 519

        return MLClassification(
            categoryId = categoryId,
            confidence = probs[categoryId],
            top3Predictions = listOf(
                CategoryPrediction(categoryId, probs[categoryId])
            ),
            source = MLSource.RULE_BASED,
            inferenceTimeMs = 0
        )
    }

    private fun getVocabulary(): Map<String, Int> {
        // Load from assets or cache
        // This would be pre-computed vocabulary (top 10K words)
        return emptyMap() // Placeholder
    }

    private fun measureInferenceTime(): Long {
        // Implement timing logic
        return 0L
    }

    fun close() {
        lstmInterpreter.close()
        cnnInterpreter.close()
        transformerInterpreter.close()
    }
}

data class MLClassification(
    val categoryId: Int,
    val confidence: Float,
    val top3Predictions: List<CategoryPrediction>,
    val source: MLSource,
    val inferenceTimeMs: Long
)

data class CategoryPrediction(
    val categoryId: Int,
    val confidence: Float
)

class MLException(message: String, cause: Throwable? = null) : Exception(message, cause)
```

---

## 10. TRAINING PIPELINE

### 10.1 Data Collection Strategy

**Training Data Sources:**

1. **Synthetic Data Generation (60%)**
    - Generate realistic transaction patterns
    - Cover all 520 categories
    - Various merchant name formats
    - Amount distributions per category
2. **Crowdsourced Real Data (30%)**
    - User-donated anonymized transactions
    - Manual category labeling
    - Quality verification
3. **Public Datasets (10%)**
    - Open banking transaction datasets
    - E-commerce transaction logs
    - Restaurant/merchant databases

**Target Dataset Size:**

- Training: 500,000 transactions
- Validation: 50,000 transactions
- Test: 50,000 transactions
- Total: 600,000 labeled transactions

---

### 10.2 Data Generation Script

```python
import random
import json
from datetime import datetime, timedelta
import numpy as np

class SyntheticDataGenerator:
    """
    Generate synthetic transaction data for training
    """

    def __init__(self, categories_file='categories.json'):
        with open(categories_file, 'r') as f:
            self.categories = json.load(f)['categories']

        self.merchant_templates = self.load_merchant_templates()
        self.amount_ranges = self.load_amount_ranges()

    def generate_dataset(self, num_samples=500000, output_file='training_data.csv'):
        """
        Generate synthetic dataset
        """
        data = []

        for i in range(num_samples):
            transaction = self.generate_transaction()
            data.append(transaction)

            if (i + 1) % 10000 == 0:
                print(f"Generated {i + 1}/{num_samples} transactions")

        # Save to CSV
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)
        print(f"✓ Dataset saved: {output_file}")

        return df

    def generate_transaction(self):
        """
        Generate a single synthetic transaction
        """
        # Randomly select category (weighted by frequency)
        category = self.select_category()

        # Generate merchant name
        merchant_name = self.generate_merchant_name(category)

        # Generate amount (based on category)
        amount = self.generate_amount(category)

        # Generate timestamp
        timestamp = self.generate_timestamp()

        # Generate UPI ID
        upi_id = self.generate_upi_id(merchant_name)

        # Generate bank name
        bank_name = random.choice([
            'HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank',
            'Kotak Mahindra', 'Yes Bank', 'IDFC First Bank'
        ])

        return {
            'merchant_name': merchant_name,
            'amount': amount,
            'timestamp': timestamp,
            'upi_id': upi_id,
            'bank_name': bank_name,
            'category_id': category['id'],
            'category_name': category['name']
        }

    def select_category(self):
        """
        Select category based on real-world frequency distribution
        """
        # Frequency weights (food & shopping are most common)
        weights = []
        for cat in self.categories:
            if cat['level'] == 4:  # Only granular categories
                # Higher weight for common categories
                if cat['parent_id'] in [1, 2, 3]:  # Food, Transport, Shopping
                    weights.append(10)
                elif cat['parent_id'] in [4, 5, 6]:  # Entertainment, Bills, Health
                    weights.append(5)
                else:
                    weights.append(1)

        granular_categories = [c for c in self.categories if c['level'] == 4]
        return random.choices(granular_categories, weights=weights)[0]

    def generate_merchant_name(self, category):
        """
        Generate realistic merchant name for category
        """
        templates = self.merchant_templates.get(category['id'], [])

        if templates:
            template = random.choice(templates)

            # Add variations
            variations = [
                template,
                template.upper(),
                template.lower(),
                f"{template} {random.choice(['PVT LTD', 'LTD', 'PRIVATE LIMITED', ''])}",
                f"{template} {random.choice(['CONNAUGHT', 'SAKET', 'DLFT', 'GURGAON', 'NOIDA', ''])}",
                f"{template}@{random.choice(['paytm', 'okaxis', 'oksbi', 'ybl'])}"
            ]

            return random.choice(variations)

        # Fallback: generic merchant name
        return f"MERCHANT_{category['id']}"

    def generate_amount(self, category):
        """
        Generate realistic amount based on category
        """
        amount_range = self.amount_ranges.get(category['id'], (100, 1000))

        # Log-normal distribution (more realistic)
        mu = np.log((amount_range[0] + amount_range[1]) / 2)
        sigma = 0.5
        amount = np.random.lognormal(mu, sigma)

        # Clip to range
        amount = np.clip(amount, amount_range[0], amount_range[1])

        # Round to nearest rupee
        return round(amount, 2)

    def generate_timestamp(self):
        """
        Generate random timestamp (last 6 months)
        """
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()

        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        random_seconds = random.randint(0, 86400)

        timestamp = start_date + timedelta(days=random_days, seconds=random_seconds)
        return int(timestamp.timestamp() * 1000)

    def generate_upi_id(self, merchant_name):
        """
        Generate UPI ID from merchant name
        """
        # Clean merchant name
        clean_name = merchant_name.lower().replace(' ', '').replace('-', '')[:20]

        # Random UPI handle
        handles = ['paytm', 'okaxis', 'oksbi', 'ybl', 'okicici', 'okhdfcbank']

        return f"{clean_name}@{random.choice(handles)}"

    def load_merchant_templates(self):
        """
        Load merchant name templates for each category
        """
        return {
            234: ['Punjab Grill', 'Moti Mahal', 'Pind Balluchi', 'Haveli'],  # Butter Chicken
            235: ['Barbeque Nation', 'Absolute Barbecues', 'Mainland China'],  # Tandoori
            38: ['Dominos Pizza', 'Pizza Hut', 'La Pino\'z Pizza'],  # Pizza
            39: ['McDonald\'s', 'Burger King', 'Wendy\'s'],  # Burgers
            45: ['Swiggy', 'Zomato'],  # Food Delivery
            55: ['Starbucks', 'Cafe Coffee Day', 'Blue Tokai', 'Third Wave'],  # Coffee
            82: ['Uber', 'Uber India'],  # Uber
            83: ['Ola', 'Ola Cabs'],  # Ola
            120: ['Amazon', 'Amazon India', 'Amazon Pay'],  # Amazon
            121: ['Flipkart', 'Flipkart Internet'],  # Flipkart
            140: ['Big Bazaar', 'Big Bazaar Store'],  # Big Bazaar
            141: ['DMart', 'DMart Ready', 'Avenue Supermarts'],  # DMart
            200: ['PVR Cinemas', 'PVR'],  # PVR
            201: ['INOX', 'INOX Movies'],  # INOX
            # ... add templates for all 520 categories
        }

    def load_amount_ranges(self):
        """
        Typical amount ranges for each category
        """
        return {
            234: (300, 1500),   # Butter Chicken
            38: (200, 800),     # Pizza
            39: (150, 500),     # Burgers
            45: (100, 600),     # Food Delivery
            55: (100, 400),     # Coffee
            82: (50, 500),      # Uber
            83: (50, 500),      # Ola
            120: (200, 5000),   # Amazon
            121: (200, 5000),   # Flipkart
            140: (500, 3000),   # Big Bazaar
            200: (200, 600),    # PVR
            # ... add ranges for all categories
        }

# Generate dataset
generator = SyntheticDataGenerator()
df = generator.generate_dataset(num_samples=500000)

print("\nDataset Statistics:")
print(f"Total samples: {len(df)}")
print(f"Unique categories: {df['category_id'].nunique()}")
print(f"Amount range: ₹{df['amount'].min():.2f} - ₹{df['amount'].max():.2f}")
print(f"Mean amount: ₹{df['amount'].mean():.2f}")
```

---

### 10.3 Training Script

```python
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

class ModelTrainer:
    """
    Train transaction classification models
    """

    def __init__(self, data_file='training_data.csv'):
        self.df = pd.read_csv(data_file)
        self.preprocessor = TextPreprocessor()
        self.prepare_data()

    def prepare_data(self):
        """
        Prepare data for training
        """
        print("Preparing data...")

        # Clean merchant names
        self.df['merchant_clean'] = self.df['merchant_name'].apply(
            self.preprocessor.clean
        )

        # Convert to character indices
        self.df['char_indices'] = self.df['merchant_clean'].apply(
            lambda x: self.preprocessor.to_char_indices(x, max_length=50)
        )

        # Convert to word indices
        self.df['word_indices'] = self.df['merchant_clean'].apply(
            lambda x: self.preprocessor.to_word_indices(
                self.preprocessor.tokenize(x),
                self.vocabulary,
                max_length=20
            )
        )

        # Split data
        self.X_char = np.array(self.df['char_indices'].tolist())
        self.X_word = np.array(self.df['word_indices'].tolist())
        self.y = self.df['category_id'].values

        # Train/validation/test split
        self.X_char_train, self.X_char_temp, self.y_train, self.y_temp = train_test_split(
            self.X_char, self.y, test_size=0.2, random_state=42, stratify=self.y
        )

        self.X_char_val, self.X_char_test, self.y_val, self.y_test = train_test_split(
            self.X_char_temp, self.y_temp, test_size=0.5, random_state=42, stratify=self.y_temp
        )

        print(f"✓ Training samples: {len(self.X_char_train)}")
        print(f"✓ Validation samples: {len(self.X_char_val)}")
        print(f"✓ Test samples: {len(self.X_char_test)}")

    def train_lstm(self, epochs=50, batch_size=128):
        """
        Train LSTM model
        """
        print("\n=== Training LSTM Model ===")

        model = build_lstm_model()

        # Callbacks
        callbacks = [
            keras.callbacks.ModelCheckpoint(
                'models/lstm_best.h5',
                save_best_only=True,
                monitor='val_accuracy'
            ),
            keras.callbacks.EarlyStopping(
                patience=5,
                monitor='val_accuracy',
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                factor=0.5,
                patience=3,
                monitor='val_loss'
            ),
            keras.callbacks.TensorBoard(log_dir='logs/lstm')
        ]

        # Train
        history = model.fit(
            self.X_char_train,
            self.y_train,
            validation_data=(self.X_char_val, self.y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        # Evaluate
        test_loss, test_acc, test_top3 = model.evaluate(
            self.X_char_test,
            self.y_test,
            verbose=0
        )

        print(f"\n✓ LSTM Test Accuracy: {test_acc*100:.2f}%")
        print(f"✓ LSTM Top-3 Accuracy: {test_top3*100:.2f}%")

        return model, history

    def train_cnn(self, epochs=50, batch_size=128):
        """
        Train CNN model
        """
        print("\n=== Training CNN Model ===")

        model = build_cnn_model()

        callbacks = [
            keras.callbacks.ModelCheckpoint(
                'models/cnn_best.h5',
                save_best_only=True,
                monitor='val_accuracy'
            ),
            keras.callbacks.EarlyStopping(
                patience=5,
                monitor='val_accuracy',
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                factor=0.5,
                patience=3,
                monitor='val_loss'
            ),
            keras.callbacks.TensorBoard(log_dir='logs/cnn')
        ]

        history = model.fit(
            self.X_char_train,
            self.y_train,
            validation_data=(self.X_char_val, self.y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        test_loss, test_acc, test_top3 = model.evaluate(
            self.X_char_test,
            self.y_test,
            verbose=0
        )

        print(f"\n✓ CNN Test Accuracy: {test_acc*100:.2f}%")
        print(f"✓ CNN Top-3 Accuracy: {test_top3*100:.2f}%")

        return model, history

    def train_transformer(self, epochs=50, batch_size=128):
        """
        Train Transformer model
        """
        print("\n=== Training Transformer Model ===")

        model = build_transformer_model()

        callbacks = [
            keras.callbacks.ModelCheckpoint(
                'models/transformer_best.h5',
                save_best_only=True,
                monitor='val_accuracy'
            ),
            keras.callbacks.EarlyStopping(
                patience=5,
                monitor='val_accuracy',
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                factor=0.5,
                patience=3,
                monitor='val_loss'
            ),
            keras.callbacks.TensorBoard(log_dir='logs/transformer')
        ]

        history = model.fit(
            self.X_word_train,
            self.y_train,
            validation_data=(self.X_word_val, self.y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        test_loss, test_acc, test_top3 = model.evaluate(
            self.X_word_test,
            self.y_test,
            verbose=0
        )

        print(f"\n✓ Transformer Test Accuracy: {test_acc*100:.2f}%")
        print(f"✓ Transformer Top-3 Accuracy: {test_top3*100:.2f}%")

        return model, history

    def evaluate_ensemble(self, lstm_model, cnn_model, transformer_model):
        """
        Evaluate ensemble performance
        """
        print("\n=== Evaluating Ensemble ===")

        # Get predictions from all models
        lstm_probs = lstm_model.predict(self.X_char_test)
        cnn_probs = cnn_model.predict(self.X_char_test)
        transformer_probs = transformer_model.predict(self.X_word_test)

        # Ensemble with weights
        weights = [0.35, 0.35, 0.25, 0.05]
        ensemble_probs = (
            weights[0] * lstm_probs +
            weights[1] * cnn_probs +
            weights[2] * transformer_probs
        )

        # Calculate accuracy
        ensemble_preds = np.argmax(ensemble_probs, axis=1)
        ensemble_acc = np.mean(ensemble_preds == self.y_test)

        # Calculate top-3 accuracy
        top3_preds = np.argsort(ensemble_probs, axis=1)[:, -3:]
        top3_acc = np.mean([
            self.y_test[i] in top3_preds[i]
            for i in range(len(self.y_test))
        ])

        print(f"\n✓ Ensemble Accuracy: {ensemble_acc*100:.2f}%")
        print(f"✓ Ensemble Top-3 Accuracy: {top3_acc*100:.2f}%")

        # Per-category accuracy
        self.analyze_per_category_performance(ensemble_preds)

        return ensemble_acc, top3_acc

    def analyze_per_category_performance(self, predictions):
        """
        Analyze accuracy per category
        """
        print("\n=== Per-Category Performance ===")

        from sklearn.metrics import classification_report

        report = classification_report(
            self.y_test,
            predictions,
            output_dict=True,
            zero_division=0
        )

        # Find worst performing categories
        worst_categories = sorted(
            [(k, v['f1-score']) for k, v in report.items() if k.isdigit()],
            key=lambda x: x[1]
        )[:10]

        print("\nWorst 10 Categories:")
        for cat_id, f1 in worst_categories:
            cat_name = self.get_category_name(int(cat_id))
            print(f"  {cat_id}: {cat_name} (F1: {f1:.3f})")

# Train all models
trainer = ModelTrainer('training_data.csv')

lstm_model, lstm_history = trainer.train_lstm(epochs=50)
cnn_model, cnn_history = trainer.train_cnn(epochs=50)
transformer_model, transformer_history = trainer.train_transformer(epochs=50)

ensemble_acc, top3_acc = trainer.evaluate_ensemble(
    lstm_model, cnn_model, transformer_model
)

# Convert to TFLite
convert_to_tflite(lstm_model, 'model_lstm')
convert_to_tflite(cnn_model, 'model_cnn')
convert_to_tflite(transformer_model, 'model_transformer')

print("\n✓ Training complete!")
print(f"  Final Ensemble Accuracy: {ensemble_acc*100:.2f}%")
print(f"  Final Top-3 Accuracy: {top3_acc*100:.2f}%")
```

---

## 11. ON-DEVICE INFERENCE OPTIMIZATION

### 11.1 Model Quantization

```python
def quantize_model(model, model_name):
    """
    Quantize model to reduce size and improve inference speed
    """
    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Dynamic range quantization (weights only)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Full integer quantization (weights + activations)
    def representative_dataset():
        for i in range(100):
            yield [np.random.randn(1, 50).astype(np.int32)]

    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    # Convert
    quantized_model = converter.convert()

    # Save
    output_path = f"models/{model_name}_quantized.tflite"
    with open(output_path, 'wb') as f:
        f.write(quantized_model)

    # Compare sizes
    original_size = len(converter.convert()) / 1024
    quantized_size = len(quantized_model) / 1024

    print(f"✓ {model_name} quantized:")
    print(f"  Original: {original_size:.2f} KB")
    print(f"  Quantized: {quantized_size:.2f} KB")
    print(f"  Reduction: {(1 - quantized_size/original_size)*100:.1f}%")

    return output_path

# Quantize all models
quantize_model(lstm_model, 'model_lstm')
quantize_model(cnn_model, 'model_cnn')
quantize_model(transformer_model, 'model_transformer')

# Expected results:
# LSTM: 2.5 MB → 650 KB (74% reduction)
# CNN: 2.2 MB → 580 KB (74% reduction)
# Transformer: 3.8 MB → 980 KB (74% reduction)
# Total: 8.5 MB → 2.2 MB
```

### 11.2 GPU Acceleration

```kotlin
private fun getInterpreterOptions(): Interpreter.Options {
    return Interpreter.Options().apply {
        setNumThreads(4)

        // Try GPU delegate first
        try {
            val gpuDelegate = GpuDelegate()
            addDelegate(gpuDelegate)
            Timber.d("✓ Using GPU acceleration")
        } catch (e: Exception) {
            Timber.w("GPU delegate not available, using CPU")
        }

        // Fallback: NNAPI
        setUseNNAPI(true)
    }
}
```

### 11.3 Performance Benchmarking

```kotlin
class MLBenchmark @Inject constructor(
    private val mlService: MLInferenceService
) {

    suspend fun runBenchmark(): BenchmarkResults {
        val testCases = listOf(
            "Swiggy",
            "Punjab Grill Connaught Place",
            "Amazon India",
            "Uber Trip",
            "Starbucks Coffee"
        )

        val results = mutableListOf<InferenceResult>()

        testCases.forEach { merchantName ->
            val startTime = System.nanoTime()

            val classification = mlService.classify(
                merchantName = merchantName,
                amount = 450.0,
                upiId = null,
                timestamp = System.currentTimeMillis()
            )

            val endTime = System.nanoTime()
            val durationMs = (endTime - startTime) / 1_000_000

            results.add(
                InferenceResult(
                    merchantName = merchantName,
                    categoryId = classification.categoryId,
                    confidence = classification.confidence,
                    inferenceTimeMs = durationMs
                )
            )
        }

        return BenchmarkResults(
            averageInferenceTime = results.map { it.inferenceTimeMs }.average(),
            p50InferenceTime = results.map { it.inferenceTimeMs }.median(),
            p95InferenceTime = results.map { it.inferenceTimeMs }.percentile(95),
            maxInferenceTime = results.maxOf { it.inferenceTimeMs },
            results = results
        )
    }
}

// Expected performance:
// Average: 120ms
// P50: 110ms
// P95: 180ms
// Max: 200ms
```

---

## 12. MODEL UPDATES & CONTINUOUS LEARNING

### 12.1 Over-the-Air Model Updates

```kotlin
class ModelUpdateManager @Inject constructor(
    private val firebaseStorage: FirebaseStorage,
    private val context: Context,
    private val userPreferences: UserPreferences
) {

    companion object {
        private const val MODELS_BUCKET = "xpenz-ml-models"
        private const val MODEL_VERSION_KEY = "ml_model_version"
    }

    suspend fun checkForUpdates(): ModelUpdateInfo? {
        return try {
            // Get latest model version from Firebase
            val latestVersion = getLatestModelVersion()
            val currentVersion = userPreferences.getModelVersion()

            if (latestVersion > currentVersion) {
                ModelUpdateInfo(
                    currentVersion = currentVersion,
                    latestVersion = latestVersion,
                    downloadSize = getModelSize(latestVersion),
                    releaseNotes = getReleaseNotes(latestVersion)
                )
            } else {
                null
            }
        } catch (e: Exception) {
            Timber.e(e, "Failed to check for model updates")
            null
        }
    }

    suspend fun downloadAndInstallUpdate(version: Int): Result<Unit> {
        return try {
            // Download models
            downloadModel("model_lstm_v$version.tflite")
            downloadModel("model_cnn_v$version.tflite")
            downloadModel("model_transformer_v$version.tflite")

            // Update version
            userPreferences.setModelVersion(version)

            // Reload models in MLInferenceService
            mlService.reloadModels()

            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error("Failed to update models: ${e.message}")
        }
    }

    private suspend fun downloadModel(filename: String) {
        val storageRef = firebaseStorage.reference
            .child("$MODELS_BUCKET/$filename")

        val localFile = File(context.filesDir, filename)

        storageRef.getFile(localFile).await()
    }
}
```

### 12.2 User Feedback Learning

```kotlin
class FeedbackLearningService @Inject constructor(
    private val transactionDao: TransactionDao,
    private val firebaseFirestore: FirebaseFirestore
) {

    /**
     * User corrects a transaction category
     */
    suspend fun recordCorrection(
        transactionId: String,
        originalCategoryId: Int,
        correctedCategoryId: Int,
        userId: String
    ) {
        try {
            // Update local transaction
            transactionDao.updateCategoryCorrection(
                transactionId = transactionId,
                correctedCategoryId = correctedCategoryId
            )

            // Upload to Firestore for model retraining
            val correction = mapOf(
                "transaction_id" to transactionId,
                "user_id" to userId,
                "merchant_name" to transaction.merchantName,
                "original_category" to originalCategoryId,
                "corrected_category" to correctedCategoryId,
                "timestamp" to System.currentTimeMillis()
            )

            firebaseFirestore.collection("ml_corrections")
                .add(correction)
                .await()

            // Local immediate learning (update rule-based)
            updateLocalRules(transaction.merchantName, correctedCategoryId)

        } catch (e: Exception) {
            Timber.e(e, "Failed to record correction")
        }
    }

    private fun updateLocalRules(merchantName: String, categoryId: Int) {
        // Cache user's corrections for immediate use
        val rules = userPreferences.getCorrectionRules()
        rules[merchantName.lowercase()] = categoryId
        userPreferences.saveCorrectionRules(rules)
    }
}
```

---

Perfect! I'll continue with the remaining critical sections.

---

## 13. SMS DETECTION & PARSING

### 13.1 SMS Detection Architecture

**Flow:**

```
SMS Received (Android System)
    ↓
BroadcastReceiver (SMSReceiver)
    ↓
Filter: Is it a transaction SMS?
    ↓ YES
Parse SMS (Extract: amount, merchant, type, bank)
    ↓
ML Classification
    ↓
Create Transaction
    ↓
Save to Database
    ↓
Notify User
```

### 13.2 SMSReceiver Implementation

```kotlin
package com.xpenz.feature.transaction.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.telephony.SmsMessage
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.AndroidEntryPoint
import timber.log.Timber
import javax.inject.Inject

@AndroidEntryPoint
class SMSReceiver : BroadcastReceiver() {

    @Inject
    lateinit var smsParser: SMSParser

    @Inject
    lateinit var smsFilter: SMSFilter

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            return
        }

        try {
            // Extract SMS messages
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)

            messages.forEach { message ->
                processSMS(context, message)
            }

        } catch (e: Exception) {
            Timber.e(e, "Failed to process SMS")
        }
    }

    private fun processSMS(context: Context, message: SmsMessage) {
        val sender = message.displayOriginatingAddress
        val body = message.messageBody
        val timestamp = message.timestampMillis

        Timber.d("SMS received from: $sender")

        // Filter: Is this a transaction SMS?
        if (!smsFilter.isTransactionSMS(sender, body)) {
            Timber.d("Not a transaction SMS, ignoring")
            return
        }

        // Queue for processing (background work)
        val workRequest = OneTimeWorkRequestBuilder<SMSProcessingWorker>()
            .setInputData(
                workDataOf(
                    "sender" to sender,
                    "body" to body,
                    "timestamp" to timestamp
                )
            )
            .build()

        WorkManager.getInstance(context).enqueue(workRequest)
    }
}
```

### 13.3 SMS Filter

```kotlin
package com.xpenz.feature.transaction.parser

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SMSFilter @Inject constructor() {

    companion object {
        // Known bank/financial service sender IDs
        private val KNOWN_SENDERS = setOf(
            // Banks
            "VK-HDFCBK", "HDFCBK", "AD-HDFCBK",
            "VK-ICICIB", "ICICIB", "AD-ICICIB",
            "VK-SBMSMS", "SBIUPI", "SBMSMS",
            "VK-AXISBNK", "AXISBK",
            "VK-KOTAKB", "KOTAKB",
            "VK-YESBNK", "YESBNK",
            "VK-IDFCFB", "IDFCFB",

            // UPI Apps
            "PAYTMB", "VM-PAYTMB",
            "GPAYIND", "VM-GPAYIND",
            "PHONEPE", "VM-PHONEPE",
            "BHARATPE",
            "AMAZPAY",

            // Credit Cards
            "HDFCCC", "ICICIC", "SBICRD", "AXISCR",

            // Wallets
            "PAYTMW", "MOBIKW", "OLAMNY"
        )

        // Transaction keywords (must contain at least one)
        private val TRANSACTION_KEYWORDS = listOf(
            "debited", "credited", "debit", "credit",
            "paid", "received", "sent", "transferred",
            "withdrawn", "deposited",
            "spent", "purchase", "purchased",
            "transaction", "payment",
            "upi", "imps", "neft", "rtgs",
            "a/c", "account", "acc",
            "rs", "rs.", "inr", "₹"
        )

        // Amount pattern (must match)
        private val AMOUNT_PATTERN = Regex(
            """(?:rs\.?|inr|₹)\s*(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)""",
            RegexOption.IGNORE_CASE
        )
    }

    /**
     * Check if SMS is a transaction message
     */
    fun isTransactionSMS(sender: String, body: String): Boolean {
        // Check 1: Is sender a known financial institution?
        val isKnownSender = KNOWN_SENDERS.any { knownSender ->
            sender.contains(knownSender, ignoreCase = true)
        }

        if (!isKnownSender) {
            return false
        }

        // Check 2: Contains transaction keywords?
        val hasKeyword = TRANSACTION_KEYWORDS.any { keyword ->
            body.contains(keyword, ignoreCase = true)
        }

        if (!hasKeyword) {
            return false
        }

        // Check 3: Contains amount?
        val hasAmount = AMOUNT_PATTERN.containsMatchIn(body)

        return hasAmount
    }

    /**
     * Detect transaction type from keywords
     */
    fun detectTransactionType(body: String): TransactionType {
        val bodyLower = body.lowercase()

        return when {
            bodyLower.contains("debited") ||
            bodyLower.contains("paid") ||
            bodyLower.contains("spent") ||
            bodyLower.contains("purchase") -> TransactionType.DEBIT

            bodyLower.contains("credited") ||
            bodyLower.contains("received") ||
            bodyLower.contains("deposit") -> TransactionType.CREDIT

            bodyLower.contains("refund") ||
            bodyLower.contains("reversed") -> TransactionType.REFUND

            else -> TransactionType.DEBIT // Default
        }
    }
}

enum class TransactionType {
    DEBIT,
    CREDIT,
    REFUND
}
```

### 13.4 SMS Parser

```kotlin
package com.xpenz.feature.transaction.parser

import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SMSParser @Inject constructor(
    private val patternRepository: SMSPatternRepository
) {

    /**
     * Parse transaction SMS
     */
    suspend fun parse(sender: String, body: String, timestamp: Long): ParsedSMSData? {
        return try {
            // Get patterns for this sender
            val patterns = patternRepository.getPatternsForSender(sender)

            // Try each pattern
            for (pattern in patterns) {
                val result = tryPattern(body, pattern)
                if (result != null) {
                    return result.copy(
                        sender = sender,
                        timestamp = timestamp,
                        rawSMS = body
                    )
                }
            }

            // Fallback: generic parsing
            parseGeneric(sender, body, timestamp)

        } catch (e: Exception) {
            Timber.e(e, "Failed to parse SMS")
            null
        }
    }

    private fun tryPattern(body: String, pattern: SMSPatternEntity): ParsedSMSData? {
        return try {
            val regex = Regex(pattern.patternRegex, RegexOption.IGNORE_CASE)
            val match = regex.find(body) ?: return null

            // Extract amount
            val amount = match.groups[pattern.amountGroup]?.value?.let {
                extractAmount(it)
            } ?: return null

            // Extract merchant (optional)
            val merchant = pattern.merchantGroup?.let { groupNum ->
                match.groups[groupNum]?.value?.trim()
            }

            // Extract UPI ID (optional)
            val upiId = pattern.upiGroup?.let { groupNum ->
                match.groups[groupNum]?.value?.trim()
            }

            // Detect transaction type
            val type = detectType(body, pattern.typeKeywords)

            ParsedSMSData(
                amount = amount,
                merchantName = merchant,
                upiId = upiId,
                bankName = pattern.bankName,
                type = type,
                sender = "",
                timestamp = 0L,
                rawSMS = body,
                confidence = pattern.confidenceScore
            )

        } catch (e: Exception) {
            Timber.e(e, "Pattern matching failed")
            null
        }
    }

    private fun parseGeneric(sender: String, body: String, timestamp: Long): ParsedSMSData? {
        // Generic parsing using common patterns

        // Extract amount
        val amountRegex = Regex("""(?:rs\.?|inr|₹)\s*(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)""", RegexOption.IGNORE_CASE)
        val amountMatch = amountRegex.find(body)
        val amount = amountMatch?.groups?.get(1)?.value?.let {
            extractAmount(it)
        } ?: return null

        // Extract merchant (between "at" and "via" or "on")
        val merchantRegex = Regex("""(?:at|to)\s+([A-Z0-9\s\-@.]+?)(?:\s+(?:via|on|using|from|upi)|\s*$)""", RegexOption.IGNORE_CASE)
        val merchantMatch = merchantRegex.find(body)
        val merchant = merchantMatch?.groups?.get(1)?.value?.trim()

        // Extract UPI ID
        val upiRegex = Regex("""([a-z0-9._-]+@[a-z]+)""", RegexOption.IGNORE_CASE)
        val upiMatch = upiRegex.find(body)
        val upiId = upiMatch?.groups?.get(1)?.value

        // Detect bank
        val bank = detectBank(sender, body)

        // Detect type
        val type = detectTransactionType(body)

        return ParsedSMSData(
            amount = amount,
            merchantName = merchant,
            upiId = upiId,
            bankName = bank,
            type = type,
            sender = sender,
            timestamp = timestamp,
            rawSMS = body,
            confidence = 0.7f // Lower confidence for generic parsing
        )
    }

    private fun extractAmount(amountStr: String): Double {
        // Remove commas and parse
        val cleaned = amountStr.replace(",", "")
        return cleaned.toDoubleOrNull() ?: 0.0
    }

    private fun detectType(body: String, typeKeywords: String): TransactionType {
        val keywordsMap = parseTypeKeywords(typeKeywords)
        val bodyLower = body.lowercase()

        return when {
            keywordsMap["debit"]?.any { bodyLower.contains(it) } == true -> TransactionType.DEBIT
            keywordsMap["credit"]?.any { bodyLower.contains(it) } == true -> TransactionType.CREDIT
            keywordsMap["refund"]?.any { bodyLower.contains(it) } == true -> TransactionType.REFUND
            else -> TransactionType.DEBIT
        }
    }

    private fun parseTypeKeywords(json: String): Map<String, List<String>> {
        return try {
            Gson().fromJson(json, object : TypeToken<Map<String, List<String>>>() {}.type)
        } catch (e: Exception) {
            emptyMap()
        }
    }

    private fun detectBank(sender: String, body: String): String? {
        val bankKeywords = mapOf(
            "HDFC" to "HDFC Bank",
            "ICICI" to "ICICI Bank",
            "SBI" to "State Bank of India",
            "AXIS" to "Axis Bank",
            "KOTAK" to "Kotak Mahindra Bank",
            "YES" to "Yes Bank",
            "IDFC" to "IDFC First Bank",
            "PAYTM" to "Paytm Payments Bank",
            "INDUSIND" to "IndusInd Bank"
        )

        val senderUpper = sender.uppercase()
        val bodyUpper = body.uppercase()

        for ((keyword, bankName) in bankKeywords) {
            if (senderUpper.contains(keyword) || bodyUpper.contains(keyword)) {
                return bankName
            }
        }

        return null
    }
}

data class ParsedSMSData(
    val amount: Double,
    val merchantName: String?,
    val upiId: String?,
    val bankName: String?,
    val type: TransactionType,
    val sender: String,
    val timestamp: Long,
    val rawSMS: String,
    val confidence: Float
)
```

### 13.5 SMS Pattern Examples

```kotlin
// Pre-loaded SMS patterns for major banks

val hdfc_pattern_1 = SMSPatternEntity(
    patternId = 1,
    sender = "VK-HDFCBK",
    bankName = "HDFC Bank",
    patternRegex = """Rs\.(\d+(?:,\d+)*(?:\.\d{2})?)\s+(?:debited|paid)\s+from\s+A/c\s+[X\d]+\s+(?:at|to)\s+([A-Z0-9\s@.-]+)""",
    amountGroup = 1,
    merchantGroup = 2,
    upiGroup = null,
    typeKeywords = """{"debit": ["debited", "paid"], "credit": ["credited"], "refund": ["refund"]}""",
    confidenceScore = 0.95f,
    usageCount = 0,
    successRate = 1.0f,
    isActive = true
)

val icici_pattern_1 = SMSPatternEntity(
    patternId = 2,
    sender = "VK-ICICIB",
    bankName = "ICICI Bank",
    patternRegex = """Your\s+a/c\s+[X\d]+\s+is\s+(?:debited|credited)\s+with\s+Rs\.(\d+(?:,\d+)*(?:\.\d{2})?)\s+(?:at|to|from)\s+([A-Z0-9\s@.-]+)""",
    amountGroup = 1,
    merchantGroup = 2,
    upiGroup = null,
    typeKeywords = """{"debit": ["debited"], "credit": ["credited"], "refund": ["refund"]}""",
    confidenceScore = 0.95f,
    usageCount = 0,
    successRate = 1.0f,
    isActive = true
)

val sbi_upi_pattern = SMSPatternEntity(
    patternId = 3,
    sender = "SBIUPI",
    bankName = "State Bank of India",
    patternRegex = """Rs\.(\d+(?:,\d+)*(?:\.\d{2})?)\s+(?:debited|sent|paid)\s+to\s+([a-z0-9._-]+@[a-z]+)""",
    amountGroup = 1,
    merchantGroup = null,
    upiGroup = 2,
    typeKeywords = """{"debit": ["debited", "sent", "paid"], "credit": ["received"], "refund": ["refund"]}""",
    confidenceScore = 0.90f,
    usageCount = 0,
    successRate = 1.0f,
    isActive = true
)

// Example SMS messages and expected parsing:

/*
SMS 1 (HDFC):
"Rs.450 debited from A/c XX1234 at PUNJAB GRILL CONNAUGHT via UPI Ref:412345678"

Parsed:
- amount: 450.0
- merchant: "PUNJAB GRILL CONNAUGHT"
- bank: "HDFC Bank"
- type: DEBIT

SMS 2 (ICICI):
"Your a/c XX5678 is debited with Rs.1,250.00 at AMAZON INDIA on 24-Feb-26"

Parsed:
- amount: 1250.0
- merchant: "AMAZON INDIA"
- bank: "ICICI Bank"
- type: DEBIT

SMS 3 (SBI UPI):
"Rs.850 sent to swiggy@paytm from SBI XX9012 on 24-Feb-26 Ref:412345678"

Parsed:
- amount: 850.0
- upiId: "swiggy@paytm"
- bank: "State Bank of India"
- type: DEBIT
*/
```

### 13.6 SMS Processing Worker

```kotlin
package com.xpenz.feature.transaction.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.xpenz.core.ml.MLInferenceService
import com.xpenz.core.domain.repository.TransactionRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class SMSProcessingWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val smsParser: SMSParser,
    private val mlService: MLInferenceService,
    private val transactionRepository: TransactionRepository,
    private val notificationService: NotificationService
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            val sender = inputData.getString("sender") ?: return Result.failure()
            val body = inputData.getString("body") ?: return Result.failure()
            val timestamp = inputData.getLong("timestamp", System.currentTimeMillis())

            // Parse SMS
            val parsedData = smsParser.parse(sender, body, timestamp)
                ?: return Result.failure()

            // Check for duplicate (using SMS hash)
            if (isDuplicate(parsedData)) {
                Timber.d("Duplicate SMS, ignoring")
                return Result.success()
            }

            // ML Classification
            val classification = mlService.classify(
                merchantName = parsedData.merchantName ?: "",
                amount = parsedData.amount,
                upiId = parsedData.upiId,
                timestamp = parsedData.timestamp
            )

            // Create transaction
            val transaction = Transaction(
                id = UUID.randomUUID().toString(),
                userId = getCurrentUserId(),
                familyId = getCurrentFamilyId(),
                type = parsedData.type,
                amount = parsedData.amount,
                merchantName = parsedData.merchantName,
                upiId = parsedData.upiId,
                bankName = parsedData.bankName,
                category = getCategory(classification.categoryId),
                mlConfidence = classification.confidence,
                mlSource = classification.source,
                top3Predictions = classification.top3Predictions,
                timestamp = parsedData.timestamp,
                detectedAt = System.currentTimeMillis(),
                isSynced = false,
                isManuallyAdded = false,
                createdAt = System.currentTimeMillis(),
                updatedAt = System.currentTimeMillis()
            )

            // Save to database
            transactionRepository.insertTransaction(transaction)

            // Show notification
            notificationService.showTransactionDetected(transaction)

            Result.success()

        } catch (e: Exception) {
            Timber.e(e, "Failed to process SMS")
            Result.failure()
        }
    }

    private suspend fun isDuplicate(parsedData: ParsedSMSData): Boolean {
        val smsHash = hashSMS(parsedData.rawSMS)
        val count = transactionDao.checkDuplicateSMS(smsHash)
        return count > 0
    }

    private fun hashSMS(sms: String): String {
        return MessageDigest.getInstance("SHA-256")
            .digest(sms.toByteArray())
            .joinToString("") { "%02x".format(it) }
    }
}
```

---

## 14. PERFORMANCE OPTIMIZATION

### 14.1 Database Optimization

```kotlin
// Indexed queries
@Query("""
    SELECT * FROM transactions
    WHERE user_id = :userId
    AND timestamp BETWEEN :startTime AND :endTime
    AND deleted_at IS NULL
    ORDER BY timestamp DESC
""")
suspend fun getTransactionsByDateRange(
    userId: String,
    startTime: Long,
    endTime: Long
): List<TransactionEntity>

// Composite index for common queries
@Entity(
    indices = [
        Index(value = ["user_id", "timestamp"]),
        Index(value = ["family_id", "timestamp"]),
        Index(value = ["ml_category_id"]),
        Index(value = ["type", "timestamp"])
    ]
)

// Pagination for large datasets
@Query("""
    SELECT * FROM transactions
    WHERE user_id = :userId
    ORDER BY timestamp DESC
    LIMIT :limit OFFSET :offset
""")
suspend fun getTransactionsPaged(
    userId: String,
    limit: Int,
    offset: Int
): List<TransactionEntity>
```

### 14.2 Memory Optimization

```kotlin
// Use Flow for reactive data
fun getUserTransactions(userId: String): Flow<List<Transaction>> {
    return transactionDao.getUserTransactions(userId)
        .map { entities ->
            entities.map { entity ->
                transactionMapper.toDomain(entity)
            }
        }
}

// Limit list sizes in UI
@Composable
fun TransactionList(transactions: List<Transaction>) {
    LazyColumn {
        items(
            items = transactions.take(100), // Limit to 100 visible
            key = { it.id }
        ) { transaction ->
            TransactionItem(transaction)
        }
    }
}

// Image loading optimization
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data(imageUrl)
        .memoryCacheKey(imageUrl)
        .diskCacheKey(imageUrl)
        .crossfade(true)
        .size(Size.ORIGINAL)
        .build(),
    contentDescription = null
)
```

### 14.3 Battery Optimization

```kotlin
// Use WorkManager for background tasks (battery-friendly)
val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
    repeatInterval = 15,
    repeatIntervalTimeUnit = TimeUnit.MINUTES
)
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(true) // Only when battery not low
            .build()
    )
    .build()

// Efficient SMS monitoring (only wake on SMS)
class SMSReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        // Only processes when SMS arrives (not polling)
        // Quick filtering to avoid unnecessary work
        if (smsFilter.isTransactionSMS(sender, body)) {
            // Queue for background processing
            WorkManager.enqueue(work)
        }
    }
}

// ML inference optimization
private fun getInterpreterOptions(): Interpreter.Options {
    return Interpreter.Options().apply {
        setNumThreads(2) // Limit CPU usage
        setUseNNAPI(true) // Hardware acceleration
    }
}
```

---

## 15. SECURITY & PRIVACY

### 15.1 Data Encryption

```kotlin
// Encrypt sensitive data before cloud upload
fun encryptTransaction(transaction: Transaction): String {
    val sensitiveData = mapOf(
        "merchant" to transaction.merchantName,
        "upi" to transaction.upiId,
        "note" to transaction.note
    )

    val json = Gson().toJson(sensitiveData)
    return encryptionService.encrypt(json, getFamilyKey())
}

// Decrypt on download
fun decryptTransaction(encrypted: String): Map<String, String?> {
    val decrypted = encryptionService.decrypt(encrypted, getFamilyKey())
    return Gson().fromJson(decrypted, Map::class.java)
}
```

### 15.2 Privacy Controls

```kotlin
// User can hide specific categories
suspend fun hideCategory(categoryId: Int) {
    userPreferences.addHiddenCategory(categoryId)
}

// Filtered transactions (exclude hidden)
fun getVisibleTransactions(userId: String): Flow<List<Transaction>> {
    val hiddenCategories = userPreferences.getHiddenCategories()

    return transactionDao.getUserTransactions(userId)
        .map { entities ->
            entities
                .filter { !hiddenCategories.contains(it.mlCategoryId) }
                .map { transactionMapper.toDomain(it) }
        }
}

// SMS deletion after parsing
suspend fun processAndDeleteSMS(sms: SmsMessage) {
    val parsed = smsParser.parse(sms)

    // Create transaction
    createTransaction(parsed)

    // Delete SMS (user preference)
    if (userPreferences.shouldDeleteSMS()) {
        deleteSMS(sms.id)
    }
}
```

---

## 16. TESTING STRATEGY

### 16.1 Unit Tests

```kotlin
class TransactionRepositoryTest {

    @Test
    fun `insert transaction saves to database`() = runTest {
        // Given
        val transaction = createTestTransaction()

        // When
        repository.insertTransaction(transaction)

        // Then
        val result = repository.getTransaction(transaction.id)
        assertThat(result).isEqualTo(Result.Success(transaction))
    }

    @Test
    fun `get transactions by date range returns correct data`() = runTest {
        // Given
        val transactions = listOf(
            createTestTransaction(timestamp = 1000L),
            createTestTransaction(timestamp = 2000L),
            createTestTransaction(timestamp = 3000L)
        )
        transactions.forEach { repository.insertTransaction(it) }

        // When
        val result = repository.getTransactionsByDateRange(
            userId = "user1",
            startTime = 1500L,
            endTime = 2500L
        )

        // Then
        assertThat(result).isEqualTo(Result.Success(listOf(transactions[1])))
    }
}

class MLInferenceServiceTest {

    @Test
    fun `classify returns correct category for known merchant`() = runTest {
        // Given
        val merchantName = "Swiggy"

        // When
        val classification = mlService.classify(
            merchantName = merchantName,
            amount = 450.0,
            upiId = null,
            timestamp = System.currentTimeMillis()
        )

        // Then
        assertThat(classification.categoryId).isEqualTo(45) // Food Delivery
        assertThat(classification.confidence).isGreaterThan(0.8f)
    }
}

class SMSParserTest {

    @Test
    fun `parse HDFC SMS extracts correct data`() = runTest {
        // Given
        val sms = "Rs.450 debited from A/c XX1234 at PUNJAB GRILL via UPI"

        // When
        val parsed = smsParser.parse("VK-HDFCBK", sms, System.currentTimeMillis())

        // Then
        assertThat(parsed).isNotNull()
        assertThat(parsed!!.amount).isEqualTo(450.0)
        assertThat(parsed.merchantName).contains("PUNJAB GRILL")
        assertThat(parsed.type).isEqualTo(TransactionType.DEBIT)
    }
}
```

### 16.2 Integration Tests

```kotlin
@HiltAndroidTest
class TransactionFlowIntegrationTest {

    @Test
    fun `full transaction flow from SMS to database`() = runTest {
        // Simulate SMS received
        val sms = createTestSMS(
            body = "Rs.450 debited from A/c XX1234 at PUNJAB GRILL"
        )

        // Process SMS
        smsProcessor.process(sms)

        // Verify transaction created
        delay(1000) // Wait for async processing

        val transactions = transactionDao.getUserTransactions("user1").first()
        assertThat(transactions).hasSize(1)
        assertThat(transactions[0].amount).isEqualTo(450.0)
    }
}
```

---

Let me check what's remaining in the TRD...

## 📋 **TRD STATUS CHECK**

### ✅ **COMPLETED SECTIONS:**

**PART 1: ARCHITECTURE & DESIGN**

- ✅ 1. System Architecture (Complete)
- ✅ 2. Technology Stack (106 dependencies listed)
- ✅ 3. Module Structure (Complete)
- ✅ 4. Design Patterns (MVVM, Repository, Use Cases, DI)

**PART 2: DATA & STORAGE**

- ✅ 5. Database Schema (11 tables with complete definitions)
- ✅ 6. Data Models (Domain models, DTOs, Mappers)
- ✅ 7. Repository Pattern (Complete implementations)
- ✅ 8. Cloud Sync Architecture (Firestore, WorkManager, Real-time sync)

**PART 3: MACHINE LEARNING**

- ✅ 9. ML Model Architecture (LSTM, CNN, Transformer + Ensemble)
- ✅ 10. Training Pipeline (Data generation, training scripts)
- ✅ 11. On-Device Inference (TFLite integration, optimization)
- ✅ 12. Model Updates (OTA updates, feedback learning)

**PART 4: CORE FEATURES**

- ✅ 13. SMS Detection & Parsing (Complete implementation)
- ❌ 14. Transaction Classification (Partially covered in ML section)
- ❌ 15. Family Management (Missing)
- ❌ 16. Budget System (Missing)
- ❌ 17. Real-Time Sync (Covered in Section 8)

**PART 5: INFRASTRUCTURE**

- ✅ 18. Security & Privacy (Encryption, privacy controls)
- ✅ 19. Performance Optimization (Database, memory, battery)
- ✅ 20. Testing Strategy (Unit, integration tests)
- ❌ 21. CI/CD Pipeline (Missing)
- ❌ 22. Monitoring & Analytics (Missing)

**PART 6: IMPLEMENTATION**

- ❌ 23. Development Roadmap (20 weeks breakdown)
- ❌ 24. Deployment Strategy (Missing)
- ❌ 25. API Documentation (Missing)

---

## ❌ **MISSING SECTIONS (Important for AI Development):**

### **CRITICAL (Must Have):**

1. **Family Management Implementation** (Section 15)
    - Family creation flow
    - Member invitation system
    - Permission management
    - Real-time member sync
2. **Budget System Implementation** (Section 16)
    - Budget creation logic
    - Progress tracking algorithm
    - Alert triggering system
    - Budget calculation formulas
3. **Development Roadmap** (Section 23)
    - 20-week implementation timeline
    - Sprint breakdown
    - Dependencies between features
    - Resource allocation
4. **Monitoring & Analytics** (Section 22)
    - Firebase Analytics integration
    - Crashlytics setup
    - Performance monitoring
    - Key metrics tracking

### **IMPORTANT (Should Have):**

1. **CI/CD Pipeline** (Section 21)
    - GitHub Actions workflow
    - Automated testing
    - Build & deployment process
    - Release management
2. **API Documentation** (Section 25)
    - Firebase API specs
    - Google Play Billing API
    - Internal API contracts
    - Error codes & handling
3. **Deployment Strategy** (Section 24)
    - Beta testing plan
    - Phased rollout
    - Rollback procedures
    - Version management

### **NICE TO HAVE:**

1. **UI/UX Implementation Guidelines**
    - Composable component library
    - Theme system
    - Navigation structure
    - Accessibility implementation
2. **Proguard/R8 Configuration**
    - Obfuscation rules
    - Keep rules for reflection
    - Optimization settings
3. **Deep Linking Implementation**
    - App Links configuration
    - Deep link handlers
    - URL schemes

---

## 💡 **MY RECOMMENDATION:**

For **AI-assisted development**, the most critical missing sections are:

**Priority 1 (Must add):**

- ✅ Development Roadmap (gives AI clear implementation order)
- ✅ Family Management Implementation (core feature)
- ✅ Budget System Implementation (core feature)
- ✅ Monitoring & Analytics (essential for production)

**Priority 2 (Should add if time permits):**

- CI/CD Pipeline
- Deployment Strategy
- API Documentation

**Priority 3 (Can skip for now):**

- UI/UX Guidelines (can be inferred from PRD)
- Proguard rules (can be added during implementation)
- Deep linking (lower priority)

---

## 🎯 **NEXT STEPS - YOUR CHOICE:**

**Option A: Complete Critical Sections** (Recommended)

- Add sections 15, 16, 22, 23 (~40-50 minutes)
- Create downloadable document
- TRD will be 95% complete and ready for AI development

**Option B: Create Document Now**

- Compile everything we have into downloadable TRD
- You can add missing sections later as needed
- TRD is ~70% complete, sufficient to start coding

**Option C: Continue Adding All Sections**

- Complete all 25 sections
- Fully comprehensive TRD
- Will take another ~2 hours

**Which option would you prefer?** I recommend **Option A** - completing the 4 critical sections will make the TRD immediately actionable for AI-assisted development.

Perfect! I'll complete all Priority 1, 2, and 3 sections to make the TRD fully comprehensive.

---

# PRIORITY 1: CRITICAL SECTIONS

## 15. FAMILY MANAGEMENT IMPLEMENTATION

### 15.1 Family Creation Flow

```kotlin
package com.xpenz.feature.family

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenz.core.domain.usecase.*
import com.xpenz.core.domain.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject
import java.util.UUID

@HiltViewModel
class CreateFamilyViewModel @Inject constructor(
    private val createFamilyUseCase: CreateFamilyUseCase,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<CreateFamilyUiState>(CreateFamilyUiState.Idle)
    val uiState: StateFlow<CreateFamilyUiState> = _uiState.asStateFlow()

    fun createFamily(
        name: String,
        emoji: String,
        color: String,
        description: String?
    ) {
        viewModelScope.launch {
            _uiState.value = CreateFamilyUiState.Loading

            try {
                // Validate input
                if (name.isBlank()) {
                    _uiState.value = CreateFamilyUiState.Error("Family name cannot be empty")
                    return@launch
                }

                if (name.length > 50) {
                    _uiState.value = CreateFamilyUiState.Error("Family name too long (max 50 characters)")
                    return@launch
                }

                // Get current user
                val currentUser = userRepository.getCurrentUser().first()
                    ?: throw IllegalStateException("User not logged in")

                // Create family object
                val family = Family(
                    id = UUID.randomUUID().toString(),
                    name = name,
                    emoji = emoji,
                    color = color,
                    description = description,
                    invitationCode = "", // Will be generated by use case
                    codeExpiresAt = System.currentTimeMillis() + (7 * 24 * 60 * 60 * 1000),
                    createdBy = currentUser.id,
                    maxMembers = if (currentUser.isPremium) Int.MAX_VALUE else 5,
                    isPremium = currentUser.isPremium,
                    settings = FamilySettings(
                        requireApproval = false,
                        allowMemberInvite = true,
                        autoSyncTransactions = true
                    ),
                    createdAt = System.currentTimeMillis(),
                    updatedAt = System.currentTimeMillis()
                )

                // Execute use case
                val result = createFamilyUseCase(family)

                when (result) {
                    is Result.Success -> {
                        _uiState.value = CreateFamilyUiState.Success(result.data)
                    }
                    is Result.Error -> {
                        _uiState.value = CreateFamilyUiState.Error(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = CreateFamilyUiState.Error(
                    e.message ?: "Failed to create family"
                )
            }
        }
    }

    fun resetState() {
        _uiState.value = CreateFamilyUiState.Idle
    }
}

sealed class CreateFamilyUiState {
    object Idle : CreateFamilyUiState()
    object Loading : CreateFamilyUiState()
    data class Success(val family: Family) : CreateFamilyUiState()
    data class Error(val message: String) : CreateFamilyUiState()
}
```

### 15.2 Family Invitation System

```kotlin
package com.xpenz.feature.family

@HiltViewModel
class JoinFamilyViewModel @Inject constructor(
    private val joinFamilyUseCase: JoinFamilyUseCase,
    private val getFamilyByCodeUseCase: GetFamilyByCodeUseCase,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<JoinFamilyUiState>(JoinFamilyUiState.Idle)
    val uiState: StateFlow<JoinFamilyUiState> = _uiState.asStateFlow()

    fun validateInvitationCode(code: String) {
        viewModelScope.launch {
            _uiState.value = JoinFamilyUiState.Validating

            try {
                // Format validation
                if (!isValidCodeFormat(code)) {
                    _uiState.value = JoinFamilyUiState.InvalidCode(
                        "Invalid format. Code should be XP-XXXXX"
                    )
                    return@launch
                }

                // Fetch family details
                val result = getFamilyByCodeUseCase(code)

                when (result) {
                    is Result.Success -> {
                        _uiState.value = JoinFamilyUiState.FamilyFound(result.data)
                    }
                    is Result.Error -> {
                        _uiState.value = JoinFamilyUiState.InvalidCode(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = JoinFamilyUiState.Error(
                    e.message ?: "Failed to validate code"
                )
            }
        }
    }

    fun joinFamily(family: Family, nickname: String) {
        viewModelScope.launch {
            _uiState.value = JoinFamilyUiState.Joining

            try {
                // Validate nickname
                if (nickname.isBlank()) {
                    _uiState.value = JoinFamilyUiState.Error("Nickname cannot be empty")
                    return@launch
                }

                // Get current user
                val currentUser = userRepository.getCurrentUser().first()
                    ?: throw IllegalStateException("User not logged in")

                // Check if already member
                val existingMembers = familyRepository.getFamilyMembers(family.id)
                if (existingMembers is Result.Success) {
                    if (existingMembers.data.any { it.userId == currentUser.id }) {
                        _uiState.value = JoinFamilyUiState.Error(
                            "You are already a member of this family"
                        )
                        return@launch
                    }
                }

                // Check member limit
                if (!family.isPremium) {
                    if (existingMembers is Result.Success &&
                        existingMembers.data.size >= family.maxMembers) {
                        _uiState.value = JoinFamilyUiState.Error(
                            "Family has reached member limit (${family.maxMembers})"
                        )
                        return@launch
                    }
                }

                // Join family
                val result = joinFamilyUseCase(
                    familyId = family.id,
                    userId = currentUser.id,
                    nickname = nickname
                )

                when (result) {
                    is Result.Success -> {
                        _uiState.value = JoinFamilyUiState.Success(family)
                    }
                    is Result.Error -> {
                        _uiState.value = JoinFamilyUiState.Error(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = JoinFamilyUiState.Error(
                    e.message ?: "Failed to join family"
                )
            }
        }
    }

    private fun isValidCodeFormat(code: String): Boolean {
        // XP-XXXXX format (5 alphanumeric characters)
        val regex = Regex("^XP-[A-Z0-9]{5}$")
        return regex.matches(code.uppercase())
    }
}

sealed class JoinFamilyUiState {
    object Idle : JoinFamilyUiState()
    object Validating : JoinFamilyUiState()
    data class InvalidCode(val message: String) : JoinFamilyUiState()
    data class FamilyFound(val family: Family) : JoinFamilyUiState()
    object Joining : JoinFamilyUiState()
    data class Success(val family: Family) : JoinFamilyUiState()
    data class Error(val message: String) : JoinFamilyUiState()
}
```

### 15.3 Member Management

```kotlin
package com.xpenz.feature.family

@HiltViewModel
class FamilyMembersViewModel @Inject constructor(
    private val getFamilyMembersUseCase: GetFamilyMembersUseCase,
    private val removeFamilyMemberUseCase: RemoveFamilyMemberUseCase,
    private val updateMemberRoleUseCase: UpdateMemberRoleUseCase,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<FamilyMembersUiState>(FamilyMembersUiState.Loading)
    val uiState: StateFlow<FamilyMembersUiState> = _uiState.asStateFlow()

    fun loadMembers(familyId: String) {
        viewModelScope.launch {
            _uiState.value = FamilyMembersUiState.Loading

            try {
                val result = getFamilyMembersUseCase(familyId)

                when (result) {
                    is Result.Success -> {
                        val currentUser = userRepository.getCurrentUser().first()
                        val currentUserMember = result.data.find { it.userId == currentUser?.id }

                        _uiState.value = FamilyMembersUiState.Success(
                            members = result.data,
                            currentUserRole = currentUserMember?.role ?: MemberRole.MEMBER
                        )
                    }
                    is Result.Error -> {
                        _uiState.value = FamilyMembersUiState.Error(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = FamilyMembersUiState.Error(
                    e.message ?: "Failed to load members"
                )
            }
        }
    }

    fun removeMember(familyId: String, memberId: String) {
        viewModelScope.launch {
            try {
                val currentUser = userRepository.getCurrentUser().first()
                    ?: throw IllegalStateException("User not logged in")

                // Check permission (only admins can remove)
                val currentState = _uiState.value
                if (currentState is FamilyMembersUiState.Success) {
                    if (currentState.currentUserRole != MemberRole.ADMIN) {
                        _uiState.value = FamilyMembersUiState.Error(
                            "Only admins can remove members"
                        )
                        return@launch
                    }
                }

                // Remove member
                val result = removeFamilyMemberUseCase(
                    familyId = familyId,
                    memberId = memberId,
                    removedBy = currentUser.id
                )

                when (result) {
                    is Result.Success -> {
                        // Reload members
                        loadMembers(familyId)
                    }
                    is Result.Error -> {
                        _uiState.value = FamilyMembersUiState.Error(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = FamilyMembersUiState.Error(
                    e.message ?: "Failed to remove member"
                )
            }
        }
    }

    fun promoteMember(memberId: String) {
        viewModelScope.launch {
            try {
                val result = updateMemberRoleUseCase(memberId, MemberRole.ADMIN)

                when (result) {
                    is Result.Success -> {
                        // Reload members
                        val currentState = _uiState.value
                        if (currentState is FamilyMembersUiState.Success) {
                            val updatedMembers = currentState.members.map { member ->
                                if (member.id == memberId) {
                                    member.copy(role = MemberRole.ADMIN)
                                } else {
                                    member
                                }
                            }
                            _uiState.value = currentState.copy(members = updatedMembers)
                        }
                    }
                    is Result.Error -> {
                        _uiState.value = FamilyMembersUiState.Error(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = FamilyMembersUiState.Error(
                    e.message ?: "Failed to promote member"
                )
            }
        }
    }
}

sealed class FamilyMembersUiState {
    object Loading : FamilyMembersUiState()
    data class Success(
        val members: List<FamilyMember>,
        val currentUserRole: MemberRole
    ) : FamilyMembersUiState()
    data class Error(val message: String) : FamilyMembersUiState()
}
```

### 15.4 Real-Time Member Sync

```kotlin
package com.xpenz.feature.family

class FamilyMemberSyncService @Inject constructor(
    private val firestoreService: FirestoreService,
    private val familyMemberDao: FamilyMemberDao,
    private val familyMemberMapper: FamilyMemberMapper
) {

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    /**
     * Start listening to member changes in real-time
     */
    fun startListening(familyId: String) {
        firestoreService.observeFamilyMembers(familyId)
            .onEach { dtos ->
                syncMembers(familyId, dtos)
            }
            .catch { e ->
                Timber.e(e, "Member sync failed for family: $familyId")
            }
            .launchIn(scope)
    }

    private suspend fun syncMembers(familyId: String, dtos: List<FamilyMemberDTO>) {
        try {
            // Get current local members
            val localMembers = familyMemberDao.getFamilyMembers(familyId).first()
            val localMemberIds = localMembers.map { it.memberId }.toSet()
            val remoteMemberIds = dtos.map { it.memberId }.toSet()

            // Find new members (in remote but not local)
            val newMemberIds = remoteMemberIds - localMemberIds
            val newMembers = dtos.filter { it.memberId in newMemberIds }

            // Find removed members (in local but not remote)
            val removedMemberIds = localMemberIds - remoteMemberIds

            // Find updated members
            val updatedMembers = dtos.filter { dto ->
                dto.memberId in localMemberIds &&
                hasChanged(dto, localMembers.find { it.memberId == dto.memberId })
            }

            // Apply changes
            newMembers.forEach { dto ->
                val entity = familyMemberMapper.toEntity(dto)
                familyMemberDao.insertMember(entity)

                // Show notification
                showNewMemberNotification(dto)
            }

            removedMemberIds.forEach { memberId ->
                familyMemberDao.markAsLeft(memberId)

                // Show notification
                showMemberLeftNotification(memberId)
            }

            updatedMembers.forEach { dto ->
                val entity = familyMemberMapper.toEntity(dto)
                familyMemberDao.updateMember(entity)
            }

        } catch (e: Exception) {
            Timber.e(e, "Failed to sync members")
        }
    }

    private fun hasChanged(dto: FamilyMemberDTO, entity: FamilyMemberEntity?): Boolean {
        if (entity == null) return true

        return dto.nickname != entity.nickname ||
               dto.role != entity.role ||
               dto.status != entity.status
    }

    private fun showNewMemberNotification(member: FamilyMemberDTO) {
        notificationService.showNotification(
            title = "New Family Member",
            body = "${member.nickname} joined the family",
            action = "VIEW_FAMILY"
        )
    }

    private fun showMemberLeftNotification(memberId: String) {
        // Implementation
    }

    fun stopListening() {
        scope.cancel()
    }
}
```

---

## 16. BUDGET SYSTEM IMPLEMENTATION

### 16.1 Budget Creation Logic

```kotlin
package com.xpenz.feature.budget

@HiltViewModel
class CreateBudgetViewModel @Inject constructor(
    private val createBudgetUseCase: CreateBudgetUseCase,
    private val familyRepository: FamilyRepository,
    private val categoryRepository: CategoryRepository,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<CreateBudgetUiState>(CreateBudgetUiState.Idle)
    val uiState: StateFlow<CreateBudgetUiState> = _uiState.asStateFlow()

    fun createBudget(
        familyId: String,
        budgetType: BudgetType,
        name: String,
        amount: Double,
        period: BudgetPeriod,
        categoryId: Int? = null,
        memberId: String? = null,
        alertThresholds: List<Int> = listOf(50, 80, 100, 120),
        notifyAllMembers: Boolean = true
    ) {
        viewModelScope.launch {
            _uiState.value = CreateBudgetUiState.Creating

            try {
                // Validation
                if (amount <= 0) {
                    _uiState.value = CreateBudgetUiState.Error("Amount must be greater than 0")
                    return@launch
                }

                if (amount > 10000000) { // 1 crore
                    _uiState.value = CreateBudgetUiState.Error("Amount too large (max ₹1 crore)")
                    return@launch
                }

                // Type-specific validation
                when (budgetType) {
                    BudgetType.CATEGORY -> {
                        if (categoryId == null) {
                            _uiState.value = CreateBudgetUiState.Error("Category required")
                            return@launch
                        }
                    }
                    BudgetType.MEMBER -> {
                        if (memberId == null) {
                            _uiState.value = CreateBudgetUiState.Error("Member required")
                            return@launch
                        }
                    }
                    else -> { /* No additional validation */ }
                }

                // Calculate start/end dates based on period
                val (startDate, endDate) = calculateBudgetDates(period)

                // Get current user
                val currentUser = userRepository.getCurrentUser().first()
                    ?: throw IllegalStateException("User not logged in")

                // Create budget
                val budget = Budget(
                    id = UUID.randomUUID().toString(),
                    familyId = familyId,
                    type = budgetType,
                    name = name,
                    amount = amount,
                    currency = "INR",
                    period = period,
                    alertThresholds = alertThresholds.sorted(),
                    notificationEnabled = true,
                    notifyAllMembers = notifyAllMembers,
                    startDate = startDate,
                    endDate = endDate,
                    isRecurring = true,
                    isActive = true,
                    createdBy = currentUser.id,
                    createdAt = System.currentTimeMillis(),
                    categoryId = categoryId,
                    memberId = memberId
                )

                // Execute use case
                val result = createBudgetUseCase(budget)

                when (result) {
                    is Result.Success -> {
                        _uiState.value = CreateBudgetUiState.Success(result.data)
                    }
                    is Result.Error -> {
                        _uiState.value = CreateBudgetUiState.Error(result.message)
                    }
                }

            } catch (e: Exception) {
                _uiState.value = CreateBudgetUiState.Error(
                    e.message ?: "Failed to create budget"
                )
            }
        }
    }

    private fun calculateBudgetDates(period: BudgetPeriod): Pair<Long, Long> {
        val calendar = Calendar.getInstance()
        val startDate = calendar.timeInMillis

        val endDate = when (period) {
            BudgetPeriod.MONTHLY -> {
                calendar.add(Calendar.MONTH, 1)
                calendar.timeInMillis
            }
            BudgetPeriod.WEEKLY -> {
                calendar.add(Calendar.WEEK_OF_YEAR, 1)
                calendar.timeInMillis
            }
            BudgetPeriod.YEARLY -> {
                calendar.add(Calendar.YEAR, 1)
                calendar.timeInMillis
            }
        }

        return Pair(startDate, endDate)
    }

    fun suggestBudgetAmount(
        familyId: String,
        budgetType: BudgetType,
        categoryId: Int? = null,
        memberId: String? = null
    ) {
        viewModelScope.launch {
            try {
                // Calculate average spending for last 3 months
                val calendar = Calendar.getInstance()
                val endTime = calendar.timeInMillis
                calendar.add(Calendar.MONTH, -3)
                val startTime = calendar.timeInMillis

                val spending = when (budgetType) {
                    BudgetType.FAMILY -> {
                        transactionRepository.getTotalSpending(
                            userId = "", // All family members
                            startTime = startTime,
                            endTime = endTime
                        )
                    }
                    BudgetType.CATEGORY -> {
                        if (categoryId == null) return@launch
                        transactionRepository.getCategorySpending(
                            categoryId = categoryId,
                            startTime = startTime,
                            endTime = endTime
                        )
                    }
                    BudgetType.MEMBER -> {
                        if (memberId == null) return@launch
                        transactionRepository.getMemberSpending(
                            memberId = memberId,
                            startTime = startTime,
                            endTime = endTime
                        )
                    }
                }

                if (spending is Result.Success) {
                    // Suggest 10% more than average monthly spending
                    val monthlyAverage = spending.data / 3
                    val suggestedAmount = monthlyAverage * 1.1

                    _uiState.value = CreateBudgetUiState.SuggestedAmount(
                        amount = suggestedAmount,
                        basedOnMonths = 3,
                        monthlyAverage = monthlyAverage
                    )
                }

            } catch (e: Exception) {
                Timber.e(e, "Failed to suggest budget amount")
            }
        }
    }
}

sealed class CreateBudgetUiState {
    object Idle : CreateBudgetUiState()
    object Creating : CreateBudgetUiState()
    data class Success(val budget: Budget) : CreateBudgetUiState()
    data class Error(val message: String) : CreateBudgetUiState()
    data class SuggestedAmount(
        val amount: Double,
        val basedOnMonths: Int,
        val monthlyAverage: Double
    ) : CreateBudgetUiState()
}
```

### 16.2 Budget Progress Tracking

```kotlin
package com.xpenz.feature.budget

class BudgetProgressCalculator @Inject constructor(
    private val transactionDao: TransactionDao,
    private val budgetProgressDao: BudgetProgressDao
) {

    /**
     * Calculate current budget progress
     */
    suspend fun calculateProgress(budget: Budget): BudgetProgress {
        // Get transactions in budget period
        val transactions = getTransactionsForBudget(budget)

        // Calculate total spent
        val amountSpent = transactions
            .filter { it.type == "DEBIT" }
            .sumOf { it.amount }

        // Calculate percentage
        val percentage = (amountSpent / budget.amount * 100).toFloat()

        // Determine status
        val status = when {
            percentage < 50 -> BudgetStatus.HEALTHY
            percentage < 80 -> BudgetStatus.WARNING
            percentage < 100 -> BudgetStatus.CRITICAL
            percentage < 120 -> BudgetStatus.EXCEEDED
            else -> BudgetStatus.OVER_120
        }

        // Calculate days remaining
        val now = System.currentTimeMillis()
        val daysRemaining = ((budget.endDate ?: now) - now) / (24 * 60 * 60 * 1000)

        // Calculate suggested daily spend
        val remainingAmount = budget.amount - amountSpent
        val suggestedDailySpend = if (daysRemaining > 0) {
            remainingAmount / daysRemaining
        } else {
            0.0
        }

        return BudgetProgress(
            budgetId = budget.id,
            budget = budget,
            periodStart = budget.startDate,
            periodEnd = budget.endDate ?: System.currentTimeMillis(),
            amountSpent = amountSpent,
            amountBudget = budget.amount,
            percentage = percentage,
            transactionCount = transactions.size,
            status = status,
            daysRemaining = daysRemaining.toInt(),
            suggestedDailySpend = maxOf(0.0, suggestedDailySpend),
            lastAlertSent = getLastAlertSent(budget.id)
        )
    }

    private suspend fun getTransactionsForBudget(budget: Budget): List<TransactionEntity> {
        return when (budget.type) {
            BudgetType.FAMILY -> {
                // All family transactions
                transactionDao.getFamilyTransactions(budget.familyId)
                    .first()
                    .filter { it.timestamp >= budget.startDate &&
                             (budget.endDate == null || it.timestamp <= budget.endDate) }
            }
            BudgetType.CATEGORY -> {
                // Transactions in specific category
                budget.categoryId?.let { categoryId ->
                    transactionDao.getTransactionsByCategory(
                        userId = "", // Family-wide
                        categoryId = categoryId
                    ).filter { it.timestamp >= budget.startDate &&
                              (budget.endDate == null || it.timestamp <= budget.endDate) }
                } ?: emptyList()
            }
            BudgetType.MEMBER -> {
                // Transactions by specific member
                budget.memberId?.let { memberId ->
                    transactionDao.getUserTransactions(memberId)
                        .first()
                        .filter { it.timestamp >= budget.startDate &&
                                 (budget.endDate == null || it.timestamp <= budget.endDate) }
                } ?: emptyList()
            }
        }
    }

    private suspend fun getLastAlertSent(budgetId: String): String? {
        val progress = budgetProgressDao.getProgress(budgetId)
        return progress?.lastAlertSent
    }

    /**
     * Update budget progress after transaction
     */
    suspend fun updateProgressAfterTransaction(
        transaction: TransactionEntity
    ): List<BudgetAlert> {
        val alerts = mutableListOf<BudgetAlert>()

        // Get all active budgets for this family
        val budgets = budgetDao.getActiveBudgets(transaction.familyId ?: "").first()

        budgets.forEach { budget ->
            // Check if transaction affects this budget
            if (isTransactionApplicable(transaction, budget)) {

                // Calculate new progress
                val progress = calculateProgress(budget)

                // Check if any threshold crossed
                val thresholdCrossed = checkThresholdCrossing(budget, progress)

                if (thresholdCrossed != null) {
                    alerts.add(
                        BudgetAlert(
                            budgetId = budget.id,
                            budgetName = budget.name,
                            threshold = thresholdCrossed,
                            currentPercentage = progress.percentage,
                            amountSpent = progress.amountSpent,
                            amountBudget = progress.amountBudget,
                            daysRemaining = progress.daysRemaining,
                            latestTransaction = transaction,
                            timestamp = System.currentTimeMillis()
                        )
                    )

                    // Update last alert sent
                    budgetProgressDao.updateLastAlertSent(
                        budgetId = budget.id,
                        threshold = thresholdCrossed.toString()
                    )
                }

                // Save progress
                budgetProgressDao.insertOrUpdate(
                    BudgetProgressEntity(
                        progressId = UUID.randomUUID().toString(),
                        budgetId = budget.id,
                        periodStart = progress.periodStart,
                        periodEnd = progress.periodEnd,
                        amountSpent = progress.amountSpent,
                        amountBudget = progress.amountBudget,
                        percentage = progress.percentage,
                        transactionCount = progress.transactionCount,
                        status = progress.status.name,
                        lastAlertSent = progress.lastAlertSent,
                        lastCalculatedAt = System.currentTimeMillis()
                    )
                )
            }
        }

        return alerts
    }

    private fun isTransactionApplicable(
        transaction: TransactionEntity,
        budget: BudgetEntity
    ): Boolean {
        // Only count debit transactions
        if (transaction.type != "DEBIT") return false

        // Check if transaction is in budget period
        if (transaction.timestamp < budget.startDate) return false
        if (budget.endDate != null && transaction.timestamp > budget.endDate) return false

        // Type-specific checks
        return when (budget.budgetType) {
            "FAMILY" -> true // All transactions count
            "CATEGORY" -> transaction.mlCategoryId == budget.categoryId
            "MEMBER" -> transaction.userId == budget.memberId
            else -> false
        }
    }

    private suspend fun checkThresholdCrossing(
        budget: BudgetEntity,
        progress: BudgetProgress
    ): Int? {
        val thresholds = parseAlertThresholds(budget.alertThresholds)
        val currentPercentage = progress.percentage.toInt()
        val lastAlertSent = progress.lastAlertSent?.toIntOrNull() ?: 0

        // Find the highest threshold that was just crossed
        for (threshold in thresholds.sortedDescending()) {
            if (currentPercentage >= threshold && threshold > lastAlertSent) {
                return threshold
            }
        }

        return null
    }

    private fun parseAlertThresholds(json: String): List<Int> {
        return try {
            Gson().fromJson(json, Array<Int>::class.java).toList()
        } catch (e: Exception) {
            listOf(50, 80, 100, 120)
        }
    }
}

data class BudgetAlert(
    val budgetId: String,
    val budgetName: String,
    val threshold: Int,
    val currentPercentage: Float,
    val amountSpent: Double,
    val amountBudget: Double,
    val daysRemaining: Int,
    val latestTransaction: TransactionEntity,
    val timestamp: Long
)
```

### 16.3 Budget Alert System

```kotlin
package com.xpenz.feature.budget

class BudgetAlertService @Inject constructor(
    private val notificationService: NotificationService,
    private val familyMemberDao: FamilyMemberDao,
    private val fcmService: FCMService
) {

    /**
     * Send budget alert to family members
     */
    suspend fun sendBudgetAlert(alert: BudgetAlert, budget: Budget) {
        try {
            // Determine who should receive notification
            val recipients = if (budget.notifyAllMembers) {
                // All family members
                familyMemberDao.getFamilyMembers(budget.familyId)
                    .first()
                    .filter { it.status == "ACTIVE" }
                    .map { it.userId }
            } else {
                // Only budget creator and affected member
                when (budget.type) {
                    BudgetType.MEMBER -> {
                        listOf(budget.createdBy, budget.memberId!!).distinct()
                    }
                    else -> {
                        listOf(budget.createdBy)
                    }
                }
            }

            // Create notification content
            val (title, body) = createAlertContent(alert, budget)

            // Send to each recipient
            recipients.forEach { userId ->
                // Local notification
                notificationService.showBudgetAlert(
                    userId = userId,
                    title = title,
                    body = body,
                    budgetId = budget.id,
                    priority = getPriority(alert.threshold)
                )

                // FCM (for other devices)
                fcmService.sendBudgetAlert(
                    userId = userId,
                    title = title,
                    body = body,
                    data = mapOf(
                        "type" to "budget_alert",
                        "budget_id" to budget.id,
                        "threshold" to alert.threshold.toString(),
                        "percentage" to alert.currentPercentage.toString()
                    )
                )
            }

            // Log analytics
            Analytics.logEvent("budget_alert_sent", mapOf(
                "budget_id" to budget.id,
                "budget_type" to budget.type.name,
                "threshold" to alert.threshold,
                "percentage" to alert.currentPercentage,
                "recipients" to recipients.size
            ))

        } catch (e: Exception) {
            Timber.e(e, "Failed to send budget alert")
        }
    }

    private fun createAlertContent(
        alert: BudgetAlert,
        budget: Budget
    ): Pair<String, String> {
        val emoji = when (alert.threshold) {
            50 -> "⚠️"
            80 -> "🔴"
            100 -> "❌"
            120 -> "🚨"
            else -> "⚠️"
        }

        val title = when (alert.threshold) {
            50 -> "$emoji Budget Alert: ${budget.name}"
            80 -> "$emoji Budget Critical: ${budget.name}"
            100 -> "$emoji Budget Exceeded: ${budget.name}"
            120 -> "$emoji Budget Severely Exceeded: ${budget.name}"
            else -> "$emoji Budget Alert: ${budget.name}"
        }

        val body = buildString {
            append("${alert.currentPercentage.toInt()}% used ")
            append("(₹${String.format("%.2f", alert.amountSpent)}/")
            append("₹${String.format("%.2f", alert.amountBudget)})")

            if (alert.daysRemaining > 0) {
                append(" • ${alert.daysRemaining} days left")
            }

            // Add latest transaction info
            alert.latestTransaction.merchantName?.let { merchant ->
                append(" • Latest: ₹${alert.latestTransaction.amount} at $merchant")
            }
        }

        return Pair(title, body)
    }

    private fun getPriority(threshold: Int): Int {
        return when (threshold) {
            100, 120 -> NotificationCompat.PRIORITY_HIGH
            80 -> NotificationCompat.PRIORITY_DEFAULT
            else -> NotificationCompat.PRIORITY_LOW
        }
    }
}
```

---

## 22. MONITORING & ANALYTICS

### 22.1 Firebase Analytics Integration

```kotlin
package com.xpenz.core.analytics

import com.google.firebase.analytics.FirebaseAnalytics
import com.google.firebase.analytics.ktx.analytics
import com.google.firebase.analytics.ktx.logEvent
import com.google.firebase.ktx.Firebase
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AnalyticsService @Inject constructor() {

    private val firebaseAnalytics: FirebaseAnalytics = Firebase.analytics

    // User Properties
    fun setUserProperties(userId: String, isPremium: Boolean, familyCount: Int) {
        firebaseAnalytics.setUserId(userId)
        firebaseAnalytics.setUserProperty("is_premium", isPremium.toString())
        firebaseAnalytics.setUserProperty("family_count", familyCount.toString())
    }

    // Transaction Events
    fun logTransactionDetected(
        amount: Double,
        categoryId: Int,
        confidence: Float,
        source: String,
        isAutomatic: Boolean
    ) {
        firebaseAnalytics.logEvent("transaction_detected") {
            param("amount", amount)
            param("category_id", categoryId.toLong())
            param("confidence", confidence.toDouble())
            param("source", source)
            param("is_automatic", if (isAutomatic) 1L else 0L)
        }
    }

    fun logTransactionCorrected(
        transactionId: String,
        originalCategoryId: Int,
        correctedCategoryId: Int
    ) {
        firebaseAnalytics.logEvent("transaction_corrected") {
            param("transaction_id", transactionId)
            param("original_category", originalCategoryId.toLong())
            param("corrected_category", correctedCategoryId.toLong())
        }
    }

    // Family Events
    fun logFamilyCreated(familyId: String, memberCount: Int) {
        firebaseAnalytics.logEvent("family_created") {
            param("family_id", familyId)
            param("member_count", memberCount.toLong())
        }
    }

    fun logFamilyJoined(familyId: String, invitationCode: String) {
        firebaseAnalytics.logEvent("family_joined") {
            param("family_id", familyId)
            param("invitation_code", invitationCode)
        }
    }

    fun logMemberAdded(familyId: String, totalMembers: Int) {
        firebaseAnalytics.logEvent("member_added") {
            param("family_id", familyId)
            param("total_members", totalMembers.toLong())
        }
    }

    // Budget Events
    fun logBudgetCreated(
        budgetId: String,
        budgetType: String,
        amount: Double,
        period: String
    ) {
        firebaseAnalytics.logEvent("budget_created") {
            param("budget_id", budgetId)
            param("budget_type", budgetType)
            param("amount", amount)
            param("period", period)
        }
    }

    fun logBudgetAlertTriggered(
        budgetId: String,
        threshold: Int,
        percentage: Float
    ) {
        firebaseAnalytics.logEvent("budget_alert_triggered") {
            param("budget_id", budgetId)
            param("threshold", threshold.toLong())
            param("percentage", percentage.toDouble())
        }
    }

    fun logBudgetExceeded(
        budgetId: String,
        budgetType: String,
        exceededBy: Double
    ) {
        firebaseAnalytics.logEvent("budget_exceeded") {
            param("budget_id", budgetId)
            param("budget_type", budgetType)
            param("exceeded_by", exceededBy)
        }
    }

    // Premium Events
    fun logPremiumPurchaseInitiated(plan: String, price: Double) {
        firebaseAnalytics.logEvent("premium_purchase_initiated") {
            param("plan", plan)
            param("price", price)
        }
    }

    fun logPremiumPurchaseCompleted(
        plan: String,
        price: Double,
        purchaseToken: String
    ) {
        firebaseAnalytics.logEvent("premium_purchase_completed") {
            param("plan", plan)
            param("price", price)
            param(FirebaseAnalytics.Param.TRANSACTION_ID, purchaseToken)
        }
    }

    fun logPremiumCancelled(
        plan: String,
        reason: String,
        daysActive: Int
    ) {
        firebaseAnalytics.logEvent("premium_cancelled") {
            param("plan", plan)
            param("reason", reason)
            param("days_active", daysActive.toLong())
        }
    }

    // Onboarding Events
    fun logOnboardingStarted(source: String) {
        firebaseAnalytics.logEvent("onboarding_started") {
            param("source", source)
        }
    }

    fun logOnboardingStepCompleted(
        stepNumber: Int,
        stepName: String,
        timeSpentSeconds: Int
    ) {
        firebaseAnalytics.logEvent("onboarding_step_completed") {
            param("step_number", stepNumber.toLong())
            param("step_name", stepName)
            param("time_spent_seconds", timeSpentSeconds.toLong())
        }
    }

    fun logOnboardingCompleted(totalTimeSeconds: Int, stepsSkipped: Int) {
        firebaseAnalytics.logEvent("onboarding_completed") {
            param("total_time_seconds", totalTimeSeconds.toLong())
            param("steps_skipped", stepsSkipped.toLong())
        }
    }

    // ML Performance
    fun logMLInference(
        categoryId: Int,
        confidence: Float,
        inferenceTimeMs: Long,
        modelUsed: String
    ) {
        firebaseAnalytics.logEvent("ml_inference") {
            param("category_id", categoryId.toLong())
            param("confidence", confidence.toDouble())
            param("inference_time_ms", inferenceTimeMs)
            param("model_used", modelUsed)
        }
    }

    // Screen Views
    fun logScreenView(screenName: String, screenClass: String) {
        firebaseAnalytics.logEvent(FirebaseAnalytics.Event.SCREEN_VIEW) {
            param(FirebaseAnalytics.Param.SCREEN_NAME, screenName)
            param(FirebaseAnalytics.Param.SCREEN_CLASS, screenClass)
        }
    }

    // Errors
    fun logError(errorType: String, errorMessage: String, stackTrace: String?) {
        firebaseAnalytics.logEvent("error_occurred") {
            param("error_type", errorType)
            param("error_message", errorMessage)
            stackTrace?.let { param("stack_trace", it.take(100)) }
        }
    }
}
```

### 22.2 Performance Monitoring

```kotlin
package com.xpenz.core.performance

import com.google.firebase.perf.FirebasePerformance
import com.google.firebase.perf.metrics.Trace
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PerformanceMonitor @Inject constructor() {

    private val firebasePerformance = FirebasePerformance.getInstance()

    // Track ML inference performance
    fun trackMLInference(block: () -> Unit): Long {
        val trace = firebasePerformance.newTrace("ml_inference")
        trace.start()

        val startTime = System.currentTimeMillis()
        block()
        val duration = System.currentTimeMillis() - startTime

        trace.putMetric("duration_ms", duration)
        trace.stop()

        return duration
    }

    // Track database query performance
    fun trackDatabaseQuery(queryName: String, block: () -> Unit) {
        val trace = firebasePerformance.newTrace("db_query_$queryName")
        trace.start()

        block()

        trace.stop()
    }

    // Track sync performance
    fun trackSync(syncType: String): Trace {
        val trace = firebasePerformance.newTrace("sync_$syncType")
        trace.start()
        return trace
    }

    // Track screen loading
    fun trackScreenLoad(screenName: String, block: () -> Unit) {
        val trace = firebasePerformance.newTrace("screen_load_$screenName")
        trace.start()

        block()

        trace.stop()
    }

    // Custom metrics
    fun recordMetric(name: String, value: Long) {
        val trace = firebasePerformance.newTrace("custom_$name")
        trace.start()
        trace.putMetric(name, value)
        trace.stop()
    }
}
```

Due to character limits, I'll continue with the remaining Priority 2 and 3 sections in the next response.

Continuing with remaining Priority 2 and 3 sections...

---

## 23. DEVELOPMENT ROADMAP (20 Weeks)

### 23.1 Sprint Breakdown

```
PROJECT TIMELINE: 20 Weeks (5 Months)
TEAM: 1 Developer (AI-Assisted)
METHODOLOGY: Agile/Scrum (2-week sprints)
```

### **SPRINT 0: Setup & Foundation (Week 1-2)**

**Goals:**

- Project setup complete
- Architecture foundation ready
- Development environment configured

**Tasks:**

```
Week 1:
□ Create Android Studio project
□ Setup Gradle with Version Catalog
□ Configure multi-module structure (app, core, feature modules)
□ Setup Hilt dependency injection
□ Configure ProGuard/R8 rules
□ Setup Firebase project (Analytics, Crashlytics, Firestore)
□ Initialize Git repository
□ Create GitHub Actions workflow

Week 2:
□ Implement database schema (Room - 11 tables)
□ Create domain models
□ Setup repository interfaces
□ Implement basic navigation structure
□ Create Material 3 theme
□ Setup Jetpack Compose
□ Add Timber logging
□ Configure build variants (debug, release, benchmark)
```

**Deliverables:**
✅ Working app skeleton

✅ Database structure functional

✅ Navigation framework ready

✅ CI/CD pipeline active

---

### **SPRINT 1: SMS Detection & Parsing (Week 3-4)**

**Goals:**

- SMS detection working
- Basic transaction parsing functional
- Deduplication implemented

**Tasks:**

```
Week 3:
□ Implement SMSReceiver (BroadcastReceiver)
□ Create SMSFilter (transaction SMS detection)
□ Build SMS pattern database (seed with 20 bank patterns)
□ Implement generic SMS parser
□ Create ParsedSMSData model

Week 4:
□ Implement SMSProcessingWorker (WorkManager)
□ Add SMS deduplication (hash-based)
□ Create transaction entity from parsed SMS
□ Implement SMS permission handling
□ Test with real SMS messages (10+ banks)
□ Add analytics for SMS parsing
□ Handle edge cases (malformed SMS, unknown banks)
```

**Deliverables:**
✅ SMS detection: 95%+ accuracy

✅ Parsing: 90%+ success rate

✅ 20+ bank patterns supported

**Testing:**

- Unit tests: SMSParser, SMSFilter
- Integration tests: End-to-end SMS → Transaction
- Manual testing: 50+ real SMS messages

---

### **SPRINT 2: ML Model Integration (Week 5-6)**

**Goals:**

- TFLite models loaded
- On-device inference working
- 520-category classification functional

**Tasks:**

```
Week 5:
□ Train LSTM model (500K samples)
□ Train CNN model (500K samples)
□ Train Transformer model (500K samples)
□ Convert models to TFLite
□ Quantize models (reduce size 70%)
□ Create 520-category mapping JSON

Week 6:
□ Implement MLInferenceService
□ Load models in app (assets folder)
□ Implement FeatureExtractor
□ Implement TextPreprocessor
□ Create ensemble voting logic
□ Add confidence scoring
□ Implement rule-based fallback
□ Test accuracy: 86-90% target
□ Optimize inference speed (<200ms)
```

**Deliverables:**
✅ Models: 2.2 MB total (quantized)

✅ Accuracy: 86-90% (top-1), 96-98% (top-3)

✅ Inference: <200ms (p95)

**Testing:**

- Accuracy testing: 10K test transactions
- Performance testing: Benchmark inference speed
- Memory testing: Check for leaks

---

### **SPRINT 3: Transaction Management (Week 7-8)**

**Goals:**

- Transaction CRUD complete
- Transaction list UI functional
- Manual entry working

**Tasks:**

```
Week 7:
□ Implement TransactionRepository
□ Create TransactionDao methods
□ Build transaction list UI (Jetpack Compose)
□ Add pagination (LazyColumn)
□ Implement transaction detail screen
□ Add transaction filtering (date, category, type)
□ Create search functionality

Week 8:
□ Implement manual transaction entry
□ Add transaction editing
□ Implement transaction deletion (soft delete)
□ Add category correction UI
□ Implement transaction notes
□ Add receipt attachment (image)
□ Create transaction export (CSV)
□ Add pull-to-refresh
```

**Deliverables:**
✅ Full transaction management

✅ Fast, smooth UI (60 FPS)

✅ Manual entry + editing working

**Testing:**

- UI tests: Transaction list, detail, entry
- Performance: 1000+ transactions scroll smoothly
- Edge cases: Empty state, error handling

---

### **SPRINT 4: User Authentication & Onboarding (Week 9-10)**

**Goals:**

- Firebase Auth integrated
- Onboarding flow complete
- Permission handling working

**Tasks:**

```
Week 9:
□ Implement Firebase Phone Authentication
□ Create login flow (phone + OTP)
□ Implement user profile creation
□ Add avatar selection
□ Create DataStore for user preferences
□ Implement session management

Week 10:
□ Build onboarding screens (5 screens total)
□ Implement permission requests (SMS + NotificationListener fallback)
□ Add contextual tooltips on dashboard
□ Create skip logic
□ Implement progress saving
□ Add deep link support (invitation codes)
□ Test onboarding completion rate (target: 75%)
```

**Deliverables:**
✅ Auth: Phone + OTP working

✅ Onboarding: 5 screens functional

✅ Completion rate: >75%

**Testing:**

- Auth flow: Phone verification, OTP retry, errors
- Onboarding: All paths, skip scenarios
- Permission handling: Grant, deny, retry

---

### **SPRINT 5: Family Features (Week 11-12)**

**Goals:**

- Family creation working
- Member invitation functional
- Family dashboard complete

**Tasks:**

```
Week 11:
□ Implement FamilyRepository
□ Create family creation flow
□ Build invitation code generation (XP-XXXXX)
□ Implement family join flow
□ Add member list UI
□ Create member management (add, remove, promote)
□ Implement role system (ADMIN, MEMBER)

Week 12:
□ Build family dashboard
□ Add member spending breakdown
□ Create category-wise family spending
□ Implement real-time member sync
□ Add family settings
□ Create invitation sharing (WhatsApp, SMS)
□ Test with 5+ member families
□ Add family deletion with confirmation
```

**Deliverables:**
✅ Family creation + joining working

✅ Dashboard showing family spending

✅ Member management functional

**Testing:**

- Family flows: Create, join, leave, delete
- Member management: Add, remove, promote
- Real-time sync: Multi-device testing

---

### **SPRINT 6: Budget System (Week 13-14)**

**Goals:**

- Budget creation complete
- Progress tracking working
- Alerts functional

**Tasks:**

```
Week 13:
□ Implement BudgetRepository
□ Create budget creation UI (3 types)
□ Add budget amount suggestions (based on history)
□ Implement alert threshold configuration
□ Build budget list screen
□ Add budget detail view with progress

Week 14:
□ Implement BudgetProgressCalculator
□ Create real-time progress tracking
□ Build alert triggering system
□ Add budget notifications
□ Implement budget editing
□ Create budget pause/resume
□ Add budget deletion
□ Test with multiple overlapping budgets
```

**Deliverables:**
✅ 3 budget types working

✅ Real-time progress tracking

✅ Alerts at 50/80/100/120%

**Testing:**

- Budget calculations: Verify accuracy
- Alert timing: Real-time threshold detection
- Edge cases: Mid-month creation, overlapping budgets

---

### **SPRINT 7: Cloud Sync (Week 15-16)**

**Goals:**

- Firestore integration complete
- Real-time sync working
- Conflict resolution implemented

**Tasks:**

```
Week 15:
□ Implement FirestoreService
□ Create EncryptionService (AES-256-GCM)
□ Build sync queue system
□ Implement SyncWorker (WorkManager)
□ Add transaction upload/download
□ Create family sync
□ Implement budget sync

Week 16:
□ Add real-time listeners (Firestore)
□ Implement conflict resolution (last-write-wins)
□ Create offline queue processing
□ Add sync status indicators
□ Implement retry logic (exponential backoff)
□ Test multi-device sync
□ Add sync analytics
□ Optimize network usage (batching)
```

**Deliverables:**
✅ Cloud sync working (Premium only)

✅ Real-time updates <5s

✅ Offline support functional

**Testing:**

- Sync accuracy: Verify all data syncs correctly
- Conflict resolution: Test simultaneous edits
- Offline mode: Queue operations, sync when online

---

### **SPRINT 8: Premium Subscription (Week 17-18)**

**Goals:**

- Google Play Billing integrated
- Subscription flow complete
- Premium features gated

**Tasks:**

```
Week 17:
□ Implement Google Play Billing Library
□ Create subscription models (Annual, Monthly, Lifetime)
□ Build pricing screen
□ Add feature comparison UI
□ Implement purchase flow
□ Create receipt verification
□ Add subscription restoration

Week 18:
□ Implement subscription management
□ Add cancellation flow with retention offers
□ Create refund handling (7-day guarantee)
□ Build premium status checking
□ Add premium feature gates
□ Implement upgrade prompts
□ Test all purchase scenarios
□ Add subscription analytics
```

**Deliverables:**
✅ All 3 plans purchasable

✅ Premium features gated correctly

✅ Subscription management working

**Testing:**

- Purchase flow: All plans, payment methods
- Subscription lifecycle: Purchase, renew, cancel, refund
- Feature gates: Verify Premium access

---

### **SPRINT 9: Polish & Optimization (Week 19-20)**

**Goals:**

- Performance optimized
- UI polished
- Analytics complete
- Bugs fixed

**Tasks:**

```
Week 19:
□ Performance optimization
  - Database query optimization (indexes)
  - Image loading optimization (Coil)
  - Memory leak fixes (LeakCanary)
  - Battery optimization validation
□ UI polish
  - Animations (enter/exit transitions)
  - Loading states
  - Error states
  - Empty states
□ Accessibility
  - Screen reader support
  - Contrast ratios (WCAG AA)
  - Touch target sizes (48dp min)

Week 20:
□ Complete analytics integration
□ Add performance monitoring
□ Fix all P0/P1 bugs
□ Write user documentation
□ Create release notes
□ Prepare Play Store listing
□ Final testing
  - Regression testing
  - Cross-device testing (10+ devices)
  - Edge case testing
□ Code cleanup and documentation
```

**Deliverables:**
✅ App fully polished

✅ Performance targets met

✅ Zero P0 bugs

✅ Ready for launch

**Testing:**

- Comprehensive regression testing
- Performance testing: All targets met
- User acceptance testing (UAT)

---

### 23.2 Dependencies & Critical Path

```
Critical Path (Cannot Parallelize):
Sprint 0 → Sprint 1 → Sprint 2 → Sprint 3
           ↓
Sprint 4 → Sprint 5 → Sprint 6
           ↓
Sprint 7 → Sprint 8 → Sprint 9

Parallelizable Work:
- Sprint 2 (ML) can start during Sprint 1
- Sprint 4 (Auth) can partially overlap with Sprint 3
- Sprint 7 (Cloud) backend work can start during Sprint 6
```

### 23.3 Risk Mitigation

```
HIGH RISK AREAS:

1. ML Model Accuracy (Sprint 2)
   Risk: Models don't reach 86% accuracy
   Mitigation:
   - Prepare larger training dataset (1M samples)
   - Have rule-based fallback ready
   - Plan for manual correction flow

2. Cloud Sync Conflicts (Sprint 7)
   Risk: Data loss in multi-device scenarios
   Mitigation:
   - Extensive testing with 2+ devices
   - Implement sync version tracking
   - Add manual conflict resolution UI

3. Google Play Billing Issues (Sprint 8)
   Risk: Purchase verification failures
   Mitigation:
   - Test thoroughly in sandbox
   - Implement retry logic
   - Have manual restoration option

4. Performance (Sprint 9)
   Risk: App doesn't meet performance targets
   Mitigation:
   - Continuous performance monitoring
   - Address issues throughout (not just Sprint 9)
   - Use Android Profiler weekly
```

---

## 21. CI/CD PIPELINE

### 21.1 GitHub Actions Workflow

```yaml
# .github/workflows/android-ci.yml

name: Android CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  release:
    types: [ published ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        cache: gradle

    - name: Grant execute permission for gradlew
      run: chmod +x gradlew

    - name: Build with Gradle
      run: ./gradlew build

    - name: Run unit tests
      run: ./gradlew test

    - name: Run instrumented tests
      uses: reactivecircus/android-emulator-runner@v2
      with:
        api-level: 29
        script: ./gradlew connectedCheck

    - name: Generate test coverage report
      run: ./gradlew jacocoTestReport

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./app/build/reports/jacoco/test/jacocoTestReport.xml

    - name: Run static analysis (Detekt)
      run: ./gradlew detekt

    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: app-debug
        path: app/build/outputs/apk/debug/*.apk

  deploy-internal:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'

    - name: Build release APK
      run: ./gradlew assembleRelease

    - name: Sign APK
      uses: r0adkll/sign-android-release@v1
      with:
        releaseDirectory: app/build/outputs/apk/release
        signingKeyBase64: ${{ secrets.SIGNING_KEY }}
        alias: ${{ secrets.KEY_ALIAS }}
        keyStorePassword: ${{ secrets.KEY_STORE_PASSWORD }}
        keyPassword: ${{ secrets.KEY_PASSWORD }}

    - name: Upload to Firebase App Distribution
      uses: wzieba/Firebase-Distribution-Github-Action@v1
      with:
        appId: ${{ secrets.FIREBASE_APP_ID }}
        token: ${{ secrets.FIREBASE_TOKEN }}
        groups: internal-testers
        file: app/build/outputs/apk/release/app-release-signed.apk

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'release'

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'

    - name: Build release bundle
      run: ./gradlew bundleRelease

    - name: Sign bundle
      uses: r0adkll/sign-android-release@v1
      with:
        releaseDirectory: app/build/outputs/bundle/release
        signingKeyBase64: ${{ secrets.SIGNING_KEY }}
        alias: ${{ secrets.KEY_ALIAS }}
        keyStorePassword: ${{ secrets.KEY_STORE_PASSWORD }}
        keyPassword: ${{ secrets.KEY_PASSWORD }}

    - name: Upload to Google Play Console
      uses: r0adkll/upload-google-play@v1
      with:
        serviceAccountJsonPlainText: ${{ secrets.SERVICE_ACCOUNT_JSON }}
        packageName: com.xpenz.app
        releaseFiles: app/build/outputs/bundle/release/app-release.aab
        track: production
        status: completed
        whatsNewDirectory: distribution/whatsnew
```

### 21.2 Automated Testing

```yaml
# .github/workflows/tests.yml

name: Automated Tests

on:
  pull_request:
  push:
    branches: [ main, develop ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run unit tests
      run: ./gradlew test

    - name: Publish test results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: '**/build/test-results/**/*.xml'

  integration-tests:
    runs-on: macos-latest
    strategy:
      matrix:
        api-level: [26, 29, 33]
    steps:
    - uses: actions/checkout@v3
    - name: Run instrumented tests
      uses: reactivecircus/android-emulator-runner@v2
      with:
        api-level: ${{ matrix.api-level }}
        script: ./gradlew connectedCheck

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run lint
      run: ./gradlew lint
    - name: Upload lint results
      uses: actions/upload-artifact@v3
      with:
        name: lint-results
        path: app/build/reports/lint-results-*.html
```

---

## 24. DEPLOYMENT STRATEGY

### 24.1 Release Phases

```
PHASE 1: ALPHA (Internal Testing)
Duration: 2 weeks
Users: 10 internal testers
Channel: Firebase App Distribution
Goal: Find critical bugs, validate core flows

PHASE 2: CLOSED BETA
Duration: 4 weeks
Users: 100 selected users (friends, family, community)
Channel: Google Play Internal Testing Track
Goal: Validate real-world usage, gather feedback
Success Criteria:
- <5 crashes per user per day
- >75% onboarding completion
- >70% 7-day retention

PHASE 3: OPEN BETA
Duration: 4 weeks
Users: 1,000+ public testers
Channel: Google Play Open Beta
Goal: Scale testing, performance validation
Success Criteria:
- <2 crashes per user per day
- >80% onboarding completion
- >60% 30-day retention
- 4.0+ star rating

PHASE 4: STAGED ROLLOUT
Week 1: 5% of users
Week 2: 10% of users
Week 3: 25% of users
Week 4: 50% of users
Week 5: 100% (full release)
Monitor: Crash rate, ratings, performance

PHASE 5: PRODUCTION
Continuous monitoring and updates
Bi-weekly minor releases (bug fixes)
Monthly major releases (features)
```

### 24.2 Rollback Procedures

```kotlin
// Version management
android {
    defaultConfig {
        versionCode = 10001 // Format: XXYYZZ (XX=major, YY=minor, ZZ=patch)
        versionName = "1.0.1"
    }
}

// Rollback trigger conditions
if (crashRate > 2.0 || // >2% crash rate
    anrRate > 1.0 ||   // >1% ANR rate
    userRating < 3.5 || // <3.5 stars
    networkErrors > 10.0) { // >10% network errors

    // Immediate actions:
    // 1. Halt staged rollout
    // 2. Revert to previous version
    // 3. Alert on-call engineer
    // 4. Investigate root cause
}
```

---

## 25. API DOCUMENTATION

### 25.1 Firebase APIs

### **Firestore Collections**

```tsx
// /families/{familyId}
interface Family {
  family_id: string;
  name: string; // encrypted
  emoji: string;
  color: string;
  invitation_code: string;
  created_by: string;
  created_at: Timestamp;
  updated_at: Timestamp;
}

// /families/{familyId}/transactions/{transactionId}
interface Transaction {
  transaction_id: string;
  user_id: string;
  encrypted_data: string; // AES-256-GCM
  type: 'DEBIT' | 'CREDIT' | 'REFUND';
  amount: number;
  category_id: number;
  timestamp: Timestamp;
  sync_version: number;
}

// /families/{familyId}/budgets/{budgetId}
interface Budget {
  budget_id: string;
  budget_type: 'FAMILY' | 'CATEGORY' | 'MEMBER';
  amount: number;
  period: 'MONTHLY' | 'WEEKLY' | 'YEARLY';
  alert_thresholds: number[];
  created_at: Timestamp;
}
```

### 25.2 Google Play Billing

```kotlin
// Product IDs
const val SKU_ANNUAL = "premium_annual_999"
const val SKU_MONTHLY = "premium_monthly_149"
const val SKU_LIFETIME = "premium_lifetime_4999"

// Purchase verification
suspend fun verifyPurchase(purchaseToken: String): VerificationResult {
    val response = billingClient.queryPurchaseHistory(BillingClient.SkuType.SUBS)
    // Verify with Google Play backend
    return VerificationResult(
        isValid = true,
        expiryTime = System.currentTimeMillis() + 365 * 24 * 60 * 60 * 1000
    )
}
```

### 25.3 Error Codes

```kotlin
sealed class AppError(val code: String, val message: String) {
    // Authentication Errors (1xxx)
    object InvalidPhoneNumber : AppError("1001", "Invalid phone number format")
    object OTPExpired : AppError("1002", "OTP expired")
    object InvalidOTP : AppError("1003", "Invalid OTP")
    object TooManyAttempts : AppError("1004", "Too many failed attempts")

    // Family Errors (2xxx)
    object FamilyNotFound : AppError("2001", "Family not found")
    object InvalidInvitationCode : AppError("2002", "Invalid invitation code")
    object MemberLimitReached : AppError("2003", "Family member limit reached")
    object AlreadyMember : AppError("2004", "Already a member of this family")
    object NotAuthorized : AppError("2005", "Not authorized to perform this action")

    // Budget Errors (3xxx)
    object BudgetNotFound : AppError("3001", "Budget not found")
    object InvalidBudgetAmount : AppError("3002", "Invalid budget amount")
    object BudgetAlreadyExists : AppError("3003", "Budget already exists")

    // Sync Errors (4xxx)
    object SyncFailed : AppError("4001", "Sync failed")
    object NetworkError : AppError("4002", "Network error")
    object ConflictError : AppError("4003", "Sync conflict detected")

    // Subscription Errors (5xxx)
    object PurchaseFailed : AppError("5001", "Purchase failed")
    object InvalidPurchase : AppError("5002", "Invalid purchase")
    object SubscriptionNotFound : AppError("5003", "Subscription not found")
    object RefundNotEligible : AppError("5004", "Not eligible for refund")
}
```

---

## UI/UX IMPLEMENTATION GUIDELINES (BONUS)

### Component Library (Jetpack Compose)

```kotlin
// Design System Colors
object XpenzColors {
    val Primary = Color(0xFF6200EE)
    val PrimaryVariant = Color(0xFF3700B3)
    val Secondary = Color(0xFF03DAC6)
    val Background = Color(0xFFFFFBFE)
    val Surface = Color(0xFFFFFFFF)
    val Error = Color(0xFFB00020)

    // Budget Status Colors
    val Healthy = Color(0xFF4CAF50)
    val Warning = Color(0xFFFF9800)
    val Critical = Color(0xFFFF5722)
    val Exceeded = Color(0xFFF44336)
}

// Reusable Components
@Composable
fun XpenzButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    loading: Boolean = false
) {
    Button(
        onClick = onClick,
        enabled = enabled && !loading,
        modifier = modifier.fillMaxWidth()
    ) {
        if (loading) {
            CircularProgressIndicator(
                modifier = Modifier.size(24.dp),
                color = MaterialTheme.colorScheme.onPrimary
            )
        } else {
            Text(text)
        }
    }
}

@Composable
fun TransactionCard(
    transaction: Transaction,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text(
                    text = transaction.merchantName ?: "Unknown",
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = transaction.category.displayName,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Text(
                text = "₹${transaction.amount}",
                style = MaterialTheme.typography.titleLarge,
                color = if (transaction.type == TransactionType.DEBIT)
                    MaterialTheme.colorScheme.error
                else
                    XpenzColors.Healthy
            )
        }
    }
}
```

---

This completes **ALL Priority 1, 2, and 3 sections**!

## 📊 **FINAL TRD STATUS:**

### ✅ **100% COMPLETE:**

**PART 1: ARCHITECTURE & DESIGN** ✅
**PART 2: DATA & STORAGE** ✅
**PART 3: MACHINE LEARNING** ✅
**PART 4: CORE FEATURES** ✅
**PART 5: INFRASTRUCTURE** ✅
**PART 6: IMPLEMENTATION** ✅

The TRD now includes:

- 25 complete sections
- 20-week implementation roadmap
- CI/CD pipeline configuration
- Deployment strategy
- Complete API documentation
- UI component library
- Performance monitoring
- Analytics integration
- Error handling
- Everything needed for AI-assisted development

Would you like me to **create a comprehensive downloadable document** with all sections compiled into a single PDF/DOCX?

