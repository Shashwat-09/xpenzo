package com.xpenzo.ui.settings

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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CloudDone
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.xpenzo.firebase.SyncWorker
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Surface
import java.text.DateFormat
import java.util.Date

@Composable
fun BackupSyncScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    var syncEnabled by remember {
        mutableStateOf(SettingsPreferences.getBool(context, SettingsPreferences.KEY_SYNC_ENABLED, true))
    }
    val lastSync = SettingsPreferences.of(context).getLong(SettingsPreferences.KEY_LAST_SYNC, 0L)

    Column(modifier = Modifier.fillMaxSize().background(Cream)) {
        SettingsTopBar("Backup & Sync", onBack)

        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Status hero
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MintSoft),
                elevation = CardDefaults.cardElevation(0.dp),
            ) {
                Column(Modifier.padding(20.dp)) {
                    Box(
                        modifier = Modifier.size(48.dp).background(Mint.copy(alpha = 0.18f), RoundedCornerShape(14.dp)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Rounded.CloudDone, contentDescription = null, tint = Mint, modifier = Modifier.size(24.dp))
                    }
                    Spacer(Modifier.height(12.dp))
                    Text(
                        "Cloud backup",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold, color = Mint),
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "Your transactions sync securely to Firebase so you never lose them. " +
                            "Raw SMS text is never uploaded.",
                        style = MaterialTheme.typography.bodySmall,
                        color = Mint.copy(alpha = 0.85f),
                    )
                }
            }

            // Settings card
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Surface),
                elevation = CardDefaults.cardElevation(2.dp),
            ) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text("Automatic sync", style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold, color = Ink))
                            Text("Sync in the background every few hours", style = MaterialTheme.typography.bodySmall, color = Muted)
                        }
                        Switch(
                            checked = syncEnabled,
                            onCheckedChange = {
                                syncEnabled = it
                                SettingsPreferences.setBool(context, SettingsPreferences.KEY_SYNC_ENABLED, it)
                            },
                            colors = SwitchDefaults.colors(checkedTrackColor = Mint),
                        )
                    }
                    Divider(color = Muted.copy(alpha = 0.12f), modifier = Modifier.padding(horizontal = 16.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text("Last synced", style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold, color = Ink))
                            Text(
                                if (lastSync > 0) DateFormat.getDateTimeInstance().format(Date(lastSync)) else "Not synced yet",
                                style = MaterialTheme.typography.bodySmall,
                                color = Muted,
                            )
                        }
                    }
                }
            }

            Button(
                onClick = {
                    WorkManager.getInstance(context).enqueue(
                        OneTimeWorkRequestBuilder<SyncWorker>().build(),
                    )
                    SettingsPreferences.of(context).edit()
                        .putLong(SettingsPreferences.KEY_LAST_SYNC, System.currentTimeMillis()).apply()
                },
                modifier = Modifier.fillMaxWidth().height(56.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Mint),
                shape = RoundedCornerShape(16.dp),
            ) {
                Icon(Icons.Rounded.Sync, contentDescription = null, tint = Surface)
                Spacer(Modifier.width(8.dp))
                Text("Sync now", fontWeight = FontWeight.SemiBold, color = Surface)
            }
        }
    }
}
