package com.xpenzo.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

// ── Color scheme ─────────────────────────────────────────────────────────────

private val XpenzoLightColors = lightColorScheme(
    primary            = Coral,
    onPrimary          = Color.White,
    primaryContainer   = CoralSoft,
    onPrimaryContainer = Ink,

    secondary          = Mint,
    onSecondary        = Color.White,
    secondaryContainer = MintSoft,
    onSecondaryContainer = Ink,

    tertiary           = Grape,
    onTertiary         = Color.White,
    tertiaryContainer  = GrapeSoft,
    onTertiaryContainer = Ink,

    background         = Cream,
    onBackground       = Ink,

    surface            = Surface,
    onSurface          = Ink,
    surfaceVariant     = Cream,
    onSurfaceVariant   = Muted,

    error              = Error,
    onError            = Color.White,
    errorContainer     = ErrorSoft,
    onErrorContainer   = Error,

    outline            = Muted.copy(alpha = 0.4f),
)

// ── Shapes ───────────────────────────────────────────────────────────────────

private val XpenzoShapes = Shapes(
    extraSmall = RoundedCornerShape(8.dp),
    small      = RoundedCornerShape(12.dp),
    medium     = RoundedCornerShape(16.dp),
    large      = RoundedCornerShape(20.dp),
    extraLarge = RoundedCornerShape(28.dp),
)

// ── Extended colors (coral/mint/sun/grape/sky) accessible anywhere ────────────

data class XpenzoExtendedColors(
    val coral: Color,
    val coralSoft: Color,
    val mint: Color,
    val mintSoft: Color,
    val sun: Color,
    val sunSoft: Color,
    val grape: Color,
    val grapeSoft: Color,
    val sky: Color,
    val skySoft: Color,
    val ink: Color,
    val muted: Color,
    val cream: Color,
)

val LocalXpenzoColors = staticCompositionLocalOf {
    XpenzoExtendedColors(
        coral = Coral, coralSoft = CoralSoft,
        mint = Mint, mintSoft = MintSoft,
        sun = Sun, sunSoft = SunSoft,
        grape = Grape, grapeSoft = GrapeSoft,
        sky = Sky, skySoft = SkySoft,
        ink = Ink, muted = Muted, cream = Cream,
    )
}

/** Access extended brand colors via `MaterialTheme.xpenzo.coral` etc. */
val MaterialTheme.xpenzo: XpenzoExtendedColors
    @Composable get() = LocalXpenzoColors.current

// ── Theme composable ─────────────────────────────────────────────────────────

@Composable
fun XpenzoTheme(content: @Composable () -> Unit) {
    CompositionLocalProvider(
        LocalXpenzoColors provides XpenzoExtendedColors(
            coral = Coral, coralSoft = CoralSoft,
            mint = Mint, mintSoft = MintSoft,
            sun = Sun, sunSoft = SunSoft,
            grape = Grape, grapeSoft = GrapeSoft,
            sky = Sky, skySoft = SkySoft,
            ink = Ink, muted = Muted, cream = Cream,
        ),
    ) {
        MaterialTheme(
            colorScheme = XpenzoLightColors,
            typography = XpenzoTypography,
            shapes = XpenzoShapes,
            content = content,
        )
    }
}
