package com.xpenzo.ui.settings

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.Download
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Policy
import androidx.compose.material.icons.rounded.Shield
import androidx.compose.material.icons.rounded.DeleteForever
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Error
import com.xpenzo.ui.theme.ErrorSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.SkySoft
import com.xpenzo.ui.theme.Surface

private const val PRIVACY_POLICY_URL = "https://xpenzo.app/privacy"

@Composable
fun PrivacySecurityScreen(
    onBack: () -> Unit,
    onExportData: () -> Unit,
    onAppPermissions: () -> Unit,
    onDeleteAccount: () -> Unit,
) {
    val context = LocalContext.current

    Column(modifier = Modifier.fillMaxSize().background(Cream)) {
        SettingsTopBar("Privacy & Security", onBack)

        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Privacy promise hero
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MintSoft),
                elevation = CardDefaults.cardElevation(0.dp),
            ) {
                Row(Modifier.padding(20.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier.size(44.dp).background(Mint.copy(alpha = 0.18f), RoundedCornerShape(14.dp)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Rounded.Shield, contentDescription = null, tint = Mint, modifier = Modifier.size(22.dp))
                    }
                    Spacer(Modifier.width(14.dp))
                    Text(
                        "Your SMS and transactions are processed on your device. Only anonymized, " +
                            "normalized data is ever shared — never raw SMS or account numbers.",
                        style = MaterialTheme.typography.bodySmall,
                        color = Mint,
                    )
                }
            }

            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Surface),
                elevation = CardDefaults.cardElevation(2.dp),
            ) {
                Column {
                    LinkRow(
                        Icons.Rounded.Policy, Sky, SkySoft, "Privacy policy", "Read how we handle your data",
                        onClick = {
                            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(PRIVACY_POLICY_URL)))
                        },
                    )
                    RowDivider()
                    LinkRow(Icons.Rounded.Download, Sky, SkySoft, "Export my data", "Download a CSV copy (DPDP Act)", onExportData)
                    RowDivider()
                    LinkRow(Icons.Rounded.Lock, Mint, MintSoft, "App permissions", "Review SMS & notification access", onAppPermissions)
                }
            }

            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Surface),
                elevation = CardDefaults.cardElevation(2.dp),
            ) {
                LinkRow(Icons.Rounded.DeleteForever, Error, ErrorSoft, "Delete account", "Permanently erase all your data", onDeleteAccount, destructive = true)
            }
        }
    }
}

@Composable
private fun RowDivider() = Divider(color = Muted.copy(alpha = 0.12f), modifier = Modifier.padding(horizontal = 16.dp))

@Composable
private fun LinkRow(
    icon: ImageVector,
    tint: Color,
    bg: Color,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
    destructive: Boolean = false,
) {
    Row(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick).padding(horizontal = 16.dp, vertical = 14.dp),
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
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = if (destructive) Error else Ink,
                ),
            )
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Muted)
        }
        Icon(Icons.Rounded.ChevronRight, contentDescription = null, tint = Muted, modifier = Modifier.size(20.dp))
    }
}
