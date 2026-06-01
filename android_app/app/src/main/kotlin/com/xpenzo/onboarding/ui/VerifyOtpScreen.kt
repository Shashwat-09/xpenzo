package com.xpenzo.onboarding.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Pin
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.onboarding.OnboardingViewModel
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

@Composable
fun VerifyOtpScreen(
    viewModel: OnboardingViewModel,
    onAuthenticated: () -> Unit,
    onBack: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.isAuthenticated) {
        if (state.isAuthenticated) onAuthenticated()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream)
            .padding(24.dp),
    ) {
        IconButton(onClick = onBack) {
            Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
        }

        Spacer(Modifier.height(24.dp))

        Box(
            modifier = Modifier
                .size(80.dp)
                .background(CoralSoft, RoundedCornerShape(24.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(Icons.Rounded.Pin, contentDescription = null, tint = Coral, modifier = Modifier.size(40.dp))
        }

        Spacer(Modifier.height(24.dp))

        Text(
            "Enter verification code",
            style = MaterialTheme.typography.headlineMedium.copy(
                fontWeight = FontWeight.Bold,
                color = Ink,
            ),
        )

        Spacer(Modifier.height(8.dp))

        Text(
            "We sent a 6-digit code to +91 ${formatPhone(state.phoneNumber)}",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )

        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = state.otpInput,
            onValueChange = viewModel::updateOtp,
            label = { Text("6-digit code") },
            placeholder = { Text("•  •  •  •  •  •") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            textStyle = MaterialTheme.typography.titleLarge.copy(
                fontWeight = FontWeight.Bold,
                letterSpacing = 8.sp,
                textAlign = TextAlign.Center,
            ),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Coral,
                cursorColor = Coral,
                focusedContainerColor = Surface,
                unfocusedContainerColor = Surface,
            ),
            isError = state.error != null,
        )

        state.error?.let { errorMsg ->
            Spacer(Modifier.height(8.dp))
            Text(errorMsg, color = Error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(16.dp))

        TextButton(onClick = onBack) {
            Text("Didn't get a code? Try again", color = Coral)
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = viewModel::verifyOtp,
            enabled = state.canVerifyOtp,
            modifier = Modifier.fillMaxWidth().height(56.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Coral,
                disabledContainerColor = Muted.copy(alpha = 0.3f),
            ),
            shape = RoundedCornerShape(20.dp),
        ) {
            if (state.isVerifyingOtp) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp), color = Surface, strokeWidth = 2.dp,
                )
            } else {
                Text(
                    "Verify and continue",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold, color = Surface,
                    ),
                )
            }
        }
    }
}

private fun formatPhone(digits: String): String =
    if (digits.length == 10) "${digits.take(5)} ${digits.takeLast(5)}" else digits
