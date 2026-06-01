package com.xpenzo.ui.common

import androidx.compose.ui.graphics.Color
import com.xpenzo.ui.theme.Coral
import com.xpenzo.ui.theme.Grape
import com.xpenzo.ui.theme.Mint
import com.xpenzo.ui.theme.Muted
import com.xpenzo.ui.theme.Sky
import com.xpenzo.ui.theme.Sun

/** Returns a brand color for a given L1 category label. */
fun categoryColor(l1: String): Color = when (l1.lowercase()) {
    "food", "dining"         -> Coral
    "transport", "travel"    -> Sky
    "shopping"               -> Grape
    "groceries"              -> Mint
    "bills", "utilities"     -> Sun
    "health", "medical"      -> Color(0xFFEF5350)
    "entertainment"          -> Grape
    "education"              -> Sky
    else                     -> Muted
}

fun categoryEmoji(l1: String): String = when (l1.lowercase()) {
    "food", "dining"         -> "🍽️"
    "transport", "travel"    -> "🚗"
    "shopping"               -> "🛍️"
    "groceries"              -> "🛒"
    "bills", "utilities"     -> "⚡"
    "health", "medical"      -> "💊"
    "entertainment"          -> "🎬"
    "education"              -> "📚"
    else                     -> "💳"
}

fun formatRupees(paise: Long): String {
    val r = paise / 100.0
    return when {
        r >= 1_00_000 -> "%.1fL".format(r / 1_00_000)
        r >= 1_000    -> "%.1fK".format(r / 1_000)
        else          -> r.toInt().toString()
    }
}
