package com.xpenzo.ui.settings

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ErrorOutline
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Sms
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.ErrorSoft
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface

/**
 * Reviews the runtime permission state. Each row shows whether the permission
 * is granted and a button to open the system settings page for it.
 *
 * Re-checks state when the activity resumes (after returning from Settings).
 */
@Composable
fun AppPermissionsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    fun isGranted(perm: String): Boolean =
        ContextCompat.checkSelfPermission(context, perm) == PackageManager.PERMISSION_GRANTED

    fun isNotificationListenerGranted(): Boolean {
        val enabled = Settings.Secure.getString(
            context.contentResolver, "enabled_notification_listeners",
        ).orEmpty()
        return enabled.contains(context.packageName)
    }

    var smsGranted by remember { mutableStateOf(isGranted(Manifest.permission.RECEIVE_SMS)) }
    var notifGranted by remember { mutableStateOf(isNotificationListenerGranted()) }

    // Re-check permission state when the screen resumes (after system settings)
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                smsGranted = isGranted(Manifest.permission.RECEIVE_SMS)
                notifGranted = isNotificationListenerGranted()
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

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
                "App Permissions",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold, color = Ink,
                ),
            )
        }

        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            PermissionRow(
                icon = Icons.Rounded.Sms,
                iconBg = MintSoft, iconTint = Mint,
                title = "SMS",
                description = "Required to detect bank/UPI transactions. " +
                    "OTPs and promotional SMS are filtered locally and discarded.",
                granted = smsGranted,
                onOpenSettings = { openAppDetails(context) },
            )

            PermissionRow(
                icon = Icons.Rounded.Notifications,
                iconBg = GrapeSoft, iconTint = Grape,
                title = "Notification Access",
                description = "Optional. Catches PhonePe/GPay transactions delivered as " +
                    "notifications instead of SMS.",
                granted = notifGranted,
                onOpenSettings = {
                    // Guarded: some OEM ROMs hide this settings screen
                    runCatching {
                        context.startActivity(
                            Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                        )
                    }
                },
            )
        }
    }
}

@Composable
private fun PermissionRow(
    icon: ImageVector,
    iconBg: Color,
    iconTint: Color,
    title: String,
    description: String,
    granted: Boolean,
    onOpenSettings: () -> Unit,
) {
    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        elevation = CardDefaults.cardElevation(2.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
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
                    Text(title, style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.SemiBold, color = Ink,
                    ))
                    StatusChip(granted)
                }
            }
            Spacer(Modifier.height(8.dp))
            Text(description, style = MaterialTheme.typography.bodySmall, color = Muted)
            Spacer(Modifier.height(12.dp))
            TextButton(onClick = onOpenSettings) {
                Text(
                    if (granted) "Manage in Settings" else "Grant in Settings",
                    color = iconTint,
                )
            }
        }
    }
}

@Composable
private fun StatusChip(granted: Boolean) {
    val bg = if (granted) MintSoft else ErrorSoft
    val tint = if (granted) Mint else Error
    val icon = if (granted) Icons.Rounded.CheckCircle else Icons.Rounded.ErrorOutline
    val label = if (granted) "Granted" else "Not granted"
    Row(
        modifier = Modifier
            .background(bg, RoundedCornerShape(8.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(14.dp))
        Spacer(Modifier.width(4.dp))
        Text(label, style = MaterialTheme.typography.labelSmall, color = tint)
    }
}

private fun openAppDetails(context: android.content.Context) {
    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = Uri.fromParts("package", context.packageName, null)
        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
    runCatching { context.startActivity(intent) }
}
