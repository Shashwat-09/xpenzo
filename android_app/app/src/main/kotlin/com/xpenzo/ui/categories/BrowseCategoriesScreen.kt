package com.xpenzo.ui.categories

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.ExpandLess
import androidx.compose.material.icons.rounded.ExpandMore
import androidx.compose.material.icons.rounded.Search
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
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.Surface

@Composable
fun BrowseCategoriesScreen(
    onBack: () -> Unit,
    viewModel: BrowseCategoriesViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier = Modifier.fillMaxSize().background(Cream),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
            }
            Text(
                "Browse Categories",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        OutlinedTextField(
            value = state.query,
            onValueChange = viewModel::updateQuery,
            placeholder = { Text("Search 520 categories or merchants…") },
            singleLine = true,
            leadingIcon = { Icon(Icons.Rounded.Search, contentDescription = null, tint = Muted) },
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
            shape = RoundedCornerShape(16.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = Surface, unfocusedContainerColor = Surface,
            ),
        )

        if (state.isLoading) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            return@Column
        }

        if (state.filteredTaxonomy.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No matches for \"${state.query}\"", color = Muted)
            }
            return@Column
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 8.dp),
        ) {
            items(state.filteredTaxonomy, key = { it.code }) { l1 ->
                L1Card(
                    node = l1,
                    expanded = l1.code in state.expandedL1,
                    onToggleL1 = { viewModel.toggleL1(l1.code) },
                    expandedL2 = state.expandedL2,
                    onToggleL2 = viewModel::toggleL2,
                )
            }
        }
    }
}

@Composable
private fun L1Card(
    node: BrowseCategoriesViewModel.L1Node,
    expanded: Boolean,
    onToggleL1: () -> Unit,
    expandedL2: Set<String>,
    onToggleL2: (String) -> Unit,
) {
    val color = colorForL1(node.code)
    val emoji = emojiForIcon(node.icon)

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(1.dp),
    ) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(onClick = onToggleL1)
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(color.copy(alpha = 0.18f)),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(emoji, style = MaterialTheme.typography.titleLarge)
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(
                        node.name,
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.SemiBold, color = Ink,
                        ),
                    )
                    Text(
                        "${node.children.size} sub-categories · ${node.children.sumOf { it.children.size }} micro-cats",
                        style = MaterialTheme.typography.bodySmall, color = Muted,
                    )
                }
                Icon(
                    if (expanded) Icons.Rounded.ExpandLess else Icons.Rounded.ExpandMore,
                    contentDescription = null, tint = Muted,
                )
            }

            AnimatedVisibility(visible = expanded) {
                Column(Modifier.padding(start = 24.dp, end = 16.dp, bottom = 12.dp)) {
                    node.children.forEach { l2 ->
                        L2Row(
                            node = l2,
                            expanded = l2.code in expandedL2,
                            onToggle = { onToggleL2(l2.code) },
                            color = color,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun L2Row(
    node: BrowseCategoriesViewModel.L2Node,
    expanded: Boolean,
    onToggle: () -> Unit,
    color: Color,
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth().clickable(onClick = onToggle).padding(vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier.size(6.dp).clip(CircleShape).background(color),
            )
            Spacer(Modifier.width(12.dp))
            Text(
                node.name,
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Medium, color = Ink,
                ),
                modifier = Modifier.weight(1f),
            )
            Text(
                "${node.children.size}",
                style = MaterialTheme.typography.bodySmall, color = Muted,
            )
            Icon(
                if (expanded) Icons.Rounded.ExpandLess else Icons.Rounded.ExpandMore,
                contentDescription = null, tint = Muted, modifier = Modifier.size(18.dp),
            )
        }

        AnimatedVisibility(visible = expanded) {
            Column(Modifier.padding(start = 18.dp, bottom = 8.dp)) {
                node.children.forEach { l3 ->
                    Column(Modifier.padding(vertical = 4.dp)) {
                        Text("• ${l3.name}", style = MaterialTheme.typography.bodySmall, color = Ink)
                        if (l3.exampleMerchants.isNotEmpty()) {
                            Text(
                                l3.exampleMerchants.joinToString(" · "),
                                style = MaterialTheme.typography.labelSmall,
                                color = Muted,
                                modifier = Modifier.padding(start = 12.dp),
                            )
                        }
                    }
                }
            }
        }
    }
}

// L1 code → brand color
private fun colorForL1(code: String): Color = when (code) {
    "FD"        -> Coral           // Food & Dining
    "TR"        -> Sky             // Transportation
    "SH"        -> Grape           // Shopping
    "EN"        -> Grape           // Entertainment
    "HC"        -> Color(0xFFEF5350) // Healthcare
    "UB"        -> Sun             // Utilities & Bills
    "FI"        -> Mint            // Finance
    "ED"        -> Sky             // Education
    "TV"        -> Sky             // Travel
    "FS"        -> Coral           // Family & Social
    "PC"        -> Coral           // Personal Care
    "PS"        -> Grape           // Professional Services
    "TC"        -> Sun             // Telecom
    "GT"        -> Muted           // Government
    else        -> Muted
}

// Best-effort emoji for the JSON's icon string
private fun emojiForIcon(icon: String): String = when (icon) {
    "restaurant" -> "🍽️"
    "directions_car", "transportation" -> "🚕"
    "shopping_bag", "shopping_cart" -> "🛍️"
    "movie", "entertainment" -> "🎬"
    "local_hospital", "healthcare" -> "🏥"
    "receipt", "utilities" -> "💡"
    "account_balance" -> "🏦"
    "school", "education" -> "🎓"
    "flight" -> "✈️"
    "people", "family" -> "👨‍👩‍👧"
    "spa", "personal_care" -> "💆"
    "work", "business_center" -> "💼"
    "phone_android" -> "📱"
    "policy", "gavel" -> "⚖️"
    else -> "💳"
}
