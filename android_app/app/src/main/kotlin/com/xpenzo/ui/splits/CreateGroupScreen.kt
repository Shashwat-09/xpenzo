package com.xpenzo.ui.splits

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.PersonAdd
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.xpenzo.data.db.entity.FriendEntity
import com.xpenzo.splits.SplitsRepository
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CreateGroupViewModel @Inject constructor(
    private val splitsRepository: SplitsRepository,
) : ViewModel() {

    private val _selectedFriendIds = MutableStateFlow<Set<String>>(emptySet())

    val uiState: StateFlow<UiState> = combine(
        splitsRepository.friends, _selectedFriendIds,
    ) { friends, selected ->
        UiState(friends = friends, selectedFriendIds = selected)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = UiState(),
    )

    fun toggleFriend(id: String) = _selectedFriendIds.update {
        if (id in it) it - id else it + id
    }

    suspend fun create(name: String, emoji: String, creatorDisplayName: String): String? {
        if (name.isBlank()) return null
        val state = uiState.value
        val others = state.friends
            .filter { it.id in state.selectedFriendIds }
            .map { it.otherUserId to it.displayName }

        val creatorUid = FirebaseAuth.getInstance().currentUser?.uid ?: "local_user"

        return splitsRepository.createGroup(
            name = name.trim(),
            emoji = emoji,
            creatorUserId = creatorUid,
            creatorDisplayName = creatorDisplayName.ifBlank { "You" },
            otherMembers = others,
        )
    }

    data class UiState(
        val friends: List<FriendEntity> = emptyList(),
        val selectedFriendIds: Set<String> = emptySet(),
    )
}

private val EMOJI_OPTIONS = listOf("👥", "✈️", "🏠", "🍽️", "🎉", "💼", "🚗", "💑", "🏖️", "👨‍👩‍👧")

@Composable
fun CreateGroupScreen(
    onBack: () -> Unit,
    onCreated: (groupId: String) -> Unit,
    viewModel: CreateGroupViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var name by remember { mutableStateOf("") }
    var emoji by remember { mutableStateOf("👥") }
    var saving by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().background(Cream)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
            }
            Text(
                "Create group",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Emoji picker
            Text("Pick an emoji", style = MaterialTheme.typography.labelLarge.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(horizontal = 4.dp),
            ) {
                items(EMOJI_OPTIONS) { e ->
                    Box(
                        modifier = Modifier
                            .size(48.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (emoji == e) Grape.copy(alpha = 0.2f) else Surface)
                            .clickable { emoji = e },
                        contentAlignment = Alignment.Center,
                    ) {
                        Text(e, style = MaterialTheme.typography.headlineSmall)
                    }
                }
            }

            // Group name
            OutlinedTextField(
                value = name,
                onValueChange = { name = it.take(40) },
                label = { Text("Group name") },
                placeholder = { Text("e.g. Goa Trip, Flatmates, Couple") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Grape, cursorColor = Grape,
                    focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                ),
            )

            // Friends picker
            Text("Add members from your friends", style = MaterialTheme.typography.labelLarge.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))

            if (state.friends.isEmpty()) {
                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Surface),
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(Icons.Rounded.PersonAdd, contentDescription = null, tint = Muted)
                        Spacer(Modifier.width(12.dp))
                        Text("No friends added yet. You can create the group and add members later.",
                            style = MaterialTheme.typography.bodySmall, color = Muted)
                    }
                }
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    state.friends.forEach { friend ->
                        FriendSelectRow(
                            friend = friend,
                            selected = friend.id in state.selectedFriendIds,
                            onToggle = { viewModel.toggleFriend(friend.id) },
                        )
                    }
                }
            }

            Spacer(Modifier.weight(1f))

            Button(
                onClick = {
                    if (name.isBlank() || saving) return@Button
                    saving = true
                    scope.launch {
                        val id = viewModel.create(name, emoji, "You")
                        saving = false
                        if (id != null) onCreated(id)
                    }
                },
                enabled = name.isNotBlank() && !saving,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Coral),
                shape = RoundedCornerShape(20.dp),
            ) {
                Text(if (saving) "Creating…" else "Create group",
                    fontWeight = FontWeight.SemiBold, color = Surface)
            }
        }
    }
}

@Composable
private fun FriendSelectRow(
    friend: FriendEntity,
    selected: Boolean,
    onToggle: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(if (selected) Mint.copy(alpha = 0.1f) else Surface)
            .clickable(onClick = onToggle)
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .background(Muted.copy(alpha = 0.15f), RoundedCornerShape(50)),
            contentAlignment = Alignment.Center,
        ) {
            Text(friend.displayName.take(1).uppercase(),
                style = MaterialTheme.typography.titleSmall.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ))
        }
        Spacer(Modifier.width(12.dp))
        Text(friend.displayName, modifier = Modifier.weight(1f), color = Ink,
            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Medium))
        if (selected) {
            Icon(Icons.Rounded.Check, contentDescription = "Selected", tint = Mint)
        }
    }
}
