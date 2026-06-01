package com.xpenzo.onboarding.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AccountBalanceWallet
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.onboarding.OnboardingViewModel
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

@Composable
fun UpiIdSetupScreen(
    viewModel: OnboardingViewModel,
    onContinue: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.upiSaved) {
        if (state.upiSaved) onContinue()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream)
            .padding(24.dp),
    ) {
        Spacer(Modifier.height(48.dp))

        Box(
            modifier = Modifier
                .size(80.dp)
                .background(MintSoft, RoundedCornerShape(24.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                Icons.Rounded.AccountBalanceWallet, contentDescription = null,
                tint = Mint, modifier = Modifier.size(40.dp),
            )
        }

        Spacer(Modifier.height(24.dp))

        Text(
            "Your primary UPI ID",
            style = MaterialTheme.typography.headlineMedium.copy(
                fontWeight = FontWeight.Bold,
                color = Ink,
            ),
        )

        Spacer(Modifier.height(8.dp))

        Text(
            "Helps us match incoming transactions faster. " +
                "Optional — you can skip and add later.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )

        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = state.upiId,
            onValueChange = viewModel::updateUpiId,
            label = { Text("UPI ID") },
            placeholder = { Text("yourname@ybl") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Mint,
                cursorColor = Mint,
                focusedContainerColor = Surface,
                unfocusedContainerColor = Surface,
            ),
            isError = state.error != null,
        )

        state.error?.let { errorMsg ->
            Spacer(Modifier.height(8.dp))
            Text(errorMsg, color = Error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = { viewModel.saveUpiId(skipped = false) },
            enabled = state.upiId.isNotBlank(),
            modifier = Modifier.fillMaxWidth().height(56.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Coral,
                disabledContainerColor = Muted.copy(alpha = 0.3f),
            ),
            shape = RoundedCornerShape(20.dp),
        ) {
            Text(
                "Continue",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold, color = Surface,
                ),
            )
        }

        Spacer(Modifier.height(8.dp))

        TextButton(
            onClick = { viewModel.saveUpiId(skipped = true) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Skip for now", color = Muted)
        }
    }
}
