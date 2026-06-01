package com.xpenzo.ui.settings

import android.content.Context
import android.content.SharedPreferences

/**
 * Lightweight SharedPreferences-backed store for app-level settings toggles
 * (notifications, appearance, last sync). Read/written directly from Composables
 * via [of] — no Hilt wiring needed for these simple primitives.
 */
object SettingsPreferences {
    private const val PREFS_NAME = "app_settings"

    const val KEY_BUDGET_ALERTS = "budget_alerts"
    const val KEY_WEEKLY_DIGEST = "weekly_digest"
    const val KEY_TXN_NOTIFS = "txn_notifications"
    const val KEY_THEME_MODE = "theme_mode" // auto | light | dark
    const val KEY_LAST_SYNC = "last_sync_at"
    const val KEY_SYNC_ENABLED = "sync_enabled"

    const val THEME_AUTO = "auto"
    const val THEME_LIGHT = "light"
    const val THEME_DARK = "dark"

    fun of(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getBool(context: Context, key: String, default: Boolean): Boolean =
        of(context).getBoolean(key, default)

    fun setBool(context: Context, key: String, value: Boolean) {
        of(context).edit().putBoolean(key, value).apply()
    }

    fun getString(context: Context, key: String, default: String): String =
        of(context).getString(key, default) ?: default

    fun setString(context: Context, key: String, value: String) {
        of(context).edit().putString(key, value).apply()
    }
}
