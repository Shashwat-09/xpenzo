package com.xpenzo.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Download
import androidx.compose.material.icons.rounded.Share
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.SkySoft
import com.xpenzo.ui.theme.Surface

@Composable
fun ExportDataScreen(
    onBack: () -> Unit,
    viewModel: ExportDataViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
            }
            Text(
                "Export Data",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Hero card
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = SkySoft),
                elevation = CardDefaults.cardElevation(0.dp),
            ) {
                Column(Modifier.padding(20.dp)) {
                    Box(
                        modifier = Modifier
                            .size(48.dp)
                            .background(Sky.copy(alpha = 0.18f), RoundedCornerShape(14.dp)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Rounded.Download, contentDescription = null, tint = Sky, modifier = Modifier.size(24.dp))
                    }
                    Spacer(Modifier.height(12.dp))
                    Text(
                        "Download all your data",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.SemiBold, color = Sky,
                        ),
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "Generates a CSV file with every transaction Xpenzo has " +
                            "categorized for you. The file stays on your device until you share it.",
                        style = MaterialTheme.typography.bodySmall,
                        color = Sky.copy(alpha = 0.85f),
                    )
                }
            }

            // Action card
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Surface),
                elevation = CardDefaults.cardElevation(2.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    if (state.fileUri == null) {
                        Button(
                            onClick = viewModel::exportCsv,
                            enabled = !state.isExporting,
                            modifier = Modifier.fillMaxWidth().height(56.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Sky),
                            shape = RoundedCornerShape(16.dp),
                        ) {
                            if (state.isExporting) {
                                CircularProgressIndicator(
                                    color = Surface, modifier = Modifier.size(20.dp), strokeWidth = 2.dp,
                                )
                                Spacer(Modifier.width(12.dp))
                                Text("Generating CSV...", color = Surface)
                            } else {
                                Icon(Icons.Rounded.Download, contentDescription = null, tint = Surface)
                                Spacer(Modifier.width(8.dp))
                                Text("Generate CSV", fontWeight = FontWeight.SemiBold, color = Surface)
                            }
                        }
                    } else {
                        Icon(
                            Icons.Rounded.CheckCircle,
                            contentDescription = null,
                            tint = Mint,
                            modifier = Modifier.size(48.dp),
                        )
                        Spacer(Modifier.height(12.dp))
                        Text(
                            "Ready to share",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.SemiBold, color = Ink,
                            ),
                        )
                        Text(
                            "${state.transactionCount} transactions exported",
                            style = MaterialTheme.typography.bodySmall,
                            color = Muted,
                        )
                        Spacer(Modifier.height(16.dp))
                        Button(
                            onClick = {
                                val intent = viewModel.buildShareIntent(state.fileUri!!)
                                context.startActivity(android.content.Intent.createChooser(intent, "Share CSV"))
                            },
                            modifier = Modifier.fillMaxWidth().height(56.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Mint),
                            shape = RoundedCornerShape(16.dp),
                        ) {
                            Icon(Icons.Rounded.Share, contentDescription = null, tint = Surface)
                            Spacer(Modifier.width(8.dp))
                            Text("Share CSV", fontWeight = FontWeight.SemiBold, color = Surface)
                        }
                        Spacer(Modifier.height(8.dp))
                        TextButton(
                            onClick = viewModel::exportCsv,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text("Regenerate", color = Muted)
                        }
                    }

                    state.error?.let { msg ->
                        Spacer(Modifier.height(12.dp))
                        Text("Error: $msg", color = Error, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }

            // Privacy note
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MintSoft),
                elevation = CardDefaults.cardElevation(0.dp),
            ) {
                Text(
                    "Per the Digital Personal Data Protection Act 2023, you have the " +
                        "right to a complete copy of your data. Xpenzo never restricts this.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Mint,
                    modifier = Modifier.padding(16.dp),
                )
            }
        }
    }
}
