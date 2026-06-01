package com.xpenzo.ml.models

import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassifierInput
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Room-backed wrapper around [HabitModel].
 *
 * Responsibilities:
 *  1. At startup ([warmUp]) load all persisted habits from Room into the fast in-memory cache.
 *  2. On [recordConfirmation] update both the in-memory cache and the Room [habits] table.
 *
 * The in-memory [HabitModel] is still the hot path for every [classify] call — Room is only
 * touched on warm-up and on user confirmations/corrections, keeping inference latency unaffected.
 */
class RoomBackedHabitModel(
    private val repository: TransactionRepository,
) : HabitModel() {

    /** Load all persisted habits into the in-memory cache. Call once on app start. */
    override suspend fun warmUp() = withContext(Dispatchers.IO) {
        val dbEntries = repository.getAllHabits().map { entity ->
            HabitDbEntry(
                upiId = entity.upiId,
                merchantName = entity.merchantNormalized, // already normalized
                l1Category = entity.l1Category,
                l2Category = entity.l2Category,
                l3Category = entity.l3Category,
                count = entity.confirmationCount,
            )
        }
        loadFromDb(dbEntries)
    }

    /**
     * Record a confirmed classification — updates the in-memory cache immediately and
     * persists to Room asynchronously on the IO dispatcher.
     */
    suspend fun recordAndPersist(
        merchantNormalized: String,
        upiId: String,
        l1: String,
        l2: String,
        l3: String,
    ) = withContext(Dispatchers.IO) {
        // 1. Update in-memory HabitModel (super class)
        recordConfirmation(upiId, merchantNormalized, l1, l2, l3)
        // 2. Persist to Room
        repository.recordHabit(merchantNormalized, upiId, l1, l2, l3)
    }

    // Ensure the public API of TransactionClassifier is forwarded to the base class
    override suspend fun classify(input: ClassifierInput): ClassificationResult =
        super.classify(input)
}
