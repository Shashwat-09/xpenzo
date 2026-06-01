package com.xpenzo.ui.transactions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.ml.data.DataCollectionManager
import com.xpenzo.ml.data.DataCollectionPreferences
import com.xpenzo.ml.manager.ModelManager
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * ViewModel for the main transactions list screen.
 *
 * Exposes a [UiState] that consolidates all data needed for the home screen:
 *  - sorted transaction list (newest first)
 *  - loading / error state
 *  - month-to-date spend total
 *
 * Also keeps the ensemble habit count in sync so the adaptive weights stay
 * up to date without a round-trip through ModelManager internals.
 */
@HiltViewModel
class TransactionViewModel @Inject constructor(
    private val repository: TransactionRepository,
    private val modelManager: ModelManager,
    private val dataCollectionManager: DataCollectionManager,
    private val dataCollectionPreferences: DataCollectionPreferences,
) : ViewModel() {

    private val _filterState = MutableStateFlow(FilterState())

    val uiState: StateFlow<UiState> = combine(
        repository.allTransactions,
        _filterState,
        repository.flowHabits(),
    ) { transactions, filter, habits ->
        // Update ensemble weights whenever habit count changes
        modelManager.updateHabitCount(habits.count { it.confirmationCount >= 3 })

        val filtered = when (filter.period) {
            Period.ALL -> transactions
            Period.THIS_MONTH -> {
                val (start, end) = currentMonthBounds()
                transactions.filter { it.timestamp in start..end }
            }
            Period.THIS_WEEK -> {
                val (start, end) = currentWeekBounds()
                transactions.filter { it.timestamp in start..end }
            }
        }.let { list ->
            if (filter.l1Category != null) list.filter { it.l1Category == filter.l1Category } else list
        }

        val totalSpendPaise = filtered.filter { !it.isCredit }.sumOf { it.amount }

        UiState(
            transactions = filtered,
            totalSpendPaise = totalSpendPaise,
            isLoading = false,
            habitCount = habits.count { it.confirmationCount >= 3 },
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = UiState(isLoading = true),
    )

    // ── user actions ──────────────────────────────────────────────────────────

    fun setFilter(period: Period = Period.THIS_MONTH, l1Category: String? = null) {
        _filterState.update { it.copy(period = period, l1Category = l1Category) }
    }

    fun deleteTransaction(id: String) = viewModelScope.launch {
        repository.deleteTransaction(id)
    }

    /**
     * Apply a user correction to a transaction.
     *
     * Delegates to [DataCollectionManager] which:
     *  1. Updates the in-memory HabitModel + Room habit row.
     *  2. Persists the correction + updates the transaction row via [TransactionRepository].
     *  3. If the user is opted in, uploads an anonymized sample to Firestore.
     */
    fun applyCorrection(
        transaction: TransactionEntity,
        correctedL1: String,
        correctedL2: String,
        correctedL3: String,
    ) = viewModelScope.launch {
        dataCollectionManager.recordCorrection(
            transactionId = transaction.id,
            merchantNormalized = transaction.merchantNormalized,
            upiId = transaction.upiId,
            amountPaise = transaction.amount,
            originalL1 = transaction.l1Category,
            originalL2 = transaction.l2Category,
            originalL3 = transaction.l3Category,
            correctedL1 = correctedL1,
            correctedL2 = correctedL2,
            correctedL3 = correctedL3,
            isOptedIn = dataCollectionPreferences.isOptedIn,
        )
    }

    // ── helpers ───────────────────────────────────────────────────────────────

    private fun currentMonthBounds(): Pair<Long, Long> {
        val now = java.time.LocalDate.now()
        val start = now.withDayOfMonth(1).atStartOfDay()
            .toEpochSecond(java.time.ZoneOffset.UTC) * 1000
        val end = now.withDayOfMonth(now.lengthOfMonth())
            .atTime(23, 59, 59)
            .toEpochSecond(java.time.ZoneOffset.UTC) * 1000
        return start to end
    }

    private fun currentWeekBounds(): Pair<Long, Long> {
        val now = java.time.LocalDate.now()
        val start = now.with(java.time.temporal.TemporalAdjusters.previousOrSame(java.time.DayOfWeek.MONDAY))
            .atStartOfDay().toEpochSecond(java.time.ZoneOffset.UTC) * 1000
        val end = System.currentTimeMillis()
        return start to end
    }

    // ── UI models ─────────────────────────────────────────────────────────────

    data class UiState(
        val transactions: List<TransactionEntity> = emptyList(),
        val totalSpendPaise: Long = 0L,
        val isLoading: Boolean = false,
        val error: String? = null,
        val habitCount: Int = 0,
    ) {
        val totalSpendRupees: Double get() = totalSpendPaise / 100.0
        val modelMaturity: ModelMaturity get() = when {
            habitCount < 10 -> ModelMaturity.COLD
            habitCount < 50 -> ModelMaturity.WARM
            else -> ModelMaturity.MATURE
        }
    }

    data class FilterState(
        val period: Period = Period.THIS_MONTH,
        val l1Category: String? = null,
    )

    enum class Period { THIS_MONTH, THIS_WEEK, ALL }

    enum class ModelMaturity { COLD, WARM, MATURE }
}
