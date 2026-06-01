package com.xpenzo.ui.budget

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.data.db.entity.BudgetEntity
import com.xpenzo.data.repository.TransactionRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.LocalDate
import java.time.ZoneOffset
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class BudgetViewModel @Inject constructor(
    private val repository: TransactionRepository,
) : ViewModel() {

    val uiState = combine(
        repository.activeBudgets,
        repository.allTransactions,
    ) { budgets, transactions ->
        val (startMs, endMs) = currentMonthBounds()
        val spent = budgets.associate { budget ->
            val s = transactions
                .filter { tx ->
                    !tx.isCredit &&
                        tx.timestamp in startMs..endMs &&
                        (budget.l1Category.isBlank() || tx.l1Category == budget.l1Category) &&
                        (budget.l2Category.isBlank() || tx.l2Category == budget.l2Category)
                }
                .sumOf { it.amount }
            budget.id to s
        }
        BudgetUiState(budgets = budgets, spent = spent)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), BudgetUiState())

    fun collectAsStateWithLifecycle() = uiState

    private fun currentMonthBounds(): Pair<Long, Long> {
        val now = LocalDate.now()
        val start = now.withDayOfMonth(1).atStartOfDay().toEpochSecond(ZoneOffset.UTC) * 1000
        val end = now.withDayOfMonth(now.lengthOfMonth()).atTime(23, 59, 59).toEpochSecond(ZoneOffset.UTC) * 1000
        return start to end
    }

    data class BudgetUiState(
        val budgets: List<BudgetEntity> = emptyList(),
        val spent: Map<String, Long> = emptyMap(),
    )
}
