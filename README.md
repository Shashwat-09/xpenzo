<div align="center">

# 💸 Xpenzo

**An Android app that reads Indian UPI/bank SMS and classifies your spending on-device — privately, offline, instantly.**

[![Download APK](https://img.shields.io/badge/Download-v1.0.0%20APK-FF6F61?style=for-the-badge&logo=android&logoColor=white)](https://github.com/Shashwat-09/xpenzo/releases/latest)
&nbsp;
![Platform](https://img.shields.io/badge/Android-8.0%2B-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-Compose-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white)

</div>

---

## What it does

Xpenzo turns the flood of bank/UPI SMS on your phone into a clean, categorized view of where your money goes — **without sending your messages anywhere**. A bundled ~5 MB neural model classifies every transaction into a **3-level, 520-category taxonomy** entirely on-device.

- 📩 **Automatic** — reads transactional SMS (HDFC, SBI, ICICI, Axis, Paytm, GPay, PhonePe…), extracts amount + merchant, and categorizes it.
- 🧠 **On-device ML** — a custom 520-class classifier (CHT) runs offline in <100 ms. Your SMS never leaves the device.
- 🔒 **Private by design** — only an anonymized, digit-masked merchant string is ever (optionally) shared to improve the model. No raw SMS, amounts, or account numbers.
- 📈 **Budgets & insights** — monthly spend, budget alerts, habit analysis, full category browser.
- 👥 **Groups & Splits** — Splitwise-style bill splitting with friends + UPI settle-up.
- 🔁 **Self-improving** — your corrections update predictions immediately and (opt-in) feed periodic retraining.

## Download & install

1. Grab the latest **[`app-release.apk`](https://github.com/Shashwat-09/xpenzo/releases/latest)** on an Android 8.0+ (API 26) phone.
2. Open it → if prompted, allow **Install unknown apps** for your browser/file manager.
3. Install, sign in with your phone number (OTP), and grant SMS permission.

> Not on the Play Store (yet). This is a directly-installable signed release.

## Tech stack

| Layer | Tech |
|---|---|
| UI | Jetpack Compose, Material 3, Navigation-Compose |
| Architecture | MVVM, Hilt (DI), Kotlin Coroutines/Flow |
| Local data | Room (transactions, habits, budgets, groups, splits) |
| ML | TensorFlow Lite (520-class CHT model) + SentencePiece tokenizer, on-device |
| Background | WorkManager (SMS ingestion, sync, model update) |
| Backend | Firebase Auth (Phone OTP), Cloud Firestore (offline-first sync), Cloud Functions (Groups) |

## How the ML works

```
Bank SMS ──▶ UpiSmsParser ──▶ normalize merchant + 16 numeric features
                                        │
                                        ▼
                          CHTClassifier (TFLite, on-device)
                                        │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                       L1 (15)      L2 (80)      L3 (520)
                                        │
                       Ensemble with habit cache + rules ──▶ category
```

The text normalization and 16-dim numeric feature pipeline are kept **byte-for-byte in sync** with the Python training pipeline (`ml/`) so on-device inference matches training exactly.

## Project structure

```
android_app/        Android app (Kotlin, Compose) — the shippable client
  app/src/main/
    kotlin/com/xpenzo/
      ml/           classifiers, ensemble, model manager, tokenizer
      sms/          SMS receiver, parser, ingestion worker
      data/         Room entities, DAOs, repository
      firebase/     auth, Firestore sync, model updates
      splits/       split engine (4 split types + debt simplification)
      ui/           Compose screens (home, transactions, budgets, splits, settings…)
ml/                 Python training & data pipeline (datasets gitignored)
functions/          Cloud Functions (Groups & Splits backend, TypeScript)
docs/               PRD, TRD, architecture, backend schema, roadmap
firestore.rules     Firestore security rules
```

## Build from source

Requirements: JDK 17, Android SDK (compileSdk 34), and your own `google-services.json` in `android_app/app/`.

```bash
cd android_app
./gradlew :app:assembleDebug          # debug APK
./gradlew :app:testDebugUnitTest      # run unit tests
./gradlew :app:assembleRelease        # signed release (needs keystore props)
```

Release signing reads `XPENZO_KEYSTORE_PATH`, `XPENZO_KEYSTORE_PASSWORD`, `XPENZO_KEY_ALIAS`, `XPENZO_KEY_PASSWORD` from `~/.gradle/gradle.properties`.

## Status

✅ Core app (SMS → ML → categorized transactions), on-device 520-class model, budgets, insights, Groups & Splits, Phone Auth, Firestore sync — **built and unit-tested**.
🔜 Cloud Functions deploy + model OTA (require Firebase Blaze), Play Store listing.

## License

Proprietary — © 2026. All rights reserved.

<div align="center">
<sub>Built with ❤️ in India.</sub>
</div>
