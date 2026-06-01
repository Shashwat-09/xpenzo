# Xpenzo — Release Build & Keystore Setup

This document covers the one-time setup needed to produce a signed release
build for Play Store upload.

---

## 1. Generate the release keystore (once, ever)

> 🔒 **CRITICAL:** This keystore is the ONLY way to sign updates to the Xpenzo app on Play Store.
> If you lose it, you cannot publish updates — Play Store requires the same signing key forever
> (or you go through Play App Signing migration, which is painful). Back up everywhere.

```bash
keytool -genkey -v \
  -keystore ~/xpenzo-release.keystore \
  -alias xpenzo \
  -keyalg RSA -keysize 2048 \
  -validity 10000
```

You will be prompted for:
- Keystore password (use 20+ chars, save to password manager)
- Key password (can be same as keystore password)
- Distinguished name (use the app developer's real details)

After generation:
- [ ] Upload the keystore to a secure password manager (1Password, Bitwarden, etc.)
- [ ] Print the SHA-1 + SHA-256 fingerprints and add them to Firebase Console:
  ```bash
  keytool -list -v -keystore ~/xpenzo-release.keystore -alias xpenzo
  ```

---

## 2. Configure Gradle to use the keystore

Add to `~/.gradle/gradle.properties` (NEVER commit):

```properties
XPENZO_KEYSTORE_PATH=/Users/you/xpenzo-release.keystore
XPENZO_KEYSTORE_PASSWORD=your_long_password
XPENZO_KEY_ALIAS=xpenzo
XPENZO_KEY_PASSWORD=your_key_password
```

Or pass them via `-P` flags on the command line:

```bash
./gradlew :app:bundleRelease \
  -PXPENZO_KEYSTORE_PATH=$HOME/xpenzo-release.keystore \
  -PXPENZO_KEYSTORE_PASSWORD=... \
  -PXPENZO_KEY_PASSWORD=...
```

If `XPENZO_KEYSTORE_PATH` is unset or points to a missing file, the release
build will still succeed but produce an **unsigned** APK/AAB — useful for CI
review but not uploadable to Play Store.

---

## 3. Build the release AAB

```bash
cd android_app
./gradlew :app:bundleRelease
```

Output: `android_app/app/build/outputs/bundle/release/app-release.aab`

Size budget: should be < 30 MB (the bundled v5 TFLite model is ~5 MB; the
rest is Compose runtime, TFLite native libs, and Firebase SDKs).

---

## 4. Verify the build before upload

```bash
# Confirm the AAB is signed with the expected key
jarsigner -verify -verbose -certs app/build/outputs/bundle/release/app-release.aab

# Install on a connected device to smoke test
bundletool build-apks --bundle=app-release.aab --output=app.apks --mode=universal
bundletool install-apks --apks=app.apks
```

Smoke test checklist:
- [ ] Onboarding flow completes (welcome → OTP → permissions)
- [ ] An incoming SMS is correctly categorized
- [ ] Insights screen shows transactions
- [ ] Delete account purges all data

---

## 5. Upload to Play Console

1. Go to Play Console → Release → Production → Create new release
2. Upload `app-release.aab`
3. Fill in "What's new in this version" notes
4. Submit for review

For the **first** release:
- [ ] Complete the Play App Signing enrollment (Google manages the upload key)
- [ ] Fill in all store listing assets (icon, screenshots, descriptions)
- [ ] Complete the Data safety form
- [ ] Submit the SMS Permissions Declaration (see `docs/play_store_sms_declaration.md`)
- [ ] Add a privacy policy URL
- [ ] Set up at least one internal test track before promoting to production

---

## 6. Versioning convention

| Field | Format | Bump on |
|-------|--------|---------|
| `versionCode` | integer, monotonically increasing | Every Play upload |
| `versionName` | semver "X.Y.Z" | Marketing — user-facing |

Use a single Git tag per Play release: `v1.0.0`, `v1.0.1`, `v1.1.0`, etc.

---

## 7. CI integration (future)

A GitHub Actions workflow at `.github/workflows/release.yml` should:
1. Decrypt the keystore from a base64-encoded GH secret
2. Run `./gradlew :app:bundleRelease` with the keystore path set
3. Upload the AAB to Play Console via the [Play Developer API](https://developers.google.com/android-publisher)

Not yet built — track in Phase 9.x.
