package com.xpenzo.ui.insights

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.Surface
import com.xpenzo.ui.transactions.TransactionViewModel

@Composable
fun InsightsScreen(viewModel: TransactionViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // Compute spend by L1 category
    val spendByCategory = uiState.transactions
        .filter { !it.isCredit }
        .groupBy { it.l1Category }
        .mapValues { (_, txs) -> txs.sumOf { it.amount } }
        .entries
        .sortedByDescending { it.value }

    val totalSpend = spendByCategory.sumOf { it.value }.coerceAtLeast(1L)

    LazyColumn(
        modifier = Modifier.fillMaxSize().background(Cream),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Text(
                "Insights",
                style = MaterialTheme.typography.headlineLarge,
                color = Ink,
                modifier = Modifier.padding(vertical = 8.dp),
            )
        }

        // AI maturity card
        item {
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = GrapeSoft),
                elevation = CardDefaults.cardElevation(0.dp),
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        "AI MODEL STATUS",
                        style = MaterialTheme.typography.labelMedium,
                        color = Grape,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        when (uiState.modelMaturity) {
                            TransactionViewModel.ModelMaturity.COLD -> "🌱 Cold start — learning your habits"
                            TransactionViewModel.ModelMaturity.WARM -> "🔥 Warming up — ${uiState.habitCount} patterns learned"
                            TransactionViewModel.ModelMaturity.MATURE -> "✨ Mature — personalised to you"
                        },
                        style = MaterialTheme.typography.titleMedium,
                        color = Ink,
                    )
                    Spacer(Modifier.height(8.dp))
                    LinearProgressIndicator(
                        progress = { (uiState.habitCount / 50f).coerceIn(0f, 1f) },
                        modifier = Modifier.fillMaxWidth().height(6.dp).clip(RoundedCornerShape(3.dp)),
                        color = Grape,
                        trackColor = Grape.copy(alpha = 0.2f),
                        strokeCap = StrokeCap.Round,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "${uiState.habitCount} / 50 habits for mature mode",
                        style = MaterialTheme.typography.labelSmall,
                        color = Muted,
                    )
                }
            }
        }

        // Spend by category
        item {
            Text(
                "Spending breakdown",
                style = MaterialTheme.typography.headlineSmall,
                color = Ink,
            )
        }

        if (spendByCategory.isEmpty()) {
            item {
                Box(
                    modifier = Modifier.fillMaxWidth().padding(32.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text("No data yet. Transactions will appear here.", color = Muted)
                }
            }
        } else {
            items(spendByCategory.size) { idx ->
                val (l1, spend) = spendByCategory[idx]
                val pct = spend.toFloat() / totalSpend
                val color = CATEGORY_COLORS.getOrElse(idx) { Muted }

                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Surface),
                    elevation = CardDefaults.cardElevation(2.dp),
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(color),
                        )
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(l1.ifBlank { "Others" }, style = MaterialTheme.typography.titleMedium, color = Ink)
                                Text(
                                    "₹${formatRupees(spend)}",
                                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.ExtraBold),
                                    color = Ink,
                                )
                            }
                            Spacer(Modifier.height(6.dp))
                            LinearProgressIndicator(
                                progress = { pct },
                                modifier = Modifier.fillMaxWidth().height(5.dp).clip(RoundedCornerShape(3.dp)),
                                color = color,
                                trackColor = color.copy(alpha = 0.15f),
                                strokeCap = StrokeCap.Round,
                            )
                            Spacer(Modifier.height(2.dp))
                            Text(
                                "${(pct * 100).toInt()}% of spending",
                                style = MaterialTheme.typography.labelSmall,
                                color = Muted,
                            )
                        }
                    }
                }
            }
        }
    }
}

private val CATEGORY_COLORS = listOf(Coral, Mint, Sky, Grape, Sun, Color(0xFFEF5350), Muted)

private fun formatRupees(paise: Long): String {
    val r = paise / 100.0
    return if (r >= 100_000) "%.1fL".format(r / 100_000)
    else if (r >= 1_000) "%.1fK".format(r / 1_000)
    else r.toInt().toString()
}
