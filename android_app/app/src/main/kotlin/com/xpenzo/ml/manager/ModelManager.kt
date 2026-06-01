package com.xpenzo.ml.manager

import android.content.Context
import android.util.Log
import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassificationSource
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.core.TransactionClassifier
import com.xpenzo.ml.ensemble.EnsembleClassifier
import com.xpenzo.ml.models.CHTClassifier
import com.xpenzo.ml.models.HabitModel
import com.xpenzo.ml.models.RuleEngine
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

class ModelManager private constructor(
    private val context: Context,
    private val habitModel: HabitModel,
) {
    private val registry = mutableMapOf<String, TransactionClassifier>()
    private val mutex = Mutex()
    private var initialized = false
    private var activeClassifier: TransactionClassifier? = null

    private val _activeModelId = MutableStateFlow("booting")
    val activeModelId: StateFlow<String> = _activeModelId

    private val _modelInfo = MutableStateFlow<ModelInfo?>(null)
    val modelInfo: StateFlow<ModelInfo?> = _modelInfo

    /** Kept so the ensemble can update weights when habit count changes. */
    private var ensembleClassifier: EnsembleClassifier? = null

    suspend fun initializeIfNeeded(): Unit = mutex.withLock {
        if (initialized) return@withLock

        val ruleEngine = RuleEngine()
        val chtClassifier = CHTClassifier(context)
        val ensemble = EnsembleClassifier(chtClassifier, ruleEngine, habitModel)
        ensembleClassifier = ensemble

        registry["ensemble"] = ensemble
        registry["cht_only"] = chtClassifier
        registry["rule_engine"] = ruleEngine
        registry["habit_only"] = habitModel

        initialized = true
        val bootstrapTarget = if (assetBackedModelExists()) "ensemble" else "rule_engine"
        runCatching {
            switchModelInternal(bootstrapTarget)
        }.onFailure {
            Log.w("ModelManager", "Failed to boot $bootstrapTarget, falling back to rules only.", it)
            switchModelInternal("rule_engine")
        }
    }

    /**
     * Called by the repository/ViewModel after habits are loaded or updated.
     * Drives the cold→warm→mature ensemble weighting transition.
     */
    fun updateHabitCount(count: Int) {
        ensembleClassifier?.updateTransactionCount(count)
        Log.d("ModelManager", "Habit count updated: $count")
    }

    suspend fun classify(input: ClassifierInput): ClassificationResult {
        if (!initialized) {
            initializeIfNeeded()
        }
        val classifier = activeClassifier ?: return fallback()
        return runCatching { classifier.classify(input) }
            .getOrElse {
                Log.e("ModelManager", "Classification failed", it)
                fallback()
            }
    }

    fun registerModel(id: String, model: TransactionClassifier) {
        registry[id] = model
    }

    suspend fun switchModel(modelId: String) = mutex.withLock {
        if (!initialized) {
            initializeIfNeeded()
            return@withLock
        }
        switchModelInternal(modelId)
    }

    fun availableModels(): Map<String, ModelInfo> = registry.mapValues { (id, model) ->
        ModelInfo(
            id = id,
            displayName = model.displayName,
            version = model.version,
            modelSizeBytes = model.modelSizeBytes,
            supportsColdStart = model.supportsColdStart,
        )
    }

    fun closeModel(modelId: String) {
        if (_activeModelId.value == modelId) {
            error("Cannot close the active model.")
        }
        registry.remove(modelId)?.close()
    }

    private suspend fun switchModelInternal(modelId: String) {
        val model = registry[modelId] ?: error("Model '$modelId' is not registered.")
        model.warmUp()
        activeClassifier = model
        _activeModelId.value = modelId
        _modelInfo.value = ModelInfo(
            id = modelId,
            displayName = model.displayName,
            version = model.version,
            modelSizeBytes = model.modelSizeBytes,
            supportsColdStart = model.supportsColdStart,
        )
    }

    private fun assetBackedModelExists(): Boolean =
        runCatching {
            context.assets.open(BundledModelAssets.tfliteModel).close()
            context.assets.open(BundledModelAssets.l1Labels).close()
            true
        }.getOrDefault(false)

    private fun fallback(): ClassificationResult = ClassificationResult(
        l1Category = "Others",
        l1Confidence = 0f,
        l2Category = "Miscellaneous",
        l2Confidence = 0f,
        l3Category = "Miscellaneous",
        l3Confidence = 0f,
        source = ClassificationSource.FALLBACK,
    )

    companion object {
        @Volatile
        private var instance: ModelManager? = null

        /**
         * Primary factory — called by Hilt with the Room-backed habit model injected.
         * Subsequent calls return the same singleton.
         */
        fun getInstance(context: Context, habitModel: HabitModel): ModelManager =
            instance ?: synchronized(this) {
                instance ?: ModelManager(context.applicationContext, habitModel).also { instance = it }
            }

        /**
         * Legacy no-arg factory for places that don't have a Room-backed habit model yet
         * (e.g. previews, tests). Falls back to an in-memory [HabitModel].
         */
        fun getInstance(context: Context): ModelManager =
            instance ?: synchronized(this) {
                instance ?: ModelManager(context.applicationContext, HabitModel()).also { instance = it }
            }
    }
}

data class ModelInfo(
    val id: String,
    val displayName: String,
    val version: String,
    val modelSizeBytes: Long,
    val supportsColdStart: Boolean,
) {
    val modelSizeMb: String get() = "%.1f MB".format(modelSizeBytes / 1_048_576.0)
}
