package com.xpenzo.onboarding

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Tracks whether the user has completed the onboarding flow.
 * Backed by SharedPreferences (single boolean — no need for DataStore).
 */
@Singleton
class OnboardingPreferences @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    var isCompleted: Boolean
        get() = prefs.getBoolean(KEY_COMPLETED, false)
        set(value) = prefs.edit().putBoolean(KEY_COMPLETED, value).apply()

    var userName: String?
        get() = prefs.getString(KEY_USER_NAME, null)
        set(value) = prefs.edit().putString(KEY_USER_NAME, value).apply()

    var primaryUpiId: String?
        get() = prefs.getString(KEY_UPI_ID, null)
        set(value) = prefs.edit().putString(KEY_UPI_ID, value).apply()

    fun reset() {
        prefs.edit().clear().apply()
    }

    companion object {
        private const val PREFS_NAME = "onboarding_prefs"
        private const val KEY_COMPLETED = "completed"
        private const val KEY_USER_NAME = "user_name"
        private const val KEY_UPI_ID = "upi_id"
    }
}
