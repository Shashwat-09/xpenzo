package com.xpenzo.ui.splits

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Payments
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.xpenzo.data.db.entity.GroupEntity
import com.xpenzo.data.db.entity.GroupMemberEntity
import com.xpenzo.data.db.entity.SplitExpenseEntity
import com.xpenzo.splits.SplitCalculator.Transfer
import com.xpenzo.splits.SplitsRepository
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@HiltViewModel
class GroupBalancesViewModel @Inject constructor(
    savedState: SavedStateHandle,
    private val splitsRepository: SplitsRepository,
) : ViewModel() {

    private val groupId: String = checkNotNull(savedState["groupId"]) { "groupId arg missing" }

    val currentUserId: String =
        FirebaseAuth.getInstance().currentUser?.uid ?: "local_user"

    val uiState: StateFlow<UiState> = combine(
        splitsRepository.groupById(groupId),
        splitsRepository.groupMembers(groupId),
        splitsRepository.groupExpenses(groupId),
        splitsRepository.groupNetBalances(groupId),
        splitsRepository.groupSimplifiedTransfers(groupId),
    ) { group, members, expenses, balances, transfers ->
        UiState(
            group = group, members = members, expenses = expenses,
            balances = balances, simplifiedTransfers = transfers,
            isLoading = false,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = UiState(isLoading = true),
    )

    fun deleteExpense(id: String) = viewModelScope.launch {
        splitsRepository.deleteExpense(id)
    }

    data class UiState(
        val group: GroupEntity? = null,
        val members: List<GroupMemberEntity> = emptyList(),
        val expenses: List<SplitExpenseEntity> = emptyList(),
        val balances: Map<String, Long> = emptyMap(),
        val simplifiedTransfers: List<Transfer> = emptyList(),
        val isLoading: Boolean = false,
    ) {
        fun memberName(userId: String): String =
            members.firstOrNull { it.userId == userId }?.displayName ?: "Someone"
    }
}

@Composable
fun GroupBalancesScreen(
    onBack: () -> Unit,
    onAddExpense: (groupId: String) -> Unit,
    onSettleUp: (groupId: String, from: String, to: String, amountPaise: Long) -> Unit,
    viewModel: GroupBalancesViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val group = state.group

    Scaffold(
        containerColor = Cream,
        floatingActionButton = {
            if (group != null) {
                ExtendedFloatingActionButton(
                    onClick = { onAddExpense(group.id) },
                    containerColor = Coral,
                    contentColor = Surface,
                ) {
                    Icon(Icons.Rounded.Add, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Add expense", fontWeight = FontWeight.SemiBold)
                }
            }
        },
    ) { inner ->
        Column(modifier = Modifier.padding(inner).fillMaxSize()) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onBack) {
                    Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
                }
                Text(
                    group?.emoji + "  " + (group?.name ?: "Group"),
                    style = MaterialTheme.typography.titleLarge.copy(
                        fontWeight = FontWeight.Bold, color = Ink,
                    ),
                )
            }

            if (state.isLoading || group == null) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                return@Column
            }

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                // Your balance card
                item {
                    val yourBalance = state.balances[viewModel.currentUserId] ?: 0L
                    YourBalanceCard(yourBalancePaise = yourBalance)
                }

                // Suggested settlements
                if (state.simplifiedTransfers.isNotEmpty()) {
                    item {
                        SectionHeader("Suggested settlements")
                    }
                    items(state.simplifiedTransfers) { transfer ->
                        SettlementSuggestion(
                            fromName = state.memberName(transfer.from),
                            toName = state.memberName(transfer.to),
                            amountPaise = transfer.amountPaise,
                            isYou = transfer.from == viewModel.currentUserId,
                            onSettle = {
                                if (transfer.from == viewModel.currentUserId) {
                                    onSettleUp(group.id, transfer.from, transfer.to, transfer.amountPaise)
                                }
                            },
                        )
                    }
                }

                // Per-member balances
                item { SectionHeader("Member balances") }
                items(state.members) { member ->
                    MemberBalanceRow(
                        name = member.displayName + if (member.userId == viewModel.currentUserId) " (you)" else "",
                        balancePaise = state.balances[member.userId] ?: 0L,
                    )
                }

                // Expenses log
                item { SectionHeader("Expense history") }
                if (state.expenses.isEmpty()) {
                    item {
                        Text("No expenses yet — tap + to add one.",
                            style = MaterialTheme.typography.bodyMedium, color = Muted,
                            modifier = Modifier.padding(8.dp))
                    }
                } else {
                    items(state.expenses, key = { it.id }) { expense ->
                        ExpenseRow(expense = expense, payerName = state.memberName(expense.paidBy))
                    }
                }
            }
        }
    }
}

@Composable
private fun SectionHeader(text: String) {
    Text(
        text.uppercase(),
        style = MaterialTheme.typography.labelMedium.copy(
            fontWeight = FontWeight.Bold, color = Muted,
        ),
        modifier = Modifier.padding(vertical = 4.dp, horizontal = 4.dp),
    )
}

@Composable
private fun YourBalanceCard(yourBalancePaise: Long) {
    val isPositive = yourBalancePaise > 0
    val color = when {
        yourBalancePaise > 0 -> Mint
        yourBalancePaise < 0 -> Error
        else -> Muted
    }
    val bg = when {
        yourBalancePaise > 0 -> MintSoft
        yourBalancePaise < 0 -> Color(0xFFFFEBEE)
        else -> Surface
    }
    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = bg),
        elevation = CardDefaults.cardElevation(0.dp),
    ) {
        Column(
            modifier = Modifier.padding(24.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                when {
                    yourBalancePaise > 0 -> "You're owed"
                    yourBalancePaise < 0 -> "You owe"
                    else -> "All settled up"
                },
                style = MaterialTheme.typography.bodyMedium, color = color,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "₹${"%.2f".format(kotlin.math.abs(yourBalancePaise) / 100.0)}",
                style = MaterialTheme.typography.displaySmall.copy(
                    fontWeight = FontWeight.Bold, color = color,
                ),
            )
        }
    }
}

@Composable
private fun SettlementSuggestion(
    fromName: String,
    toName: String,
    amountPaise: Long,
    isYou: Boolean,
    onSettle: () -> Unit,
) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = GrapeSoft),
        elevation = CardDefaults.cardElevation(0.dp),
    ) {
        Row(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Rounded.Payments, contentDescription = null, tint = Grape)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    "$fromName → $toName",
                    style = MaterialTheme.typography.titleSmall.copy(
                        fontWeight = FontWeight.SemiBold, color = Grape,
                    ),
                )
                Text(
                    "₹${"%.2f".format(amountPaise / 100.0)}",
                    style = MaterialTheme.typography.bodyMedium, color = Grape,
                )
            }
            if (isYou) {
                Button(
                    onClick = onSettle,
                    colors = ButtonDefaults.buttonColors(containerColor = Grape),
                    shape = RoundedCornerShape(12.dp),
                ) { Text("Pay", color = Surface) }
            }
        }
    }
}

@Composable
private fun MemberBalanceRow(name: String, balancePaise: Long) {
    val color = when {
        balancePaise > 0 -> Mint
        balancePaise < 0 -> Error
        else -> Muted
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Surface)
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(name, modifier = Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium.copy(
            color = Ink, fontWeight = FontWeight.Medium,
        ))
        Text(
            when {
                balancePaise > 0 -> "+₹${"%.2f".format(balancePaise / 100.0)}"
                balancePaise < 0 -> "−₹${"%.2f".format(-balancePaise / 100.0)}"
                else -> "₹0"
            },
            style = MaterialTheme.typography.bodyMedium.copy(
                fontWeight = FontWeight.SemiBold, color = color,
            ),
        )
    }
}

@Composable
private fun ExpenseRow(expense: SplitExpenseEntity, payerName: String) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(1.dp),
    ) {
        Row(
            modifier = Modifier.padding(12.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(expense.title, style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.SemiBold, color = Ink,
                ))
                Text("Paid by $payerName", style = MaterialTheme.typography.bodySmall, color = Muted)
            }
            Text(
                "₹${"%.2f".format(expense.amountPaise / 100.0)}",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }
    }
}

