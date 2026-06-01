package com.xpenzo.firebase

import android.util.Log
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.SetOptions
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.data.repository.TransactionRepository
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.tasks.await

/**
 * Syncs local Room transactions to Firestore.
 *
 * Design:
 *  - Offline-first: transactions are always written to Room first.
 *  - Sync runs after successful transactions are persisted (WorkManager job).
 *  - Security: only non-sensitive fields are uploaded (no rawSms).
 *  - Batches up to 50 unsynced transactions per call.
 *
 * Firestore schema (per docs/04 - Backend Schema Documentation.md):
 *   /users/{uid}/transactions/{txId}
 */
@Singleton
class FirestoreSyncRepository @Inject constructor(
    private val repository: TransactionRepository,
    private val auth: AuthRepository,
) {
    private val db = FirebaseFirestore.getInstance()

    /**
     * Upload up to [limit] unsynced transactions for the current user.
     * Marks them synced in Room on success.
     */
    suspend fun syncTransactions(limit: Int = 50) {
        val uid = auth.currentUser?.uid ?: return
        val unsynced = repository.getUnsynced(limit)
        if (unsynced.isEmpty()) return

        val batch = db.batch()
        val ids = mutableListOf<String>()

        unsynced.forEach { tx ->
            val ref = db.collection("users").document(uid)
                .collection("transactions").document(tx.id)
            batch.set(ref, tx.toFirestoreMap(), SetOptions.merge())
            ids.add(tx.id)
        }

        runCatching { batch.commit().await() }
            .onSuccess {
                repository.markSynced(ids)
                Log.d(TAG, "Synced ${ids.size} transactions")
            }
            .onFailure { Log.w(TAG, "Batch sync failed", it) }
    }

    /**
     * Upload pending ML corrections for the self-improving loop.
     * Only anonymized fields are sent (see DataCollectionManager for payload contract).
     */
    suspend fun syncCorrections() {
        val uid = auth.currentUser?.uid ?: return
        val pending = repository.getUnuploadedCorrections()
        if (pending.isEmpty()) return

        val batch = db.batch()
        val ids = mutableListOf<String>()

        pending.forEach { correction ->
            val ref = db.collection("ml_corrections").document(correction.id)
            batch.set(
                ref,
                mapOf(
                    "uid" to uid,
                    "merchant_norm" to com.xpenzo.sms.UpiSmsParser.maskDigitsForUpload(correction.merchantNormalized),
                    "upi_domain" to correction.upiDomain,
                    "amount_bucket" to correction.amountBucket,
                    "original_l1" to correction.originalL1,
                    "corrected_l1" to correction.correctedL1,
                    "corrected_l2" to correction.correctedL2,
                    "corrected_l3" to correction.correctedL3,
                    "timestamp" to correction.timestamp,
                ),
            )
            ids.add(correction.id)
        }

        runCatching { batch.commit().await() }
            .onSuccess {
                repository.markCorrectionsUploaded(ids)
                Log.d(TAG, "Uploaded ${ids.size} corrections")
            }
            .onFailure { Log.w(TAG, "Correction sync failed", it) }
    }

    private fun TransactionEntity.toFirestoreMap(): Map<String, Any?> = mapOf(
        "id" to id,
        "merchant_normalized" to merchantNormalized,
        "upi_id" to upiId,
        "amount_paise" to amount,
        "is_credit" to isCredit,
        "timestamp" to timestamp,
        "l1_category" to l1Category,
        "l2_category" to l2Category,
        "l3_category" to l3Category,
        "confidence" to confidence,
        "source" to source,
        "is_corrected" to isCorrected,
        "synced_at" to System.currentTimeMillis(),
        // rawSms intentionally excluded — never uploaded
    )

    companion object {
        private const val TAG = "FirestoreSync"
    }
}
