package com.xpenzo.ml.models

import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassificationSource
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.core.ComponentScores
import com.xpenzo.ml.core.TransactionClassifier
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlin.system.measureTimeMillis

open class HabitModel : TransactionClassifier {
    override val displayName = "User Habit Cache"
    override val version = "live"
    override val modelSizeBytes = 10_000L
    override val supportsColdStart = false

    private val upiCache = HashMap<String, HabitEntry>(256)
    private val merchantCache = HashMap<String, HabitEntry>(512)

    override suspend fun warmUp() = Unit

    override fun close() {
        upiCache.clear()
        merchantCache.clear()
    }

    override suspend fun classify(input: ClassifierInput): ClassificationResult =
        withContext(Dispatchers.Default) {
            lateinit var result: ClassificationResult
            val elapsed = measureTimeMillis {
                result = lookup(input)
            }
            result.copy(inferenceMs = elapsed)
        }

    fun recordConfirmation(
        upiId: String,
        merchantName: String,
        l1: String,
        l2: String,
        l3: String,
    ) {
        val upiKey = upiId.lowercase().trim()
        val merchantKey = normalizeMerchant(merchantName)
        upiCache[upiKey] = upiCache[upiKey].incrementOrCreate(l1, l2, l3)
        merchantCache[merchantKey] = merchantCache[merchantKey].incrementOrCreate(l1, l2, l3)
    }

    fun loadFromDb(entries: List<HabitDbEntry>) {
        upiCache.clear()
        merchantCache.clear()
        entries.forEach { entry ->
            val habitEntry = HabitEntry(
                l1Category = entry.l1Category,
                l2Category = entry.l2Category,
                l3Category = entry.l3Category,
                count = entry.count,
            )
            upiCache[entry.upiId] = habitEntry
            merchantCache[normalizeMerchant(entry.merchantName)] = habitEntry
        }
    }

    private fun lookup(input: ClassifierInput): ClassificationResult {
        val upiKey = input.upiId.lowercase().trim()
        upiCache[upiKey]?.takeIf { it.count >= minimumHabitCount }?.let {
            return it.toResult()
        }

        val merchantKey = normalizeMerchant(input.merchantName)
        merchantCache[merchantKey]?.takeIf { it.count >= minimumHabitCount }?.let {
            return it.toResult()
        }

        return ClassificationResult(
            l1Category = "",
            l1Confidence = 0f,
            l2Category = "",
            l2Confidence = 0f,
            l3Category = "",
            l3Confidence = 0f,
            source = ClassificationSource.HABIT_CACHE,
            componentScores = ComponentScores(habitConfidence = 0f),
        )
    }

    private fun HabitEntry?.incrementOrCreate(l1: String, l2: String, l3: String): HabitEntry =
        if (this != null && l3Category == l3) copy(count = count + 1) else HabitEntry(l1, l2, l3, 1)

    private fun HabitEntry.toResult(): ClassificationResult = ClassificationResult(
        l1Category = l1Category,
        l1Confidence = 0.95f,
        l2Category = l2Category,
        l2Confidence = 0.90f,
        l3Category = l3Category,
        l3Confidence = 0.85f,
        top3 = listOf(l3Category to 0.95f),
        source = ClassificationSource.HABIT_CACHE,
        componentScores = ComponentScores(habitConfidence = 0.95f),
    )

    private fun normalizeMerchant(name: String): String =
        name.lowercase().replace(Regex("[^a-z0-9 ]"), "").trim()

    companion object {
        const val minimumHabitCount = 3
    }

    data class HabitEntry(
        val l1Category: String,
        val l2Category: String,
        val l3Category: String,
        val count: Int,
    )

    data class HabitDbEntry(
        val upiId: String,
        val merchantName: String,
        val l1Category: String,
        val l2Category: String,
        val l3Category: String,
        val count: Int,
    )
}
