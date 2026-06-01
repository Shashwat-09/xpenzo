package com.xpenzo.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Shield
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

/**
 * "Help Improve AI" screen — user controls opted-in correction upload.
 *
 * Privacy guarantees displayed to user:
 *  - Only normalized merchant text (digits replaced with #) is sent.
 *  - No raw amounts, no account numbers, no UPI IDs.
 *  - Data is aggregated and used only to improve the on-device ML model.
 *  - Opt out at any time; previously uploaded data cannot be recalled.
 */
@Composable
fun HelpImproveAiScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        // Back button + header
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
            }
            Text(
                "Help Improve AI",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold,
                    color = Ink,
                ),
            )
        }

        Spacer(Modifier.height(16.dp))

        // Hero card
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = GrapeSoft),
            elevation = CardDefaults.cardElevation(0.dp),
        ) {
            Column(Modifier.padding(20.dp)) {
                androidx.compose.foundation.layout.Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(Grape.copy(alpha = 0.15f), RoundedCornerShape(14.dp)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(Icons.Rounded.AutoAwesome, contentDescription = null, tint = Grape, modifier = Modifier.size(24.dp))
                }
                Spacer(Modifier.height(12.dp))
                Text(
                    "Make Xpenzo smarter for everyone",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold,
                        color = Grape,
                    ),
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    "When you correct a category, you can optionally help train the AI " +
                        "for all Xpenzo users. Contributions are completely anonymous.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Grape.copy(alpha = 0.8f),
                )
            }
        }

        Spacer(Modifier.height(20.dp))

        // Toggle card
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = Surface),
            elevation = CardDefaults.cardElevation(2.dp),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(
                        "Share anonymized corrections",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.SemiBold,
                            color = Ink,
                        ),
                    )
                    Text(
                        if (state.isOptedInToDataCollection) "You're helping improve the AI ✨"
                        else "Off — corrections stay on your device only",
                        style = MaterialTheme.typography.bodySmall,
                        color = Muted,
                    )
                }
                Switch(
                    checked = state.isOptedInToDataCollection,
                    onCheckedChange = { viewModel.setDataCollectionOptIn(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Surface,
                        checkedTrackColor = Grape,
                    ),
                )
            }
        }

        Spacer(Modifier.height(20.dp))

        // Privacy guarantees
        Text(
            "WHAT WE COLLECT (when opted in)",
            style = MaterialTheme.typography.labelMedium,
            color = Muted,
            modifier = Modifier.padding(horizontal = 4.dp),
        )

        Spacer(Modifier.height(8.dp))

        val guarantees = listOf(
            "Normalized merchant name (digits replaced with #, no brand names)",
            "UPI domain only (e.g. 'ybl', 'icici') — NOT your full VPA",
            "Amount range bucket (e.g. '₹200–500') — NOT the exact amount",
            "The category you corrected to (L1 / L2 / L3)",
        )

        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MintSoft),
            elevation = CardDefaults.cardElevation(0.dp),
        ) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                guarantees.forEach { text ->
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                        verticalAlignment = Alignment.Top,
                    ) {
                        Icon(
                            Icons.Rounded.CheckCircle,
                            contentDescription = null,
                            tint = Mint,
                            modifier = Modifier.size(18.dp).padding(top = 1.dp),
                        )
                        Text(
                            text,
                            style = MaterialTheme.typography.bodySmall,
                            color = Ink,
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Rounded.Shield, contentDescription = null, tint = Muted, modifier = Modifier.size(16.dp))
            Text(
                "We NEVER collect raw SMS, account numbers, full VPAs, or exact transaction amounts.",
                style = MaterialTheme.typography.bodySmall,
                color = Muted,
            )
        }
    }
}
