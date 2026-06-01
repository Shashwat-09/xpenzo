package com.xpenzo.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.CalendarMonth
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Savings
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface

@Composable
fun NotificationSettingsScreen(onBack: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().background(Cream),
    ) {
        SettingsTopBar("Notifications", onBack)

        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Surface),
                elevation = CardDefaults.cardElevation(2.dp),
            ) {
                Column {
                    NotifToggleRow(
                        icon = Icons.Rounded.Savings, tint = Mint, bg = MintSoft,
                        title = "Budget alerts",
                        subtitle = "When you approach or exceed a budget",
                        prefKey = SettingsPreferences.KEY_BUDGET_ALERTS,
                    )
                    Divider(color = Muted.copy(alpha = 0.12f), modifier = Modifier.padding(horizontal = 16.dp))
                    NotifToggleRow(
                        icon = Icons.Rounded.CalendarMonth, tint = Sun, bg = SunSoft,
                        title = "Weekly digest",
                        subtitle = "A Sunday summary of your week's spend",
                        prefKey = SettingsPreferences.KEY_WEEKLY_DIGEST,
                    )
                    Divider(color = Muted.copy(alpha = 0.12f), modifier = Modifier.padding(horizontal = 16.dp))
                    NotifToggleRow(
                        icon = Icons.Rounded.Notifications, tint = Mint, bg = MintSoft,
                        title = "Transaction notifications",
                        subtitle = "When a new SMS transaction is categorized",
                        prefKey = SettingsPreferences.KEY_TXN_NOTIFS,
                    )
                }
            }

            Text(
                "Notifications require the system notification permission. You can review " +
                    "it under App Permissions.",
                style = MaterialTheme.typography.bodySmall,
                color = Muted,
                modifier = Modifier.padding(horizontal = 4.dp),
            )
        }
    }
}

@Composable
private fun NotifToggleRow(
    icon: ImageVector,
    tint: Color,
    bg: Color,
    title: String,
    subtitle: String,
    prefKey: String,
) {
    val context = LocalContext.current
    var checked by remember {
        mutableStateOf(SettingsPreferences.getBool(context, prefKey, true))
    }
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier.size(40.dp).background(bg, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(20.dp))
        }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(
                title,
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold, color = Ink),
            )
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Muted)
        }
        Switch(
            checked = checked,
            onCheckedChange = {
                checked = it
                SettingsPreferences.setBool(context, prefKey, it)
            },
            colors = SwitchDefaults.colors(checkedTrackColor = Mint),
        )
    }
}

@Composable
internal fun SettingsTopBar(title: String, onBack: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(start = 8.dp, top = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        IconButton(onClick = onBack) {
            Icon(Icons.Rounded.ArrowBack, contentDescription = "Back", tint = Ink)
        }
        Text(
            title,
            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold, color = Ink),
        )
    }
}
