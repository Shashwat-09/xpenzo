package com.xpenzo.onboarding

import android.app.Activity
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xpenzo.firebase.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Drives the entire onboarding funnel:
 *   Welcome → PhoneLogin → VerifyOtp → ProfileSetup → UpiIdSetup → SmsPermission → Home
 *
 * Shared state across all six screens lives here. Each screen reads what it needs
 * from [uiState] and calls the relevant action.
 *
 * On [completeOnboarding], persists [OnboardingPreferences.isCompleted] = true so
 * MainActivity routes the user past onboarding on next launch.
 */
@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val preferences: OnboardingPreferences,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    // ── Phone OTP flow ────────────────────────────────────────────────────────

    fun updatePhoneNumber(input: String) {
        _uiState.update {
            it.copy(
                phoneNumber = input.filter { ch -> ch.isDigit() }.take(10),
                error = null,
            )
        }
    }

    fun sendOtp(activity: Activity) {
        val phone = _uiState.value.phoneNumber
        if (phone.length != 10) {
            _uiState.update { it.copy(error = "Enter a valid 10-digit phone number") }
            return
        }

        _uiState.update { it.copy(isSendingOtp = true, error = null) }
        val e164 = "+91$phone"

        authRepository.sendOtp(e164, activity) { result ->
            when (result) {
                is AuthRepository.OtpResult.CodeSent -> _uiState.update {
                    it.copy(
                        isSendingOtp = false,
                        verificationId = result.verificationId,
                        otpSent = true,
                    )
                }
                is AuthRepository.OtpResult.AutoVerified -> {
                    // Auto-verified — sign in directly
                    viewModelScope.launch {
                        runCatching { authRepository.signInWithCredential(result.credential) }
                            .onSuccess {
                                _uiState.update { st ->
                                    st.copy(isSendingOtp = false, isAuthenticated = true)
                                }
                            }
                            .onFailure { e ->
                                _uiState.update { st ->
                                    st.copy(isSendingOtp = false, error = e.message)
                                }
                            }
                    }
                }
                is AuthRepository.OtpResult.Error -> _uiState.update {
                    it.copy(isSendingOtp = false, error = result.message)
                }
            }
        }
    }

    fun updateOtp(input: String) {
        _uiState.update {
            it.copy(
                otpInput = input.filter { ch -> ch.isDigit() }.take(6),
                error = null,
            )
        }
    }

    fun verifyOtp() {
        val verificationId = _uiState.value.verificationId
        val otp = _uiState.value.otpInput
        if (verificationId == null || otp.length != 6) {
            _uiState.update { it.copy(error = "Enter the 6-digit code") }
            return
        }

        _uiState.update { it.copy(isVerifyingOtp = true, error = null) }
        viewModelScope.launch {
            runCatching { authRepository.verifyOtp(verificationId, otp) }
                .onSuccess {
                    _uiState.update { it.copy(isVerifyingOtp = false, isAuthenticated = true) }
                }
                .onFailure { e ->
                    _uiState.update { it.copy(isVerifyingOtp = false, error = e.message) }
                }
        }
    }

    // ── Profile setup ─────────────────────────────────────────────────────────

    fun updateName(input: String) {
        _uiState.update { it.copy(userName = input.take(50), error = null) }
    }

    fun saveName() {
        val name = _uiState.value.userName.trim()
        if (name.isBlank()) {
            _uiState.update { it.copy(error = "Please enter your name") }
            return
        }
        preferences.userName = name
        _uiState.update { it.copy(error = null, nameSaved = true) }
    }

    fun updateUpiId(input: String) {
        _uiState.update { it.copy(upiId = input.lowercase(), error = null) }
    }

    fun saveUpiId(skipped: Boolean = false) {
        val upi = _uiState.value.upiId
        if (!skipped && !upi.matches(Regex("^[\\w.\\-]+@[a-z]+$"))) {
            _uiState.update { it.copy(error = "Enter a valid UPI ID (e.g. yourname@ybl)") }
            return
        }
        preferences.primaryUpiId = if (skipped) null else upi
        _uiState.update { it.copy(error = null, upiSaved = true) }
    }

    // ── SMS permission step ───────────────────────────────────────────────────

    fun smsPermissionGranted() {
        _uiState.update { it.copy(smsPermissionGranted = true) }
    }

    fun completeOnboarding() {
        preferences.isCompleted = true
        _uiState.update { it.copy(onboardingCompleted = true) }
    }

    fun clearError() = _uiState.update { it.copy(error = null) }

    // ── UI model ──────────────────────────────────────────────────────────────

    data class UiState(
        val phoneNumber: String = "",
        val otpInput: String = "",
        val verificationId: String? = null,
        val isSendingOtp: Boolean = false,
        val isVerifyingOtp: Boolean = false,
        val otpSent: Boolean = false,
        val isAuthenticated: Boolean = false,
        val userName: String = "",
        val nameSaved: Boolean = false,
        val upiId: String = "",
        val upiSaved: Boolean = false,
        val smsPermissionGranted: Boolean = false,
        val onboardingCompleted: Boolean = false,
        val error: String? = null,
    ) {
        val canSendOtp: Boolean get() = phoneNumber.length == 10 && !isSendingOtp
        val canVerifyOtp: Boolean get() = otpInput.length == 6 && !isVerifyingOtp
    }
}
