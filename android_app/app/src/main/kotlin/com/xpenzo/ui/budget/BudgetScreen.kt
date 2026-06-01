package com.xpenzo.ui.budget

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.xpenzo.data.db.entity.BudgetEntity
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface

@Composable
fun BudgetScreen(viewModel: BudgetViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        containerColor = Cream,
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { /* navigate to create budget */ },
                containerColor = Coral,
                contentColor = Color.White,
                shape = RoundedCornerShape(16.dp),
                icon = { Icon(Icons.Rounded.Add, contentDescription = null) },
                text = { Text("New budget", style = MaterialTheme.typography.titleMedium) },
            )
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                Text(
                    "Budgets",
                    style = MaterialTheme.typography.headlineLarge,
                    color = Ink,
                    modifier = Modifier.padding(vertical = 8.dp),
                )
            }

            if (uiState.budgets.isEmpty()) {
                item { BudgetEmptyState() }
            } else {
                items(uiState.budgets, key = { it.id }) { budget ->
                    BudgetCard(
                        budget = budget,
                        spentPaise = uiState.spent[budget.id] ?: 0L,
                    )
                }
            }
        }
    }
}

@Composable
private fun BudgetCard(budget: BudgetEntity, spentPaise: Long) {
    val progress = if (budget.amountPaise > 0) (spentPaise.toFloat() / budget.amountPaise).coerceIn(0f, 1f) else 0f
    val leftPaise = (budget.amountPaise - spentPaise).coerceAtLeast(0L)
    val isOverBudget = spentPaise > budget.amountPaise

    val trackColor = when {
        progress > 0.9f -> Error
        progress > 0.7f -> Sun
        else -> Mint
    }

    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(2.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column {
                    Text(
                        budget.l1Category.ifBlank { "All" },
                        style = MaterialTheme.typography.titleLarge,
                        color = Ink,
                    )
                    if (budget.l2Category.isNotBlank()) {
                        Text(budget.l2Category, style = MaterialTheme.typography.bodySmall, color = Muted)
                    }
                    Text(budget.periodType, style = MaterialTheme.typography.labelMedium, color = Muted)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        "₹${formatRupees(budget.amountPaise)}",
                        style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.ExtraBold),
                        color = Ink,
                    )
                    Text("budget", style = MaterialTheme.typography.labelSmall, color = Muted)
                }
            }

            Spacer(Modifier.height(16.dp))

            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(4.dp)),
                color = trackColor,
                trackColor = trackColor.copy(alpha = 0.15f),
                strokeCap = StrokeCap.Round,
            )

            Spacer(Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    "Spent: ₹${formatRupees(spentPaise)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = if (isOverBudget) Error else Muted,
                )
                Text(
                    if (isOverBudget) "Over by ₹${formatRupees(spentPaise - budget.amountPaise)}"
                    else "₹${formatRupees(leftPaise)} left",
                    style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                    color = trackColor,
                )
            }
        }
    }
}

@Composable
private fun BudgetEmptyState() {
    Column(
        modifier = Modifier.fillMaxWidth().padding(vertical = 48.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("🎯", style = MaterialTheme.typography.displayMedium)
        Text("No budgets set", style = MaterialTheme.typography.headlineSmall, color = Ink)
        Text(
            "Set spending limits to stay on track each month.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )
    }
}

private fun formatRupees(paise: Long): String {
    val rupees = paise / 100.0
    return if (rupees >= 1_00_000) "%.1fL".format(rupees / 100_000)
    else if (rupees >= 1_000) "%.1fK".format(rupees / 1_000)
    else rupees.toInt().toString()
}
