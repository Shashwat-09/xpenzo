# Xpenzo Privacy Policy

**Effective date:** 2026-06-01  
**App:** Xpenzo — UPI Expense Tracker  
**Developer:** Xpenzo (shashwatshah993@gmail.com)

---

## 1. What data we collect

### 1.1 On-device only (never uploaded)

| Data | Purpose |
|------|---------|
| Raw SMS bodies | Parsed locally to extract transaction amount & merchant; **deleted from memory immediately after parsing** |
| Bank account suffixes | Displayed in the app; never stored or transmitted |
| Full UPI VPAs (e.g. user@ybl) | Used for dedup and habit lookup on-device; only the **domain part** (e.g. "ybl") is ever uploaded |

### 1.2 Uploaded to our servers (Firebase)

Only the following fields leave your device when you create an account:

| Field | What it contains | Purpose |
|-------|------------------|---------|
| Phone number hash (SHA-256) | Not reversible to your number | Account lookup |
| Normalized transaction data | Merchant name (digits replaced with `#`), amount category, timestamp | Cloud backup & sync |
| Anonymous ML corrections (opt-in only) | Normalized merchant name, UPI domain, amount **bucket** (not exact amount), chosen category | Improving the on-device AI model |

### 1.3 What we explicitly do NOT collect

- Raw SMS content
- Full bank account numbers or IFSCs
- Full UPI VPAs
- Exact transaction amounts (only range buckets are uploaded for ML training)
- Location data (unless you grant location permission for geo-tagged insights)
- Contacts or address book

---

## 2. SMS & Notification Listener permissions

Xpenzo uses `READ_SMS` and `NotificationListenerService` solely to detect UPI and bank debit/credit transactions. We do not:

- Read promotional, personal, or OTP messages (filtered out before processing)
- Store raw SMS text beyond the current parsing session
- Transmit SMS content to any server

This usage complies with Google Play's [SMS & Call Log policy](https://support.google.com/googleplay/android-developer/answer/9047303).

---

## 3. How we use your data

| Data | Use |
|------|-----|
| Transaction records | Categorization, budget tracking, insights — displayed only to you |
| Firestore sync | Backup & restore across devices |
| Anonymous ML corrections | Retraining the on-device model to improve category accuracy |

---

## 4. Data sharing

We do not sell, rent, or share your personal data with third parties except:

- **Firebase (Google):** cloud sync, authentication. Governed by [Google's Privacy Policy](https://policies.google.com/privacy).
- **Legal requirement:** if required by Indian law or a valid court order.

---

## 5. Data retention & deletion

- You may delete your account at any time from **Settings → Delete Account**.
- Local Room database is cleared immediately.
- Firestore data is purged within **30 days** of account deletion per the Digital Personal Data Protection Act 2023 (DPDP Act).
- Anonymous ML correction samples that have already been aggregated into a retrained model cannot be individually recalled; the normalized form contains no personally identifiable information.

---

## 6. Security

- All Firestore traffic uses TLS 1.3.
- Security rules restrict each user's data to their own authenticated UID.
- SMS bodies are never written to disk or transmitted.

---

## 7. Children

Xpenzo is not directed at children under 13. We do not knowingly collect data from minors.

---

## 8. Changes to this policy

We will notify you in-app before making material changes to this policy. Continued use constitutes acceptance.

---

## 9. Contact

shashwatshah993@gmail.com
