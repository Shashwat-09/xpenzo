# XPENZ - COMPLETE APP FLOW DOCUMENTATION

## 📱 **APPLICATION FLOW ARCHITECTURE**

---

## 1. HIGH-LEVEL APP FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                         APP LAUNCH                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌──────────────────┐
                    │  Is User Logged  │
                    │      In?         │
                    └──────────────────┘
                       ↓              ↓
                    YES              NO
                       ↓              ↓
              ┌──────────────┐  ┌──────────────┐
              │  DASHBOARD   │  │  ONBOARDING  │
              │    FLOW      │  │     FLOW     │
              └──────────────┘  └──────────────┘
                       ↓              ↓
              ┌─────────────────┐    │
              │ Family Selected?│◄───┘
              └─────────────────┘
                  ↓          ↓
               YES          NO
                  ↓          ↓
          ┌────────────┐  ┌──────────────┐
          │  MAIN APP  │  │ CREATE/JOIN  │
          │   FLOWS    │  │    FAMILY    │
          └────────────┘  └──────────────┘
                  ↓              ↓
          ┌──────────────────────────┐
          │  • Dashboard             │
          │  • Transactions          │
          │  • Family                │
          │  • Budgets               │
          │  • Settings              │
          └──────────────────────────┘
```

---

## 2. ONBOARDING FLOW (5 SCREENS)

> **Design Principle:** Minimum steps to first value moment. Target time-to-dashboard ≤ 90 seconds.
> Battery optimization and location permissions are deferred to contextual prompts post-onboarding.
> Tutorial content is replaced by an in-app first-time overlay on the Dashboard itself.

### 2.1 Complete Onboarding Journey

```
START: App First Launch
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SCREEN 1: PHONE NUMBER                                      │
│ • App logo + tagline: "Smart Family Expense Tracking"      │
│ • Country code selector (+91)                               │
│ • Phone number input (10 digits)                           │
│ • [Continue] button                                         │
│                                                             │
│ Validation:                                                 │
│ • Must be 10 digits                                         │
│ • Must be valid Indian number                              │
└─────────────────────────────────────────────────────────────┘
    ↓ Valid number entered → Firebase sends OTP
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SCREEN 2: OTP VERIFICATION                                  │
│ • "Enter 6-digit code sent to +91XXXXXXXXXX"               │
│ • 6-digit OTP input (auto-read if READ_SMS granted)        │
│ • Timer: "Resend OTP in 30s"                               │
│ • [Verify] button                                           │
│                                                             │
│ States:                                                     │
│ • Loading: Verifying OTP                                    │
│ • Error: "Invalid OTP" (3 attempts max, then 15-min lock)  │
│ • Success: Auto-advance to next screen                     │
└─────────────────────────────────────────────────────────────┘
    ↓ OTP Verified → User authenticated
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SCREEN 3: PROFILE SETUP                                     │
│ • "What should we call you?"                                │
│ • Name input field (required)                               │
│ • Avatar selection (8 options + emoji picker)              │
│ • [Continue] button                                         │
│                                                             │
│ Optional (expandable section):                              │
│ • Email input (for premium reports)                        │
│ • Primary UPI ID                                            │
└─────────────────────────────────────────────────────────────┘
    ↓ Profile created
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SCREEN 4: SMS PERMISSION + HISTORICAL IMPORT                │
│ • "Enable Automatic Transaction Tracking"                  │
│ • Icon: SMS with checkmark                                 │
│ • Benefit explanation:                                      │
│   - 95% less manual entry                                   │
│   - Instant expense tracking                               │
│   - Never miss a transaction                               │
│ • [Allow SMS Access] button → Android permission dialog    │
│ • [Continue without] (small link, shows manual-entry note) │
│                                                             │
│ Flow (permission GRANTED):                                  │
│ • Step A: Android READ_SMS permission granted              │
│ • Step B: Request notification listener permission         │
│   (Fallback channel if SMS permission is later restricted) │
│   - "Also allow notification access for backup tracking"   │
│   - [Allow Notification Access] or [Skip]                  │
│ • Step C: Historical SMS Import prompt:                    │
│   "Found 3 months of UPI transactions in your SMS.        │
│    Import them to see your spending history?"              │
│   - [Import History] → background parse (non-blocking)    │
│   - [Start Fresh] → skip import                            │
│ • Success animation → Auto-advance (1.5s)                 │
│                                                             │
│ Flow (permission DENIED):                                   │
│ • Check if Notification Listener can serve as fallback     │
│ • Prompt for notification access instead                   │
│ • Inform user: "You can manually add transactions anytime" │
└─────────────────────────────────────────────────────────────┘
    ↓ Permission handled
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SCREEN 5: FAMILY SETUP                                      │
│ • "How do you want to use Xpenz?"                          │
│                                                             │
│ ┌─────────────────────────────────────────┐               │
│ │ [CREATE FAMILY]                          │               │
│ │ Start tracking with your family          │               │
│ └─────────────────────────────────────────┘               │
│                                                             │
│ ┌─────────────────────────────────────────┐               │
│ │ [JOIN FAMILY]                            │               │
│ │ Have an invitation code?                 │               │
│ └─────────────────────────────────────────┘               │
│                                                             │
│ [Skip for now - Use solo]                                  │
│                                                             │
│ On "Join Family": inline code input field appears           │
└─────────────────────────────────────────────────────────────┘
    ↓
    ├── CREATE FAMILY ──► Family name input inline → DASHBOARD
    ├── JOIN FAMILY ────► Code entry inline → DASHBOARD
    └── SKIP ───────────► DASHBOARD
    ↓
┌─────────────────────────────────────────────────────────────┐
│ DASHBOARD (First Load)                                      │
│ • Celebration: "You're All Set! 🎉" (Toast/Snackbar)       │
│ • First-time overlay tooltip system (3 tooltips,           │
│   dismissed individually, not a blocking tutorial)         │
│ • If historical import running: "Importing your history... │
│   This takes a moment." (background progress indicator)    │
└─────────────────────────────────────────────────────────────┘
```

> **Deferred Contextual Prompts (Post-Onboarding):**
> - **Battery Optimization:** Triggered the FIRST TIME a transaction SMS arrives
>   but is detected late (>5 min delay). Shows a non-blocking card:
>   "We noticed a delayed transaction. Disable battery optimization
>    for reliable real-time tracking." → [Fix Now] → device-specific guide.
> - **Location Permission:** Prompted inline when user first views a transaction
>   detail and taps the location field. Not a blocking screen.
> - **Tutorial:** Replaced by contextual first-time tooltips on the Dashboard
>   for each widget (dismissible, never blocking).

### 2.2 Onboarding Edge Cases

```
EDGE CASE 1: Deep Link Invitation
    User clicks invitation link → App opens
    ↓
    Skip to Screen 1 (Welcome)
    ↓
    After auth (Screen 3), auto-fill invitation code
    ↓
    Show family info (name, members count, creator)
    ↓
    [Join Family] button
    ↓
    Skip tutorial → Dashboard

EDGE CASE 2: Phone Already Registered
    Screen 2 (Phone Number)
    ↓
    Backend detects existing account
    ↓
    Show: "This number is already registered"
    ↓
    Options:
    • [Sign In Instead]
    • [Use Different Number]

EDGE CASE 3: OTP Failures
    Invalid OTP (3 attempts)
    ↓
    Show error: "Invalid code"
    ↓
    After 3 failures: 15-minute lockout
    ↓
    Show: "Too many attempts. Try again in 15 min"

EDGE CASE 4: Mid-Onboarding Exit
    User exits at Screen 3 (Profile Setup)
    ↓
    Save progress: { step: 3, phone: "XXX" }
    ↓
    Next launch:
    ↓
    Show: "Welcome Back! Continue Setup (2/5 completed)"
    ↓
    Resume from Screen 3

EDGE CASE 5: All Permissions Denied
    SMS: Denied, Location: Denied, Battery: Not Done
    ↓
    Show warning: "Limited Mode"
    ↓
    "You'll need to enter transactions manually"
    ↓
    [Continue Anyway]
    ↓
    Can enable later in Settings
```

---

## 3. DASHBOARD FLOW

### 3.1 Main Dashboard Screen

```
┌─────────────────────────────────────────────────────────────┐
│ DASHBOARD                                                    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ HEADER                                                │   │
│ │ • Family selector dropdown                            │   │
│ │ • Date range selector (Today/Week/Month/Year/Custom) │   │
│ │ • Notification bell (with badge)                      │   │
│ │ • Settings icon                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ SPENDING SUMMARY CARD                                 │   │
│ │ ┌────────────┬────────────┬────────────┐            │   │
│ │ │   SPENT    │   INCOME   │  BALANCE   │            │   │
│ │ │  ₹12,450   │   ₹45,000  │  ₹32,550   │            │   │
│ │ └────────────┴────────────┴────────────┘            │   │
│ │ • Trend indicator: ↑ 12% vs last month              │   │
│ │ • Progress bar for monthly spending                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ACTIVE BUDGETS (Horizontal Scroll)                   │   │
│ │                                                       │   │
│ │ [Family Budget]  [Food Budget]  [Transport Budget]   │   │
│ │  78% used        65% used       45% used             │   │
│ │  ₹19,500/₹25K   ₹3,250/₹5K     ₹2,250/₹5K          │   │
│ │  🔴 Critical    🟡 Warning      🟢 Healthy           │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ CATEGORY BREAKDOWN (Pie Chart)                       │   │
│ │ • Food & Dining: 35% (₹4,358)                        │   │
│ │ • Transportation: 20% (₹2,490)                       │   │
│ │ • Shopping: 18% (₹2,241)                             │   │
│ │ • Entertainment: 12% (₹1,494)                        │   │
│ │ • Others: 15% (₹1,867)                               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ RECENT TRANSACTIONS (Last 10)                        │   │
│ │                                                       │   │
│ │ [Swiggy]              Today, 1:30 PM      -₹450      │   │
│ │ [Punjab Grill]        Today, 8:45 PM      -₹2,340    │   │
│ │ [Uber]                Yesterday, 9:15 AM  -₹180      │   │
│ │ [Amazon India]        Yesterday, 2:30 PM  -₹1,299    │   │
│ │ ...                                                   │   │
│ │ [View All Transactions →]                            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ FAMILY ACTIVITY (If Premium)                         │   │
│ │ • Papa spent ₹450 at Swiggy                          │   │
│ │ • Mom added manual entry: Groceries ₹850             │   │
│ │ • Sister spent ₹1,299 at Amazon                      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ BOTTOM NAVIGATION                                     │   │
│ │ [Dashboard] [Transactions] [Family] [Budgets] [More] │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ • FAB: [+ Add Transaction] (manual entry)                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Dashboard Interactions

```
USER ACTIONS:

1. Tap Family Selector
   ↓
   Show dropdown with all families
   ↓
   Select family → Reload dashboard data

2. Tap Date Range
   ↓
   Show date picker (Today/Week/Month/Year/Custom)
   ↓
   Update all cards with filtered data

3. Tap Budget Card
   ↓
   Navigate to Budget Detail Screen
   ↓
   Show progress, transactions, alerts

4. Tap Category in Pie Chart
   ↓
   Navigate to Category Transactions Screen
   ↓
   Show all transactions in that category

5. Tap Transaction
   ↓
   Navigate to Transaction Detail Screen
   ↓
   Show full details, edit, delete options

6. Tap FAB (+ Add Transaction)
   ↓
   Navigate to Manual Transaction Entry
   ↓
   Fill form → Save → Return to Dashboard

7. Pull to Refresh
   ↓
   Sync with cloud (if Premium)
   ↓
   Show loading indicator
   ↓
   Update UI with latest data
```

---

## 4. TRANSACTION FLOWS

### 4.1 Automatic Transaction Detection

```
SMS RECEIVED
    ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKGROUND: BroadcastReceiver Triggered                     │
│ • SMSReceiver receives SMS                                  │
│ • Extract: sender, body, timestamp                          │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Filter SMS                                          │
│ • Is sender a bank/UPI app? (Check whitelist)              │
│ • Contains keywords? (debited, credited, paid, etc.)        │
│ • Contains amount? (Rs., INR, ₹)                            │
│                                                             │
│ Decision:                                                   │
│ • YES → Continue to parsing                                │
│ • NO → Ignore SMS                                           │
└─────────────────────────────────────────────────────────────┘
    ↓ Transaction SMS detected
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Queue for Processing                               │
│ • Create WorkManager job: SMSProcessingWorker              │
│ • Pass: sender, body, timestamp                             │
│ • Constraint: None (process immediately)                    │
└─────────────────────────────────────────────────────────────┘
    ↓ Background worker started
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Parse SMS                                           │
│ • SMSParser.parse(sender, body, timestamp)                 │
│ • Try bank-specific patterns (95% accuracy)                │
│ • Fallback: Generic parsing (70% accuracy)                 │
│                                                             │
│ Extracted:                                                  │
│ • Amount: 450.0                                             │
│ • Merchant: "Punjab Grill Connaught"                       │
│ • Type: DEBIT                                               │
│ • Bank: "HDFC Bank"                                         │
│ • UPI ID: null                                              │
│ • Confidence: 0.95                                          │
└─────────────────────────────────────────────────────────────┘
    ↓ SMS parsed successfully
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Deduplication Check                                │
│ • Hash SMS body (SHA-256)                                   │
│ • Query database: SELECT COUNT(*) WHERE sms_hash = ?       │
│                                                             │
│ Decision:                                                   │
│ • Count > 0 → Duplicate, ignore                            │
│ • Count = 0 → New transaction, continue                    │
└─────────────────────────────────────────────────────────────┘
    ↓ Not a duplicate
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: ML Classification                                  │
│ • Extract features from merchant name                       │
│ • Run 3 models: LSTM, CNN, Transformer                     │
│ • Ensemble voting                                           │
│                                                             │
│ Result:                                                     │
│ • Category ID: 234 (North Indian - Butter Chicken)         │
│ • Confidence: 0.89                                          │
│ • Top-3: [234 (0.89), 235 (0.78), 12 (0.65)]              │
│ • Inference time: 145ms                                     │
└─────────────────────────────────────────────────────────────┘
    ↓ Category predicted
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Create Transaction Entity                          │
│ • ID: UUID.randomUUID()                                     │
│ • User ID: getCurrentUserId()                               │
│ • Family ID: getCurrentFamilyId()                           │
│ • Amount: 450.0                                             │
│ • Merchant: "Punjab Grill Connaught"                       │
│ • Category ID: 234                                          │
│ • Confidence: 0.89                                          │
│ • Type: DEBIT                                               │
│ • Timestamp: SMS timestamp                                  │
│ • Detected At: System.currentTimeMillis()                   │
│ • Is Synced: false                                          │
└─────────────────────────────────────────────────────────────┘
    ↓ Entity created
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Save to Local Database                             │
│ • TransactionDao.insertTransaction(entity)                  │
│ • Room emits Flow update                                    │
│ • UI receives update automatically                          │
└─────────────────────────────────────────────────────────────┘
    ↓ Saved locally
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Budget Progress Update                             │
│ • BudgetProgressCalculator.update(transaction)              │
│ • Check all active budgets                                  │
│ • Update progress for affected budgets                      │
│                                                             │
│ Threshold Check:                                            │
│ • Budget at 85% → Trigger alert (80% threshold crossed)    │
└─────────────────────────────────────────────────────────────┘
    ↓ Budget updated
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: Show Notification                                  │
│ • Title: "₹450 spent at Punjab Grill"                      │
│ • Body: "Food & Dining - North Indian"                     │
│ • Icon: Category emoji 🍛                                   │
│ • Action: Tap to view/edit                                  │
└─────────────────────────────────────────────────────────────┘
    ↓ User sees notification
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: Queue for Cloud Sync (If Premium)                 │
│ • Add to SyncQueue table                                    │
│ • SyncWorker will process (next sync cycle)                │
│ • Encrypt sensitive data before upload                      │
└─────────────────────────────────────────────────────────────┘
    ↓ Queued for sync
    ↓
COMPLETE: Transaction tracked successfully
Total time: ~500ms (SMS to notification)
```

### 4.2 Manual Transaction Entry

```
USER TAPS FAB (+)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ MANUAL ENTRY SCREEN                                         │
│                                                             │
│ [← Back]                           [Save]                   │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Transaction Type                             │           │
│ │ ( ) Expense  (•) Income  ( ) Refund         │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Amount *                                     │           │
│ │ ₹ [________]                                 │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Merchant/Payee Name                          │           │
│ │ [_____________________________]              │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Category *                                   │           │
│ │ [Select Category ▼]                          │           │
│ │   → Shows 520 categories in hierarchy        │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Date & Time *                                │           │
│ │ [Feb 24, 2026  8:45 PM ▼]                   │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Note (Optional)                              │           │
│ │ [_____________________________]              │           │
│ │ [_____________________________]              │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Add Receipt (Optional)                       │           │
│ │ [📷 Take Photo] [📁 Choose File]            │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│ ┌─────────────────────────────────────────────┐           │
│ │ Add to Budget (Optional)                     │           │
│ │ [Select Budget ▼]                            │           │
│ └─────────────────────────────────────────────┘           │
│                                                             │
│              [Cancel]  [Save Transaction]                   │
└─────────────────────────────────────────────────────────────┘

VALIDATION:
• Amount > 0 ✓
• Category selected ✓
• Date not in future ✓

USER TAPS SAVE
    ↓
LOADING (Saving transaction...)
    ↓
CREATE TRANSACTION
    ↓
SAVE TO DATABASE
    ↓
UPDATE BUDGETS
    ↓
SUCCESS ANIMATION ✓
    ↓
NAVIGATE BACK TO DASHBOARD
    ↓
SHOW SNACKBAR: "Transaction added successfully"
```

### 4.3 Transaction Detail & Edit

```
USER TAPS TRANSACTION FROM LIST
    ↓
┌─────────────────────────────────────────────────────────────┐
│ TRANSACTION DETAIL SCREEN                                    │
│                                                              │
│ [← Back]                              [⋮ Menu]              │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ MERCHANT HEADER                                       │   │
│ │ • Logo/Icon (if available)                            │   │
│ │ • Punjab Grill Connaught                              │   │
│ │ • Connaught Place, New Delhi                          │   │
│ │ • Map thumbnail (if location available)               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ AMOUNT                                                │   │
│ │ -₹450.00                                              │   │
│ │ 🔴 Expense                                            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ DETAILS                                               │   │
│ │ Category: 🍛 North Indian - Butter Chicken           │   │
│ │ Date: Feb 24, 2026, 8:45 PM                          │   │
│ │ Payment: HDFC Bank (UPI)                             │   │
│ │ Reference: UPI/412345678                             │   │
│ │ Detected: Auto (SMS)                                  │   │
│ │ Confidence: 89% ⭐⭐⭐⭐                               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ CATEGORY SUGGESTIONS (If confidence < 80%)           │   │
│ │ "Not sure about category? Try these:"                │   │
│ │ • South Indian (78%)                                  │   │
│ │ • Fine Dining (65%)                                   │   │
│ │ [Tap to change]                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ NOTE                                                  │   │
│ │ "Dinner with family"                                  │   │
│ │ [Edit]                                                │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ RECEIPT                                               │   │
│ │ [📄 View Receipt]                                     │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ BUDGETS AFFECTED                                      │   │
│ │ • Family Budget: +₹450 (now 78%)                     │   │
│ │ • Food Budget: +₹450 (now 65%)                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ [Edit Transaction]  [Delete Transaction]                    │
└─────────────────────────────────────────────────────────────┘

MENU OPTIONS (⋮):
• Edit Transaction
• Change Category
• Add Note
• Add Receipt
• Share Transaction
• Delete Transaction
```

---

## 5. FAMILY MANAGEMENT FLOW

### 5.1 Create Family Flow

```
USER TAPS "CREATE FAMILY" (from dashboard or onboarding)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ CREATE FAMILY SCREEN                                         │
│                                                              │
│ [← Back]                              [Create]              │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Family Name *                                         │   │
│ │ [_____________________________]                       │   │
│ │ Example: "The Sharmas", "Home Sweet Home"            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Choose Emoji                                          │   │
│ │ [👨‍👩‍👧‍👦] [👨‍👩‍👧] [👨‍👩‍👦‍👦] [🏠] [💰] [❤️] [Custom...]    │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Pick Color                                            │   │
│ │ [🔵] [🔴] [🟢] [🟡] [🟣] [🟠]                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Description (Optional)                                │   │
│ │ [_____________________________]                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│              [Cancel]  [Create Family]                       │
└─────────────────────────────────────────────────────────────┘

USER TAPS "CREATE FAMILY"
    ↓
VALIDATING...
    ↓
CREATING FAMILY...
    ↓
GENERATING INVITATION CODE (XP-XXXXX)
    ↓
ADDING USER AS ADMIN
    ↓
SYNCING TO CLOUD (if Premium)
    ↓
SUCCESS! ✓
    ↓
┌─────────────────────────────────────────────────────────────┐
│ FAMILY CREATED SUCCESS SCREEN                               │
│                                                              │
│ 🎉 Family Created!                                          │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 👨‍👩‍👧‍👦 The Sharmas                                        │   │
│ │                                                       │   │
│ │ Invitation Code: XP-A7K2M                            │   │
│ │ [Copy Code] [Share Code]                             │   │
│ │                                                       │   │
│ │ Valid for: 7 days                                     │   │
│ │ Max Members: 5 (Free) / Unlimited (Premium)          │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ Share via:                                                   │
│ [WhatsApp] [SMS] [Email] [More...]                         │
│                                                              │
│              [Go to Dashboard]                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Join Family Flow

```
USER TAPS "JOIN FAMILY" OR CLICKS INVITATION LINK
    ↓
┌─────────────────────────────────────────────────────────────┐
│ JOIN FAMILY SCREEN                                           │
│                                                              │
│ [← Back]                                                     │
│                                                              │
│ Enter Invitation Code                                        │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ XP - [___] [___] [___] [___] [___]                   │   │
│ │     (Auto-splits into boxes)                          │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│              [Verify Code]                                   │
└─────────────────────────────────────────────────────────────┘

USER ENTERS CODE: XP-A7K2M
    ↓
VALIDATING CODE...
    ↓
┌─────────────────────────────────────────────────────────────┐
│ VALIDATION CHECKS:                                           │
│ 1. Format valid? (XP-XXXXX) ✓                              │
│ 2. Code exists in database? ✓                              │
│ 3. Code expired? (> 7 days) ✗                              │
│ 4. Member limit reached? ✗                                  │
│ 5. Already a member? ✗                                      │
└─────────────────────────────────────────────────────────────┘
    ↓ All checks passed
    ↓
┌─────────────────────────────────────────────────────────────┐
│ FAMILY PREVIEW SCREEN                                        │
│                                                              │
│ You're invited to join:                                      │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 👨‍👩‍👧‍👦 The Sharmas                                        │   │
│ │                                                       │   │
│ │ Created by: Rahul Sharma                             │   │
│ │ Members: 3/5                                          │   │
│ │ Created: 2 days ago                                   │   │
│ │                                                       │   │
│ │ Current Members:                                      │   │
│ │ • Rahul Sharma (Admin)                               │   │
│ │ • Priya Sharma                                       │   │
│ │ • Arjun Sharma                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Your Nickname in Family                               │   │
│ │ [_____________________________]                       │   │
│ │ Example: Papa, Mom, Beta, etc.                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│              [Cancel]  [Join Family]                         │
└─────────────────────────────────────────────────────────────┘

USER TAPS "JOIN FAMILY"
    ↓
JOINING...
    ↓
ADDING AS MEMBER
    ↓
SYNCING WITH FAMILY
    ↓
SUCCESS! ✓
    ↓
NAVIGATE TO DASHBOARD (with new family selected)
    ↓
SHOW WELCOME: "Welcome to The Sharmas! 🎉"
```

### 5.3 Family Management Screen

```
USER NAVIGATES TO "FAMILY" TAB
    ↓
┌─────────────────────────────────────────────────────────────┐
│ FAMILY SCREEN                                                │
│                                                              │
│ [← Back]                              [⚙ Settings]          │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ FAMILY HEADER                                         │   │
│ │ 👨‍👩‍👧‍👦 The Sharmas                                        │   │
│ │ • 4 members • Created Feb 22, 2026                    │   │
│ │ • Code: XP-A7K2M (Expires in 5 days)                 │   │
│ │ [Regenerate Code] [Share]                            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ FAMILY SPENDING SUMMARY                               │   │
│ │ This Month: ₹45,230                                   │   │
│ │ Last Month: ₹38,450 (↑ 18%)                          │   │
│ │                                                       │   │
│ │ Top Spender: Papa (₹18,450)                          │   │
│ │ Most Active: Mom (127 transactions)                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ MEMBERS (4)                                           │   │
│ │                                                       │   │
│ │ ┌────────────────────────────────────────────────┐  │   │
│ │ │ 👨 Papa (You) • Admin                            │  │   │
│ │ │ ₹18,450 this month • 89 transactions            │  │   │
│ │ │ Last active: 5 mins ago                         │  │   │
│ │ └────────────────────────────────────────────────┘  │   │
│ │                                                       │   │
│ │ ┌────────────────────────────────────────────────┐  │   │
│ │ │ 👩 Mom • Member                                  │  │   │
│ │ │ ₹12,350 this month • 127 transactions           │  │   │
│ │ │ Last active: 1 hour ago                         │  │   │
│ │ │ [Promote to Admin] [Remove]                     │  │   │
│ │ └────────────────────────────────────────────────┘  │   │
│ │                                                       │   │
│ │ ┌────────────────────────────────────────────────┐  │   │
│ │ │ 🧒 Beta • Member                                 │  │   │
│ │ │ ₹8,230 this month • 45 transactions             │  │   │
│ │ │ Last active: Yesterday                          │  │   │
│ │ │ [Promote to Admin] [Remove]                     │  │   │
│ │ └────────────────────────────────────────────────┘  │   │
│ │                                                       │   │
│ │ ┌────────────────────────────────────────────────┐  │   │
│ │ │ 👧 Beti • Member                                 │  │   │
│ │ │ ₹6,200 this month • 32 transactions             │  │   │
│ │ │ Last active: 3 days ago                         │  │   │
│ │ │ [Promote to Admin] [Remove]                     │  │   │
│ │ └────────────────────────────────────────────────┘  │   │
│ │                                                       │   │
│ │ [+ Invite Member]                                     │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ RECENT ACTIVITY                                       │   │
│ │ • Papa spent ₹450 at Swiggy (2 mins ago)            │   │
│ │ • Mom added manual entry: Groceries ₹850 (1 hr ago) │   │
│ │ • Beta spent ₹180 at Uber (Yesterday)               │   │
│ │ • Beti spent ₹1,299 at Amazon (2 days ago)          │   │
│ │ [View All Activity →]                                │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

MEMBER LIMIT CHECKING:
If member count >= maxMembers (5 for free, ∞ for premium):
    Show: "Member limit reached (5/5)"
    Show upgrade prompt: "Upgrade to Premium for unlimited members"
    [Upgrade Now]
```

---

Due to length constraints, I'll create a **downloadable complete App Flow document** with all remaining flows (Budgets, Premium, Settings, etc.).

Would you like me to:

1. **Continue with remaining flows in next response** (Budget Flow, Premium Flow, Settings Flow)?
2. **Create a visual flowchart/diagram**?
3. **Create a downloadable document with all flows**?

Continuing with remaining app flows...

---

## 6. BUDGET MANAGEMENT FLOW

### 6.1 Create Budget Flow

```
USER TAPS "CREATE BUDGET" (from Budgets tab or Dashboard)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ CREATE BUDGET SCREEN - STEP 1: Type Selection               │
│                                                              │
│ [← Back]                                     [Next]          │
│                                                              │
│ What type of budget do you want to create?                  │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ [FAMILY BUDGET]                                       │   │
│ │ 👨‍👩‍👧‍👦 Track total family spending                        │   │
│ │ Perfect for: Overall spending control                │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ [CATEGORY BUDGET]                                     │   │
│ │ 🍽️ Limit spending in specific category                │   │
│ │ Perfect for: Food, Transport, Shopping, etc.         │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ [MEMBER BUDGET]                                       │   │
│ │ 👤 Set spending limit for family member              │   │
│ │ Perfect for: Kids' allowance, individual limits      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ 💡 Tip: You can create multiple budgets!                    │
└─────────────────────────────────────────────────────────────┘

USER SELECTS "CATEGORY BUDGET"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ CREATE BUDGET SCREEN - STEP 2: Details                      │
│                                                              │
│ [← Back]                              [Create Budget]        │
│                                                              │
│ Category Budget Setup                                        │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Budget Name                                           │   │
│ │ [Food & Dining Budget]                                │   │
│ │ (Auto-filled based on category, can edit)            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Select Category *                                     │   │
│ │ [🍽️ Food & Dining ▼]                                 │   │
│ │ → Opens hierarchical category selector               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Budget Amount *                                       │   │
│ │ ₹ [5,000]                                             │   │
│ │                                                       │   │
│ │ 💡 Suggestion based on last 3 months:                │   │
│ │    Average: ₹4,523/month                             │   │
│ │    [Use Suggestion]                                   │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Budget Period *                                       │   │
│ │ (•) Monthly  ( ) Weekly  ( ) Yearly                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Start Date                                            │   │
│ │ [Feb 24, 2026 ▼] (Default: Today)                   │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Alert Thresholds                                      │   │
│ │ Send alerts when budget reaches:                     │   │
│ │ ☑ 50% (₹2,500)                                       │   │
│ │ ☑ 80% (₹4,000)                                       │   │
│ │ ☑ 100% (₹5,000) - Budget exceeded                   │   │
│ │ ☑ 120% (₹6,000) - Severely exceeded                 │   │
│ │ [Customize Thresholds]                               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Notifications                                         │   │
│ │ ☑ Notify all family members                          │   │
│ │ ☑ Send push notifications                            │   │
│ │ ☐ Send email alerts (Premium)                        │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│              [Cancel]  [Create Budget]                       │
└─────────────────────────────────────────────────────────────┘

USER TAPS "CREATE BUDGET"
    ↓
VALIDATION:
✓ Amount > 0
✓ Category selected
✓ Period selected
    ↓
CREATING BUDGET...
    ↓
CALCULATING START/END DATES
    ↓
SAVING TO DATABASE
    ↓
SYNCING TO CLOUD (if Premium)
    ↓
SUCCESS! ✓
    ↓
┌─────────────────────────────────────────────────────────────┐
│ BUDGET CREATED SUCCESS                                       │
│                                                              │
│ 🎉 Budget Created Successfully!                             │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 🍽️ Food & Dining Budget                              │   │
│ │                                                       │   │
│ │ ₹5,000/month                                          │   │
│ │ Feb 24 - Mar 24, 2026                                │   │
│ │                                                       │   │
│ │ Current Spending: ₹850 (17%)                         │   │
│ │ Remaining: ₹4,150                                     │   │
│ │ Days Left: 28                                         │   │
│ │ Suggested Daily Limit: ₹148                          │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│              [View Budget]  [Create Another]                 │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Budget Detail & Monitoring

```
USER TAPS BUDGET CARD (from Dashboard or Budgets List)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ BUDGET DETAIL SCREEN                                         │
│                                                              │
│ [← Back]                              [⋮ Menu]              │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ BUDGET HEADER                                         │   │
│ │ 🍽️ Food & Dining Budget                              │   │
│ │ Feb 24 - Mar 24, 2026 (Monthly)                      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PROGRESS (85% - Critical) 🔴                          │   │
│ │ ┌──────────────────────────────────────────────┐    │   │
│ │ │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░│    │   │
│ │ └──────────────────────────────────────────────┘    │   │
│ │                                                       │   │
│ │ Spent: ₹4,250                                         │   │
│ │ Budget: ₹5,000                                        │   │
│ │ Remaining: ₹750                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ALERT STATUS                                          │   │
│ │ ⚠️ Warning: You've reached 85% of your budget!       │   │
│ │ Last alert sent: 50%, 80%                            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ INSIGHTS                                              │   │
│ │ • Days remaining: 18                                  │   │
│ │ • Suggested daily spend: ₹42 (to stay on budget)    │   │
│ │ • Current daily average: ₹236                        │   │
│ │ • Pace: You're spending 5.6x faster than suggested   │   │
│ │ • Prediction: Will exceed by ₹3,498 at current rate │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ SPENDING BREAKDOWN (This Month)                       │   │
│ │                                                       │   │
│ │ [Chart: Daily spending trend line]                    │   │
│ │                                                       │   │
│ │ By Sub-Category:                                      │   │
│ │ • Restaurants: ₹2,450 (58%)                          │   │
│ │ • Groceries: ₹980 (23%)                              │   │
│ │ • Food Delivery: ₹680 (16%)                          │   │
│ │ • Fast Food: ₹140 (3%)                               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ RECENT TRANSACTIONS (12 this period)                  │   │
│ │                                                       │   │
│ │ [Swiggy]              Today, 1:30 PM      -₹450      │   │
│ │ [Punjab Grill]        Today, 8:45 PM      -₹2,340    │   │
│ │ [DMart]               Yesterday           -₹980       │   │
│ │ [Dominos]             Feb 22              -₹340       │   │
│ │ ...                                                   │   │
│ │ [View All Transactions in Budget →]                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ALERTS HISTORY                                        │   │
│ │ • 80% threshold reached - Feb 23, 6:30 PM            │   │
│ │ • 50% threshold reached - Feb 20, 2:15 PM            │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ [Edit Budget]  [Pause Budget]  [View History]              │
└─────────────────────────────────────────────────────────────┘

MENU OPTIONS (⋮):
• Edit Budget
• Pause Budget
• View Alert Settings
• Export Budget Report (Premium)
• Delete Budget

REAL-TIME UPDATES:
When new transaction detected:
    ↓
BudgetProgressCalculator.updateProgressAfterTransaction()
    ↓
Check if transaction affects this budget
    ↓
Update progress percentage
    ↓
Check threshold crossing
    ↓
If threshold crossed:
    ↓
    Send notification to all family members
    ↓
    Update UI in real-time (Flow emission)
```

### 6.3 Budget Alert Flow

```
TRANSACTION DETECTED: ₹450 at Swiggy
    ↓
BudgetProgressCalculator.updateProgressAfterTransaction()
    ↓
Get all active budgets for family
    ↓
Check if transaction affects each budget:
    - Family Budget: YES (all transactions)
    - Food Budget: YES (category matches)
    - Transport Budget: NO (category doesn't match)
    ↓
UPDATE: Food Budget
    ↓
Previous: ₹3,800 / ₹5,000 (76%)
New: ₹4,250 / ₹5,000 (85%)
    ↓
CHECK THRESHOLDS:
    - 50%: Already sent ✓
    - 80%: Already sent ✓
    - 100%: Not reached yet
    ↓
THRESHOLD CROSSED: 80% → 85%
Last alert sent: 80%
    ↓
CREATE ALERT:
┌─────────────────────────────────────────────────────────────┐
│ BudgetAlert {                                                │
│   budgetId: "budget_123"                                     │
│   threshold: 80                                              │
│   currentPercentage: 85.0                                    │
│   amountSpent: 4250.0                                        │
│   amountBudget: 5000.0                                       │
│   daysRemaining: 18                                          │
│   latestTransaction: Swiggy ₹450                            │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
    ↓
SEND NOTIFICATIONS:
    ↓
┌─────────────────────────────────────────────────────────────┐
│ NOTIFICATION TO ALL FAMILY MEMBERS                           │
│                                                              │
│ 🔴 Budget Critical: Food & Dining                           │
│                                                              │
│ 85% used (₹4,250/₹5,000)                                    │
│ • 18 days left                                               │
│ • Latest: ₹450 at Swiggy                                    │
│                                                              │
│ [View Budget] [Dismiss]                                      │
└─────────────────────────────────────────────────────────────┘
    ↓
UPDATE DATABASE:
    - Save alert to history
    - Mark lastAlertSent: "85"
    ↓
SEND FCM TO OTHER DEVICES:
    - Papa's phone (current device - local notification)
    - Mom's phone (FCM)
    - Beta's phone (FCM)
    ↓
LOG ANALYTICS:
    Event: "budget_alert_triggered"
    Properties: {
      budget_id: "budget_123",
      budget_type: "CATEGORY",
      threshold: 85,
      days_remaining: 18
    }
```

### 6.4 Budget Exceeded Flow

```
WHEN BUDGET REACHES 100%:
    ↓
┌─────────────────────────────────────────────────────────────┐
│ HIGH-PRIORITY NOTIFICATION                                   │
│                                                              │
│ ❌ Budget Exceeded: Food & Dining                           │
│                                                              │
│ You've spent ₹5,120 out of ₹5,000 budget                   │
│ Over budget by: ₹120 (102%)                                │
│ 18 days remaining in this period                            │
│                                                              │
│ 💡 Suggestions:                                             │
│ • Reduce daily spending to ₹-7/day (not possible)          │
│ • Cook at home more often                                   │
│ • Use food delivery less                                    │
│                                                              │
│ [Increase Budget] [View Details] [Dismiss]                  │
└─────────────────────────────────────────────────────────────┘

WHEN BUDGET REACHES 120%:
    ↓
┌─────────────────────────────────────────────────────────────┐
│ CRITICAL ALERT                                               │
│                                                              │
│ 🚨 Severely Over Budget: Food & Dining                      │
│                                                              │
│ You've spent ₹6,250 out of ₹5,000 budget                   │
│ Over budget by: ₹1,250 (125%)                              │
│                                                              │
│ This is significantly above your planned spending.          │
│ Consider reviewing your budget or spending habits.          │
│                                                              │
│ [View Spending Details] [Adjust Budget]                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. PREMIUM SUBSCRIPTION FLOW

### 7.1 Premium Upgrade Triggers

```
TRIGGER SCENARIOS:

SCENARIO 1: Member Limit Reached
User tries to add 6th member (Free tier max: 5)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ UPGRADE PROMPT                                               │
│                                                              │
│ 🔒 Member Limit Reached                                     │
│                                                              │
│ You've reached the maximum of 5 family members on Free.     │
│ Upgrade to Premium for unlimited members!                   │
│                                                              │
│ Premium Benefits:                                            │
│ ✓ Unlimited family members                                  │
│ ✓ Cloud sync across devices                                │
│ ✓ Advanced analytics                                        │
│ ✓ PDF/Excel exports                                         │
│ ✓ Priority support                                          │
│                                                              │
│              [Upgrade to Premium]  [Maybe Later]            │
└─────────────────────────────────────────────────────────────┘

SCENARIO 2: Trying to Join 2nd Family
User tries to join second family (Free: 1 family max)
    ↓
Show upgrade prompt

SCENARIO 3: PDF Export Attempt
User taps "Export as PDF" button
    ↓
Show upgrade prompt with feature highlight

SCENARIO 4: 30-Day Proactive Prompt
After 30 days of usage with 487 transactions:
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PROACTIVE OFFER                                              │
│                                                              │
│ 🎉 You're a Power User!                                     │
│                                                              │
│ You've tracked 487 transactions in 30 days!                 │
│ Ready to unlock the full potential?                         │
│                                                              │
│ Premium at just ₹83/month:                                  │
│ • Cloud backup (never lose data)                           │
│ • Unlimited families & members                              │
│ • Advanced insights & predictions                           │
│ • Export reports (PDF, Excel)                               │
│                                                              │
│ Special Offer: Get 20% off (₹799/year)                     │
│ Valid for next 48 hours only!                               │
│                                                              │
│              [Claim Offer]  [Not Now]                       │
└─────────────────────────────────────────────────────────────┘

SCENARIO 5: Ad Banner (Non-Intrusive)
Small banner at bottom of dashboard (4% conversions)
```

### 7.2 Premium Purchase Flow

```
USER TAPS "UPGRADE TO PREMIUM"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PREMIUM PRICING SCREEN                                       │
│                                                              │
│ [← Back]                                                     │
│                                                              │
│ Choose Your Plan                                             │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 🏆 MOST POPULAR                                       │   │
│ │ ┌────────────────────────────────────────────────┐  │   │
│ │ │ ANNUAL PLAN                                     │  │   │
│ │ │                                                 │  │   │
│ │ │ ₹999/year                                       │  │   │
│ │ │ Just ₹83/month                                  │  │   │
│ │ │                                                 │  │   │
│ │ │ 💰 Save ₹789 (44% OFF)                         │  │   │
│ │ │                                                 │  │   │
│ │ │          [Select Annual Plan]                   │  │   │
│ │ └────────────────────────────────────────────────┘  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ MONTHLY PLAN                                          │   │
│ │                                                       │   │
│ │ ₹149/month                                            │   │
│ │ Billed monthly                                        │   │
│ │                                                       │   │
│ │ (₹1,788/year - 78% more expensive)                   │   │
│ │                                                       │   │
│ │          [Select Monthly Plan]                        │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ⭐ BEST VALUE                                         │   │
│ │ LIFETIME PLAN                                         │   │
│ │                                                       │   │
│ │ ₹4,999 one-time                                       │   │
│ │ Pay once, use forever!                                │   │
│ │                                                       │   │
│ │ (Equivalent to 5 years Annual)                        │   │
│ │                                                       │   │
│ │          [Select Lifetime Plan]                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ✓ 7-day money-back guarantee                                │
│ ✓ Cancel anytime (Annual/Monthly)                           │
│ ✓ Secure payment via Google Play                            │
│                                                              │
│ All plans include:                                           │
│ • Unlimited family members & families                       │
│ • Cloud sync across 5 devices                               │
│ • Advanced analytics & insights                             │
│ • PDF & Excel exports                                       │
│ • Email reports (weekly/monthly)                            │
│ • Priority support (<24hr)                                  │
│ • Ad-free experience                                        │
│ • Early access to new features                              │
└─────────────────────────────────────────────────────────────┘

USER SELECTS "ANNUAL PLAN"
    ↓
LOADING: Initializing purchase...
    ↓
┌─────────────────────────────────────────────────────────────┐
│ GOOGLE PLAY BILLING DIALOG                                   │
│                                                              │
│ [Google Play Native Dialog]                                  │
│                                                              │
│ Xpenz Premium - Annual                                       │
│ ₹999.00                                                      │
│                                                              │
│ Payment Method:                                              │
│ •••• 1234 (Visa)                                            │
│ [Change]                                                     │
│                                                              │
│ Total: ₹999.00                                               │
│                                                              │
│              [Cancel]  [Subscribe]                           │
└─────────────────────────────────────────────────────────────┘

USER TAPS "SUBSCRIBE"
    ↓
PROCESSING PAYMENT...
    ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND VERIFICATION                                         │
│                                                              │
│ 1. Google Play confirms purchase ✓                          │
│ 2. Receive purchase token                                    │
│ 3. Send to backend for verification                          │
│ 4. Backend validates with Google Play API                    │
│ 5. Activation successful ✓                                   │
└─────────────────────────────────────────────────────────────┘
    ↓ Purchase verified (< 5 seconds)
    ↓
UPDATE LOCAL DATABASE:
    - Set user.isPremium = true
    - Set user.premiumExpiresAt = now + 365 days
    - Create SubscriptionEntity
    ↓
SYNC TO FIRESTORE:
    - Update user premium status
    - Sync across all devices
    ↓
ENABLE PREMIUM FEATURES:
    - Unlock cloud sync
    - Remove member limits
    - Enable advanced features
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SUCCESS SCREEN                                               │
│                                                              │
│ 🎉 Welcome to Premium!                                      │
│                                                              │
│ [Celebration Animation - Lottie]                             │
│                                                              │
│ Your Premium features are now active:                        │
│ ✓ Cloud sync enabled                                        │
│ ✓ Unlimited members unlocked                                │
│ ✓ Advanced analytics ready                                  │
│ ✓ Export features available                                 │
│                                                              │
│ Receipt sent to: user@example.com                           │
│                                                              │
│              [Start Using Premium]                           │
└─────────────────────────────────────────────────────────────┘
    ↓ Auto-redirect after 3 seconds
    ↓
NAVIGATE TO DASHBOARD
    ↓
SHOW SNACKBAR: "Premium activated! ⭐"
    ↓
SEND ANALYTICS:
    Event: "premium_purchase_completed"
    Properties: {
      plan: "ANNUAL",
      price: 999,
      purchase_token: "xxx"
    }
```

### 7.3 Premium Management Flow

```
USER NAVIGATES TO: Settings → Premium Subscription
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PREMIUM SUBSCRIPTION MANAGEMENT                              │
│                                                              │
│ [← Back]                                                     │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ SUBSCRIPTION STATUS                                   │   │
│ │ ⭐ Premium Active                                     │   │
│ │                                                       │   │
│ │ Plan: Annual (₹999/year)                             │   │
│ │ Next Renewal: Feb 24, 2027                           │   │
│ │ Payment Method: •••• 1234 (Visa)                     │   │
│ │ Auto-Renew: ON                                        │   │
│ │                                                       │   │
│ │ [View Receipt] [Update Payment]                      │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ USAGE STATISTICS                                      │   │
│ │ • 8 family members (vs 5 limit on Free)              │   │
│ │ • Synced across 3 devices                            │   │
│ │ • 12 AI insights generated this month                │   │
│ │ • 6 PDF reports exported                             │   │
│ │ • Cloud backup: 2.3 MB used                          │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PREMIUM FEATURES                                      │   │
│ │ ✓ Unlimited family members                           │   │
│ │ ✓ Cloud sync (5 devices)                             │   │
│ │ ✓ Advanced analytics                                 │   │
│ │ ✓ PDF/Excel exports                                  │   │
│ │ ✓ Email reports                                      │   │
│ │ ✓ Priority support                                   │   │
│ │ ✓ Ad-free experience                                 │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ BILLING HISTORY                                       │   │
│ │ • Feb 24, 2026: ₹999 (Annual Plan)                   │   │
│ │ • [View All Invoices]                                │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ [Change Plan] [Cancel Subscription]                         │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Cancellation Flow (with Retention)

```
USER TAPS "CANCEL SUBSCRIPTION"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: CONFIRMATION                                         │
│                                                              │
│ Cancel Premium Subscription?                                 │
│                                                              │
│ ⚠️ You will lose access to:                                 │
│ • Unlimited family members (must remove 3 members)          │
│ • Cloud sync across devices                                 │
│ • Advanced analytics & insights                             │
│ • PDF/Excel export features                                 │
│ • Email reports                                             │
│                                                              │
│ Your subscription is active until: Feb 24, 2027             │
│ (8 months remaining = ₹664 value)                           │
│                                                              │
│              [Keep Premium]  [Continue Cancel]              │
└─────────────────────────────────────────────────────────────┘

USER TAPS "CONTINUE CANCEL"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: REASON COLLECTION                                    │
│                                                              │
│ Help us improve. Why are you cancelling?                    │
│                                                              │
│ ( ) Too expensive                                           │
│ ( ) Not using the features                                  │
│ ( ) Missing features I need                                 │
│ ( ) Technical issues                                        │
│ ( ) Found a better alternative                              │
│ ( ) Temporary - will re-subscribe later                     │
│ ( ) Other: [___________________]                            │
│                                                              │
│ Optional: Tell us more                                       │
│ [_________________________________]                          │
│ [_________________________________]                          │
│                                                              │
│              [Back]  [Continue]                              │
└─────────────────────────────────────────────────────────────┘

USER SELECTS "TOO EXPENSIVE"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: RETENTION OFFER                                      │
│                                                              │
│ 🎁 Wait! Special Offer Just For You                         │
│                                                              │
│ We'd love to keep you as a Premium member.                  │
│ Here's an exclusive offer:                                   │
│                                                              │
│ ┌────────────────────────────────────────────────────┐     │
│ │ 🎉 3 MONTHS FREE                                    │     │
│ │                                                     │     │
│ │ Continue Premium at no cost!                       │     │
│ │ (₹375 value)                                       │     │
│ │                                                     │     │
│ │ • Keep all Premium features                        │     │
│ │ • No payment until May 24, 2026                    │     │
│ │ • Cancel anytime during free period                │     │
│ │                                                     │     │
│ │ This is a one-time offer!                          │     │
│ └────────────────────────────────────────────────────┘     │
│                                                              │
│ [Accept Offer] [No Thanks, Cancel Anyway]                   │
└─────────────────────────────────────────────────────────────┘

IF USER ACCEPTS OFFER (20% acceptance rate):
    ↓
    Extend subscription by 3 months at no charge
    ↓
    Show success message
    ↓
    Navigate back to Premium Management
    ↓
    ANALYTICS: "retention_offer_accepted"

IF USER REJECTS OFFER:
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: FINAL CONFIRMATION                                   │
│                                                              │
│ Final Step: Confirm Cancellation                            │
│                                                              │
│ ⚠️ Important Information:                                   │
│ • You'll lose Premium benefits immediately                  │
│ • Must remove 3 family members (limit: 5)                   │
│ • Cloud sync will stop                                      │
│ • Cannot re-activate mid-period                             │
│                                                              │
│ Your access continues until: Feb 24, 2027                   │
│ No refund for remaining period (policy)                     │
│                                                              │
│ Type "CANCEL" to confirm:                                   │
│ [_________________________________]                          │
│                                                              │
│              [Go Back]  [Confirm Cancellation]              │
└─────────────────────────────────────────────────────────────┘

USER TYPES "CANCEL" AND CONFIRMS
    ↓
PROCESSING CANCELLATION...
    ↓
STEPS:
1. Disable auto-renewal in Google Play ✓
2. Update subscription status to CANCELLED ✓
3. Keep premium features active until expiry date ✓
4. Send confirmation email ✓
5. Log analytics ✓
    ↓
┌─────────────────────────────────────────────────────────────┐
│ CANCELLATION CONFIRMED                                       │
│                                                              │
│ Your Premium subscription has been cancelled.               │
│                                                              │
│ • Auto-renewal: OFF                                         │
│ • Premium access until: Feb 24, 2027                        │
│ • No further charges                                        │
│                                                              │
│ Confirmation sent to: user@example.com                      │
│                                                              │
│ We're sad to see you go! 😢                                 │
│ You can re-subscribe anytime.                               │
│                                                              │
│              [Back to Settings]                              │
└─────────────────────────────────────────────────────────────┘
    ↓
ANALYTICS LOG:
    Event: "premium_cancelled"
    Properties: {
      reason: "too_expensive",
      retention_offer_shown: true,
      retention_offer_accepted: false,
      days_active: 127,
      remaining_value: 664
    }
```

---

## 8. SETTINGS FLOW

### 8.1 Settings Screen Structure

```
USER TAPS "SETTINGS" (from bottom nav or menu)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SETTINGS SCREEN                                              │
│                                                              │
│ [← Back]                                                     │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PROFILE SECTION                                       │   │
│ │ [👤 Avatar]  Rahul Sharma                            │   │
│ │             +91 98765 43210                           │   │
│ │             rahul@example.com                         │   │
│ │                                                       │   │
│ │ ⭐ Premium Member (Expires: Feb 24, 2027)            │   │
│ │ [Edit Profile]                                        │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PREMIUM                                               │   │
│ │ ⭐ Premium Subscription                               │   │
│ │    Manage your subscription                          │   │
│ │    →                                                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ GENERAL                                               │   │
│ │ 👨‍👩‍👧‍👦 Family Management                                 │   │
│ │    Manage families & members                         │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 🔔 Notifications                                      │   │
│ │    Configure alerts & notifications                  │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 📊 Data & Sync                                        │   │
│ │    Cloud sync, backup & restore                      │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 🔐 Privacy & Security                                │   │
│ │    Permissions, privacy controls                     │   │
│ │    →                                                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ PREFERENCES                                           │   │
│ │ 💱 Currency                                           │   │
│ │    INR (₹) →                                          │   │
│ │                                                       │   │
│ │ 🌙 Theme                                              │   │
│ │    Light / Dark / Auto →                             │   │
│ │                                                       │   │
│ │ 🌐 Language                                           │   │
│ │    English →                                          │   │
│ │                                                       │   │
│ │ 📅 Date Format                                        │   │
│ │    DD/MM/YYYY →                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ SUPPORT                                               │   │
│ │ 💬 Help & Support                                     │   │
│ │    FAQs, contact support                             │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ ⭐ Rate Xpenz                                         │   │
│ │    Share feedback on Play Store                      │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 📱 Share Xpenz                                        │   │
│ │    Invite friends & family                           │   │
│ │    →                                                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ABOUT                                                 │   │
│ │ ℹ️ About Xpenz                                        │   │
│ │    Version 1.0.0 (Build 10001)                       │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 📄 Terms & Privacy                                    │   │
│ │    Terms of Service, Privacy Policy                  │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 🔓 Open Source Licenses                               │   │
│ │    Third-party licenses                              │   │
│ │    →                                                  │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ DANGER ZONE                                           │   │
│ │ 🚪 Sign Out                                           │   │
│ │    →                                                  │   │
│ │                                                       │   │
│ │ 🗑️ Delete Account                                     │   │
│ │    Permanently delete all data                       │   │
│ │    →                                                  │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. GROUPS & SPLITS FLOW (Post-MVP, Option B)

> Splitwise-style bill splitting. **Separate subsystem from Family** (PRD F8,
> Backend Schema §3.8, TRD Tables 12–17). Groups = ad-hoc circles you split with;
> Family = your one shared household. A user can have many groups + many friends.

### 9.1 Add Friend Flow

```
Splits Tab → "Add friend"
  ├─ Pick from contacts (matched via phone_hash) / enter UPI / share invite link
  ├─ If friend is an Xpenzo user → PENDING request → they ACCEPT
  ├─ If not → invite link (deep link); placeholder friend until they join
  └─ Friend appears under "Friends" with ₹0 balance
```

### 9.2 Create Group Flow

```
Splits Tab → "+ New group"
  ├─ Name (e.g., "Goa Trip 2026"), type (TRIP/HOME/COUPLE/OTHER), emoji
  ├─ Add members (existing friends or invite by code GRP-XXXXX)
  ├─ Toggle "Simplify debts" (default ON)
  └─ Group created → creator is ADMIN → empty expense list
```

### 9.3 Split a Transaction / Add Expense Flow

```
Entry A: Transaction detail → "Split this"   (pre-fills amount + category)
Entry B: Group → "+ Add expense"
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ SPLIT SHEET                                                 │
│ ├─ Description, total amount, category (520 taxonomy)       │
│ ├─ Paid by: [You ▼]                                         │
│ ├─ Participants: ☑ You ☑ Rahul ☑ Priya ☑ Aman               │
│ ├─ Split type: ( EQUAL ) ( EXACT ) ( PERCENT ) ( SHARES )   │
│ │     EQUAL → ₹3000 ÷ 4 = ₹750 each (leftover paise → payer)│
│ └─ [ Save split ]                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
  ├─ SplitExpense + per-user shares written (synced)
  ├─ If created from a transaction → links transaction_id,
  │    sets reimbursable_amount so the budget isn't double-counted
  └─ Balances recompute → "You are owed ₹2,250"
```

### 9.4 View Balances Flow ("Who owes whom")

```
Splits Tab
  ├─ Top: net across everything ("Overall, you are owed ₹3,470")
  ├─ Per group card: "Goa Trip — you are owed ₹1,250"
  ├─ Per friend row: "Rahul owes you ₹450" / "You owe Priya ₹120"
  └─ Group detail → if simplify_debts ON, shows minimized plan:
        "Aman → You ₹750", "Priya → Rahul ₹300"  (≤ N-1 payments)
```

### 9.5 Settle Up Flow

```
Group/Friend → "Settle up"
  ├─ Prefilled from simplified plan (who pays whom, amount)
  ├─ Method:
  │     ├─ CASH → record only
  │     └─ UPI  → open upi://pay?pa=<vpa>&am=<amt> deep link → capture ref
  ├─ Settlement created with status PENDING
  ├─ Payee gets notification → confirms receipt → status CONFIRMED
  └─ Balances recompute → pair nets to ₹0
```

### 9.6 Edge Cases

```
├─ Friend not yet on Xpenzo → split is held against a placeholder; reconciles on join
├─ Expense edited/deleted → balances recompute; settled expenses warn before edit
├─ Member leaves group with non-zero balance → must settle or admin writes off
├─ Currency: one currency per group (MVP of feature); multi-currency deferred
└─ Offline → all writes queue in Room sync_queue; balances computed locally meanwhile
```

---

This completes the **COMPLETE APP FLOW DOCUMENTATION**!

## 📊 **SUMMARY OF ALL FLOWS:**

✅ **1. High-Level App Flow** (Entry point logic)

✅ **2. Onboarding Flow** (5 screens + deferred prompts + edge cases)

✅ **3. Dashboard Flow** (Main screen + interactions)

✅ **4. Transaction Flows** (Automatic + Manual + Detail)

✅ **5. Family Management Flow** (Create + Join + Manage)

✅ **6. Budget Management Flow** (Create + Monitor + Alerts)

✅ **7. Premium Subscription Flow** (Purchase + Management + Cancellation)

✅ **8. Settings Flow** (Complete settings structure)

✅ **9. Groups & Splits Flow** (Add friend + Create group + Split + Balances + Settle up) — *post-MVP, Option B*

Would you like me to:

1. **Create a visual flowchart** (using Mermaid diagrams)?
2. **Create a downloadable document** with all flows?
3. **Add more detailed flows** (notifications, deep linking, error states)?

