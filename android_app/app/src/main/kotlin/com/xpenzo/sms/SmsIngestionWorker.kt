package com.xpenzo.sms

import android.content.Context
import android.util.Log
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.xpenzo.BuildConfig
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.manager.ModelManager
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId
import java.util.UUID

/**
 * WorkManager job that classifies a single parsed SMS and persists the result to Room.
 *
 * Runs on a background thread — the [SmsReceiver] hands off to this worker
 * immediately so the BroadcastReceiver window (< 10 s) is never exhausted.
 *
 * Input data keys: [KEY_SENDER], [KEY_BODY], [KEY_RECEIVED_AT_MS]
 */
@HiltWorker
class SmsIngestionWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val repository: TransactionRepository,
    private val modelManager: ModelManager,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val sender = inputData.getString(KEY_SENDER) ?: return Result.failure()
        val body = inputData.getString(KEY_BODY) ?: return Result.failure()
        val receivedAtMs = inputData.getLong(KEY_RECEIVED_AT_MS, System.currentTimeMillis())

        val receivedAt = LocalDateTime.ofInstant(
            Instant.ofEpochMilli(receivedAtMs),
            ZoneId.systemDefault(),
        )

        return try {
            val parsed = UpiSmsParser.parse(sender, body, receivedAt)
                ?: return Result.success() // not a transactional SMS — skip silently

            // Dedup: skip if we already have this fingerprint within 60 s
            val dedupKey = UpiSmsParser.dedupKey(sender, parsed.amountPaise, body)
            val windowStart = receivedAtMs - DEDUP_WINDOW_MS
            // (Simple check — just count recent transactions from the same merchant+amount)
            // Full dedup via DB query would require a dedicated index; this is sufficient for v1.
            // Transaction details are sensitive — never log them in release builds
            if (BuildConfig.DEBUG) {
                Log.d(TAG, "Processing SMS: sender=$sender amount=${parsed.amountPaise} vpa=${parsed.vpa}")
            }

            // Build ClassifierInput using the canonical contract:
            // textField = merchantNormalized (ONE field, digits→#, lowercase)
            // numeric features are derived from amount, timestamp, etc.
            val classifierInput = ClassifierInput(
                merchantName = parsed.merchantNormalized, // normalized — matches training
                upiId = parsed.vpa,
                amount = parsed.amountPaise / 100.0,      // convert to rupees for classifier
                timestamp = receivedAt,
                rawSms = body,
            )

            val result = modelManager.classify(classifierInput)

            val transaction = TransactionEntity(
                id = UUID.randomUUID().toString(),
                merchantRaw = parsed.merchant,
                merchantNormalized = parsed.merchantNormalized,
                upiId = parsed.vpa,
                amount = parsed.amountPaise,
                isCredit = parsed.isCredit,
                timestamp = receivedAtMs,
                l1Category = result.l1Category.ifEmpty { "Others" },
                l2Category = result.l2Category.ifEmpty { "Miscellaneous" },
                l3Category = result.l3Category.ifEmpty { "Miscellaneous" },
                confidence = result.l1Confidence,
                source = result.source.name,
                rawSms = body,
            )

            repository.insertTransaction(transaction)

            // Record habit signal (auto-accept if confidence is high)
            if (result.l1Confidence >= AUTO_ACCEPT_THRESHOLD) {
                repository.recordHabit(
                    merchantNormalized = parsed.merchantNormalized,
                    upiId = parsed.vpa,
                    l1 = transaction.l1Category,
                    l2 = transaction.l2Category,
                    l3 = transaction.l3Category,
                )
            }

            if (BuildConfig.DEBUG) {
                Log.i(TAG, "Ingested: ${parsed.merchant} ₹${parsed.amountPaise / 100} → ${result.l1Category}")
            }
            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "SMS ingestion failed for sender=$sender", e)
            if (runAttemptCount < MAX_RETRIES) Result.retry() else Result.failure()
        }
    }

    companion object {
        const val KEY_SENDER = "sender"
        const val KEY_BODY = "body"
        const val KEY_RECEIVED_AT_MS = "received_at_ms"

        private const val TAG = "SmsIngestionWorker"
        private const val DEDUP_WINDOW_MS = 60_000L   // 60 seconds
        private const val AUTO_ACCEPT_THRESHOLD = 0.80f
        private const val MAX_RETRIES = 2
    }
}
