package com.xpenzo.ui.transactions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.sms.UpiSmsParser
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

@HiltViewModel
class ManualEntryViewModel @Inject constructor(
    private val repository: TransactionRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun updateMerchant(text: String) =
        _uiState.update { it.copy(merchant = text.take(60), error = null) }

    fun updateAmount(text: String) {
        // Keep only digits and at most one decimal point, max 2 decimals
        val cleaned = buildString {
            var seenDot = false
            var decimalsAfterDot = 0
            for (ch in text) {
                when {
                    ch.isDigit() && (!seenDot || decimalsAfterDot < 2) -> {
                        append(ch)
                        if (seenDot) decimalsAfterDot++
                    }
                    ch == '.' && !seenDot -> { append(ch); seenDot = true }
                }
            }
        }.take(10)
        _uiState.update { it.copy(amountRupees = cleaned, error = null) }
    }

    fun selectCategory(l1: String) =
        _uiState.update { it.copy(l1Category = l1, error = null) }

    fun toggleCredit() =
        _uiState.update { it.copy(isCredit = !it.isCredit) }

    fun save(onSaved: () -> Unit) = viewModelScope.launch {
        val s = _uiState.value
        val amountRupees = s.amountRupees.toDoubleOrNull()
        if (s.merchant.isBlank() || amountRupees == null || amountRupees <= 0) {
            _uiState.update { it.copy(error = "Enter a merchant and a positive amount") }
            return@launch
        }
        if (s.l1Category.isBlank()) {
            _uiState.update { it.copy(error = "Pick a category") }
            return@launch
        }

        val tx = TransactionEntity(
            id = UUID.randomUUID().toString(),
            merchantRaw = s.merchant.trim(),
            merchantNormalized = UpiSmsParser.normalizeMerchant(s.merchant.trim()),
            upiId = "",
            amount = (amountRupees * 100).toLong(),
            isCredit = s.isCredit,
            timestamp = System.currentTimeMillis(),
            l1Category = s.l1Category,
            l2Category = s.l1Category,  // user picks broad L1; refine later via correction
            l3Category = s.l1Category,
            confidence = 1.0f,           // user-entered — 100% confidence
            source = "MANUAL",
            isCorrected = false,
            synced = false,
            rawSms = "",
        )

        repository.insertTransaction(tx)
        _uiState.update { it.copy(saved = true) }
        onSaved()
    }

    data class UiState(
        val merchant: String = "",
        val amountRupees: String = "",
        val l1Category: String = "",
        val isCredit: Boolean = false,
        val error: String? = null,
        val saved: Boolean = false,
    )

    companion object {
        /** L1 categories the user can pick. Subset of the 15 canonical L1s. */
        val L1_CATEGORIES = listOf(
            "Food & Dining" to "🍽️",
            "Transport" to "🚕",
            "Shopping" to "🛍️",
            "Entertainment" to "🎬",
            "Healthcare" to "🏥",
            "Bills & Utilities" to "💡",
            "Finance" to "🏦",
            "Education" to "🎓",
            "Travel" to "✈️",
            "Social" to "🎁",
            "Personal Care" to "💆",
            "Home" to "🏠",
            "Pets" to "🐾",
            "Subscriptions" to "🔁",
            "Others" to "📝",
        )
    }
}
