package com.xpenzo.ml.core

data class ClassificationResult(
    val l1Category: String,
    val l1Confidence: Float,
    val l2Category: String,
    val l2Confidence: Float,
    val l3Category: String,
    val l3Confidence: Float,
    val top3: List<Pair<String, Float>> = emptyList(),
    val source: ClassificationSource,
    val componentScores: ComponentScores? = null,
    val inferenceMs: Long = 0,
)

enum class ClassificationSource {
    ML_MODEL,
    RULE_ENGINE,
    HABIT_CACHE,
    AMOUNT_TIME_PRIOR,
    ML_ENSEMBLE,
    FALLBACK,
}

data class ComponentScores(
    val chtConfidence: Float = 0f,
    val rulesConfidence: Float = 0f,
    val habitConfidence: Float = 0f,
    val atpConfidence: Float = 0f,
)
