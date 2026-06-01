package com.xpenzo.sms

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Fixture-driven unit tests for [UpiSmsParser].
 *
 * Each fixture is a real-world SMS body (numbers anonymized) from one of the major
 * Indian banks and UPI apps. The test verifies:
 *   - amount extraction (paise)
 *   - debit vs credit direction
 *   - VPA extraction where present
 *   - merchant normalization
 *   - OTP/promo rejection
 */
class UpiSmsParserTest {

    // ── HDFC ──────────────────────────────────────────────────────────────────

    @Test
    fun hdfc_upiDebit_swiggy() {
        val parsed = parse(
            sender = "HDFCBK",
            body = "Rs.450.00 debited from your A/c XXXX1234 on 22-05-26. Info: UPI/swiggy@icici/Swiggy Order. Avl Bal:Rs.12,345.00",
        )
        assertNotNull(parsed)
        assertEquals(45_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("swiggy@icici", parsed.vpa)
    }

    @Test
    fun hdfc_upiDebit_zomato() {
        val parsed = parse(
            sender = "HDFC-",
            body = "INR 320.00 debited from A/c **1234 on 22-05-26;UPI Ref No 123456789012.Info: zomato@icici-Zomato Technologies.",
        )
        assertNotNull(parsed)
        assertEquals(32_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("zomato@icici", parsed.vpa)
    }

    @Test
    fun hdfc_creditAlert() {
        val parsed = parse(
            sender = "HDFCBK",
            body = "Rs.5,000.00 credited to A/c XXXX1234 on 22-05-26. Info: NEFT from JOHN DOE. Avl Bal:Rs.17,345.00",
        )
        assertNotNull(parsed)
        assertEquals(500_000L, parsed!!.amountPaise)
        assertTrue(parsed.isCredit)
    }

    @Test
    fun hdfc_otp_isRejected() {
        val parsed = parse(
            sender = "HDFCBK",
            body = "Your OTP for transaction is 123456. Do not share this OTP with anyone. Valid for 10 mins.",
        )
        assertNull(parsed)
    }

    // ── SBI ───────────────────────────────────────────────────────────────────

    @Test
    fun sbi_upiDebit_merchant() {
        val parsed = parse(
            sender = "SBIINB",
            body = "Your A/c XXXX1234 is debited by Rs 1,200.00 on 22-05-26. UPI Ref: 123456789012. Paid to petrol@sbi.",
        )
        assertNotNull(parsed)
        assertEquals(120_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("petrol@sbi", parsed.vpa)
    }

    @Test
    fun sbi_atm_withdrawal() {
        val parsed = parse(
            sender = "SBI-",
            body = "Rs.2,000.00 withdrawn from A/c no XXXXXXXX1234 at ATM on 22-05-26.",
        )
        assertNotNull(parsed)
        assertEquals(200_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
    }

    @Test
    fun sbi_credit() {
        val parsed = parse(
            sender = "SBIINB",
            body = "Your A/c XXXX1234 is credited by Rs 2,500.00 on 22-05-26 by NEFT from JANE DOE. Available Balance: Rs 15,000.00",
        )
        assertNotNull(parsed)
        assertTrue(parsed!!.isCredit)
        assertEquals(250_000L, parsed.amountPaise)
    }

    // ── ICICI ─────────────────────────────────────────────────────────────────

    @Test
    fun icici_upiDebit_amazon() {
        val parsed = parse(
            sender = "ICICIB",
            body = "ICICI Bank: Rs 899.00 debited from your account ending 1234 for UPI payment to amazon@apl on 22-05-26. UPI Ref 123456789.",
        )
        assertNotNull(parsed)
        assertEquals(89_900L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("amazon@apl", parsed.vpa)
    }

    @Test
    fun icici_creditCard_payment() {
        val parsed = parse(
            sender = "ICICIBANK",
            body = "₹3,499.00 spent on your ICICI Bank Credit Card ending 1234 at BIGBASKET on 22-May-26. Available limit: ₹45,501.00",
        )
        assertNotNull(parsed)
        assertEquals(349_900L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
    }

    @Test
    fun icici_otp_isRejected() {
        val parsed = parse(
            sender = "ICICIB",
            body = "Your ICICI Bank One Time Password (OTP) is 765432. It is valid for 10 minutes. Do not share with anyone.",
        )
        assertNull(parsed)
    }

    // ── Axis ──────────────────────────────────────────────────────────────────

    @Test
    fun axis_upiDebit() {
        val parsed = parse(
            sender = "AXISBK",
            body = "Rs.575.00 paid to ola@olamoney from Axis Bank A/c XX1234 on 22-May-26. UPI Ref: 123456789012.",
        )
        assertNotNull(parsed)
        assertEquals(57_500L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("ola@olamoney", parsed.vpa)
    }

    @Test
    fun axis_credit() {
        val parsed = parse(
            sender = "AXISBANK",
            body = "Axis Bank: Rs 10,000.00 received in A/c XX5678 from JOHN DOE on 22-05-26. Avl Bal: Rs 35,000.",
        )
        assertNotNull(parsed)
        assertTrue(parsed!!.isCredit)
        assertEquals(1_000_000L, parsed.amountPaise)
    }

    // ── Kotak ─────────────────────────────────────────────────────────────────

    @Test
    fun kotak_upiDebit() {
        val parsed = parse(
            sender = "KOTAKB",
            body = "Dear Customer, Rs.250.00 has been debited from your Kotak Bank account XXXX1234 for UPI payment to bigbazaar@kotak on 22-05-26.",
        )
        assertNotNull(parsed)
        assertEquals(25_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("bigbazaar@kotak", parsed.vpa)
    }

    // ── Paytm ─────────────────────────────────────────────────────────────────

    @Test
    fun paytm_walletDebit() {
        val parsed = parse(
            sender = "PAYTM",
            body = "You paid Rs. 180 to DOMINOS PIZZA using Paytm UPI. UPI Ref: 123456789012. Your Paytm balance: Rs. 420.",
        )
        assertNotNull(parsed)
        assertEquals(18_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
    }

    @Test
    fun paytm_cashbackCredit() {
        val parsed = parse(
            sender = "PAYTM",
            body = "₹ 50 cashback credited to your Paytm wallet! Your balance is now Rs. 470.",
        )
        // Cashback is a credit
        assertNotNull(parsed)
        assertTrue(parsed!!.isCredit)
    }

    // ── GPay ──────────────────────────────────────────────────────────────────

    @Test
    fun gpay_sentMoney() {
        val parsed = parse(
            sender = "GPAY",
            body = "You sent ₹500 to john.doe@okicici via Google Pay. UPI transaction ID: 123456789012.",
        )
        assertNotNull(parsed)
        assertEquals(50_000L, parsed!!.amountPaise)
        assertTrue(!parsed.isCredit)
        assertEquals("john.doe@okicici", parsed.vpa)
    }

    // ── Normalization contract ────────────────────────────────────────────────

    @Test
    fun normalizeMerchant_keepsDigits_matchingTrainingPipeline() {
        // The bundled 520-class model was trained on text_normalized with digits KEPT
        // (10_feature_engineering.py::normalize_merchant). Inference must match exactly.
        assertEquals("swiggy", UpiSmsParser.normalizeMerchant("Swiggy"))
        assertEquals("outlet 42", UpiSmsParser.normalizeMerchant("Outlet 42"))
        assertEquals("merchant 1st floor", UpiSmsParser.normalizeMerchant("Merchant 1st floor"))
    }

    @Test
    fun normalizeMerchant_keepsShortTokens() {
        // Canonical pipeline does NOT strip short tokens — every token is preserved.
        assertEquals("a b bigbasket ltd", UpiSmsParser.normalizeMerchant("A B BigBasket Ltd"))
    }

    @Test
    fun normalizeMerchant_doesNotCharTruncate_tokenizerCapsTokens() {
        // No char cap — the SentencePiece tokenizer caps at 32 tokens downstream,
        // matching training (which also did not truncate the normalized string).
        val long = "a".repeat(100)
        assertEquals(100, UpiSmsParser.normalizeMerchant(long).length)
    }

    @Test
    fun maskDigitsForUpload_masksEveryDigit() {
        // Privacy boundary: digits masked ONLY on the ml_corrections upload path.
        assertEquals("outlet ##", UpiSmsParser.maskDigitsForUpload("outlet 42"))
        assertEquals("merchant #st floor", UpiSmsParser.maskDigitsForUpload("merchant 1st floor"))
    }

    // ── dedup key ────────────────────────────────────────────────────────────

    @Test
    fun dedupKey_sameInputGivesSameKey() {
        val k1 = UpiSmsParser.dedupKey("HDFCBK", 45_000L, "some sms body")
        val k2 = UpiSmsParser.dedupKey("HDFCBK", 45_000L, "some sms body")
        assertEquals(k1, k2)
    }

    @Test
    fun dedupKey_differentAmountGivesDifferentKey() {
        val k1 = UpiSmsParser.dedupKey("HDFCBK", 45_000L, "some sms body")
        val k2 = UpiSmsParser.dedupKey("HDFCBK", 50_000L, "some sms body")
        assertTrue(k1 != k2)
    }

    // ── helpers ───────────────────────────────────────────────────────────────

    private fun parse(sender: String, body: String) = UpiSmsParser.parse(sender, body)
}
