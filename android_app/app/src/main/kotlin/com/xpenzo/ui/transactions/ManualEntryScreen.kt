package com.xpenzo.ui.transactions

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

@Composable
fun ManualEntryScreen(
    onBack: () -> Unit,
    onSaved: () -> Unit,
    viewModel: ManualEntryViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.saved) { if (state.saved) onSaved() }

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
                "Add transaction",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Direction toggle
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Surface, RoundedCornerShape(20.dp))
                    .padding(4.dp),
            ) {
                DirectionPill(
                    text = "Expense",
                    selected = !state.isCredit,
                    onClick = { if (state.isCredit) viewModel.toggleCredit() },
                    activeColor = Coral, activeBg = CoralSoft,
                )
                DirectionPill(
                    text = "Income",
                    selected = state.isCredit,
                    onClick = { if (!state.isCredit) viewModel.toggleCredit() },
                    activeColor = Mint, activeBg = MintSoft,
                )
            }

            // Amount
            OutlinedTextField(
                value = state.amountRupees,
                onValueChange = viewModel::updateAmount,
                label = { Text("Amount (₹)") },
                placeholder = { Text("0.00") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                textStyle = MaterialTheme.typography.headlineMedium.copy(
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                ),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = if (state.isCredit) Mint else Coral,
                    cursorColor = if (state.isCredit) Mint else Coral,
                    focusedContainerColor = Surface,
                    unfocusedContainerColor = Surface,
                ),
            )

            // Merchant
            OutlinedTextField(
                value = state.merchant,
                onValueChange = viewModel::updateMerchant,
                label = { Text("Merchant or description") },
                placeholder = { Text("e.g. Chai, Auto rickshaw, Salary") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Coral,
                    cursorColor = Coral,
                    focusedContainerColor = Surface,
                    unfocusedContainerColor = Surface,
                ),
            )

            // Category picker
            Text(
                "Category",
                style = MaterialTheme.typography.labelLarge.copy(
                    fontWeight = FontWeight.SemiBold, color = Ink,
                ),
            )

            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(horizontal = 4.dp),
            ) {
                items(ManualEntryViewModel.L1_CATEGORIES) { (name, emoji) ->
                    CategoryChip(
                        emoji = emoji,
                        name = name,
                        selected = state.l1Category == name,
                        onClick = { viewModel.selectCategory(name) },
                    )
                }
            }

            state.error?.let { msg ->
                Text(msg, color = Error, style = MaterialTheme.typography.bodySmall)
            }

            Spacer(Modifier.weight(1f))

            Button(
                onClick = { viewModel.save(onSaved) },
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (state.isCredit) Mint else Coral,
                ),
                shape = RoundedCornerShape(20.dp),
            ) {
                Text(
                    "Save transaction",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold, color = Surface,
                    ),
                )
            }
        }
    }
}

@Composable
private fun RowScope.DirectionPill(
    text: String,
    selected: Boolean,
    onClick: () -> Unit,
    activeColor: Color,
    activeBg: Color,
) {
    Button(
        onClick = onClick,
        modifier = Modifier.weight(1f),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (selected) activeBg else Color.Transparent,
            contentColor = if (selected) activeColor else Muted,
        ),
        shape = RoundedCornerShape(16.dp),
        elevation = ButtonDefaults.buttonElevation(0.dp, 0.dp, 0.dp, 0.dp, 0.dp),
    ) {
        Text(text, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun CategoryChip(emoji: String, name: String, selected: Boolean, onClick: () -> Unit) {
    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (selected) Coral else Surface)
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Text(emoji)
        Text(
            name,
            style = MaterialTheme.typography.labelMedium.copy(
                color = if (selected) Surface else Ink,
                fontWeight = FontWeight.SemiBold,
            ),
        )
    }
}
