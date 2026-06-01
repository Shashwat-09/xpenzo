package com.xpenzo.onboarding.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Person
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
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

@Composable
fun ProfileSetupScreen(
    viewModel: OnboardingViewModel,
    onContinue: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.nameSaved) {
        if (state.nameSaved) onContinue()
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
                .background(CoralSoft, RoundedCornerShape(24.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(Icons.Rounded.Person, contentDescription = null, tint = Coral, modifier = Modifier.size(40.dp))
        }

        Spacer(Modifier.height(24.dp))

        Text(
            "What should we call you?",
            style = MaterialTheme.typography.headlineMedium.copy(
                fontWeight = FontWeight.Bold,
                color = Ink,
            ),
        )

        Spacer(Modifier.height(8.dp))

        Text(
            "Used to personalize insights and reports. Stays on your device.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )

        Spacer(Modifier.height(32.dp))

        OutlinedTextField(
            value = state.userName,
            onValueChange = viewModel::updateName,
            label = { Text("Your name") },
            placeholder = { Text("e.g. Rahul") },
            singleLine = true,
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
            onClick = viewModel::saveName,
            enabled = state.userName.isNotBlank(),
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
    }
}
