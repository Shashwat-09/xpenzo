package com.xpenzo.onboarding.ui

import android.app.Activity
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Smartphone
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
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
fun PhoneLoginScreen(
    viewModel: OnboardingViewModel,
    onOtpSent: () -> Unit,
    onBack: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val activity = LocalContext.current as? Activity

    LaunchedEffect(state.otpSent) {
        if (state.otpSent) onOtpSent()
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
            Icon(
                Icons.Rounded.Smartphone, contentDescription = null,
                tint = Coral, modifier = Modifier.size(40.dp),
            )
        }

        Spacer(Modifier.height(24.dp))

        Text(
            "Sign in with your phone",
            style = MaterialTheme.typography.headlineMedium.copy(
                fontWeight = FontWeight.Bold,
                color = Ink,
            ),
        )

        Spacer(Modifier.height(8.dp))

        Text(
            "We'll send you a one-time code to verify your number. " +
                "Your phone number is never shared.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )

        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = state.phoneNumber,
            onValueChange = viewModel::updatePhoneNumber,
            label = { Text("Phone number") },
            leadingIcon = {
                Text(
                    "+91",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold,
                        color = Ink,
                    ),
                    modifier = Modifier.padding(start = 12.dp),
                )
            },
            placeholder = { Text("98765 43210") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
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

        Spacer(Modifier.weight(1f))

        Button(
            onClick = { activity?.let { viewModel.sendOtp(it) } },
            enabled = state.canSendOtp,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Coral,
                disabledContainerColor = Muted.copy(alpha = 0.3f),
            ),
            shape = RoundedCornerShape(20.dp),
        ) {
            if (state.isSendingOtp) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = Surface,
                    strokeWidth = 2.dp,
                )
            } else {
                Text(
                    "Send code",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold,
                        color = Surface,
                    ),
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        Text(
            "Standard SMS rates may apply",
            style = MaterialTheme.typography.bodySmall,
            color = Muted,
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
