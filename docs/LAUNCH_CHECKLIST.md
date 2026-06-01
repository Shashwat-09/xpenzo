# Xpenzo — Step-by-Step Launch Checklist

Everything still needed between "code-complete in repo" and "v1.0 live on Play Store".

Items are ordered so you don't get blocked — earlier steps unblock later ones. Most blockers are operational (require Android SDK, Firebase console, Play Console) — none are code.

Estimated total time: **3–5 working days of focused effort** spread over ~2 weeks (because of Play review).

---

## SECTION 1 — Local build verification (~30 min)

**Goal:** Confirm the code compiles and tests pass on a real machine.

### 1.1 Install Android Studio + SDK
1. Download Android Studio Koala 2024.1+ from https://developer.android.com/studio
2. Run installer; let it install the SDK to default location (`C:\Users\shash\AppData\Local\Android\Sdk`)
3. In Android Studio → Settings → Languages & Frameworks → Android SDK:
   - SDK Platforms tab: install **Android 14 (API 34)** and **Android 8 (API 26)**
   - SDK Tools tab: install **Android SDK Build-Tools 34.0.0**, **Android SDK Platform-Tools**, **Android Emulator**, **Android SDK Command-line Tools (latest)**
4. Set `ANDROID_HOME` env var:
   ```powershell
   [Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LOCALAPPDATA\Android\Sdk", "User")
   ```
5. Restart your terminal so the env var loads.

### 1.2 Set the SDK path in the project
Create `android_app/local.properties` (do NOT commit — already in `.gitignore`):
```properties
sdk.dir=C\:\\Users\\shash\\AppData\\Local\\Android\\Sdk
```

### 1.3 Build the debug APK
```powershell
cd D:\Codify\Xpenzo\android_app
.\gradlew :app:assembleDebug
```
Expected output: `BUILD SUCCESSFUL` and an APK at `app/build/outputs/apk/debug/app-debug.apk`.

If you get a Hilt/kapt error, run with stack trace:
```powershell
.\gradlew :app:assembleDebug --stacktrace
```

### 1.4 Run unit tests
```powershell
.\gradlew :app:testDebugUnitTest
```
Expected: ~50 tests pass across `UpiSmsParserTest`, `EnsembleWeightingTest`, `NumericalFeatureParityTest`, `SentencePieceTokenizerTest`, `TransactionRepositoryTest`, `SplitCalculatorTest`.

### 1.5 Run instrumented tests (needs emulator or device)
```powershell
# Start an emulator from Android Studio first, OR plug in a device with USB debugging
.\gradlew :app:connectedDebugAndroidTest
```
Expected: `RoomSmokeTest` (10 tests), `SmsIngestionE2ETest` (6 tests), `ClassifyPerformanceTest` (2 tests) all pass.

### 1.6 Install on a real device for manual smoke
```powershell
adb install -r app\build\outputs\apk\debug\app-debug.apk
adb shell am start -n com.xpenzo.debug/com.xpenzo.MainActivity
```
**You should see** the welcome screen. Tap "Get started" → phone login (Firebase will fail at OTP because no `google-services.json` yet — that's the next section).

---

## SECTION 2 — Firebase setup (~1 hour)

**Goal:** Wire the app to a real Firebase project so auth/sync/Crashlytics work.

### 2.1 Create the Firebase project
1. Go to https://console.firebase.google.com
2. **Add project** → name: `xpenzo-prod` → Continue
3. Disable Google Analytics for now (you can enable later) → Create project
4. Wait ~30 seconds for provisioning

### 2.2 Add the Android app
1. Project Overview → tap Android icon to add an app
2. Package name: `com.xpenzo` (or `com.xpenzo.debug` if using the debug applicationIdSuffix — add both)
3. App nickname: `Xpenzo`
4. **Debug signing SHA-1**: run this in your project:
   ```powershell
   cd D:\Codify\Xpenzo\android_app
   .\gradlew :app:signingReport
   ```
   Copy the SHA-1 line under `Variant: debug`. Paste into Firebase.
5. Click **Register app**
6. Download `google-services.json`
7. Move it to **`D:\Codify\Xpenzo\android_app\app\google-services.json`**
8. Verify it's not committed: `git status` should NOT list it (already in `.gitignore`)

### 2.3 Rebuild — Firebase plugins activate
```powershell
.\gradlew clean :app:assembleDebug
```
You should NO LONGER see the warning `⚠ google-services.json missing`.

### 2.4 Enable Phone Authentication
1. Firebase Console → Build → Authentication → Get started
2. Sign-in method tab → Phone → Enable → Save
3. For testing without burning real SMS: scroll to **Phone numbers for testing** → add `+91 9999999999` with code `123456`
4. (Optional, recommended) Enable App Check with Play Integrity to prevent OTP abuse — Build → App Check → Apps → register Android app

### 2.5 Set up Firestore Database
1. Build → Firestore Database → Create database
2. Region: **asia-south1 (Mumbai)** — closest to Indian users
3. Start in **production mode** (we'll deploy custom rules next)
4. Install Firebase CLI:
   ```powershell
   npm install -g firebase-tools
   firebase login
   ```
5. From project root:
   ```powershell
   cd D:\Codify\Xpenzo
   firebase init firestore
   ```
   Pick existing project `xpenzo-prod`. Use existing `firestore.rules` (already in repo). Use default indexes file.
6. Deploy the rules:
   ```powershell
   firebase deploy --only firestore:rules
   ```

### 2.6 Set up Firebase Storage
1. Build → Storage → Get started → Use default rules → Done
2. Region should auto-match Firestore (asia-south1)
3. Init storage in your project:
   ```powershell
   firebase init storage
   ```
   Use existing `storage.rules` from repo.
4. Deploy:
   ```powershell
   firebase deploy --only storage
   ```

### 2.7 Upload the v5.0 bundled model + manifest
The Android app expects `latest.json` and `models/v5_0/model.tflite` in Storage. Bootstrap them:

1. In Firebase Console → Storage → Files → Upload file:
   - Path: `models/v5_0/model.tflite`
   - Local file: `D:\Codify\Xpenzo\android_app\app\src\main\assets\xpenz_cht_520.tflite`
2. Create `models/latest.json` locally:
   ```json
   {
     "version": "5.0",
     "path": "models/v5_0/model.tflite",
     "min_app_version": "1.0",
     "size_bytes": 5130256,
     "l1_acc": 0.818,
     "l2_acc": 0.723,
     "l3_acc": 0.654
   }
   ```
3. Upload that file to `models/latest.json` in Storage.

### 2.8 Enable Crashlytics
1. Build → Crashlytics → Get started → Done
2. From the device with the debug APK installed, the SDK auto-initializes on first launch
3. Verify in the Crashlytics dashboard — wait ~5 minutes for first heartbeat

### 2.9 End-to-end Firebase smoke test
1. Open the app on your device
2. Onboarding: welcome → phone +91 9999999999 → OTP 123456 → profile → UPI ID → grant SMS permission → done
3. In Firebase Console → Firestore → Data: you should see `/users/{your_uid}` appear after the next sync (within 6 hours, or trigger immediately by force-quit-restart)
4. Trigger a fake SMS to test the full pipeline:
   ```powershell
   adb emu sms send HDFCBK "Rs.350.00 debited from a/c **1234 to VPA swiggy@ybl on 26-05-26."
   ```
   (works only on emulator — for real device, use a test bank SMS or the manual entry screen)

---

## SECTION 3 — Privacy policy hosting (~20 min)

**Goal:** Have a public URL Play Store can link to.

### 3.1 Pick a hosting option
**Easiest:** GitHub Pages (free). Other options: Netlify, your own xpenzo.app domain.

### 3.2 Set up GitHub Pages
1. Create a new repo `xpenzo-website` on GitHub
2. Copy `D:\Codify\Xpenzo\docs\privacy_policy.md` into the repo root
3. Rename to `privacy-policy.md`
4. Repo Settings → Pages → Source: Deploy from branch `main` → folder `/` → Save
5. Wait ~2 minutes — your URL is `https://<your-github-username>.github.io/xpenzo-website/privacy-policy.html`
   (GitHub auto-renders .md → .html)

### 3.3 Update the privacy policy URL everywhere
Search and replace `xpenzo.app/privacy` with your real URL in:
- `D:\Codify\Xpenzo\docs\privacy_policy.md` — the contact section
- Inside the app's `HelpImproveAiScreen` if you want a "View full policy" link (currently absent — adding it is optional)
- Play Store listing form (Section 5)

---

## SECTION 4 — Release build keystore (~30 min, one-time)

**Goal:** Produce a signed AAB you can upload to Play.

### 4.1 Generate the release keystore
```powershell
keytool -genkey -v `
  -keystore C:\Users\shash\xpenzo-release.keystore `
  -alias xpenzo `
  -keyalg RSA -keysize 2048 `
  -validity 10000
```
Prompts:
- Keystore password: pick 20+ chars (save to 1Password/Bitwarden)
- Key password: can be the same
- Name/org/etc: use your real details

**🔒 CRITICAL:** Back up `xpenzo-release.keystore` to your password manager AND a second location. If lost, you can never publish updates.

### 4.2 Get the release SHA-1 (add to Firebase later)
```powershell
keytool -list -v -keystore C:\Users\shash\xpenzo-release.keystore -alias xpenzo
```
Copy the SHA-1 + SHA-256 lines. Add them in Firebase Console → Project Settings → Your apps → Add fingerprint.

### 4.3 Set Gradle properties
Edit `C:\Users\shash\.gradle\gradle.properties` (create if missing):
```properties
XPENZO_KEYSTORE_PATH=C:/Users/shash/xpenzo-release.keystore
XPENZO_KEYSTORE_PASSWORD=<your password>
XPENZO_KEY_ALIAS=xpenzo
XPENZO_KEY_PASSWORD=<your key password>
```
Use forward slashes even on Windows. Do NOT commit this file.

### 4.4 Build the release AAB
```powershell
cd D:\Codify\Xpenzo\android_app
.\gradlew :app:bundleRelease
```
Output: `app\build\outputs\bundle\release\app-release.aab` (should be ~20–25 MB).

### 4.5 Smoke test the release AAB locally
```powershell
# Install bundletool one-time
# Download from https://github.com/google/bundletool/releases
# Move bundletool-all-X.Y.Z.jar to a known location, e.g. C:\Tools\bundletool.jar

java -jar C:\Tools\bundletool.jar build-apks `
  --bundle=app-release.aab `
  --output=app.apks `
  --mode=universal `
  --ks=C:\Users\shash\xpenzo-release.keystore `
  --ks-key-alias=xpenzo

java -jar C:\Tools\bundletool.jar install-apks --apks=app.apks
```

Smoke test on the device:
- Onboarding completes
- A test SMS gets categorized
- Insights shows transactions
- Delete account purges data

---

## SECTION 5 — Play Console setup (~2 hours + 7-day review)

**Goal:** App listed and approved for production track.

### 5.1 Create a developer account
1. Go to https://play.google.com/console
2. Pay the one-time $25 USD registration fee
3. Choose **Personal** or **Organization** (Personal is faster, fewer docs needed)
4. Verify identity with government ID (takes 1-3 days)

### 5.2 Create the app
1. Play Console → All apps → Create app
2. App name: `Xpenzo - UPI Expense Tracker`
3. Default language: English (India)
4. App or game: App
5. Free or Paid: Free
6. Declarations: ✓ all three checkboxes
7. Create app

### 5.3 Fill in the Store listing
Left nav → Grow → Store presence → Main store listing.

- **App icon**: 512×512 PNG. Use `D:\Codify\Xpenzo\android_app\app\src\main\res\drawable\ic_launcher_foreground.xml` rendered to PNG (use Android Studio: right-click drawable → New → Image Asset)
- **Feature graphic**: 1024×500 PNG. Quick option: any tool (Figma/Canva) with the coral brand color and "Xpenzo · Categorize every UPI transaction"
- **Phone screenshots** (need 2-8): take from the running app — Onboarding welcome, Home with transactions, Insights, Add expense, Settle up
  ```powershell
  adb shell screencap -p /sdcard/screen1.png
  adb pull /sdcard/screen1.png
  ```
- **Short description** (80 chars): `Auto-categorize UPI transactions on-device. Private. Smart. Indian.`
- **Full description** (4000 chars): pull from `D:\Codify\Xpenzo\docs\08 - Product Requirements Document (PRD).md` §5 — feature list

### 5.4 App content forms (required before publishing)
Left nav → Policy → App content.

- **Privacy policy URL**: paste the URL from Section 3
- **App access**: All functionality available without restrictions (or note that SMS access is requested at runtime)
- **Ads**: No ads
- **Content rating**: complete the IARC questionnaire (Finance category, no violence/sex/etc.) → expect "Everyone"
- **Target audience**: Ages 18+
- **News app**: No
- **Data safety**: this is the longest form. Use the answers in `D:\Codify\Xpenzo\docs\privacy_policy.md` §1.2 and §1.3.

### 5.5 Submit the SMS Permissions Declaration
Left nav → Policy → App content → Sensitive permissions and APIs → SMS or Call Log → Manage.

Paste the text from `D:\Codify\Xpenzo\docs\play_store_sms_declaration.md`:
- Core functionality: Auto-extract UPI transaction details from bank SMS
- Alternative considered: NotificationListenerService (used as secondary channel)
- Will not request SEND_SMS, READ_CALL_LOG, etc.

**Record a screencast** showing:
1. User taps "Grant SMS access" during onboarding
2. A test SMS arrives → appears categorized in the home feed
3. Settings → App Permissions shows green check for SMS
Upload the video.

### 5.6 Upload the AAB to Internal testing track first
Left nav → Release → Testing → Internal testing → Create new release.

1. Upload `app-release.aab` from Section 4.4
2. Release name: `1.0.0 (1)`
3. Release notes: `First release. Auto-categorize UPI transactions on-device with 520 categories.`
4. Save → Review release → Start rollout

### 5.7 Add internal testers
Internal testing → Testers tab → Create email list → add your own email + 5-10 friends
Internal testing → Tap "Copy link" → share with testers (they install via that link)

### 5.8 Promote to Closed beta after 1 week
Once internal testing has run for ~7 days and crash-free rate > 99%:
- Release → Testing → Closed testing → Create new track
- Reuse the AAB
- Add up to 100 testers via Google Group or email list
- Run for 2 weeks

### 5.9 Promote to Production (staged rollout)
- Release → Production → Create new release
- Same AAB
- Rollout percentage: start at **5%**
- Bump to 10% → 25% → 50% → 100% over 2 weeks, watching Crashlytics + Vitals

**Total launch timeline:** ~4 weeks from first upload to 100% production rollout.

---

## SECTION 6 — Self-improving loop activation (~1 day)

**Goal:** Get `retrain.py` running on Cloud Run so the model auto-improves.

### 6.1 Set up GCP credentials
```powershell
gcloud auth login
gcloud config set project xpenzo-prod
gcloud auth application-default login
```

### 6.2 Build the retrain container
Create `D:\Codify\Xpenzo\ml\Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt firebase-admin
COPY ml/ ./ml/
COPY ml/training/ ./ml/training/
COPY ml/models/v5_round1_3layer/ ./ml/models/v5_round1_3layer/
CMD ["python", "ml/retrain.py", "--mode", "watch", "--interval", "3600"]
```

Build + push:
```powershell
gcloud builds submit --tag gcr.io/xpenzo-prod/retrain:v1
```

### 6.3 Deploy to Cloud Run
```powershell
gcloud run deploy xpenzo-retrain `
  --image gcr.io/xpenzo-prod/retrain:v1 `
  --region asia-south1 `
  --memory 4Gi `
  --cpu 2 `
  --timeout 3600 `
  --min-instances 1 `
  --max-instances 1 `
  --no-allow-unauthenticated
```

The watch loop now polls Firestore every hour. When `RETRAINING_THRESHOLD = 500` corrections accumulate, it auto-retrains, evaluates, uploads to Storage, and bumps `latest.json`.

### 6.4 Verify the loop end-to-end
1. Open the app, opt in to "Help improve AI" in Settings
2. Make 50 corrections (manually edit categories)
3. Wait 10 minutes
4. Check Firestore `/transaction_corrections` — you should see 50 rows
5. Check Cloud Run logs:
   ```powershell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=xpenzo-retrain" --limit=20
   ```

---

## SECTION 7 — Splits Cloud Functions (~1 day)

**Goal:** Server-side automation for groups & splits.

### 7.1 Init functions
```powershell
cd D:\Codify\Xpenzo
firebase init functions
# pick TypeScript, install dependencies
```

### 7.2 Implement the 3 functions
Edit `functions/src/index.ts`:

```typescript
import {onDocumentCreated, onDocumentUpdated} from "firebase-functions/v2/firestore";
import * as admin from "firebase-admin";
admin.initializeApp();

const db = admin.firestore();

// (1) Recompute group balances on every confirmed settlement
export const onSettlementConfirmed = onDocumentUpdated(
  "groups/{groupId}/settlements/{settlementId}",
  async (event) => {
    const before = event.data?.before.data();
    const after = event.data?.after.data();
    if (before?.status !== "CONFIRMED" && after?.status === "CONFIRMED") {
      await recomputeBalances(event.params.groupId);
    }
  }
);

// (2) Recompute on expense create/delete
export const onExpenseChange = onDocumentCreated(
  "groups/{groupId}/expenses/{expenseId}",
  async (event) => {
    await recomputeBalances(event.params.groupId);
  }
);

// (3) Reciprocal friend writes
export const onFriendCreate = onDocumentCreated(
  "users/{uid}/friends/{friendUid}",
  async (event) => {
    const myUid = event.params.uid;
    const theirUid = event.params.friendUid;
    if (theirUid.startsWith("ghost_")) return; // skip ghosts

    // Mirror the relationship into the other user's collection
    await db.collection("users").doc(theirUid)
      .collection("friends").doc(myUid)
      .set({
        other_user_id: myUid,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        is_ghost: false,
      }, {merge: true});
  }
);

async function recomputeBalances(groupId: string) {
  const expensesSnap = await db.collection("groups").doc(groupId)
    .collection("expenses").where("is_deleted", "==", false).get();
  const settlementsSnap = await db.collection("groups").doc(groupId)
    .collection("settlements").where("status", "==", "CONFIRMED").get();

  const balances: {[uid: string]: number} = {};
  // ... compute net balances (same logic as SplitCalculator.computeNetBalances)
  // ... write to /groups/{groupId}/balances/{uid}
}
```

### 7.3 Deploy
```powershell
firebase deploy --only functions
```

### 7.4 Verify
Create a group on the app → add an expense → tap settle-up → confirm. Check Firestore `/groups/{id}/balances/{uid}` — should auto-update.

---

## SECTION 8 — Stretch features (can ship after v1.0)

### 8.1 EXACT / PERCENT / SHARES per-person input forms
Currently `AddExpenseScreen` falls back to EQUAL for non-EQUAL types. To finish:
- Add a TextField per participant in the "Split between" section when `splitType != EQUAL`
- Validate sum on the fly: percentages = 100, exact = total, shares > 0
- Pass `Participant(userId, value=...)` to `splitsRepository.createExpense()`

Estimated: 1 day. File: `D:\Codify\Xpenzo\android_app\app\src\main\kotlin\com\xpenzo\ui\splits\AddExpenseScreen.kt`

### 8.2 "Split this" CTA on TransactionDetailScreen
Add a button on the transaction detail screen that opens AddExpenseScreen pre-filled:
```kotlin
Button(onClick = {
    navController.navigate("splits/group/$groupId/add?txId=${tx.id}&amount=${tx.amount}")
})
```
Then in `AddExpenseViewModel`, read `txId` from SavedStateHandle and set `linkedTransactionId` on the created `SplitExpenseEntity`. On save, also update `transactions.reimbursable_amount` so budgets net out the reimbursed portion.

Estimated: 4 hours.

### 8.3 Firestore mirror for splits
The current splits code only writes to Room. To sync:
- Create `SplitsSyncWorker` modeled on `SyncWorker`
- Push unsynced groups/expenses/settlements/friends to Firestore
- Add Firestore listeners for incoming changes (other group members adding expenses)
- Conflict resolution: last-write-wins on edits, never overwrite settlements

Estimated: 2 days.

### 8.4 Hindi localization
1. Create `D:\Codify\Xpenzo\android_app\app\src\main\res\values-hi\strings.xml`
2. Move every hardcoded UI string from Compose into `strings.xml` first
3. Translate (use Google Translate as a starting point, then have a native speaker review)

Estimated: 2 days for translation, 3 days for string extraction across all 30+ screens.

### 8.5 Dark theme polish
The current theme has a light coral/cream palette only. To add dark:
- Define dark variants of every color in `Color.kt`
- Update `Theme.kt` to switch based on `isSystemInDarkTheme()`
- Verify each screen against the dark palette (especially the gradient cards on HomeScreen)

Estimated: 1 day.

---

## ABSOLUTE MINIMUM TO LAUNCH

If you skip everything optional, the bare minimum is:
1. **Section 1**: install SDK, build, smoke test (30 min)
2. **Section 2**: Firebase project + google-services.json + OTP + Firestore rules (1 hour)
3. **Section 3**: privacy policy on GitHub Pages (20 min)
4. **Section 4**: keystore + release AAB (30 min)
5. **Section 5.1-5.6**: Play Console listing + Internal testing release (2 hours)

That's **~4 hours of work** + waiting for Play review (~7 days) + 2 weeks of phased rollout.

Everything in Sections 6-8 can wait until after v1.0 is live and you have real users sending corrections.

---

## ORDER OF OPERATIONS — calendar view

| Day | Task |
|-----|------|
| 1 (morning) | Section 1 — install SDK, run build + tests |
| 1 (afternoon) | Section 2 — Firebase project + rules + Crashlytics + smoke test |
| 1 (evening) | Section 3 — privacy policy on GitHub Pages |
| 2 (morning) | Section 4 — keystore + release AAB + bundletool smoke |
| 2 (afternoon) | Section 5.1-5.5 — Play Console setup, app content forms, SMS declaration |
| 2 (evening) | Section 5.6-5.7 — upload to Internal testing track, invite testers |
| 3-9 | Internal testing — fix bugs as testers report them |
| 10 | Section 5.8 — promote to Closed beta |
| 10-23 | Closed beta — collect more feedback |
| 24 | Section 5.9 — promote to Production at 5% |
| 24-37 | Staged rollout 5% → 10% → 25% → 50% → 100% |
| Parallel | Sections 6, 7, 8 — Cloud Run retrain pipeline, Cloud Functions, stretch features |

**Total: ~5 weeks from "install SDK" to "100% production rollout".**
