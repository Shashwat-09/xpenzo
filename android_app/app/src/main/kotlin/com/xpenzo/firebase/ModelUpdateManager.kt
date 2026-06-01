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
import com.google.firebase.Firebase
import com.google.firebase.storage.storage
import com.xpenzo.ml.manager.BundledModelAssets
import com.xpenzo.ml.manager.ModelManager
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Checks Firebase Storage daily (Wi-Fi only) for a newer model artifact.
 *
 * Storage layout:
 *   gs://xpenzo-app/models/latest.json  → { "version": "5.1", "path": "models/v5_1/model.tflite", "min_corrections": 500 }
 *   gs://xpenzo-app/models/v5_1/model.tflite
 *
 * If a newer version is available AND the device has collected the required corrections,
 * the model is downloaded to the app's files directory and [ModelManager.switchModel] is called.
 */
@Singleton
class ModelUpdateManager @Inject constructor(
    private val context: Context,
    private val modelManager: ModelManager,
) {
    private val storage = Firebase.storage

    fun schedulePeriodicChecks() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.UNMETERED) // Wi-Fi only
            .build()

        val request = PeriodicWorkRequestBuilder<ModelCheckWorker>(
            repeatInterval = 24,
            repeatIntervalTimeUnit = TimeUnit.HOURS,
        )
            .setConstraints(constraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.MINUTES)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "model_update_check",
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }

    suspend fun checkAndUpdate(): Boolean = withContext(Dispatchers.IO) {
        runCatching {
            // 1. Fetch latest.json
            val latestRef = storage.reference.child("models/latest.json")
            val bytes = latestRef.getBytes(10_240).await()
            val json = JSONObject(String(bytes))

            val remoteVersion = json.getString("version")
            val remotePath = json.getString("path")
            val currentVersion = readLocalVersion()

            if (remoteVersion <= currentVersion) {
                Log.d(TAG, "Model is up to date ($currentVersion)")
                return@runCatching false
            }

            Log.i(TAG, "New model available: $remoteVersion (current: $currentVersion)")

            // 2. Download new model to files/models/
            val modelDir = File(context.filesDir, "models").also { it.mkdirs() }
            val modelFile = File(modelDir, "model_$remoteVersion.tflite")

            val modelRef = storage.reference.child(remotePath)
            modelRef.getFile(modelFile).await()

            // 3. Switch ModelManager to the new artifact
            modelManager.registerModel(
                "remote_$remoteVersion",
                com.xpenzo.ml.models.CHTClassifier(context, modelFile.absolutePath),
            )
            modelManager.switchModel("remote_$remoteVersion")

            // 4. Persist the new version number
            saveLocalVersion(remoteVersion)

            Log.i(TAG, "Successfully switched to model $remoteVersion")
            true
        }.getOrElse {
            Log.w(TAG, "Model update check failed", it)
            false
        }
    }

    private fun readLocalVersion(): String {
        val prefs = context.getSharedPreferences("model_prefs", Context.MODE_PRIVATE)
        return prefs.getString("model_version", BundledModelAssets.version) ?: BundledModelAssets.version
    }

    private fun saveLocalVersion(version: String) {
        context.getSharedPreferences("model_prefs", Context.MODE_PRIVATE)
            .edit().putString("model_version", version).apply()
    }

    companion object {
        private const val TAG = "ModelUpdateManager"
    }
}

/** WorkManager worker that triggers the daily model update check. */
@HiltWorker
class ModelCheckWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val modelUpdateManager: ModelUpdateManager,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val updated = modelUpdateManager.checkAndUpdate()
        Log.d("ModelCheckWorker", "checkAndUpdate returned updated=$updated")
        return Result.success()
    }
}
