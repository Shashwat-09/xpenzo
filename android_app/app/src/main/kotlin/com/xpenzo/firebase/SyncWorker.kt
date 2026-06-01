package com.xpenzo.firebase

import android.content.Context
import android.util.Log
import androidx.hilt.work.HiltWorker
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.util.concurrent.TimeUnit

/**
 * Periodic WorkManager worker that syncs local Room data to Firestore:
 *  1. Unsynced transactions → /users/{uid}/transactions/ (up to 50 per run)
 *  2. Opted-in correction samples → /ml_corrections/
 *
 * Runs every 6 hours on any network connection.
 * Retries with exponential back-off on failure.
 */
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val syncRepository: FirestoreSyncRepository,
    private val groupSyncRepository: GroupSyncRepository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        Log.d(TAG, "Starting Firestore sync")
        return runCatching {
            syncRepository.syncTransactions(limit = 50)
            syncRepository.syncCorrections()
            groupSyncRepository.syncAll()
        }.fold(
            onSuccess = {
                Log.d(TAG, "Sync completed")
                Result.success()
            },
            onFailure = { e ->
                Log.w(TAG, "Sync failed — will retry", e)
                if (runAttemptCount < 3) Result.retry() else Result.failure()
            },
        )
    }

    companion object {
        private const val TAG = "SyncWorker"
        private const val WORK_NAME = "firestore_sync"

        /** Enqueue (or keep) a periodic sync job. Safe to call multiple times. */
        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = PeriodicWorkRequestBuilder<SyncWorker>(
                repeatInterval = 6,
                repeatIntervalTimeUnit = TimeUnit.HOURS,
            )
                .setConstraints(constraints)
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 15, TimeUnit.MINUTES)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                request,
            )
        }
    }
}
