package com.xpenzo.ui.splits

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.xpenzo.data.db.entity.GroupMemberEntity
import com.xpenzo.splits.SplitCalculator.Participant
import com.xpenzo.splits.SplitCalculator.SplitType
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
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AddExpenseViewModel @Inject constructor(
    savedState: SavedStateHandle,
    private val splitsRepository: SplitsRepository,
) : ViewModel() {

    private val groupId: String = checkNotNull(savedState["groupId"])

    private val _payerId = MutableStateFlow(
        FirebaseAuth.getInstance().currentUser?.uid ?: "local_user",
    )
    private val _splitType = MutableStateFlow(SplitType.EQUAL)
    private val _included = MutableStateFlow<Set<String>>(emptySet())
    /** Raw per-user input for EXACT (₹) / PERCENT (%) / SHARES (count). */
    private val _shareInputs = MutableStateFlow<Map<String, String>>(emptyMap())

    val uiState: StateFlow<UiState> = combine(
        splitsRepository.groupMembers(groupId),
        _payerId, _splitType, _included, _shareInputs,
    ) { members, payerId, type, included, shareInputs ->
        UiState(
            members = members,
            payerId = if (payerId in members.map { it.userId }) payerId else members.firstOrNull()?.userId ?: payerId,
            splitType = type,
            included = if (included.isEmpty()) members.map { it.userId }.toSet() else included,
            shareInputs = shareInputs,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = UiState(),
    )

    fun setPayer(userId: String) = _payerId.update { userId }
    fun toggleIncluded(userId: String) = _included.update {
        if (it.isEmpty()) {
            // initial pre-fill
            uiState.value.members.map { m -> m.userId }.toSet() - userId
        } else if (userId in it) it - userId else it + userId
    }
    fun setSplitType(type: SplitType) = _splitType.update { type }
    fun setShareInput(userId: String, raw: String) = _shareInputs.update {
        it + (userId to raw.filter { c -> c.isDigit() || c == '.' })
    }

    /**
     * Build participants for the active split type and persist.
     * EXACT/PERCENT/SHARES carry the per-user value; [SplitCalculator] validates the
     * totals (sum==total / ==100 / >0) and throws on invalid input — surfaced as [SaveResult].
     */
    suspend fun save(title: String, amountRupees: Double): SaveResult {
        if (title.isBlank() || amountRupees <= 0) return SaveResult.Invalid("Enter a title and amount")
        val state = uiState.value
        if (state.included.isEmpty()) return SaveResult.Invalid("Pick at least one person")

        val amountPaise = (amountRupees * 100).toLong()
        val participants = state.included.map { userId ->
            val raw = state.shareInputs[userId]?.toDoubleOrNull() ?: 0.0
            when (state.splitType) {
                SplitType.EQUAL -> Participant(userId)
                SplitType.EXACT -> Participant(userId, raw * 100) // ₹ → paise
                SplitType.PERCENT -> Participant(userId, raw)
                SplitType.SHARES -> Participant(userId, raw)
            }
        }

        return try {
            splitsRepository.createExpense(
                groupId = groupId,
                title = title.trim(),
                amountPaise = amountPaise,
                payerUserId = state.payerId,
                splitType = state.splitType,
                participants = participants,
            )
            SaveResult.Success
        } catch (e: IllegalArgumentException) {
            SaveResult.Invalid(e.message ?: "Those shares don't add up")
        }
    }

    sealed interface SaveResult {
        data object Success : SaveResult
        data class Invalid(val reason: String) : SaveResult
    }

    data class UiState(
        val members: List<GroupMemberEntity> = emptyList(),
        val payerId: String = "",
        val splitType: SplitType = SplitType.EQUAL,
        val included: Set<String> = emptySet(),
        val shareInputs: Map<String, String> = emptyMap(),
    )
}

@Composable
fun AddExpenseScreen(
    onBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: AddExpenseViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var title by remember { mutableStateOf("") }
    var amountText by remember { mutableStateOf("") }
    var saving by remember { mutableStateOf(false) }
    var errorMsg by remember { mutableStateOf<String?>(null) }
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
                "Add expense",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            OutlinedTextField(
                value = title,
                onValueChange = { title = it.take(50) },
                label = { Text("What was this for?") },
                placeholder = { Text("e.g. Dinner at Toit") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Coral, cursorColor = Coral,
                    focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                ),
            )

            OutlinedTextField(
                value = amountText,
                onValueChange = { amountText = it.filter { c -> c.isDigit() || c == '.' } },
                label = { Text("Amount (₹)") },
                placeholder = { Text("0.00") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                textStyle = MaterialTheme.typography.headlineMedium.copy(
                    fontWeight = FontWeight.Bold, textAlign = TextAlign.Center,
                ),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Coral, cursorColor = Coral,
                    focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                ),
            )

            // Paid by
            Text("Paid by", style = MaterialTheme.typography.labelLarge.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(state.members, key = { it.userId }) { member ->
                    SelectChip(
                        text = member.displayName,
                        selected = member.userId == state.payerId,
                        onClick = { viewModel.setPayer(member.userId) },
                    )
                }
            }

            // Split type
            Text("Split type", style = MaterialTheme.typography.labelLarge.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(SplitType.values()) { type ->
                    SelectChip(
                        text = when (type) {
                            SplitType.EQUAL -> "Equal"
                            SplitType.EXACT -> "Exact"
                            SplitType.PERCENT -> "Percent"
                            SplitType.SHARES -> "Shares"
                        },
                        selected = state.splitType == type,
                        onClick = { viewModel.setSplitType(type) },
                    )
                }
            }

            // Participants
            Text("Split between", style = MaterialTheme.typography.labelLarge.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                state.members.forEach { member ->
                    val included = member.userId in state.included
                    val showInput = included && state.splitType != SplitType.EQUAL
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(if (included) Mint.copy(alpha = 0.08f) else Surface)
                            .clickable { viewModel.toggleIncluded(member.userId) }
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(member.displayName, modifier = Modifier.weight(1f),
                            style = MaterialTheme.typography.bodyMedium.copy(color = Ink))
                        if (showInput) {
                            ShareInputField(
                                value = state.shareInputs[member.userId] ?: "",
                                suffix = when (state.splitType) {
                                    SplitType.EXACT -> "₹"
                                    SplitType.PERCENT -> "%"
                                    SplitType.SHARES -> "×"
                                    else -> ""
                                },
                                onValueChange = { viewModel.setShareInput(member.userId, it) },
                            )
                        } else if (included) {
                            Icon(Icons.Rounded.Check, contentDescription = "Included", tint = Mint)
                        }
                    }
                }
            }

            if (state.splitType != SplitType.EQUAL) {
                Text(
                    when (state.splitType) {
                        SplitType.EXACT -> "Enter each person's exact amount (₹). Must total the full amount."
                        SplitType.PERCENT -> "Enter each person's share (%). Must total 100%."
                        SplitType.SHARES -> "Enter relative shares (e.g. 1, 2, 1). Any positive numbers."
                        else -> ""
                    },
                    style = MaterialTheme.typography.bodySmall, color = Muted,
                )
            }

            errorMsg?.let { msg ->
                Text(msg, style = MaterialTheme.typography.bodySmall, color = Coral)
            }

            Spacer(Modifier.weight(1f))

            Button(
                onClick = {
                    if (saving) return@Button
                    val amount = amountText.toDoubleOrNull() ?: 0.0
                    if (title.isBlank() || amount <= 0 || state.included.isEmpty()) return@Button
                    saving = true
                    errorMsg = null
                    scope.launch {
                        when (val res = viewModel.save(title, amount)) {
                            is AddExpenseViewModel.SaveResult.Success -> {
                                saving = false
                                onSaved()
                            }
                            is AddExpenseViewModel.SaveResult.Invalid -> {
                                saving = false
                                errorMsg = res.reason
                            }
                        }
                    }
                },
                enabled = title.isNotBlank() && amountText.isNotBlank() && !saving,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Coral),
                shape = RoundedCornerShape(20.dp),
            ) {
                Text(if (saving) "Saving…" else "Save expense",
                    fontWeight = FontWeight.SemiBold, color = Surface)
            }
        }
    }
}

@Composable
private fun ShareInputField(value: String, suffix: String, onValueChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.width(110.dp),
        singleLine = true,
        placeholder = { Text("0") },
        trailingIcon = { Text(suffix, style = MaterialTheme.typography.bodyMedium.copy(color = Muted)) },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        textStyle = MaterialTheme.typography.bodyMedium.copy(textAlign = TextAlign.End),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = Coral, cursorColor = Coral,
            focusedContainerColor = Surface, unfocusedContainerColor = Surface,
        ),
    )
}

@Composable
private fun SelectChip(text: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (selected) Grape else Surface)
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 8.dp),
    ) {
        Text(
            text,
            style = MaterialTheme.typography.labelMedium.copy(
                color = if (selected) Surface else Ink,
                fontWeight = FontWeight.SemiBold,
            ),
        )
    }
}
