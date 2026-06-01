package com.xpenzo.ml.ensemble

import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassificationSource
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.core.ComponentScores
import com.xpenzo.ml.core.TransactionClassifier
import com.xpenzo.ml.models.CHTClassifier
import com.xpenzo.ml.models.HabitModel
import com.xpenzo.ml.models.RuleEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlin.system.measureTimeMillis

class EnsembleClassifier(
    private val chtClassifier: CHTClassifier,
    private val ruleEngine: RuleEngine,
    private val habitModel: HabitModel,
    private var userTransactionCount: Int = 0,
) : TransactionClassifier {
    override val displayName = "CHT Ensemble"
    override val version = "3.0"
    override val modelSizeBytes = chtClassifier.modelSizeBytes + 60_000L
    override val supportsColdStart = true

    override suspend fun warmUp(): Unit = coroutineScope {
        awaitAll(
            async { chtClassifier.warmUp() },
            async { ruleEngine.warmUp() },
            async { habitModel.warmUp() },
        )
    }

    override fun close() {
        chtClassifier.close()
        ruleEngine.close()
        habitModel.close()
    }

    override suspend fun classify(input: ClassifierInput): ClassificationResult = coroutineScope {
        lateinit var result: ClassificationResult
        val elapsed = measureTimeMillis {
            result = classifyInternal(input)
        }
        result.copy(inferenceMs = elapsed)
    }

    fun updateTransactionCount(count: Int) {
        userTransactionCount = count
    }

    private suspend fun classifyInternal(input: ClassifierInput): ClassificationResult = coroutineScope {
        val habitResult = habitModel.classify(input)
        if (habitResult.l1Confidence >= 0.90f && userTransactionCount >= HabitModel.minimumHabitCount) {
            return@coroutineScope habitResult
        }

        val rulesDeferred = async(Dispatchers.Default) { ruleEngine.classify(input) }
        val chtDeferred = async(Dispatchers.Default) { chtClassifier.classify(input) }

        val rulesResult = rulesDeferred.await()
        val chtResult = chtDeferred.await()

        if (rulesResult.l1Confidence >= 0.98f && rulesResult.l1Category == chtResult.l1Category) {
            return@coroutineScope rulesResult.copy(
                componentScores = ComponentScores(
                    chtConfidence = chtResult.l3Confidence,
                    rulesConfidence = rulesResult.l1Confidence,
                    habitConfidence = habitResult.l1Confidence,
                ),
            )
        }

        val weights = weightsForUser()
        val l1Scores = mutableMapOf<String, Float>()
        addScore(l1Scores, chtResult.l1Category, chtResult.l1Confidence * weights.chtWeight)
        addScore(l1Scores, rulesResult.l1Category, rulesResult.l1Confidence * weights.rulesWeight)
        if (weights.habitWeight > 0f) {
            addScore(l1Scores, habitResult.l1Category, habitResult.l1Confidence * weights.habitWeight)
        }

        val bestL1 = l1Scores.maxByOrNull { it.value }?.key ?: chtResult.l1Category
        val l3Scores = mutableMapOf<String, Float>()
        addScore(l3Scores, chtResult.l3Category, chtResult.l3Confidence * weights.chtWeight)
        if (rulesResult.l1Category == bestL1) {
            addScore(l3Scores, rulesResult.l3Category, rulesResult.l3Confidence * weights.rulesWeight)
        }
        if (weights.habitWeight > 0f && habitResult.l3Category.isNotBlank()) {
            addScore(l3Scores, habitResult.l3Category, habitResult.l3Confidence * weights.habitWeight)
        }

        val bestL3 = l3Scores.maxByOrNull { it.value }?.key ?: chtResult.l3Category
        ClassificationResult(
            l1Category = bestL1,
            l1Confidence = (l1Scores[bestL1] ?: 0f).coerceIn(0f, 1f),
            l2Category = chtResult.l2Category,
            l2Confidence = chtResult.l2Confidence,
            l3Category = bestL3,
            l3Confidence = (l3Scores[bestL3] ?: 0f).coerceIn(0f, 1f),
            top3 = chtResult.top3,
            source = ClassificationSource.ML_ENSEMBLE,
            componentScores = ComponentScores(
                chtConfidence = chtResult.l3Confidence,
                rulesConfidence = rulesResult.l1Confidence,
                habitConfidence = habitResult.l1Confidence,
            ),
        )
    }

    private fun addScore(scores: MutableMap<String, Float>, key: String, value: Float) {
        if (key.isNotBlank()) {
            scores[key] = (scores[key] ?: 0f) + value
        }
    }

    private fun weightsForUser(): EnsembleWeights = when {
        userTransactionCount < 10 -> EnsembleWeights(0.60f, 0.25f, 0.15f, 0f)
        userTransactionCount < 50 -> EnsembleWeights(0.45f, 0.15f, 0.10f, 0.30f)
        else -> EnsembleWeights(0.35f, 0.10f, 0.05f, 0.50f)
    }

    private data class EnsembleWeights(
        val chtWeight: Float,
        val rulesWeight: Float,
        val atpWeight: Float,
        val habitWeight: Float,
    )
}
