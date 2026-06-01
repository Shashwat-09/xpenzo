package com.xpenzo.ui.splits

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.xpenzo.data.db.entity.FriendEntity
import com.xpenzo.data.db.entity.GroupEntity
import com.xpenzo.splits.SplitsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject
import kotlinx.coroutines.ExperimentalCoroutinesApi

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class SplitsHomeViewModel @Inject constructor(
    private val splitsRepository: SplitsRepository,
) : ViewModel() {

    private val currentUserId: String
        get() = FirebaseAuth.getInstance().currentUser?.uid ?: "local_user"

    val uiState: StateFlow<UiState> = combine(
        splitsRepository.activeGroups,
        splitsRepository.friends,
    ) { groups, friends ->
        UiState(
            groups = groups,
            friends = friends,
            currentUserId = currentUserId,
            isLoading = false,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = UiState(isLoading = true),
    )

    data class UiState(
        val groups: List<GroupEntity> = emptyList(),
        val friends: List<FriendEntity> = emptyList(),
        val currentUserId: String = "local_user",
        val isLoading: Boolean = false,
    ) {
        val hasContent: Boolean get() = groups.isNotEmpty() || friends.isNotEmpty()
    }
}
