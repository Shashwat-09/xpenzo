package com.xpenzo.ml.manager

import android.content.Context
import android.util.Log
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.storage.FirebaseStorage
import java.io.File
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext

class ModelUpdateManager(
    private val context: Context,
    private val modelManager: ModelManager,
) {
    private val storage = FirebaseStorage.getInstance()
    private val firestore = FirebaseFirestore.getInstance()
    private val modelsDir = File(context.filesDir, "models")

    private val _updateState = MutableStateFlow<UpdateState>(UpdateState.Idle)
    val updateState: StateFlow<UpdateState> = _updateState

    suspend fun checkForUpdate(forceCheck: Boolean = false): UpdateCheckResult = withContext(Dispatchers.IO) {
        if (!forceCheck && !shouldCheck()) {
            return@withContext UpdateCheckResult.AlreadyUpToDate(getInstalledVersion())
        }

        _updateState.value = UpdateState.Checking
        return@withContext runCatching {
            val manifest = fetchManifest()
            saveLastCheckTime()
            if (isNewerVersion(manifest.version, getInstalledVersion())) {
                _updateState.value = UpdateState.UpdateAvailable(manifest)
                UpdateCheckResult.UpdateAvailable(manifest)
            } else {
                _updateState.value = UpdateState.Idle
                UpdateCheckResult.AlreadyUpToDate(getInstalledVersion())
            }
        }.getOrElse {
            _updateState.value = UpdateState.Error("Check failed: ${it.message}")
            UpdateCheckResult.Error(it.message ?: "Unknown error")
        }
    }

    suspend fun downloadAndActivate(manifest: ModelManifest) = withContext(Dispatchers.IO) {
        _updateState.value = UpdateState.Downloading(0)

        val versionDir = File(modelsDir, "v${manifest.version}").apply { mkdirs() }
        val tfliteFile = File(versionDir, BundledModelAssets.tfliteModel)
        val tokenizerFile = File(versionDir, BundledModelAssets.tokenizerModel)

        runCatching {
            downloadFile(manifest.tflitePath, tfliteFile) { progress ->
                _updateState.value = UpdateState.Downloading(progress)
            }
            downloadFile(manifest.tokenizerPath, tokenizerFile) { }

            _updateState.value = UpdateState.Activating
            val updatedModel = com.xpenzo.ml.models.CHTClassifier(
                context = context,
                tfliteAsset = tfliteFile.absolutePath,
                spAsset = tokenizerFile.absolutePath,
            )
            modelManager.registerModel("downloaded_${manifest.version}", updatedModel)
            modelManager.switchModel("downloaded_${manifest.version}")
            saveInstalledVersion(manifest.version)
            cleanupOldVersions(manifest.version)
            _updateState.value = UpdateState.Updated(manifest.version)
        }.onFailure {
            tfliteFile.delete()
            tokenizerFile.delete()
            _updateState.value = UpdateState.Error("Download failed: ${it.message}")
            throw it
        }
    }

    fun schedulePeriodicChecks() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.UNMETERED)
            .setRequiresBatteryNotLow(true)
            .build()

        val request = PeriodicWorkRequestBuilder<ModelUpdateWorker>(24, TimeUnit.HOURS)
            .setConstraints(constraints)
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.MINUTES)
            .addTag(workTag)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            workTag,
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }

    private suspend fun fetchManifest(): ModelManifest {
        val bytes = storage.reference.child(manifestPath).getBytes(10_000).await()
        val json = String(bytes)
        return parseManifest(json)
    }

    private suspend fun downloadFile(storagePath: String, localFile: File, onProgress: (Int) -> Unit) {
        storage.reference.child(storagePath).getFile(localFile)
            .addOnProgressListener { snapshot ->
                val progress = (100.0 * snapshot.bytesTransferred / snapshot.totalByteCount).toInt()
                onProgress(progress)
            }
            .await()
    }

    private fun parseManifest(json: String): ModelManifest {
        fun extractString(key: String): String =
            Regex(""""$key"\s*:\s*"([^"]+)"""").find(json)?.groupValues?.get(1).orEmpty()

        fun extractLong(key: String): Long =
            Regex(""""$key"\s*:\s*([0-9]+)""").find(json)?.groupValues?.get(1)?.toLongOrNull() ?: 0L

        fun extractDouble(key: String): Double =
            Regex(""""$key"\s*:\s*([0-9.]+)""").find(json)?.groupValues?.get(1)?.toDoubleOrNull() ?: 0.0

        return ModelManifest(
            version = extractString("version"),
            minAppVersion = extractString("min_app_version"),
            tflitePath = extractString("tflite_path"),
            tokenizerPath = extractString("tokenizer_path"),
            sizeBytes = extractLong("size_bytes"),
            accuracyL3 = extractDouble("accuracy_l3"),
            trainedOnSamples = extractLong("trained_on_samples").toInt(),
            releaseNotes = extractString("release_notes"),
        )
    }

    private fun getInstalledVersion(): String =
        context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
            .getString(installedVersionKey, bundledVersion) ?: bundledVersion

    private fun saveInstalledVersion(version: String) {
        context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
            .edit()
            .putString(installedVersionKey, version)
            .apply()
    }

    private fun saveLastCheckTime() {
        context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
            .edit()
            .putLong(lastCheckKey, System.currentTimeMillis())
            .apply()
    }

    private fun shouldCheck(): Boolean {
        val lastCheck = context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
            .getLong(lastCheckKey, 0L)
        return System.currentTimeMillis() - lastCheck > TimeUnit.HOURS.toMillis(24)
    }

    private fun isNewerVersion(remote: String, installed: String): Boolean {
        fun parts(version: String) = version.split('.').mapNotNull { it.toIntOrNull() }
        val remoteParts = parts(remote)
        val installedParts = parts(installed)
        val maxLength = maxOf(remoteParts.size, installedParts.size)
        repeat(maxLength) { index ->
            val remoteValue = remoteParts.getOrElse(index) { 0 }
            val installedValue = installedParts.getOrElse(index) { 0 }
            if (remoteValue > installedValue) return true
            if (remoteValue < installedValue) return false
        }
        return false
    }

    private fun cleanupOldVersions(currentVersion: String) {
        modelsDir.listFiles()?.forEach { candidate ->
            if (candidate.isDirectory && candidate.name != "v$currentVersion") {
                candidate.deleteRecursively()
            }
        }
    }

    data class ModelManifest(
        val version: String,
        val minAppVersion: String,
        val tflitePath: String,
        val tokenizerPath: String,
        val sizeBytes: Long,
        val accuracyL3: Double,
        val trainedOnSamples: Int,
        val releaseNotes: String,
    )

    sealed class UpdateState {
        data object Idle : UpdateState()
        data object Checking : UpdateState()
        data class UpdateAvailable(val manifest: ModelManifest) : UpdateState()
        data class Downloading(val progressPercent: Int) : UpdateState()
        data object Activating : UpdateState()
        data class Updated(val version: String) : UpdateState()
        data class Error(val message: String) : UpdateState()
    }

    sealed class UpdateCheckResult {
        data class UpdateAvailable(val manifest: ModelManifest) : UpdateCheckResult()
        data class AlreadyUpToDate(val version: String) : UpdateCheckResult()
        data class Error(val message: String) : UpdateCheckResult()
    }

    private companion object {
        const val prefsName = "xpenzo_model_prefs"
        const val installedVersionKey = "installed_model_version"
        const val lastCheckKey = "last_model_check_ms"
        const val bundledVersion = "3.0"
        const val manifestPath = "models/latest.json"
        const val workTag = "model_update_check"
    }
}

class ModelUpdateWorker(
    appContext: Context,
    workerParams: WorkerParameters,
) : CoroutineWorker(appContext, workerParams) {
    override suspend fun doWork(): Result {
        return runCatching {
            val manager = ModelManager.getInstance(applicationContext)
            val updater = ModelUpdateManager(applicationContext, manager)
            when (val result = updater.checkForUpdate()) {
                is ModelUpdateManager.UpdateCheckResult.UpdateAvailable -> {
                    updater.downloadAndActivate(result.manifest)
                    Result.success()
                }
                is ModelUpdateManager.UpdateCheckResult.AlreadyUpToDate -> Result.success()
                is ModelUpdateManager.UpdateCheckResult.Error -> Result.retry()
            }
        }.getOrElse {
            Log.e("ModelUpdateWorker", "Model update worker failed", it)
            Result.retry()
        }
    }
}
