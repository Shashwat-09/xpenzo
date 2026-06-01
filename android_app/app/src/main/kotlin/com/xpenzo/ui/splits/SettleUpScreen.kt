package com.xpenzo.ui.splits

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Money
import androidx.compose.material.icons.rounded.Payments
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.splits.SplitsRepository
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettleUpViewModel @Inject constructor(
    savedState: SavedStateHandle,
    private val splitsRepository: SplitsRepository,
) : ViewModel() {

    val groupId: String? = savedState["groupId"]
    val fromUser: String = checkNotNull(savedState["from"])
    val toUser: String = checkNotNull(savedState["to"])
    val initialAmountPaise: Long = savedState.get<Long>("amount") ?: 0L

    fun recordSettlement(amountPaise: Long, method: String, notes: String, onDone: () -> Unit) =
        viewModelScope.launch {
            splitsRepository.recordSettlement(
                groupId = groupId,
                fromUser = fromUser,
                toUser = toUser,
                amountPaise = amountPaise,
                method = method,
                notes = notes,
            )
            onDone()
        }
}

@Composable
fun SettleUpScreen(
    onBack: () -> Unit,
    onSettled: () -> Unit,
    viewModel: SettleUpViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val amountRupees = viewModel.initialAmountPaise / 100.0
    var amountText by remember { mutableStateOf("%.2f".format(amountRupees)) }
    var upiId by remember { mutableStateOf("") }
    var notes by remember { mutableStateOf("") }
    var method by remember { mutableStateOf("UPI") }

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
                "Settle up",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Amount hero
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MintSoft),
                elevation = CardDefaults.cardElevation(0.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text("Amount", style = MaterialTheme.typography.labelLarge, color = Mint)
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = amountText,
                        onValueChange = { amountText = it.filter { c -> c.isDigit() || c == '.' } },
                        prefix = { Text("₹ ", color = Mint, fontWeight = FontWeight.Bold) },
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        textStyle = MaterialTheme.typography.headlineMedium.copy(
                            color = Mint, fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Center,
                        ),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = Mint, cursorColor = Mint,
                            unfocusedBorderColor = Mint.copy(alpha = 0.3f),
                        ),
                    )
                }
            }

            // Method tabs
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Surface, RoundedCornerShape(16.dp))
                    .padding(4.dp),
            ) {
                MethodPill(text = "UPI", icon = Icons.Rounded.Payments,
                    selected = method == "UPI", onClick = { method = "UPI" })
                MethodPill(text = "Cash", icon = Icons.Rounded.Money,
                    selected = method == "CASH", onClick = { method = "CASH" })
            }

            if (method == "UPI") {
                OutlinedTextField(
                    value = upiId,
                    onValueChange = { upiId = it.lowercase() },
                    label = { Text("Recipient UPI ID") },
                    placeholder = { Text("yourfriend@ybl") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Grape, cursorColor = Grape,
                        focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                    ),
                )
            }

            OutlinedTextField(
                value = notes,
                onValueChange = { notes = it.take(80) },
                label = { Text("Note (optional)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedContainerColor = Surface, unfocusedContainerColor = Surface,
                ),
            )

            Spacer(Modifier.weight(1f))

            Button(
                onClick = {
                    val amountPaise = ((amountText.toDoubleOrNull() ?: 0.0) * 100).toLong()
                    if (amountPaise <= 0) return@Button

                    // Record settlement in Room as PENDING
                    viewModel.recordSettlement(amountPaise, method, notes) {
                        // If UPI, also kick off the upi://pay intent
                        if (method == "UPI" && upiId.isNotBlank()) {
                            val uri = Uri.parse(
                                "upi://pay?pa=${Uri.encode(upiId)}" +
                                    "&pn=${Uri.encode("Xpenzo Friend")}" +
                                    "&am=${"%.2f".format(amountPaise / 100.0)}" +
                                    "&cu=INR" +
                                    "&tn=${Uri.encode(notes.ifBlank { "Xpenzo settle-up" })}"
                            )
                            val intent = Intent(Intent.ACTION_VIEW, uri)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            runCatching { context.startActivity(intent) }
                        }
                        onSettled()
                    }
                },
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Coral),
                shape = RoundedCornerShape(20.dp),
            ) {
                Text(
                    if (method == "UPI") "Pay via UPI" else "Mark as paid (cash)",
                    fontWeight = FontWeight.SemiBold, color = Surface,
                )
            }

            Text(
                "Your friend will be prompted to confirm receipt. " +
                    "The balance updates only after confirmation.",
                style = MaterialTheme.typography.bodySmall,
                color = Muted,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun RowScope.MethodPill(
    text: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    selected: Boolean,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        modifier = Modifier.weight(1f),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (selected) Grape.copy(alpha = 0.18f) else androidx.compose.ui.graphics.Color.Transparent,
            contentColor = if (selected) Grape else Muted,
        ),
        shape = RoundedCornerShape(12.dp),
        elevation = null,
    ) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
        Spacer(Modifier.width(6.dp))
        Text(text, fontWeight = FontWeight.SemiBold)
    }
}
