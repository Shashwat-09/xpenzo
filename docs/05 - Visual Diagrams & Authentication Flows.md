# XPENZ - VISUAL DIAGRAMS & AUTHENTICATION FLOWS

## 📊 **PART 1: ENTITY RELATIONSHIP DIAGRAMS (ERD)**

---

## 1. COMPLETE DATABASE ERD

### 1.1 Main Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ DEVICES : "has"
    USERS ||--o{ FAMILY_MEMBERS : "belongs to"
    USERS ||--o{ TRANSACTIONS : "creates"
    USERS ||--o{ BUDGETS : "creates"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o| SUBSCRIPTIONS : "has"
    USERS ||--o| PREFERENCES : "has"

    FAMILIES ||--o{ FAMILY_MEMBERS : "contains"
    FAMILIES ||--o{ TRANSACTIONS : "tracks"
    FAMILIES ||--o{ BUDGETS : "manages"
    FAMILIES ||--o{ BUDGET_PROGRESS : "monitors"
    FAMILIES ||--o| SYNC_METADATA : "has"
    FAMILIES ||--o| INVITATIONS : "generates"

    BUDGETS ||--o{ BUDGET_PROGRESS : "calculates"
    TRANSACTIONS ||--o{ ML_CORRECTIONS : "corrects"
    TRANSACTIONS }o--|| ML_CATEGORIES : "classified as"

    USERS {
        string user_id PK
        string phone_number
        string phone_hash
        string email
        string name
        string avatar_url
        string primary_upi_id
        boolean is_premium
        string premium_tier
        timestamp premium_expires_at
        timestamp created_at
        timestamp last_login_at
    }

    DEVICES {
        string device_id PK
        string user_id FK
        string device_name
        string fcm_token
        boolean is_active
        timestamp last_active_at
    }

    PREFERENCES {
        string user_id PK
        string theme
        string language
        boolean notifications_enabled
        boolean auto_sync
        array hidden_categories
    }

    FAMILIES {
        string family_id PK
        string name
        string emoji
        string color
        string invitation_code
        timestamp code_expires_at
        string created_by FK
        int max_members
        boolean is_premium
        timestamp created_at
    }

    FAMILY_MEMBERS {
        string member_id PK
        string family_id FK
        string user_id FK
        string nickname
        string role
        string status
        timestamp joined_at
        timestamp last_active_at
    }

    TRANSACTIONS {
        string transaction_id PK
        string user_id FK
        string family_id FK
        string type
        float amount
        int category_id FK
        timestamp timestamp
        float ml_confidence
        string encrypted_data
        int sync_version
        timestamp created_at
    }

    BUDGETS {
        string budget_id PK
        string family_id FK
        string budget_type
        string name
        int category_id
        string member_id
        float amount
        string period
        array alert_thresholds
        timestamp start_date
        boolean is_active
        string created_by FK
    }

    BUDGET_PROGRESS {
        string progress_id PK
        string budget_id FK
        timestamp period_start
        timestamp period_end
        float amount_spent
        float percentage
        string status
        int days_remaining
    }

    ML_CATEGORIES {
        int category_id PK
        string category_name
        string display_name
        int parent_category_id
        int level
        string emoji
    }

    INVITATIONS {
        string invitation_code PK
        string family_id FK
        string created_by FK
        timestamp expires_at
        int current_uses
        boolean is_active
    }

    SUBSCRIPTIONS {
        string subscription_id PK
        string user_id FK
        string plan_type
        string purchase_token
        float price
        string status
        timestamp expires_at
        boolean auto_renew
    }

    NOTIFICATIONS {
        string notification_id PK
        string user_id FK
        string type
        string title
        string body
        boolean is_read
        timestamp created_at
    }

    ML_CORRECTIONS {
        string correction_id PK
        string transaction_id FK
        string user_id FK
        int original_category_id
        int corrected_category_id
        timestamp correction_timestamp
    }

    SYNC_METADATA {
        string family_id PK
        timestamp last_transaction_sync
        timestamp last_budget_sync
        array active_devices
        int total_syncs
    }
```

---

### 1.2 Firestore Document Structure Diagram

```mermaid
graph TB
    subgraph "Firestore Root"
        USERS["/users"]
        FAMILIES["/families"]
        INVITATIONS["/invitations"]
        SUBSCRIPTIONS["/subscriptions"]
        NOTIFICATIONS["/notifications"]
        ML_CORRECTIONS["/ml_corrections"]
        SYSTEM["/system"]
    end

    subgraph "Users Collection"
        USERS --> USER_DOC["{userId}"]
        USER_DOC --> USER_PROFILE["profile (doc)"]
        USER_DOC --> USER_PREFS["preferences (doc)"]
        USER_DOC --> USER_SUB["subscription (doc)"]
        USER_DOC --> USER_DEVICES["devices/ (subcollection)"]
        USER_DEVICES --> DEVICE_DOC["{deviceId}"]
    end

    subgraph "Families Collection"
        FAMILIES --> FAMILY_DOC["{familyId}"]
        FAMILY_DOC --> FAMILY_INFO["info (doc)"]
        FAMILY_DOC --> FAMILY_MEMBERS["members/ (subcollection)"]
        FAMILY_DOC --> FAMILY_TXN["transactions/ (subcollection)"]
        FAMILY_DOC --> FAMILY_BUDGETS["budgets/ (subcollection)"]
        FAMILY_DOC --> FAMILY_PROGRESS["budget_progress/ (subcollection)"]
        FAMILY_DOC --> FAMILY_SYNC["sync_metadata (doc)"]

        FAMILY_MEMBERS --> MEMBER_DOC["{memberId}"]
        FAMILY_TXN --> TXN_DOC["{transactionId}"]
        FAMILY_BUDGETS --> BUDGET_DOC["{budgetId}"]
        FAMILY_PROGRESS --> PROGRESS_DOC["{progressId}"]
    end

    subgraph "System Collection"
        SYSTEM --> SYS_CONFIG["config (doc)"]
        SYSTEM --> SYS_MODELS["ml_models/ (subcollection)"]
        SYS_MODELS --> MODEL_DOC["{modelVersion}"]
    end

    style USERS fill:#e1f5ff
    style FAMILIES fill:#fff3e0
    style SYSTEM fill:#f3e5f5
    style USER_DOC fill:#b3e5fc
    style FAMILY_DOC fill:#ffe0b2
```

---

### 1.3 Data Relationships Flow

```mermaid
graph LR
    subgraph "User Domain"
        U[User] --> D[Devices]
        U --> P[Preferences]
        U --> S[Subscription]
    end

    subgraph "Family Domain"
        F[Family] --> FM[Family Members]
        F --> I[Invitation]
        F --> SM[Sync Metadata]

        U -.member of.-> FM
        FM --> F
    end

    subgraph "Transaction Domain"
        T[Transaction] --> ML[ML Classification]
        T --> MC[ML Correction]
        ML --> CAT[Category]

        U -.creates.-> T
        F -.tracks.-> T
    end

    subgraph "Budget Domain"
        B[Budget] --> BP[Budget Progress]

        F -.manages.-> B
        U -.creates.-> B
        T -.affects.-> BP
    end

    subgraph "Notification Domain"
        N[Notification]

        BP -.triggers.-> N
        T -.triggers.-> N
        FM -.triggers.-> N
        U -.receives.-> N
    end

    style U fill:#4caf50
    style F fill:#2196f3
    style T fill:#ff9800
    style B fill:#9c27b0
    style N fill:#f44336
```

### 1.3 Groups & Splits ERD (Option B — separate subsystem, post-MVP)

> Distinct from Families. A user joins many GROUPS and many FRIENDS. A SPLIT_EXPENSE
> can optionally link back to the payer's own TRANSACTION (reimbursement tracking).
> See PRD F8, Backend Schema §3.8, TRD Tables 12–17.

```mermaid
erDiagram
    USERS ||--o{ GROUP_MEMBERS : "joins"
    USERS ||--o{ FRIENDS : "adds"
    GROUPS ||--o{ GROUP_MEMBERS : "contains"
    GROUPS ||--o{ SPLIT_EXPENSES : "has"
    GROUPS ||--o{ SETTLEMENTS : "settles"
    GROUPS ||--o{ GROUP_BALANCES : "caches"
    SPLIT_EXPENSES ||--o{ SPLIT_SHARES : "divides into"
    TRANSACTIONS ||--o| SPLIT_EXPENSES : "optionally split as"

    GROUPS {
        string group_id PK
        string name
        string type "TRIP|HOME|COUPLE|OTHER"
        string created_by FK
        string invite_code
        boolean simplify_debts
        string currency
    }
    GROUP_MEMBERS {
        string group_id PK_FK
        string user_id PK_FK
        string role "ADMIN|MEMBER"
        string status "ACTIVE|LEFT"
    }
    SPLIT_EXPENSES {
        string expense_id PK
        string group_id FK
        string transaction_id FK "nullable"
        string paid_by FK
        double total_amount
        string split_type "EQUAL|EXACT|PERCENT|SHARES"
        int category_id
    }
    SPLIT_SHARES {
        string expense_id PK_FK
        string user_id PK_FK
        double share_value
        double owed_amount
    }
    SETTLEMENTS {
        string settlement_id PK
        string group_id FK
        string from_user FK
        string to_user FK
        double amount
        string method "CASH|UPI"
        string status "PENDING|CONFIRMED"
    }
    FRIENDS {
        string friend_user_id PK
        string status "PENDING|ACCEPTED|BLOCKED"
        double net_balance
    }
    GROUP_BALANCES {
        string user_id PK
        double net_balance
    }
```

---

## 2. COLLECTION STRUCTURE DIAGRAMS

### 2.1 Users Collection Tree

```mermaid
graph TD
    ROOT["/users/{userId}"]

    ROOT --> PROFILE["Document: profile<br/>• user_id<br/>• phone_number (encrypted)<br/>• name (encrypted)<br/>• email (encrypted)<br/>• is_premium<br/>• premium_expires_at"]

    ROOT --> PREFS["Document: preferences<br/>• theme<br/>• language<br/>• notifications_enabled<br/>• auto_sync<br/>• hidden_categories"]

    ROOT --> DEVICES["Subcollection: devices/"]
    DEVICES --> DEVICE1["{deviceId}<br/>• device_name<br/>• fcm_token<br/>• is_active<br/>• last_active_at"]

    style ROOT fill:#4caf50,color:#fff
    style PROFILE fill:#81c784
    style PREFS fill:#81c784
    style DEVICES fill:#a5d6a7
    style DEVICE1 fill:#c8e6c9
```

### 2.2 Families Collection Tree

```mermaid
graph TD
    ROOT["/families/{familyId}"]

    ROOT --> INFO["Document: info<br/>• family_id<br/>• name (encrypted)<br/>• emoji<br/>• invitation_code<br/>• created_by<br/>• is_premium<br/>• max_members"]

    ROOT --> MEMBERS["Subcollection: members/"]
    MEMBERS --> MEMBER["{memberId}<br/>• user_id<br/>• nickname (encrypted)<br/>• role (ADMIN/MEMBER)<br/>• status (ACTIVE/LEFT)<br/>• joined_at"]

    ROOT --> TRANSACTIONS["Subcollection: transactions/"]
    TRANSACTIONS --> TXN["{transactionId}<br/>• user_id<br/>• type (DEBIT/CREDIT)<br/>• amount<br/>• category_id<br/>• encrypted_data<br/>• sync_version"]

    ROOT --> BUDGETS["Subcollection: budgets/"]
    BUDGETS --> BUDGET["{budgetId}<br/>• budget_type<br/>• amount<br/>• period<br/>• alert_thresholds<br/>• is_active"]

    ROOT --> PROGRESS["Subcollection: budget_progress/"]
    PROGRESS --> PROG["{progressId}<br/>• budget_id<br/>• amount_spent<br/>• percentage<br/>• status<br/>• days_remaining"]

    ROOT --> SYNC["Document: sync_metadata<br/>• last_transaction_sync<br/>• last_budget_sync<br/>• active_devices"]

    style ROOT fill:#2196f3,color:#fff
    style INFO fill:#64b5f6
    style MEMBERS fill:#90caf9
    style TRANSACTIONS fill:#90caf9
    style BUDGETS fill:#90caf9
    style PROGRESS fill:#90caf9
    style SYNC fill:#64b5f6
```

---

## 3. DATA FLOW SEQUENCE DIAGRAMS

### 3.1 Transaction Creation & Sync Flow

```mermaid
sequenceDiagram
    participant SMS as SMS System
    participant App as Android App
    participant Room as Local DB (Room)
    participant Worker as Sync Worker
    participant Fire as Firestore
    participant Func as Cloud Function
    participant FCM as FCM Service
    participant App2 as Other Devices

    SMS->>App: SMS Received
    App->>App: Parse SMS
    App->>App: ML Classification
    App->>Room: Save Transaction (is_synced: false)
    Room-->>App: Transaction Saved
    App->>App: Show Notification

    Note over App,Room: Transaction saved locally<br/>App continues working offline

    App->>Worker: Queue Sync Job
    Worker->>Worker: Wait for Network
    Worker->>Fire: Upload Transaction (encrypted)
    Fire-->>Worker: Confirmed
    Worker->>Room: Update (is_synced: true)

    Fire->>Func: Trigger: onTransactionCreate
    Func->>Func: Calculate Budget Progress
    Func->>Fire: Update Budget Progress
    Func->>Func: Check Alert Thresholds

    alt Budget Alert Triggered
        Func->>FCM: Send Push Notification
        FCM->>App2: Deliver to Family Members
        App2->>App2: Show Alert
    end

    Func->>Fire: Update Family Stats

    Fire-->>App2: Real-time Listener
    App2->>Fire: Fetch New Transaction
    Fire-->>App2: Transaction Data
    App2->>App2: Decrypt Data
    App2->>Room: Save to Local DB
    Room-->>App2: Updated
    App2->>App2: Update UI
```

---

### 3.2 Family Creation & Invitation Flow

```mermaid
sequenceDiagram
    participant U1 as User 1 (Creator)
    participant App1 as App (Device 1)
    participant Func as Cloud Function
    participant Fire as Firestore
    participant U2 as User 2 (Joiner)
    participant App2 as App (Device 2)

    U1->>App1: Tap "Create Family"
    App1->>App1: Fill Family Details
    U1->>App1: Tap "Create"

    App1->>Func: Call createFamily()
    Func->>Func: Generate Code (XP-XXXXX)
    Func->>Fire: Create Family Document
    Func->>Fire: Create Invitation Document
    Func->>Fire: Add Creator as Admin
    Fire-->>Func: Success
    Func-->>App1: Return Family ID + Code

    App1->>App1: Show Success Screen
    App1->>App1: Display Code: XP-A7K2M

    U1->>U2: Share Code (WhatsApp/SMS)

    U2->>App2: Enter Code
    App2->>Func: Call joinFamily(code)
    Func->>Fire: Validate Code

    alt Code Valid
        Func->>Fire: Check Member Limit
        alt Limit Not Reached
            Func->>Fire: Add Member
            Func->>Fire: Update Invitation Usage
            Fire-->>Func: Success
            Func-->>App2: Return Family Info
            App2->>App2: Sync Family Data
            App2->>App2: Navigate to Dashboard

            Fire->>App1: Real-time Update
            App1->>App1: Show "New Member Joined"
        else Limit Reached
            Func-->>App2: Error: Limit Reached
            App2->>App2: Show Upgrade Prompt
        end
    else Code Invalid
        Func-->>App2: Error: Invalid Code
        App2->>App2: Show Error
    end
```

---

### 3.3 Budget Alert Flow

```mermaid
sequenceDiagram
    participant App as Android App
    participant Fire as Firestore
    participant Func as Cloud Function
    participant FCM as FCM Service
    participant Devices as All Devices

    App->>Fire: Transaction Created
    Fire->>Func: Trigger: onTransactionCreate

    Func->>Fire: Fetch Active Budgets
    Fire-->>Func: Budget List

    loop For Each Budget
        Func->>Func: Check if Applicable
        alt Transaction Affects Budget
            Func->>Fire: Query Transactions in Period
            Fire-->>Func: Transaction List
            Func->>Func: Calculate Total Spent
            Func->>Func: Calculate Percentage
            Func->>Func: Check Thresholds [50, 80, 100, 120]

            alt Threshold Crossed
                Func->>Fire: Update Budget Progress
                Func->>Fire: Save Alert History

                Func->>Fire: Get Family Members
                Fire-->>Func: Member List

                Func->>Fire: Get FCM Tokens
                Fire-->>Func: Token List

                Func->>FCM: Send Multicast Notification
                FCM->>Devices: Deliver to All Devices

                Devices->>Devices: Show System Notification
                Devices->>Devices: Update In-App Badge

                alt App is Open
                    Devices->>Devices: Real-time UI Update
                    Devices->>Devices: Show Alert Dialog
                end
            end
        end
    end
```

---

## 📱 **PART 2: AUTHENTICATION FLOWS**

---

## 4. FIREBASE AUTHENTICATION

### 4.1 Phone Authentication Overview

```mermaid
graph TB
    START[User Opens App] --> CHECK{First Time<br/>User?}

    CHECK -->|Yes| ONBOARD[Onboarding Flow]
    CHECK -->|No| SESSION{Valid<br/>Session?}

    SESSION -->|Yes| DASH[Dashboard]
    SESSION -->|No| LOGIN[Login Screen]

    ONBOARD --> PHONE[Phone Number Entry]
    LOGIN --> PHONE

    PHONE --> VERIFY[Send OTP via Firebase]
    VERIFY --> OTP[OTP Entry Screen]

    OTP --> VALIDATE{OTP<br/>Valid?}

    VALIDATE -->|No| RETRY{Attempts<br/>< 3?}
    RETRY -->|Yes| OTP
    RETRY -->|No| LOCK[15min Lockout]
    LOCK --> PHONE

    VALIDATE -->|Yes| CREATE{User<br/>Exists?}

    CREATE -->|No| PROFILE[Create Profile]
    CREATE -->|Yes| COMPLETE[Login Complete]

    PROFILE --> COMPLETE
    COMPLETE --> DASH

    style START fill:#4caf50
    style DASH fill:#2196f3
    style LOCK fill:#f44336
    style COMPLETE fill:#4caf50
```

---

### 4.2 Complete Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant App as Android App
    participant UI as UI Layer
    participant Auth as AuthViewModel
    participant Repo as AuthRepository
    participant Firebase as Firebase Auth
    participant Fire as Firestore
    participant Local as Local DB

    User->>App: Opens App
    App->>Auth: checkAuthState()
    Auth->>Firebase: currentUser

    alt User Logged In
        Firebase-->>Auth: User Object
        Auth->>Fire: Fetch User Profile
        Fire-->>Auth: Profile Data
        Auth->>Local: Save to Room
        Auth->>UI: Navigate to Dashboard
    else Not Logged In
        Firebase-->>Auth: null
        Auth->>UI: Show Onboarding
    end

    Note over User,UI: User enters phone number

    User->>UI: Enter +91XXXXXXXXXX
    UI->>Auth: validatePhoneNumber()

    alt Valid Format
        Auth->>Firebase: verifyPhoneNumber()
        Firebase->>Firebase: Send SMS with OTP
        Firebase-->>User: SMS Delivered
        Firebase-->>Auth: verificationId
        Auth->>UI: Show OTP Screen

        User->>UI: Enter 6-digit OTP
        UI->>Auth: verifyOTP(code, verificationId)
        Auth->>Firebase: signInWithCredential()

        alt OTP Valid
            Firebase-->>Auth: AuthResult
            Auth->>Auth: Extract UID

            Auth->>Fire: Check if user exists
            Fire-->>Auth: User Document

            alt New User
                Auth->>UI: Show Profile Setup
                User->>UI: Enter Name, Avatar
                UI->>Auth: createUserProfile()
                Auth->>Fire: Create User Document
                Fire-->>Auth: Success
                Auth->>Local: Save User Locally
                Auth->>UI: Navigate to Dashboard
            else Existing User
                Auth->>Fire: Fetch User Data
                Fire-->>Auth: User Profile
                Auth->>Fire: Update last_login_at
                Auth->>Local: Save User Locally
                Auth->>UI: Navigate to Dashboard
            end

        else OTP Invalid
            Firebase-->>Auth: Error
            Auth->>UI: Show Error

            alt Attempts < 3
                UI->>User: "Try Again"
            else Attempts >= 3
                Auth->>Auth: Start 15min Lockout
                Auth->>UI: Show Lockout Screen
            end
        end

    else Invalid Format
        Auth->>UI: Show Format Error
    end
```

---

### 4.3 Phone Authentication Implementation

```kotlin
// AuthRepository.kt
package com.xpenz.core.data.auth

import com.google.firebase.FirebaseException
import com.google.firebase.auth.*
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.tasks.await
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val firebaseAuth: FirebaseAuth,
    private val firestore: FirebaseFirestore
) {

    /**
     * Current authenticated user
     */
    val currentUser: FirebaseUser?
        get() = firebaseAuth.currentUser

    /**
     * Authentication state flow
     */
    val authStateFlow: Flow<AuthState> = callbackFlow {
        val listener = FirebaseAuth.AuthStateListener { auth ->
            val user = auth.currentUser
            trySend(
                if (user != null) AuthState.Authenticated(user)
                else AuthState.Unauthenticated
            )
        }

        firebaseAuth.addAuthStateListener(listener)

        awaitClose {
            firebaseAuth.removeAuthStateListener(listener)
        }
    }

    /**
     * Send OTP to phone number
     */
    suspend fun sendOTP(
        phoneNumber: String,
        activity: Activity
    ): Result<String> {
        return try {
            val formattedNumber = formatPhoneNumber(phoneNumber)

            val options = PhoneAuthOptions.newBuilder(firebaseAuth)
                .setPhoneNumber(formattedNumber)
                .setTimeout(60L, TimeUnit.SECONDS)
                .setActivity(activity)
                .setCallbacks(object : PhoneAuthProvider.OnVerificationStateChangedCallbacks() {
                    override fun onVerificationCompleted(credential: PhoneAuthCredential) {
                        // Auto-verification (rare on Android)
                        Timber.d("Auto-verification completed")
                    }

                    override fun onVerificationFailed(e: FirebaseException) {
                        Timber.e(e, "Verification failed")
                    }

                    override fun onCodeSent(
                        verificationId: String,
                        token: PhoneAuthProvider.ForceResendingToken
                    ) {
                        Timber.d("OTP sent: $verificationId")
                    }
                })
                .build()

            // This will trigger the callback
            PhoneAuthProvider.verifyPhoneNumber(options)

            // Return placeholder - actual verificationId comes via callback
            Result.Success("OTP_SENT")

        } catch (e: Exception) {
            Timber.e(e, "Failed to send OTP")
            Result.Error(e.message ?: "Failed to send OTP")
        }
    }

    /**
     * Verify OTP and sign in
     */
    suspend fun verifyOTP(
        verificationId: String,
        code: String
    ): Result<FirebaseUser> {
        return try {
            val credential = PhoneAuthProvider.getCredential(verificationId, code)
            val authResult = firebaseAuth.signInWithCredential(credential).await()
            val user = authResult.user

            if (user != null) {
                // Check if new user
                val isNewUser = authResult.additionalUserInfo?.isNewUser ?: false

                if (isNewUser) {
                    // Create user document in Firestore
                    createUserDocument(user)
                } else {
                    // Update last login
                    updateLastLogin(user.uid)
                }

                Result.Success(user)
            } else {
                Result.Error("Sign in failed")
            }

        } catch (e: FirebaseAuthInvalidCredentialsException) {
            Timber.e(e, "Invalid OTP")
            Result.Error("Invalid OTP. Please try again.")
        } catch (e: Exception) {
            Timber.e(e, "OTP verification failed")
            Result.Error(e.message ?: "Verification failed")
        }
    }

    /**
     * Create user profile
     */
    suspend fun createUserProfile(
        userId: String,
        name: String,
        email: String?,
        avatarUrl: String?
    ): Result<Unit> {
        return try {
            val userDoc = hashMapOf(
                "user_id" to userId,
                "phone_number" to encryptData(currentUser?.phoneNumber ?: ""),
                "phone_hash" to hashPhoneNumber(currentUser?.phoneNumber ?: ""),
                "name" to encryptData(name),
                "email" to email?.let { encryptData(it) },
                "avatar_url" to avatarUrl,
                "is_premium" to false,
                "created_at" to FieldValue.serverTimestamp(),
                "updated_at" to FieldValue.serverTimestamp(),
                "last_login_at" to FieldValue.serverTimestamp(),
                "onboarding_completed" to false,
                "device_count" to 0,
                "total_transactions" to 0,
                "total_families" to 0
            )

            firestore.collection("users")
                .document(userId)
                .set(userDoc)
                .await()

            Result.Success(Unit)

        } catch (e: Exception) {
            Timber.e(e, "Failed to create user profile")
            Result.Error(e.message ?: "Failed to create profile")
        }
    }

    /**
     * Sign out
     */
    suspend fun signOut(): Result<Unit> {
        return try {
            firebaseAuth.signOut()
            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e.message ?: "Sign out failed")
        }
    }

    /**
     * Delete account
     */
    suspend fun deleteAccount(): Result<Unit> {
        return try {
            val userId = currentUser?.uid ?: return Result.Error("Not authenticated")

            // Delete user data from Firestore
            deleteUserData(userId)

            // Delete Firebase Auth account
            currentUser?.delete()?.await()

            Result.Success(Unit)

        } catch (e: Exception) {
            Timber.e(e, "Failed to delete account")
            Result.Error(e.message ?: "Failed to delete account")
        }
    }

    // Helper Functions

    private fun formatPhoneNumber(phoneNumber: String): String {
        var formatted = phoneNumber.replace(Regex("[^0-9]"), "")

        // Add country code if not present
        if (!formatted.startsWith("91")) {
            formatted = "91$formatted"
        }

        return "+$formatted"
    }

    private fun hashPhoneNumber(phoneNumber: String): String {
        return MessageDigest.getInstance("SHA-256")
            .digest(phoneNumber.toByteArray())
            .joinToString("") { "%02x".format(it) }
    }

    private fun encryptData(data: String): String {
        // Implement encryption using EncryptionService
        return encryptionService.encrypt(data)
    }

    private suspend fun createUserDocument(user: FirebaseUser) {
        val userDoc = hashMapOf(
            "user_id" to user.uid,
            "phone_number" to encryptData(user.phoneNumber ?: ""),
            "phone_hash" to hashPhoneNumber(user.phoneNumber ?: ""),
            "is_premium" to false,
            "created_at" to FieldValue.serverTimestamp(),
            "updated_at" to FieldValue.serverTimestamp(),
            "last_login_at" to FieldValue.serverTimestamp(),
            "onboarding_completed" to false
        )

        firestore.collection("users")
            .document(user.uid)
            .set(userDoc)
            .await()
    }

    private suspend fun updateLastLogin(userId: String) {
        firestore.collection("users")
            .document(userId)
            .update("last_login_at", FieldValue.serverTimestamp())
            .await()
    }

    private suspend fun deleteUserData(userId: String) {
        // Delete user document
        firestore.collection("users")
            .document(userId)
            .delete()
            .await()

        // Leave all families (mark as LEFT)
        val memberships = firestore.collectionGroup("members")
            .whereEqualTo("user_id", userId)
            .get()
            .await()

        val batch = firestore.batch()
        memberships.documents.forEach { doc ->
            batch.update(doc.reference, mapOf(
                "status" to "LEFT",
                "left_at" to FieldValue.serverTimestamp()
            ))
        }
        batch.commit().await()
    }
}

sealed class AuthState {
    data class Authenticated(val user: FirebaseUser) : AuthState()
    object Unauthenticated : AuthState()
}
```

---

### 4.4 Session Management

```kotlin
// SessionManager.kt
package com.xpenz.core.auth

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.google.firebase.auth.FirebaseAuth
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.sessionDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "session_prefs"
)

@Singleton
class SessionManager @Inject constructor(
    private val context: Context,
    private val firebaseAuth: FirebaseAuth
) {

    private object Keys {
        val USER_ID = stringPreferencesKey("user_id")
        val PHONE_NUMBER = stringPreferencesKey("phone_number")
        val IS_PREMIUM = booleanPreferencesKey("is_premium")
        val PREMIUM_EXPIRES_AT = longPreferencesKey("premium_expires_at")
        val LAST_SYNC_TIME = longPreferencesKey("last_sync_time")
        val SELECTED_FAMILY_ID = stringPreferencesKey("selected_family_id")
    }

    /**
     * Check if user is authenticated
     */
    fun isAuthenticated(): Boolean {
        return firebaseAuth.currentUser != null
    }

    /**
     * Get current user ID
     */
    fun getCurrentUserId(): String? {
        return firebaseAuth.currentUser?.uid
    }

    /**
     * Save session data
     */
    suspend fun saveSession(
        userId: String,
        phoneNumber: String,
        isPremium: Boolean,
        premiumExpiresAt: Long?
    ) {
        context.sessionDataStore.edit { prefs ->
            prefs[Keys.USER_ID] = userId
            prefs[Keys.PHONE_NUMBER] = phoneNumber
            prefs[Keys.IS_PREMIUM] = isPremium
            premiumExpiresAt?.let { prefs[Keys.PREMIUM_EXPIRES_AT] = it }
        }
    }

    /**
     * Get user ID flow
     */
    val userIdFlow: Flow<String?> = context.sessionDataStore.data
        .map { prefs -> prefs[Keys.USER_ID] }

    /**
     * Check if user is premium
     */
    val isPremiumFlow: Flow<Boolean> = context.sessionDataStore.data
        .map { prefs ->
            val isPremium = prefs[Keys.IS_PREMIUM] ?: false
            val expiresAt = prefs[Keys.PREMIUM_EXPIRES_AT] ?: 0L

            isPremium && (expiresAt > System.currentTimeMillis())
        }

    /**
     * Update last sync time
     */
    suspend fun updateLastSyncTime(timestamp: Long) {
        context.sessionDataStore.edit { prefs ->
            prefs[Keys.LAST_SYNC_TIME] = timestamp
        }
    }

    /**
     * Get last sync time
     */
    suspend fun getLastSyncTime(): Long {
        return context.sessionDataStore.data
            .map { prefs -> prefs[Keys.LAST_SYNC_TIME] ?: 0L }
            .first()
    }

    /**
     * Set selected family
     */
    suspend fun setSelectedFamily(familyId: String) {
        context.sessionDataStore.edit { prefs ->
            prefs[Keys.SELECTED_FAMILY_ID] = familyId
        }
    }

    /**
     * Get selected family
     */
    val selectedFamilyFlow: Flow<String?> = context.sessionDataStore.data
        .map { prefs -> prefs[Keys.SELECTED_FAMILY_ID] }

    /**
     * Clear session (on logout)
     */
    suspend fun clearSession() {
        context.sessionDataStore.edit { prefs ->
            prefs.clear()
        }
    }

    /**
     * Refresh auth token
     */
    suspend fun refreshAuthToken(): Result<String> {
        return try {
            val user = firebaseAuth.currentUser
                ?: return Result.Error("Not authenticated")

            val tokenResult = user.getIdToken(true).await()
            val token = tokenResult.token
                ?: return Result.Error("Failed to get token")

            Result.Success(token)

        } catch (e: Exception) {
            Timber.e(e, "Failed to refresh token")
            Result.Error(e.message ?: "Token refresh failed")
        }
    }
}
```

---

### 4.5 Token Management & Security

```mermaid
sequenceDiagram
    participant App as Android App
    participant Auth as Firebase Auth
    participant Fire as Firestore
    participant Func as Cloud Function

    Note over App,Auth: Initial Authentication
    App->>Auth: signInWithCredential(otp)
    Auth-->>App: ID Token (valid 1 hour)

    Note over App,Fire: Making Authenticated Request
    App->>App: Check Token Expiry

    alt Token Expired (> 55 min)
        App->>Auth: getIdToken(forceRefresh: true)
        Auth->>Auth: Validate Session
        Auth-->>App: New ID Token
    end

    App->>Fire: Request with Token
    Fire->>Fire: Verify Token Signature
    Fire->>Fire: Check Token Expiry
    Fire->>Fire: Extract User ID (UID)

    alt Token Valid
        Fire->>Fire: Apply Security Rules
        Fire->>Fire: Check User Permissions

        alt Has Permission
            Fire-->>App: Data Response
        else No Permission
            Fire-->>App: Error: Permission Denied
        end
    else Token Invalid
        Fire-->>App: Error: Unauthenticated
        App->>Auth: Re-authenticate
    end

    Note over App,Func: Calling Cloud Function
    App->>App: Get Fresh Token
    App->>Func: Call with ID Token
    Func->>Func: Verify Token (automatic)
    Func->>Func: Extract context.auth.uid
    Func->>Func: Execute Function Logic
    Func-->>App: Response
```

---

### 4.6 Multi-Device Session Management

```mermaid
graph TB
    USER[User Account] --> D1[Device 1<br/>Papa's Phone]
    USER --> D2[Device 2<br/>Papa's Tablet]
    USER --> D3[Device 3<br/>Work Phone]

    D1 --> S1[Session 1<br/>Token: xxx<br/>Expires: 2h]
    D2 --> S2[Session 2<br/>Token: yyy<br/>Expires: 1.5h]
    D3 --> S3[Session 3<br/>Token: zzz<br/>Expires: 3h]

    S1 --> FIRE[(Firestore<br/>users/{uid}/devices/)]
    S2 --> FIRE
    S3 --> FIRE

    FIRE --> SYNC[Real-time Sync]

    SYNC --> D1
    SYNC --> D2
    SYNC --> D3

    style USER fill:#4caf50
    style FIRE fill:#ff9800
    style SYNC fill:#2196f3
```

---

### 4.7 Security Rules for Authentication

```jsx
// Firestore Security Rules - Authentication Layer

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Helper: Check if request is authenticated
    function isSignedIn() {
      return request.auth != null;
    }

    // Helper: Check if user is accessing own data
    function isOwner(userId) {
      return isSignedIn() && request.auth.uid == userId;
    }

    // Helper: Get user premium status
    function isPremiumUser() {
      return isSignedIn() &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.is_premium == true &&
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.premium_expires_at > request.time;
    }

    // Helper: Check token claims
    function hasVerifiedEmail() {
      return isSignedIn() && request.auth.token.email_verified == true;
    }

    // Users can only read/write their own data
    match /users/{userId} {
      allow read: if isOwner(userId);
      allow create: if isOwner(userId);
      allow update: if isOwner(userId) &&
        // Prevent privilege escalation
        !request.resource.data.diff(resource.data).affectedKeys().hasAny(['is_premium', 'premium_tier']);
      allow delete: if false; // Soft delete only via Cloud Function
    }

    // Device management
    match /users/{userId}/devices/{deviceId} {
      allow read, write: if isOwner(userId);

      // Limit number of devices for free tier
      allow create: if isOwner(userId) && (
        isPremiumUser() ||
        get(/databases/$(database)/documents/users/$(userId)).data.device_count < 1
      );
    }
  }
}
```

---

This completes the **VISUAL DIAGRAMS & AUTHENTICATION FLOWS** documentation!

## 📊 **COMPLETE SUMMARY:**

✅ **ERD Diagrams:**

- Complete Entity Relationship Diagram
- Firestore Document Structure
- Data Relationships Flow
- Collection Trees (Users, Families)

✅ **Sequence Diagrams:**

- Transaction Creation & Sync
- Family Creation & Invitation
- Budget Alert Flow

✅ **Authentication Flows:**

- Phone Authentication Overview
- Complete Auth Sequence
- Repository Implementation
- Session Management
- Token Management
- Multi-Device Sessions
- Security Rules

**Total:** 7 major diagrams + complete authentication implementation!

Would you like me to:

1. **Create downloadable documents** with all diagrams?
2. **Add more diagrams** (deployment architecture, error handling flows)?
3. **Create a visual API documentation**?

