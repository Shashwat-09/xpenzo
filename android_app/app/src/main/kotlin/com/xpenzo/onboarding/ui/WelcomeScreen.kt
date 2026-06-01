package com.xpenzo.onboarding.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.Insights
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Speed
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.CoralSoft
import com.xpenzo.ui.theme.Cream
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.GrapeSoft
import com.xpenzo.ui.theme.Ink
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.MintSoft
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sun
import com.xpenzo.ui.theme.SunSoft
import com.xpenzo.ui.theme.Surface

@Composable
fun WelcomeScreen(onGetStarted: () -> Unit) {
    val infinite = rememberInfiniteTransition(label = "welcome_float")
    val scale by infinite.animateFloat(
        initialValue = 1f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            tween(2_000, easing = EaseInOutSine),
            RepeatMode.Reverse,
        ),
        label = "scale",
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Cream)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(48.dp))

        // Floating hero coin
        Box(
            modifier = Modifier
                .size(160.dp)
                .scale(scale)
                .background(Coral, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                "₹",
                style = MaterialTheme.typography.displayLarge.copy(
                    fontWeight = FontWeight.Bold,
                    color = Surface,
                ),
            )
        }

        Spacer(Modifier.height(40.dp))

        Text(
            "Welcome to Xpenzo",
            style = MaterialTheme.typography.headlineLarge.copy(
                fontWeight = FontWeight.Bold,
                color = Ink,
            ),
            textAlign = TextAlign.Center,
        )

        Spacer(Modifier.height(12.dp))

        Text(
            "Your UPI transactions — automatically categorized, " +
                "privately, on your device.",
            style = MaterialTheme.typography.bodyLarge,
            color = Muted,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 16.dp),
        )

        Spacer(Modifier.height(40.dp))

        // Feature pills
        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            FeatureRow(
                icon = Icons.Rounded.AutoAwesome,
                bg = GrapeSoft,
                tint = Grape,
                title = "AI-powered categorization",
                subtitle = "520 categories, learns your habits",
            )
            FeatureRow(
                icon = Icons.Rounded.Lock,
                bg = MintSoft,
                tint = Mint,
                title = "Privacy first",
                subtitle = "SMS never leaves your phone",
            )
            FeatureRow(
                icon = Icons.Rounded.Insights,
                bg = SunSoft,
                tint = Sun,
                title = "Real insights",
                subtitle = "Spot patterns. Save smarter.",
            )
            FeatureRow(
                icon = Icons.Rounded.Speed,
                bg = CoralSoft,
                tint = Coral,
                title = "Lightning fast",
                subtitle = "Categorizes in under 100ms",
            )
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = onGetStarted,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Coral),
            shape = RoundedCornerShape(20.dp),
        ) {
            Text(
                "Get started",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = Surface,
                ),
            )
        }

        Spacer(Modifier.height(16.dp))

        Text(
            "By continuing you agree to our Privacy Policy",
            style = MaterialTheme.typography.bodySmall,
            color = Muted,
        )

        Spacer(Modifier.height(8.dp))
    }
}

@Composable
private fun FeatureRow(
    icon: ImageVector,
    bg: Color,
    tint: Color,
    title: String,
    subtitle: String,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Surface, RoundedCornerShape(16.dp))
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .background(bg, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(22.dp))
        }
        Spacer(Modifier.width(12.dp))
        Column {
            Text(title, style = MaterialTheme.typography.titleSmall.copy(
                fontWeight = FontWeight.SemiBold, color = Ink,
            ))
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Muted)
        }
    }
}
