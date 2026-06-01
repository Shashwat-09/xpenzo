package com.xpenzo.sms

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import androidx.work.Data
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkRequest

/**
 * BroadcastReceiver for incoming SMS messages.
 *
 * Constraints:
 *  - Returns as fast as possible (< 1 ms). Never do I/O or ML here.
 *  - Hands each message off to [SmsIngestionWorker] via WorkManager.
 *  - Filters to known bank senders before enqueueing — avoids processing
 *    thousands of non-transactional messages.
 */
class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages.isNullOrEmpty()) return

        // Group multi-part messages by originating address
        val grouped = messages.groupBy { it.originatingAddress ?: "" }

        grouped.forEach { (sender, parts) ->
            if (sender.isBlank()) return@forEach

            // Fast sender pre-filter — skip obvious non-bank senders
            if (!UpiSmsParser.isKnownBankSender(sender.lowercase())) return@forEach

            val body = parts.joinToString("") { it.messageBody ?: "" }
            val receivedAtMs = parts.firstOrNull()?.timestampMillis ?: System.currentTimeMillis()

            Log.d(TAG, "SMS from $sender — enqueuing worker")
            enqueueIngestion(context, sender, body, receivedAtMs)
        }
    }

    private fun enqueueIngestion(
        context: Context,
        sender: String,
        body: String,
        receivedAtMs: Long,
    ) {
        val inputData = Data.Builder()
            .putString(SmsIngestionWorker.KEY_SENDER, sender)
            .putString(SmsIngestionWorker.KEY_BODY, body)
            .putLong(SmsIngestionWorker.KEY_RECEIVED_AT_MS, receivedAtMs)
            .build()

        val request: WorkRequest = OneTimeWorkRequestBuilder<SmsIngestionWorker>()
            .setInputData(inputData)
            .addTag(TAG)
            .build()

        WorkManager.getInstance(context).enqueue(request)
    }

    companion object {
        private const val TAG = "SmsReceiver"
    }
}
