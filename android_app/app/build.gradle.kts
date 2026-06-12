plugins {
    id("com.android.application")
    kotlin("android")
    kotlin("kapt")
    id("com.google.dagger.hilt.android")
    // google-services + crashlytics applied conditionally below (require google-services.json)
}

// Apply Google Services + Crashlytics plugins only when google-services.json is present.
// This lets local/CI builds succeed without Firebase config; production builds MUST include
// google-services.json. Setup steps documented in docs/REMAINING_WORK.md §1.
val googleServicesJson = file("google-services.json")
if (googleServicesJson.exists()) {
    apply(plugin = "com.google.gms.google-services")
    apply(plugin = "com.google.firebase.crashlytics")
} else {
    logger.warn(
        "⚠ google-services.json missing — Firebase plugins skipped. " +
        "Drop the file in app/ before release builds.",
    )
}

android {
    namespace = "com.xpenzo"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.xpenzo"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
    }

    // Release signing — keystore lives outside the repo.
    // Properties expected in ~/.gradle/gradle.properties or via -P flags:
    //   XPENZO_KEYSTORE_PATH=/abs/path/to/xpenzo-release.keystore
    //   XPENZO_KEYSTORE_PASSWORD=...
    //   XPENZO_KEY_ALIAS=xpenzo
    //   XPENZO_KEY_PASSWORD=...
    // See docs/release_build.md for keystore generation steps.
    signingConfigs {
        create("release") {
            val keystorePath = (project.findProperty("XPENZO_KEYSTORE_PATH") as String?)
            if (keystorePath != null && file(keystorePath).exists()) {
                storeFile = file(keystorePath)
                storePassword = project.findProperty("XPENZO_KEYSTORE_PASSWORD") as String?
                keyAlias = project.findProperty("XPENZO_KEY_ALIAS") as String? ?: "xpenzo"
                keyPassword = project.findProperty("XPENZO_KEY_PASSWORD") as String?
            }
            // Enable v1 (JAR) signing in addition to v2/v3. Some OEM ROMs (notably
            // OnePlus/Oppo ColorOS) reject sideloaded APKs that lack a v1 signature
            // with a generic "App not installed" error.
            enableV1Signing = true
            enableV2Signing = true
            enableV3Signing = true
        }
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            // R8/resource shrinking disabled: a release-only "crash on any interaction"
            // is the classic signature of minification stripping a reflectively-used class.
            // For sideloaded distribution the size saving isn't worth the risk; re-enable
            // with verified keep-rules before a Play Store submission.
            isMinifyEnabled = false
            isShrinkResources = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            // Apply release signing only if the keystore is configured;
            // otherwise the build still produces an unsigned APK for review.
            val keystorePath = project.findProperty("XPENZO_KEYSTORE_PATH") as String?
            if (keystorePath != null && file(keystorePath).exists()) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true // generate BuildConfig (DEBUG flag used in XpenzoApplication); off by default in AGP 8
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    androidResources {
        noCompress += "tflite"
    }

    testOptions {
        // Return defaults (no-op) for android.* stubs like android.util.Log in JVM unit
        // tests, instead of throwing "not mocked" RuntimeExceptions.
        unitTests.isReturnDefaultValues = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

// Export Room schema JSON for migration auditing
kapt {
    arguments {
        arg("room.schemaLocation", "$projectDir/schemas")
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.0")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui:1.6.7")
    implementation("androidx.compose.ui:ui-tooling-preview:1.6.7")
    implementation("androidx.compose.material3:material3:1.2.1")
    implementation("androidx.compose.material:material-icons-extended:1.6.7")
    // Material Components — provides the XML Theme.Material3.* themes referenced by
    // res/values/themes.xml (Compose material3 does NOT ship the XML themes).
    implementation("com.google.android.material:material:1.12.0")
    // Lifecycle MUST stay on 2.7.x while Compose UI is 1.6.x: lifecycle 2.8.0's
    // lifecycle-runtime-compose is binary-incompatible with Compose 1.6 and throws
    // NoSuchMethodError (LocalLifecycleOwner) at first composition on-device —
    // compiles fine, passes JVM tests, crashes instantly at app open.
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    implementation("androidx.work:work-runtime-ktx:2.9.0")

    implementation("com.google.dagger:hilt-android:2.51")
    kapt("com.google.dagger:hilt-android-compiler:2.51")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")
    implementation("androidx.hilt:hilt-work:1.2.0")
    kapt("androidx.hilt:hilt-compiler:1.2.0")

    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    // BoM 33.1.2 — last line compiled against Kotlin 1.9 metadata (matches this
    // project's Kotlin 1.9.24). The 34.x line ships Kotlin 2.2/2.3 metadata which the
    // 1.9 compiler cannot read. KTX APIs are already merged into the main modules at
    // 33.0, so the non-ktx artifacts below expose Firebase.auth/firestore/storage.
    implementation(platform("com.google.firebase:firebase-bom:33.1.2"))
    // Firebase BoM 34.x merged the old *-ktx artifacts into the main modules
    // (the KTX APIs now ship in the base artifact), so the -ktx variants are no
    // longer published and must not be referenced.
    implementation("com.google.firebase:firebase-auth")
    implementation("com.google.firebase:firebase-firestore")
    implementation("com.google.firebase:firebase-storage")
    implementation("com.google.firebase:firebase-crashlytics")
    implementation("com.google.firebase:firebase-analytics")

    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
    implementation("org.tensorflow:tensorflow-lite:2.14.0")
    implementation("org.tensorflow:tensorflow-lite-support:0.4.4")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.3.1")
    testImplementation("org.mockito:mockito-inline:5.2.0")   // mock final Kotlin classes
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.6.7")
    androidTestImplementation("androidx.room:room-testing:2.6.1")
    androidTestImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")
    debugImplementation("androidx.compose.ui:ui-tooling:1.6.7")
    debugImplementation("androidx.compose.ui:ui-test-manifest:1.6.7")
}
