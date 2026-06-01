# Google Play — SMS & Call Log Permissions Declaration

**App:** Xpenzo  
**Package:** com.xpenzo  
**Permission:** READ_SMS  
**Secondary channel:** NotificationListenerService (BIND_NOTIFICATION_LISTENER_SERVICE)

---

## Declaration (to be submitted in Play Console → Policy → App content → Sensitive permissions)

### Why does your app use READ_SMS?

Xpenzo is a UPI expense tracker. Indian bank and UPI payment apps (HDFC, SBI, ICICI, Axis, Paytm, GPay, PhonePe, etc.) send transactional SMS alerts for every debit and credit. There is no alternative API to read these transaction details — UPI does not expose a payment history API to third-party apps, and Account Aggregator (AA) requires a separate financial data framework agreement.

Xpenzo uses `READ_SMS` **only** to:
1. Listen for incoming SMS from known bank sender IDs (e.g. HDFCBK, SBIINB, ICICIB).
2. Parse the SMS body locally on-device using regex to extract: amount, merchant/VPA, and debit/credit direction.
3. Classify the transaction into a spending category using a bundled on-device ML model (no network required).
4. Persist the categorized transaction to local SQLite (Room).

**We do NOT:**
- Store the raw SMS text beyond the parsing session.
- Transmit SMS content to any server.
- Read OTP, promotional, personal, or marketing SMS (filtered out before processing).
- Access contacts or call logs.

### Is there an alternative that does not require READ_SMS?

The `NotificationListenerService` is used as a secondary channel for apps like PhonePe and Google Pay that send push notifications. However, push notifications do not always arrive and the notification text format varies significantly. READ_SMS is required as the primary reliable channel for all supported banks.

### Core functionality dependency

Without READ_SMS, the primary value proposition of Xpenzo (automatic categorization of bank transactions without manual entry) is impossible. The app degrades to a manual expense tracker, which is not what users install it for.

---

## Checklist before submission

- [ ] Privacy policy URL submitted in Play Console → Store listing
- [ ] Privacy policy hosted at a publicly accessible URL (e.g. xpenzo.app/privacy)
- [ ] `READ_SMS` declared in `AndroidManifest.xml`
- [ ] BroadcastReceiver registered with intent-filter for `android.provider.Telephony.SMS_RECEIVED`
- [ ] `NotificationListenerService` registered with required permission
- [ ] App does not request SEND_SMS, READ_CALL_LOG, or READ_CONTACTS
- [ ] Declaration form filled in Play Console (all fields)

---

## Technical implementation notes (for reviewer)

- **SmsReceiver** (`com.xpenzo.sms.SmsReceiver`): BroadcastReceiver, filters known bank sender IDs before processing any body text, enqueues a WorkManager job that runs off the main thread.
- **UpiSmsParser** (`com.xpenzo.sms.UpiSmsParser`): Parses only transactional patterns; rejects OTPs, promotional keywords.
- **Raw SMS body** is passed to the parser only; the `TransactionEntity` stored in Room has `rawSms` field which is **excluded from all Firestore sync** (`toFirestoreMap()` in `FirestoreSyncRepository` intentionally omits it).
