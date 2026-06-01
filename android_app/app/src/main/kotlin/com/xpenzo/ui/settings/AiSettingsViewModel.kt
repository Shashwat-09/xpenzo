package com.xpenzo.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.data.repository.TransactionRepository
import com.xpenzo.firebase.ModelUpdateManager
import com.xpenzo.ml.manager.ModelInfo
import com.xpenzo.ml.manager.ModelManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AiSettingsViewModel @Inject constructor(
    private val modelManager: ModelManager,
    private val repository: TransactionRepository,
    private val modelUpdateManager: ModelUpdateManager,
) : ViewModel() {

    private val _actionState = MutableStateFlow(ActionState())

    val uiState: StateFlow<UiState> = combine(
        modelManager.modelInfo,
        modelManager.activeModelId,
        repository.flowHabits(),
        _actionState,
    ) { info, activeId, habits, action ->
        UiState(
            modelInfo = info,
            activeId = activeId,
            totalHabits = habits.size,
            matureHabits = habits.count { it.confirmationCount >= 3 },
            actionState = action,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = UiState(),
    )

    fun resetHabits() = viewModelScope.launch {
        _actionState.update { it.copy(isResettingHabits = true, message = null) }
        runCatching { repository.deleteAllHabits() }
            .onSuccess {
                _actionState.update {
                    it.copy(isResettingHabits = false, message = "Habits cleared")
                }
            }
            .onFailure { e ->
                _actionState.update {
                    it.copy(isResettingHabits = false, message = "Failed: ${e.message}")
                }
            }
    }

    fun checkForUpdate() = viewModelScope.launch {
        _actionState.update { it.copy(isCheckingUpdate = true, message = null) }
        val updated = runCatching { modelUpdateManager.checkAndUpdate() }.getOrDefault(false)
        _actionState.update {
            it.copy(
                isCheckingUpdate = false,
                message = if (updated) "A new model was downloaded" else "You're on the latest model",
            )
        }
    }

    fun clearMessage() = _actionState.update { it.copy(message = null) }

    data class UiState(
        val modelInfo: ModelInfo? = null,
        val activeId: String = "loading",
        val totalHabits: Int = 0,
        val matureHabits: Int = 0,
        val actionState: ActionState = ActionState(),
    ) {
        val maturityLabel: String = when {
            matureHabits < 10 -> "Cold start — model leads decisions"
            matureHabits < 50 -> "Warming up — habits getting weight"
            else -> "Mature — habits dominate predictions"
        }
    }

    data class ActionState(
        val isResettingHabits: Boolean = false,
        val isCheckingUpdate: Boolean = false,
        val message: String? = null,
    )
}
