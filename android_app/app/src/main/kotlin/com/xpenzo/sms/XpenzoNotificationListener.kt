package com.xpenzo.sms

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import androidx.work.Data
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.AndroidEntryPoint
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId

/**
 * Fallback ingestion channel — listens to status-bar notifications from UPI apps
 * that don't send transactional SMS (e.g. some Paytm wallet flows, CRED).
 *
 * Only processes notifications from known UPI/bank packages. Hands off to the
 * same [SmsIngestionWorker] pipeline so classification + persistence is identical
 * to the SMS path.
 *
 * Requires the user to explicitly grant Notification Access in System Settings.
 * The onboarding screen (Phase 6) guides the user there.
 */
@AndroidEntryPoint
class XpenzoNotificationListener : NotificationListenerService() {

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val pkg = sbn.packageName ?: return

        // Filter to known UPI/bank notification packages
        if (!isKnownUpiPackage(pkg)) return

        val extras = sbn.notification?.extras ?: return
        val title = extras.getCharSequence("android.title")?.toString() ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""
        val bigText = extras.getCharSequence("android.bigText")?.toString() ?: text

        val fullText = "$title $bigText".trim()
        if (fullText.isBlank()) return

        // Quick pre-filter: must contain a currency marker
        if (!AMOUNT_HINT.containsMatchIn(fullText)) return

        // Use package name as a pseudo-sender for the parser's known-sender check
        val pseudoSender = PACKAGE_TO_SENDER[pkg] ?: return

        Log.d(TAG, "Notification from $pkg — enqueuing worker")
        enqueueIngestion(pseudoSender, fullText, sbn.postTime)
    }

    private fun enqueueIngestion(sender: String, body: String, postedAtMs: Long) {
        val inputData = Data.Builder()
            .putString(SmsIngestionWorker.KEY_SENDER, sender)
            .putString(SmsIngestionWorker.KEY_BODY, body)
            .putLong(SmsIngestionWorker.KEY_RECEIVED_AT_MS, postedAtMs)
            .build()

        WorkManager.getInstance(applicationContext)
            .enqueue(
                OneTimeWorkRequestBuilder<SmsIngestionWorker>()
                    .setInputData(inputData)
                    .addTag(TAG)
                    .build(),
            )
    }

    private fun isKnownUpiPackage(pkg: String) = pkg in PACKAGE_TO_SENDER

    companion object {
        private const val TAG = "NotificationListener"

        /** Regex hint to skip promotional notifications fast. */
        private val AMOUNT_HINT = Regex("""[₹$]|Rs\.?\s*\d|\bINR\b""", RegexOption.IGNORE_CASE)

        /** Maps UPI app package names to pseudo-sender strings that pass the parser's allow-list. */
        val PACKAGE_TO_SENDER = mapOf(
            "net.one97.paytm" to "paytm",
            "com.google.android.apps.nbu.paisa.user" to "gpay",
            "com.phonepe.app" to "phonepe",
            "in.org.npci.upiapp" to "bhim",
            "com.amazon.mShop.android.shopping" to "amazonpay",
            "com.mobikwik_new" to "mobikwik",
            "com.freecharge.android" to "freecharge",
            // Major bank apps that also push notifications
            "com.snapwork.hdfc" to "hdfcbk",
            "com.csam.icici.bank.imobile" to "icicib",
            "com.sbi.SBIFreedomPlus" to "sbiinb",
            "com.axis.mobile" to "axisbk",
            "com.kotak.mahindra.kotak.bank" to "kotakb",
        )
    }
}
