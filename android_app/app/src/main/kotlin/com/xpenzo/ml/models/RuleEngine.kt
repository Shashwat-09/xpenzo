package com.xpenzo.ml.models

import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassificationSource
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.core.ComponentScores
import com.xpenzo.ml.core.TransactionClassifier
import kotlin.system.measureTimeMillis

class RuleEngine : TransactionClassifier {
    override val displayName = "Rule Engine"
    override val version = "2026-05-21"
    override val modelSizeBytes = 50_000L
    override val supportsColdStart = true

    override suspend fun warmUp() = Unit

    override fun close() = Unit

    override suspend fun classify(input: ClassifierInput): ClassificationResult {
        lateinit var result: ClassificationResult
        val elapsed = measureTimeMillis {
            result = matchRules(input)
        }
        return result.copy(inferenceMs = elapsed)
    }

    private fun matchRules(input: ClassifierInput): ClassificationResult {
        val text = buildString {
            append(input.merchantName.lowercase())
            append(' ')
            append(input.upiId.lowercase())
            append(' ')
            append(input.rawSms.lowercase())
        }

        for (rule in rules) {
            if (rule.pattern.containsMatchIn(text)) {
                return ClassificationResult(
                    l1Category = rule.l1,
                    l1Confidence = 0.98f,
                    l2Category = rule.l2,
                    l2Confidence = 0.95f,
                    l3Category = rule.l3,
                    l3Confidence = 0.90f,
                    top3 = listOf(rule.l3 to 0.90f),
                    source = ClassificationSource.RULE_ENGINE,
                    componentScores = ComponentScores(rulesConfidence = 0.98f),
                )
            }
        }

        return ClassificationResult(
            l1Category = "Others",
            l1Confidence = 0f,
            l2Category = "Miscellaneous",
            l2Confidence = 0f,
            l3Category = "Miscellaneous",
            l3Confidence = 0f,
            source = ClassificationSource.RULE_ENGINE,
            componentScores = ComponentScores(rulesConfidence = 0f),
        )
    }

    private data class Rule(val pattern: Regex, val l1: String, val l2: String, val l3: String)

    private val rules = listOf(
        Rule(Regex("swiggy|zomato"), "Food & Dining", "Food Delivery", "Food Delivery"),
        Rule(Regex("uber|ola|rapido"), "Transport", "Cab", "Ride Hailing"),
        Rule(Regex("netflix|spotify|hotstar"), "Entertainment", "Streaming", "Subscriptions"),
        Rule(Regex("amazon|flipkart|myntra"), "Shopping", "Online", "Marketplace"),
        Rule(Regex("petrol|diesel|iocl|hpcl|bpcl"), "Transport", "Fuel", "Fuel Station"),
        Rule(Regex("jio|airtel|bsnl|vi recharge"), "Bills & Utilities", "Mobile", "Recharge"),
    )
}
