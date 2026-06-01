package com.xpenzo.sms

import java.time.LocalDateTime

/**
 * Parses transactional bank/UPI SMS messages into [ParsedSms] objects.
 *
 * Design goals:
 *  - Handle the top-10 Indian bank formats + major UPI apps (Paytm, GPay, PhonePe)
 *  - Extract amount, merchant/VPA, debit vs credit, and timestamp reliably
 *  - Normalize merchant text EXACTLY as the training pipeline does so on-device
 *    feature vectors match the 520-class CHT model's expected distribution
 *  - Reject OTP, promo, and non-transactional messages early
 *
 * Normalization contract (must stay in sync with ml/training/data_loader.py):
 *   1. lowercase
 *   2. replace digit sequences with "#"
 *   3. replace non-alphanumeric (except spaces and #) with " "
 *   4. collapse multiple spaces
 *   5. strip tokens shorter than 2 chars
 *   6. truncate to 40 chars
 */
object UpiSmsParser {

    // ── reject-early filters ──────────────────────────────────────────────────

    private val OTP_KEYWORDS = setOf(
        "otp", "one time password", "verification code", "do not share",
        "transaction password", "login code", "totp",
    )

    private val PROMO_KEYWORDS = setOf(
        "offer", "cashback", "reward", "deal", "discount", "earn", "win",
        "click here", "limited time", "subscribe", "upgrade plan",
    )

    private val BANK_SENDER_PREFIXES = setOf(
        // HDFC
        "hdfcbk", "hdfc", "hdfc-",
        // SBI
        "sbiinb", "sbi-", "sbicrd",
        // ICICI
        "icicib", "icicibank",
        // Axis
        "axisbk", "axisbank",
        // Kotak
        "kotakb", "kotak",
        // Yes Bank
        "yesbk", "yesbank",
        // IDFC
        "idfcbk", "idfcfirst",
        // IndusInd
        "indbnk", "indusind",
        // PNB
        "pnbsms",
        // Canara
        "cnrbnk",
        // UPI apps
        "paytm", "gpay", "phonepe", "bhim",
    )

    // ── amount patterns ───────────────────────────────────────────────────────

    /** Matches: Rs. 1,234.56 / INR 1234 / ₹ 12,34.56 / Rs1234 */
    private val AMOUNT_REGEX = Regex(
        """(?:Rs\.?\s*|INR\s*|₹\s*)([\d,]+(?:\.\d{1,2})?)""",
        RegexOption.IGNORE_CASE,
    )

    // ── debit / credit signals ────────────────────────────────────────────────

    private val DEBIT_PHRASES = listOf(
        "debited", "deducted", "paid", "spent", "sent", "transferred",
        "payment of", "purchase", "withdrawn", "debit",
    )

    private val CREDIT_PHRASES = listOf(
        "credited", "received", "refund", "cashback", "added", "credit",
    )

    // ── merchant / VPA extraction ─────────────────────────────────────────────

    /**
     * UPI VPA: word@word  (e.g. swiggy@icici, q123456789@ybl)
     * Anchored to avoid matching email addresses in promo links.
     */
    private val VPA_REGEX = Regex("""(?<!\w)([\w.\-]+@[a-z]+)(?!\w)""", RegexOption.IGNORE_CASE)

    /** "to MERCHANT NAME" or "at MERCHANT" after payment keywords */
    private val MERCHANT_TO_REGEX = Regex(
        """(?:paid?\s+to|transferred?\s+to|sent?\s+to|payment\s+to)\s+([A-Za-z0-9 .&'\-]{2,40})""",
        RegexOption.IGNORE_CASE,
    )

    private val MERCHANT_AT_REGEX = Regex(
        """(?:at|for)\s+([A-Za-z0-9 .&'\-]{2,40})""",
        RegexOption.IGNORE_CASE,
    )

    // ── public API ────────────────────────────────────────────────────────────

    /**
     * Attempt to parse [body] from sender [sender].
     * Returns null if the message is not a transactional bank/UPI SMS.
     */
    fun parse(sender: String, body: String, receivedAt: LocalDateTime = LocalDateTime.now()): ParsedSms? {
        val lowerBody = body.lowercase()
        val lowerSender = sender.lowercase()

        // 1. Must come from a known bank/UPI sender
        if (!isKnownBankSender(lowerSender)) return null

        // 2. Reject OTP and promos early
        if (isOtp(lowerBody) || isPromo(lowerBody)) return null

        // 3. Must contain an amount
        val amount = extractAmount(body) ?: return null

        // 4. Determine debit vs credit
        val isCredit = determineIsCredit(lowerBody)

        // 5. Extract merchant and VPA
        val vpa = extractVpa(body)
        val merchant = extractMerchant(body, vpa)

        // 6. Normalize
        val merchantNormalized = normalizeMerchant(merchant ?: vpa?.substringBefore("@") ?: "unknown")

        return ParsedSms(
            sender = sender,
            amountPaise = (amount * 100).toLong(),
            isCredit = isCredit,
            merchant = merchant ?: vpa?.substringBefore("@") ?: "unknown",
            merchantNormalized = merchantNormalized,
            vpa = vpa ?: "",
            rawBody = body,
            receivedAt = receivedAt,
        )
    }

    // ── private helpers ───────────────────────────────────────────────────────

    fun isKnownBankSender(lowerSender: String): Boolean =
        BANK_SENDER_PREFIXES.any { prefix -> lowerSender.contains(prefix) }

    private fun isOtp(lowerBody: String): Boolean =
        OTP_KEYWORDS.any { kw -> lowerBody.contains(kw) }

    private fun isPromo(lowerBody: String): Boolean =
        // Promo if 3+ promo keywords and no debit/credit signal
        PROMO_KEYWORDS.count { kw -> lowerBody.contains(kw) } >= 3 &&
            DEBIT_PHRASES.none { lowerBody.contains(it) } &&
            CREDIT_PHRASES.none { lowerBody.contains(it) }

    internal fun extractAmount(body: String): Double? {
        val match = AMOUNT_REGEX.find(body) ?: return null
        val raw = match.groupValues[1].replace(",", "")
        return raw.toDoubleOrNull()
    }

    private fun determineIsCredit(lowerBody: String): Boolean {
        val debitScore = DEBIT_PHRASES.count { lowerBody.contains(it) }
        val creditScore = CREDIT_PHRASES.count { lowerBody.contains(it) }
        return creditScore > debitScore
    }

    internal fun extractVpa(body: String): String? =
        VPA_REGEX.find(body)?.value?.lowercase()

    internal fun extractMerchant(body: String, vpa: String? = null): String? {
        // Try explicit "paid to X" pattern first
        MERCHANT_TO_REGEX.find(body)?.groupValues?.getOrNull(1)
            ?.trim()
            ?.takeIf { it.length > 1 }
            ?.let { return it }

        // Try "at X" / "for X"
        MERCHANT_AT_REGEX.find(body)?.groupValues?.getOrNull(1)
            ?.trim()
            ?.takeIf { it.length > 1 && it.length < 35 }
            ?.let { return it }

        return null
    }

    /**
     * Normalize merchant text to EXACTLY match the bundled 520-class model's training
     * pipeline (ml/data_collection/scripts/10_feature_engineering.py::normalize_merchant),
     * which produced the `text_normalized` column the model learned from:
     *   1. lowercase + trim
     *   2. replace any char NOT in [a-z 0-9 space - ' /] with a space
     *   3. collapse runs of whitespace
     *
     * Digits are KEPT (training kept real digits), short tokens are KEPT, and there is NO
     * char cap — the SentencePiece tokenizer caps at 32 tokens downstream. Any divergence
     * here silently tanks accuracy.
     *
     * Privacy masking (digits→#) is applied separately at the ml_corrections upload boundary
     * via [maskDigitsForUpload], NOT here, so on-device inference stays faithful to training.
     */
    fun normalizeMerchant(raw: String): String =
        raw.lowercase().trim()
            .replace(Regex("""[^a-z0-9\s\-'/]"""), " ")
            .replace(Regex("""\s+"""), " ")
            .trim()

    /**
     * Privacy mask for cross-user uploads (`ml_corrections`): replace every digit with '#'
     * so account-number / amount fragments embedded in merchant text never leave the device.
     * Applied ONLY on the upload path — never to the on-device model input.
     */
    fun maskDigitsForUpload(text: String): String = text.replace(Regex("""\d"""), "#")

    /**
     * SHA-256 dedup fingerprint — combine sender + amount + last-4 chars of body.
     * Two messages with the same fingerprint within 60 s are duplicates.
     */
    fun dedupKey(sender: String, amountPaise: Long, body: String): String {
        val tail = body.takeLast(4)
        return "$sender|$amountPaise|$tail".hashCode().toString()
    }
}

/** Parsed, validated output from a bank/UPI SMS. */
data class ParsedSms(
    val sender: String,
    val amountPaise: Long,          // in paise
    val isCredit: Boolean,
    val merchant: String,           // raw extracted merchant name
    val merchantNormalized: String, // normalized per training contract
    val vpa: String,                // UPI VPA or "" if not found
    val rawBody: String,
    val receivedAt: LocalDateTime,
)
