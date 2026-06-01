package com.xpenzo.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.CloudDownload
import androidx.compose.material.icons.rounded.RestartAlt
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.SkySoft
import com.xpenzo.ui.theme.Surface

@Composable
fun AiSettingsScreen(
    onBack: () -> Unit,
    viewModel: AiSettingsViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    var showResetDialog by remember { mutableStateOf(false) }

    LaunchedEffect(state.actionState.message) {
        state.actionState.message?.let {
            snackbar.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        containerColor = Cream,
        snackbarHost = { SnackbarHost(snackbar) },
    ) { inner ->
        Column(modifier = Modifier.padding(inner)) {
            Row(
                modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onBack) {
                    Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
                }
                Text(
                    "AI Settings",
                    style = MaterialTheme.typography.titleLarge.copy(
                        fontWeight = FontWeight.Bold, color = Ink,
                    ),
                )
            }

            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // Model info card
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = GrapeSoft),
                    elevation = CardDefaults.cardElevation(0.dp),
                ) {
                    Column(Modifier.padding(20.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .background(Grape.copy(alpha = 0.18f), RoundedCornerShape(12.dp)),
                                contentAlignment = Alignment.Center,
                            ) {
                                Icon(Icons.Rounded.AutoAwesome, contentDescription = null, tint = Grape, modifier = Modifier.size(22.dp))
                            }
                            Spacer(Modifier.width(12.dp))
                            Column {
                                Text("Active model", style = MaterialTheme.typography.labelMedium, color = Grape.copy(alpha = 0.7f))
                                Text(
                                    state.modelInfo?.displayName ?: "Loading…",
                                    style = MaterialTheme.typography.titleMedium.copy(
                                        fontWeight = FontWeight.SemiBold, color = Grape,
                                    ),
                                )
                            }
                        }
                        Spacer(Modifier.height(16.dp))

                        InfoRow("Version", state.modelInfo?.version ?: "—")
                        InfoRow("Size", state.modelInfo?.modelSizeMb ?: "—")
                        InfoRow("Source", state.activeId)
                        InfoRow("Cold-start ready", if (state.modelInfo?.supportsColdStart == true) "Yes" else "No")
                    }
                }

                // Habit maturity card
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(containerColor = Surface),
                    elevation = CardDefaults.cardElevation(2.dp),
                ) {
                    Column(Modifier.padding(20.dp)) {
                        Text(
                            "Learning progress",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.SemiBold, color = Ink,
                            ),
                        )
                        Spacer(Modifier.height(4.dp))
                        Text(state.maturityLabel, style = MaterialTheme.typography.bodySmall, color = Muted)

                        Spacer(Modifier.height(16.dp))

                        Row(
                            horizontalArrangement = Arrangement.SpaceEvenly,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            StatPill(label = "Habits", value = state.totalHabits.toString(), color = Sky, bg = SkySoft)
                            StatPill(label = "Mature", value = state.matureHabits.toString(), color = Mint, bg = MintSoft)
                        }
                    }
                }

                // Action: check for update
                ActionCard(
                    icon = Icons.Rounded.CloudDownload,
                    iconBg = SkySoft, iconTint = Sky,
                    title = "Check for model update",
                    subtitle = "We check daily over Wi-Fi. Tap to check now.",
                    actionLabel = if (state.actionState.isCheckingUpdate) "Checking…" else "Check now",
                    enabled = !state.actionState.isCheckingUpdate,
                    onAction = viewModel::checkForUpdate,
                )

                // Action: reset habits (destructive)
                ActionCard(
                    icon = Icons.Rounded.RestartAlt,
                    iconBg = Error.copy(alpha = 0.12f), iconTint = Error,
                    title = "Reset learned habits",
                    subtitle = "Clears your personalized model state. The base model is unaffected.",
                    actionLabel = "Reset",
                    enabled = !state.actionState.isResettingHabits,
                    onAction = { showResetDialog = true },
                    isDestructive = true,
                )
            }
        }
    }

    if (showResetDialog) {
        AlertDialog(
            onDismissRequest = { showResetDialog = false },
            title = { Text("Reset all learned habits?") },
            text = {
                Text(
                    "Your ${state.totalHabits} learned merchant→category mappings will be deleted. " +
                        "The base ML model and your transactions are unaffected.",
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    showResetDialog = false
                    viewModel.resetHabits()
                }) {
                    Text("Reset", color = Error, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetDialog = false }) { Text("Cancel") }
            },
        )
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium, color = Grape.copy(alpha = 0.7f))
        Text(value, style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold, color = Grape))
    }
}

@Composable
private fun StatPill(label: String, value: String, color: androidx.compose.ui.graphics.Color, bg: androidx.compose.ui.graphics.Color) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier
            .background(bg, RoundedCornerShape(16.dp))
            .padding(horizontal = 24.dp, vertical = 12.dp),
    ) {
        Text(value, style = MaterialTheme.typography.headlineSmall.copy(fontWeight = FontWeight.Bold, color = color))
        Text(label, style = MaterialTheme.typography.labelSmall, color = color)
    }
}

@Composable
private fun ActionCard(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    iconBg: androidx.compose.ui.graphics.Color,
    iconTint: androidx.compose.ui.graphics.Color,
    title: String,
    subtitle: String,
    actionLabel: String,
    enabled: Boolean,
    onAction: () -> Unit,
    isDestructive: Boolean = false,
) {
    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(2.dp),
    ) {
        Row(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(iconBg, RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(icon, contentDescription = null, tint = iconTint, modifier = Modifier.size(22.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    title,
                    style = MaterialTheme.typography.titleSmall.copy(
                        fontWeight = FontWeight.SemiBold,
                        color = if (isDestructive) Error else Ink,
                    ),
                )
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Muted)
            }
            Spacer(Modifier.width(8.dp))
            Button(
                onClick = onAction,
                enabled = enabled,
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = iconTint),
            ) { Text(actionLabel, color = Surface) }
        }
    }
}
