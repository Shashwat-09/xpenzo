package com.xpenzo.ui.home

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.TrendingUp
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface
import com.xpenzo.ui.theme.xpenzo
import com.xpenzo.ui.transactions.TransactionViewModel
import java.text.NumberFormat
import java.util.Locale

@Composable
fun HomeScreen(
    onTransactionClick: (String) -> Unit,
    onSearchClick: () -> Unit,
    viewModel: TransactionViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream),
        contentPadding = PaddingValues(bottom = 100.dp),
    ) {
        // Header
        item {
            HomeHeader(onSearchClick = onSearchClick)
        }

        // Hero balance card
        item {
            HeroCard(
                totalSpendPaise = uiState.totalSpendPaise,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            )
        }

        // Budget + daily avg mini cards
        item {
            MiniStatRow(modifier = Modifier.padding(horizontal = 16.dp))
        }

        // Category filter chips
        item {
            CategoryChips(
                selectedCategory = null,
                onCategorySelected = { viewModel.setFilter(l1Category = it) },
                modifier = Modifier.padding(vertical = 8.dp),
            )
        }

        // AI nudge card
        item {
            AiNudgeCard(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
            )
        }

        // Transactions header
        item {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "Recent",
                    style = MaterialTheme.typography.headlineSmall,
                    color = Ink,
                )
                Text(
                    text = "See all",
                    style = MaterialTheme.typography.titleSmall,
                    color = Coral,
                )
            }
        }

        // Transactions
        if (uiState.isLoading) {
            item { LoadingShimmer() }
        } else if (uiState.transactions.isEmpty()) {
            item { EmptyState() }
        } else {
            items(
                items = uiState.transactions.take(20),
                key = { it.id },
            ) { tx ->
                TransactionRow(
                    tx = tx,
                    onClick = { onTransactionClick(tx.id) },
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                )
            }
        }
    }
}

// ── Header ────────────────────────────────────────────────────────────────────

@Composable
private fun HomeHeader(onSearchClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column {
            Text(
                text = "Hey there 👋",
                style = MaterialTheme.typography.bodyMedium,
                color = Muted,
            )
            Text(
                text = "Your expenses",
                style = MaterialTheme.typography.headlineMedium,
                color = Ink,
            )
        }
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = Surface,
            shadowElevation = 4.dp,
            modifier = Modifier
                .size(44.dp)
                .clickable { onSearchClick() },
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = Icons.Rounded.Search,
                    contentDescription = "Search",
                    tint = Ink,
                    modifier = Modifier.size(22.dp),
                )
            }
        }
    }
}

// ── Hero Card ─────────────────────────────────────────────────────────────────

@Composable
private fun HeroCard(totalSpendPaise: Long, modifier: Modifier = Modifier) {
    val float by rememberInfiniteTransition(label = "hero_float").animateFloat(
        initialValue = 0f, targetValue = -6f, label = "float_y",
        animationSpec = infiniteRepeatable(tween(3000, easing = FastOutSlowInEasing), RepeatMode.Reverse),
    )
    Card(
        modifier = modifier
            .fillMaxWidth()
            .offset(y = float.dp)
            .shadow(elevation = 16.dp, shape = RoundedCornerShape(28.dp), spotColor = Coral.copy(0.4f)),
        shape = RoundedCornerShape(28.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    brush = Brush.linearGradient(listOf(Coral, Color(0xFFFF8A80))),
                )
                .padding(24.dp),
        ) {
            // Decorative circles
            Box(
                modifier = Modifier
                    .size(120.dp)
                    .align(Alignment.TopEnd)
                    .offset(x = 30.dp, y = (-30).dp)
                    .clip(CircleShape)
                    .background(Color.White.copy(alpha = 0.15f)),
            )
            Box(
                modifier = Modifier
                    .size(100.dp)
                    .align(Alignment.BottomStart)
                    .offset(x = (-25).dp, y = 30.dp)
                    .clip(CircleShape)
                    .background(Color.Black.copy(alpha = 0.05f)),
            )
            Column {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(
                        text = "SPENDING · THIS MONTH",
                        style = MaterialTheme.typography.labelMedium,
                        color = Color.White.copy(alpha = 0.8f),
                    )
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .clip(CircleShape)
                            .background(Color.White.copy(alpha = 0.2f))
                            .padding(horizontal = 10.dp, vertical = 4.dp),
                    ) {
                        Icon(
                            Icons.Rounded.TrendingUp,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(14.dp),
                        )
                        Spacer(Modifier.width(4.dp))
                        Text("Live", style = MaterialTheme.typography.labelMedium, color = Color.White)
                    }
                }
                Spacer(Modifier.height(12.dp))
                Text(
                    text = "₹${formatRupees(totalSpendPaise)}",
                    style = MaterialTheme.typography.displayMedium,
                    color = Color.White,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "Total expenses",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White.copy(alpha = 0.8f),
                )
            }
        }
    }
}

// ── Mini stat cards ───────────────────────────────────────────────────────────

@Composable
private fun MiniStatRow(modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth().padding(vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        MiniStatCard(
            modifier = Modifier.weight(1f),
            backgroundColor = MintSoft,
            iconBg = Mint,
            label = "Budget left",
            value = "₹12,550",
            sub = null,
        )
        MiniStatCard(
            modifier = Modifier.weight(1f),
            backgroundColor = SunSoft,
            iconBg = Sun,
            label = "Daily avg",
            value = "₹2,100",
            sub = "↓ ₹150 vs last month",
        )
    }
}

@Composable
private fun MiniStatCard(
    modifier: Modifier = Modifier,
    backgroundColor: Color,
    iconBg: Color,
    label: String,
    value: String,
    sub: String?,
) {
    Card(
        modifier = modifier.shadow(4.dp, RoundedCornerShape(20.dp)),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = backgroundColor),
        elevation = CardDefaults.cardElevation(0.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(iconBg),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    Icons.Rounded.TrendingUp,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(20.dp),
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(label, style = MaterialTheme.typography.labelMedium, color = iconBg)
            Text(value, style = MaterialTheme.typography.displaySmall.copy(fontSize = 22.sp), color = Ink)
            if (sub != null) {
                Spacer(Modifier.height(4.dp))
                Text(sub, style = MaterialTheme.typography.bodySmall, color = iconBg)
            }
        }
    }
}

// ── Category chips ────────────────────────────────────────────────────────────

private val CATEGORY_CHIPS = listOf(
    "All" to null,
    "Food" to Coral,
    "Transport" to Sky,
    "Shopping" to Grape,
    "Groceries" to Mint,
    "Bills" to Sun,
)

@Composable
private fun CategoryChips(
    selectedCategory: String?,
    onCategorySelected: (String?) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier.horizontalScroll(rememberScrollState()).padding(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        CATEGORY_CHIPS.forEach { (label, color) ->
            val isSelected = (label == "All" && selectedCategory == null) || label == selectedCategory
            Surface(
                shape = CircleShape,
                color = if (isSelected) Ink else Surface,
                shadowElevation = if (isSelected) 0.dp else 4.dp,
                modifier = Modifier.clickable { onCategorySelected(if (label == "All") null else label) },
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    if (color != null) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (isSelected) Color.White else color),
                        )
                    }
                    Text(
                        text = label,
                        style = MaterialTheme.typography.titleSmall,
                        color = if (isSelected) Cream else Ink,
                    )
                }
            }
        }
    }
}

// ── AI Nudge ──────────────────────────────────────────────────────────────────

@Composable
private fun AiNudgeCard(modifier: Modifier = Modifier) {
    val float by rememberInfiniteTransition(label = "ai_float").animateFloat(
        initialValue = 0f, targetValue = -4f, label = "float_ai",
        animationSpec = infiniteRepeatable(tween(4000, easing = FastOutSlowInEasing), RepeatMode.Reverse),
    )
    Card(
        modifier = modifier.fillMaxWidth().shadow(4.dp, RoundedCornerShape(20.dp)),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = GrapeSoft),
        elevation = CardDefaults.cardElevation(0.dp),
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .offset(y = float.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(Grape),
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Rounded.AutoAwesome, contentDescription = null, tint = Color.White, modifier = Modifier.size(24.dp))
            }
            Column(Modifier.weight(1f)) {
                Text(
                    "XPENZO AI",
                    style = MaterialTheme.typography.labelMedium,
                    color = Grape,
                    letterSpacing = 1.sp,
                )
                Text(
                    "Tap to review your spending patterns and get personalized insights.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Ink,
                )
            }
            Box(
                modifier = Modifier
                    .size(36.dp)
                    .clip(CircleShape)
                    .background(Surface),
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Rounded.ChevronRight, contentDescription = null, tint = Grape, modifier = Modifier.size(20.dp))
            }
        }
    }
}

// ── Transaction row ───────────────────────────────────────────────────────────

@Composable
fun TransactionRow(
    tx: TransactionEntity,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val categoryColor = categoryColor(tx.l1Category)
    Card(
        modifier = modifier.fillMaxWidth().clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Category icon background
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(categoryColor.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = categoryEmoji(tx.l1Category),
                    fontSize = 20.sp,
                )
            }

            // Merchant + category
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = tx.merchantRaw.take(24).ifBlank { "Transaction" },
                    style = MaterialTheme.typography.titleMedium,
                    color = Ink,
                    maxLines = 1,
                )
                Text(
                    text = tx.l1Category,
                    style = MaterialTheme.typography.bodySmall,
                    color = Muted,
                )
            }

            // Amount
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "${if (tx.isCredit) "+" else "-"}₹${formatRupees(tx.amount)}",
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.ExtraBold),
                    color = if (tx.isCredit) Mint else Ink,
                )
                Text(
                    text = "${(tx.l1Confidence * 100).toInt()}%",
                    style = MaterialTheme.typography.labelSmall,
                    color = Muted,
                )
            }
        }
    }
}

// ── Shimmer / empty ───────────────────────────────────────────────────────────

@Composable
private fun LoadingShimmer() {
    Column(
        modifier = Modifier.padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        repeat(5) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(64.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(Muted.copy(alpha = 0.15f)),
            )
        }
    }
}

@Composable
private fun EmptyState() {
    Column(
        modifier = Modifier.fillMaxWidth().padding(48.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("💸", fontSize = 48.sp)
        Text("No transactions yet", style = MaterialTheme.typography.headlineSmall, color = Ink)
        Text(
            "Xpenzo will automatically detect your UPI payments from SMS messages.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

private fun formatRupees(paise: Long): String {
    val rupees = paise / 100.0
    return NumberFormat.getNumberInstance(Locale("en", "IN"))
        .apply { maximumFractionDigits = 0 }
        .format(rupees)
}

private val TransactionEntity.l1Confidence: Float get() = confidence

private fun categoryColor(l1: String): Color = when (l1.lowercase()) {
    "food", "dining" -> Coral
    "transport", "travel" -> Sky
    "shopping" -> Grape
    "groceries" -> Mint
    "bills", "utilities" -> Sun
    "health", "medical" -> Color(0xFFEF5350)
    else -> Muted
}

private fun categoryEmoji(l1: String): String = when (l1.lowercase()) {
    "food", "dining"      -> "🍽️"
    "transport", "travel" -> "🚗"
    "shopping"            -> "🛍️"
    "groceries"           -> "🛒"
    "bills", "utilities"  -> "⚡"
    "health", "medical"   -> "💊"
    "entertainment"       -> "🎬"
    "education"           -> "📚"
    else                  -> "💳"
}
