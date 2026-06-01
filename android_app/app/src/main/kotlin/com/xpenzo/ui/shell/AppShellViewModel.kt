package com.xpenzo.ui.shell

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class AppShellViewModel @Inject constructor(
    private val repository: AppShellRepository,
) : ViewModel() {
    val uiState: StateFlow<AppShellState> = repository.state().stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(stopTimeoutMillis = 5_000),
        initialValue = AppShellState(
            activeModel = "booting",
            modelDisplayName = "Bootstrapping",
            modelVersion = "pending",
            isReady = false,
            statusMessage = "Preparing the Android shell.",
            followOnSeams = emptyList(),
        ),
    )

    init {
        viewModelScope.launch {
            repository.bootstrap()
        }
    }
}
