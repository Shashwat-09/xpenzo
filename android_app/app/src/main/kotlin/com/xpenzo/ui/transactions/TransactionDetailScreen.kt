package com.xpenzo.ui.transactions

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.Edit
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.xpenzo.data.db.entity.TransactionEntity
import com.xpenzo.ui.common.categoryColor
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface
import java.text.NumberFormat
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TransactionDetailScreen(
    transactionId: String,
    onBack: () -> Unit,
    viewModel: TransactionViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val tx = uiState.transactions.firstOrNull { it.id == transactionId }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Transaction", style = MaterialTheme.typography.headlineSmall) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Rounded.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Cream),
            )
        },
        containerColor = Cream,
    ) { padding ->
        if (tx == null) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = Coral)
            }
        } else {
            TransactionDetailContent(
                tx = tx,
                onCorrection = { l1, l2, l3 -> viewModel.applyCorrection(tx, l1, l2, l3) },
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun TransactionDetailContent(
    tx: TransactionEntity,
    onCorrection: (String, String, String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var showCategoryPicker by remember { mutableStateOf(false) }
    val color = categoryColor(tx.l1Category)

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        // Amount hero
        Card(
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.12f)),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth().padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text(
                    text = "${if (tx.isCredit) "+" else "-"}₹${formatRupees(tx.amount)}",
                    style = MaterialTheme.typography.displayMedium.copy(fontWeight = FontWeight.Bold),
                    color = if (tx.isCredit) Mint else Ink,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = tx.merchantRaw.ifBlank { "Transaction" },
                    style = MaterialTheme.typography.titleLarge,
                    color = Ink,
                )
                Text(
                    text = formatDate(tx.timestamp),
                    style = MaterialTheme.typography.bodyMedium,
                    color = Muted,
                )
            }
        }

        // Category badge + confidence
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            InfoChip(label = "L1", value = tx.l1Category, color = color, modifier = Modifier.weight(1f))
            InfoChip(label = "L2", value = tx.l2Category, color = Muted, modifier = Modifier.weight(1f))
        }

        // Details card
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = Surface),
            elevation = CardDefaults.cardElevation(2.dp),
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                DetailRow("Merchant", tx.merchantRaw.ifBlank { "Unknown" })
                DetailRow("VPA / UPI ID", tx.upiId.ifBlank { "—" })
                DetailRow("Classified by", tx.source.replace("_", " "))
                DetailRow("Confidence", "${(tx.confidence * 100).toInt()}%")
                DetailRow("Synced", if (tx.synced) "Yes" else "Pending")
                if (tx.isCorrected) {
                    DetailRow("Note", "Category was manually corrected")
                }
            }
        }

        // Correct category button
        if (!tx.isCredit) {
            Button(
                onClick = { showCategoryPicker = true },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Coral),
            ) {
                Icon(Icons.Rounded.Edit, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.size(8.dp))
                Text("Correct Category", style = MaterialTheme.typography.titleMedium)
            }
        }
    }
}

@Composable
private fun InfoChip(label: String, value: String, color: Color, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(color.copy(alpha = 0.1f))
            .padding(12.dp),
    ) {
        Text(label, style = MaterialTheme.typography.labelMedium, color = Muted)
        Text(value, style = MaterialTheme.typography.titleMedium, color = Ink, maxLines = 1)
    }
}

@Composable
private fun DetailRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium, color = Muted)
        Text(value, style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.SemiBold), color = Ink)
    }
    Divider(color = Muted.copy(alpha = 0.15f))
}

private fun formatRupees(paise: Long): String =
    NumberFormat.getNumberInstance(Locale("en", "IN"))
        .apply { maximumFractionDigits = 0 }
        .format(paise / 100.0)

private fun formatDate(epochMs: Long): String {
    val ldt = Instant.ofEpochMilli(epochMs).atZone(ZoneId.systemDefault()).toLocalDateTime()
    return DateTimeFormatter.ofPattern("dd MMM yyyy, hh:mm a").format(ldt)
}
