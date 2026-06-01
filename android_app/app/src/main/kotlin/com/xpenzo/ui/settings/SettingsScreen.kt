package com.xpenzo.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.DataUsage
import androidx.compose.material.icons.rounded.DeleteForever
import androidx.compose.material.icons.rounded.Download
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.Palette
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.xpenzo.ui.nav.Screen
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.ErrorSoft
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.SkySoft
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface

private data class SettingsItem(
    val icon: ImageVector,
    val iconBg: Color,
    val iconTint: Color,
    val title: String,
    val subtitle: String,
    val route: String? = null,
    val isDestructive: Boolean = false,
)

private val SETTINGS_SECTIONS = listOf(
    "AI & Model" to listOf(
        SettingsItem(Icons.Rounded.AutoAwesome, GrapeSoft, Grape, "AI Settings", "Manage the on-device ML model", Screen.AiModelSettings.route),
        SettingsItem(Icons.Rounded.DataUsage, GrapeSoft, Grape, "Help improve AI", "Contribute anonymized corrections", Screen.HelpImproveAi.route),
    ),
    "Sync & Backup" to listOf(
        SettingsItem(Icons.Rounded.Sync, MintSoft, Mint, "Backup & Sync", "Cloud sync via Firebase", Screen.BackupSync.route),
        SettingsItem(Icons.Rounded.Download, SkySoft, Sky, "Export Data", "Download your transactions as CSV", Screen.ExportData.route),
    ),
    "Preferences" to listOf(
        SettingsItem(Icons.Rounded.Notifications, SunSoft, Sun, "Notifications", "Manage alerts & reminders", Screen.NotifSettings.route),
        SettingsItem(Icons.Rounded.Palette, CoralSoft, Coral, "Appearance", "Theme and language settings", Screen.Appearance.route),
        SettingsItem(Icons.Rounded.Lock, SkySoft, Sky, "App Permissions", "Review granted permissions", Screen.AppPermissions.route),
    ),
    "Account" to listOf(
        SettingsItem(Icons.Rounded.Security, MintSoft, Mint, "Privacy & Security", "Data handling and security", Screen.PrivacySecurity.route),
        SettingsItem(Icons.Rounded.DeleteForever, ErrorSoft, Error, "Delete Account", "Permanently remove all your data", Screen.DeleteAccount.route, isDestructive = true),
    ),
)

@Composable
fun SettingsScreen(navController: NavController) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().background(Cream),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp),
    ) {
        item {
            Text(
                "Settings",
                style = MaterialTheme.typography.headlineLarge,
                color = Ink,
                modifier = Modifier.padding(vertical = 8.dp),
            )
        }

        SETTINGS_SECTIONS.forEach { (sectionTitle, items) ->
            item {
                Column(verticalArrangement = Arrangement.spacedBy(0.dp)) {
                    Text(
                        sectionTitle.uppercase(),
                        style = MaterialTheme.typography.labelMedium,
                        color = Muted,
                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 8.dp),
                    )
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = Surface),
                        elevation = CardDefaults.cardElevation(2.dp),
                    ) {
                        Column {
                            items.forEachIndexed { idx, item ->
                                SettingsRow(
                                    item = item,
                                    onClick = { item.route?.let { navController.navigate(it) } },
                                )
                                if (idx < items.lastIndex) {
                                    Divider(
                                        color = Muted.copy(alpha = 0.12f),
                                        modifier = Modifier.padding(horizontal = 16.dp),
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }

        item { AppVersionFooter() }
    }
}

@Composable
private fun SettingsRow(item: SettingsItem, onClick: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Icon chip
        androidx.compose.foundation.layout.Box(
            modifier = Modifier
                .size(40.dp)
                .background(item.iconBg, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = item.icon,
                contentDescription = null,
                tint = item.iconTint,
                modifier = Modifier.size(20.dp),
            )
        }

        Spacer(Modifier.width(14.dp))

        Column(Modifier.weight(1f)) {
            Text(
                item.title,
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = if (item.isDestructive) Error else Ink,
                ),
            )
            Text(
                item.subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = Muted,
            )
        }

        Icon(
            Icons.Rounded.ChevronRight,
            contentDescription = null,
            tint = Muted,
            modifier = Modifier.size(20.dp),
        )
    }
}

@Composable
private fun AppVersionFooter() {
    Column(
        modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Xpenzo", style = MaterialTheme.typography.titleMedium, color = Muted)
        Text("v0.1 · Built with ❤️ in India", style = MaterialTheme.typography.bodySmall, color = Muted)
    }
}
