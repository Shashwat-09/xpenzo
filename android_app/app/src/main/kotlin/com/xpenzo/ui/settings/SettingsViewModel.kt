package com.xpenzo.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.xpenzo.data.db.XpenzoDatabase
import com.xpenzo.ml.data.DataCollectionPreferences
import com.xpenzo.onboarding.OnboardingPreferences
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val db: XpenzoDatabase,
    private val dataCollectionPreferences: DataCollectionPreferences,
    private val onboardingPreferences: OnboardingPreferences,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        _uiState.update { it.copy(isOptedInToDataCollection = dataCollectionPreferences.isOptedIn) }
    }

    /** Toggle anonymous data-collection opt-in. Persists to SharedPreferences immediately. */
    fun setDataCollectionOptIn(enabled: Boolean) {
        dataCollectionPreferences.isOptedIn = enabled
        _uiState.update { it.copy(isOptedInToDataCollection = enabled) }
    }

    /**
     * Delete the account:
     *  1. Purge all Room tables (transactions, habits, corrections, budgets).
     *  2. Delete the user's Firestore subcollection /users/{uid}/transactions/ (best-effort).
     *  3. Sign out from Firebase Auth.
     *
     * Step 2 is best-effort — a Cloud Function is responsible for deep deletion
     * of all user data within 30 days per DPDP compliance.
     */
    fun deleteAccount(onComplete: () -> Unit, onError: (String) -> Unit) = viewModelScope.launch {
        _uiState.update { it.copy(isDeletingAccount = true) }
        try {
            // 1. Clear local Room database
            db.clearAllTables()
            // Also reset all SharedPreferences so user re-onboards
            onboardingPreferences.reset()
            dataCollectionPreferences.isOptedIn = false

            // 2. Best-effort Firestore cleanup (fire-and-forget batch)
            val uid = FirebaseAuth.getInstance().currentUser?.uid
            if (uid != null) {
                runCatching {
                    val fs = FirebaseFirestore.getInstance()
                    val txDocs = fs.collection("users").document(uid)
                        .collection("transactions").get().await()
                    val batch = fs.batch()
                    txDocs.documents.forEach { batch.delete(it.reference) }
                    batch.commit().await()
                    // Delete user document (anonymizes profile)
                    fs.collection("users").document(uid).delete().await()
                }
            }

            // 3. Sign out
            FirebaseAuth.getInstance().signOut()

            _uiState.update { it.copy(isDeletingAccount = false, isAccountDeleted = true) }
            onComplete()
        } catch (e: Exception) {
            _uiState.update { it.copy(isDeletingAccount = false) }
            onError(e.message ?: "Unknown error")
        }
    }

    data class UiState(
        val isOptedInToDataCollection: Boolean = false,
        val isDeletingAccount: Boolean = false,
        val isAccountDeleted: Boolean = false,
    )
}
