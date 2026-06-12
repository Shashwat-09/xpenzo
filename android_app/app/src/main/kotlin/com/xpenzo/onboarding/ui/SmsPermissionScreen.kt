package com.xpenzo.onboarding.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Sms
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.xpenzo.onboarding.OnboardingViewModel
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

@Composable
fun SmsPermissionScreen(
    viewModel: OnboardingViewModel,
    onComplete: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current

    var smsGranted by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECEIVE_SMS) ==
                PackageManager.PERMISSION_GRANTED,
        )
    }
    var notifAccessGranted by remember {
        mutableStateOf(isNotificationAccessGranted(context))
    }

    val smsPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions(),
    ) { results ->
        smsGranted = results[Manifest.permission.RECEIVE_SMS] == true
        if (smsGranted) viewModel.smsPermissionGranted()
    }

    LaunchedEffect(state.onboardingCompleted) {
        if (state.onboardingCompleted) onComplete()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream)
            .padding(24.dp),
    ) {
        Spacer(Modifier.height(48.dp))

        Text(
            "One last step",
            style = MaterialTheme.typography.headlineMedium.copy(
                fontWeight = FontWeight.Bold,
                color = Ink,
            ),
        )

        Spacer(Modifier.height(8.dp))

        Text(
            "Xpenzo reads bank/UPI transaction SMS only on your device " +
                "to automatically categorize spending. Nothing leaves your phone.",
            style = MaterialTheme.typography.bodyMedium,
            color = Muted,
        )

        Spacer(Modifier.height(32.dp))

        PermissionCard(
            icon = Icons.Rounded.Sms,
            iconBg = MintSoft,
            iconTint = Mint,
            title = "SMS access",
            description = "Reads only bank/UPI transactions. " +
                "OTPs and promotional SMS are filtered out.",
            granted = smsGranted,
            onRequest = {
                smsPermissionLauncher.launch(arrayOf(
                    Manifest.permission.RECEIVE_SMS,
                    Manifest.permission.READ_SMS,
                ))
            },
        )

        Spacer(Modifier.height(16.dp))

        PermissionCard(
            icon = Icons.Rounded.Notifications,
            iconBg = GrapeSoft,
            iconTint = Grape,
            title = "Notification access (optional)",
            description = "Catches PhonePe/GPay transactions that come as notifications " +
                "instead of SMS.",
            granted = notifAccessGranted,
            onRequest = {
                // Guarded: some OEM ROMs hide this settings screen
                runCatching {
                    context.startActivity(
                        Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                    )
                }
                // Re-check on resume
                notifAccessGranted = isNotificationAccessGranted(context)
            },
        )

        Spacer(Modifier.weight(1f))

        Button(
            onClick = viewModel::completeOnboarding,
            enabled = smsGranted,  // SMS is required; notification access is optional
            modifier = Modifier.fillMaxWidth().height(56.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Coral,
                disabledContainerColor = Muted.copy(alpha = 0.3f),
            ),
            shape = RoundedCornerShape(20.dp),
        ) {
            Text(
                if (smsGranted) "Finish setup" else "Grant SMS access to continue",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = Surface,
                ),
            )
        }

        Spacer(Modifier.height(8.dp))

        Text(
            "You can change these permissions anytime in Settings.",
            style = MaterialTheme.typography.bodySmall,
            color = Muted,
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

@Composable
private fun PermissionCard(
    icon: ImageVector,
    iconBg: Color,
    iconTint: Color,
    title: String,
    description: String,
    granted: Boolean,
    onRequest: () -> Unit,
) {
    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(2.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(iconBg, RoundedCornerShape(14.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(icon, contentDescription = null, tint = iconTint, modifier = Modifier.size(24.dp))
            }

            Spacer(Modifier.width(14.dp))

            Column(Modifier.weight(1f)) {
                Text(
                    title,
                    style = MaterialTheme.typography.titleSmall.copy(
                        fontWeight = FontWeight.SemiBold, color = Ink,
                    ),
                )
                Text(
                    description,
                    style = MaterialTheme.typography.bodySmall,
                    color = Muted,
                )
            }

            Spacer(Modifier.width(12.dp))

            if (granted) {
                Icon(
                    Icons.Rounded.CheckCircle,
                    contentDescription = "Granted",
                    tint = Mint,
                    modifier = Modifier.size(28.dp),
                )
            } else {
                Button(
                    onClick = onRequest,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = iconTint),
                ) {
                    Text("Allow", color = Surface)
                }
            }
        }
    }
}

private fun isNotificationAccessGranted(context: android.content.Context): Boolean {
    val enabled = Settings.Secure.getString(
        context.contentResolver,
        "enabled_notification_listeners",
    ).orEmpty()
    return enabled.contains(context.packageName)
}
