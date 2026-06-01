package com.xpenzo.firebase

import android.app.Activity
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.PhoneAuthCredential
import com.google.firebase.auth.PhoneAuthOptions
import com.google.firebase.auth.PhoneAuthProvider
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.tasks.await

/**
 * Phone OTP authentication — wraps Firebase Auth.
 *
 * Flow:
 *  1. [sendOtp] → triggers Firebase Phone Auth; returns [OtpResult.CodeSent]
 *  2. [verifyOtp] → sign in with the 6-digit code
 *  3. [currentUser] / [authState] — observe sign-in state
 *
 * The google-services.json must be present and the `google-services` plugin
 * must be enabled in the root build.gradle.kts before this will compile
 * against real Firebase (Phase 7 prerequisite).
 */
@Singleton
class AuthRepository @Inject constructor() {

    private val auth: FirebaseAuth = FirebaseAuth.getInstance()

    val currentUser: FirebaseUser? get() = auth.currentUser

    val isSignedIn: Boolean get() = currentUser != null

    /** Emits the current [FirebaseUser] and updates on sign-in/out events. */
    val authState: Flow<FirebaseUser?> = callbackFlow {
        val listener = FirebaseAuth.AuthStateListener { trySend(it.currentUser) }
        auth.addAuthStateListener(listener)
        awaitClose { auth.removeAuthStateListener(listener) }
    }

    /**
     * Trigger Firebase Phone Auth OTP. Returns a [OtpResult] that the UI uses
     * to display the OTP input screen (on [OtpResult.CodeSent]) or show an error.
     */
    fun sendOtp(
        phoneNumber: String,  // E.164 format e.g. "+919876543210"
        activity: Activity,
        onResult: (OtpResult) -> Unit,
    ) {
        val callbacks = object : PhoneAuthProvider.OnVerificationStateChangedCallbacks() {
            override fun onVerificationCompleted(credential: PhoneAuthCredential) {
                // Auto-retrieval or instant verification
                onResult(OtpResult.AutoVerified(credential))
            }
            override fun onVerificationFailed(e: com.google.firebase.FirebaseException) {
                onResult(OtpResult.Error(e.message ?: "Verification failed"))
            }
            override fun onCodeSent(
                verificationId: String,
                token: PhoneAuthProvider.ForceResendingToken,
            ) {
                onResult(OtpResult.CodeSent(verificationId, token))
            }
        }

        PhoneAuthOptions.newBuilder(auth)
            .setPhoneNumber(phoneNumber)
            .setTimeout(60L, TimeUnit.SECONDS)
            .setActivity(activity)
            .setCallbacks(callbacks)
            .build()
            .let { PhoneAuthProvider.verifyPhoneNumber(it) }
    }

    /**
     * Sign in with a 6-digit OTP code and the [verificationId] from [OtpResult.CodeSent].
     * Returns the signed-in [FirebaseUser] or throws.
     */
    suspend fun verifyOtp(verificationId: String, otp: String): FirebaseUser {
        val credential = PhoneAuthProvider.getCredential(verificationId, otp)
        return signInWithCredential(credential)
    }

    suspend fun signInWithCredential(credential: PhoneAuthCredential): FirebaseUser {
        val result = auth.signInWithCredential(credential).await()
        return result.user ?: error("Sign-in succeeded but user is null")
    }

    suspend fun signOut() {
        auth.signOut()
    }

    sealed class OtpResult {
        data class CodeSent(
            val verificationId: String,
            val resendToken: PhoneAuthProvider.ForceResendingToken,
        ) : OtpResult()
        data class AutoVerified(val credential: PhoneAuthCredential) : OtpResult()
        data class Error(val message: String) : OtpResult()
    }
}
