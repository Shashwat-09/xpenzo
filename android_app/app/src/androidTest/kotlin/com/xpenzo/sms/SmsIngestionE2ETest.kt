package com.xpenzo.sms

import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.xpenzo.data.db.XpenzoDatabase
import com.xpenzo.data.repository.TransactionRepository
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.time.LocalDateTime

/**
 * End-to-end instrumented test for the SMS ingestion pipeline.
 *
 * Exercises the path:
 *   SMS body → UpiSmsParser.parse() → UpiSmsParser.normalizeMerchant()
 *   → [TransactionRepository.insertTransaction()] → Room
 *
 * Note: the SmsIngestionWorker step (WorkManager) is skipped here to keep
 * the test hermetic. The WorkManager e2e is covered by a separate manual
 * smoke test; this focuses on the parsing + persistence contract.
 *
 * Run with: ./gradlew :app:connectedDebugAndroidTest
 */
@RunWith(AndroidJUnit4::class)
class SmsIngestionE2ETest {

    private lateinit var db: XpenzoDatabase
    private lateinit var repository: TransactionRepository

    @Before
    fun setup() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            XpenzoDatabase::class.java,
        ).allowMainThreadQueries().build()

        repository = TransactionRepository(
            transactionDao = db.transactionDao(),
            habitDao = db.habitDao(),
            correctionDao = db.correctionDao(),
        )
    }

    @After
    fun teardown() {
        db.close()
    }

    // ── Parse + persist helpers ───────────────────────────────────────────────

    private suspend fun ingestSms(sender: String, body: String): String? {
        val now = LocalDateTime.now()
        val parsed = UpiSmsParser.parse(sender, body, now) ?: return null

        val transaction = com.xpenzo.data.db.entity.TransactionEntity(
            id = java.util.UUID.randomUUID().toString(),
            merchantRaw = parsed.merchant,
            merchantNormalized = parsed.merchantNormalized,
            upiId = parsed.vpa,
            amount = parsed.amountPaise,
            isCredit = parsed.isCredit,
            timestamp = System.currentTimeMillis(),
            l1Category = "Food & Dining",  // mock classifier output
            l2Category = "Restaurants",
            l3Category = "Quick Service",
            confidence = 0.85f,
            source = "TEST",
        )

        repository.insertTransaction(transaction)
        return transaction.id
    }

    // ── Tests ─────────────────────────────────────────────────────────────────

    @Test
    fun hdfc_upi_debit_parses_and_persists_to_room() = runBlocking {
        val id = ingestSms(
            sender = "HDFCBK",
            body = "Rs.350.00 debited from a/c **1234 to VPA swiggy@ybl on 20-03-26.",
        )
        assertNotNull("SMS should parse as a valid transaction", id)

        val allTx = repository.allTransactions.first()
        assertEquals(1, allTx.size)
        val tx = allTx.first()
        assertEquals(35_000L, tx.amount) // ₹350 = 35000 paise
        assertEquals(false, tx.isCredit)
        assertTrue("VPA should contain ybl", tx.upiId.contains("ybl"))
    }

    @Test
    fun sbi_upi_debit_persists_correct_amount_in_paise() = runBlocking {
        ingestSms(
            sender = "SBIINB",
            body = "Your a/c XXXX1234 is debited Rs 1200.00 for UPI txn " +
                "to zomato@icici on 21-03-26.",
        )
        val tx = repository.allTransactions.first().firstOrNull()
        assertNotNull(tx)
        assertEquals(120_000L, tx!!.amount) // ₹1,200 = 120,000 paise
    }

    @Test
    fun otp_sms_is_not_persisted() = runBlocking {
        val id = ingestSms(
            sender = "HDFCBK",
            body = "Your OTP for HDFC Bank is 123456. Do not share with anyone.",
        )
        assertNull("OTP SMS should return null (skipped)", id)
        assertTrue(repository.allTransactions.first().isEmpty())
    }

    @Test
    fun credit_sms_sets_is_credit_true() = runBlocking {
        ingestSms(
            sender = "SBIINB",
            body = "Rs.5000.00 credited to your a/c XX5678 by UPI ref 123456789.",
        )
        val tx = repository.allTransactions.first().firstOrNull()
        assertNotNull(tx)
        assertEquals(true, tx!!.isCredit)
        assertEquals(500_000L, tx.amount)
    }

    @Test
    fun merchant_normalized_field_is_lowercased_no_digits() = runBlocking {
        ingestSms(
            sender = "HDFCBK",
            body = "Rs.299.00 debited from a/c **9999 to VPA Swiggy123@ybl on 22-03-26.",
        )
        val tx = repository.allTransactions.first().firstOrNull()
        assertNotNull(tx)
        // normalizeMerchant: lowercase + digits→# + clean
        val norm = tx!!.merchantNormalized
        assertTrue(
            "Normalized merchant should be lowercase: '$norm'",
            norm == norm.lowercase(),
        )
        assertTrue(
            "Normalized merchant should not contain bare digits (replaced with #): '$norm'",
            !norm.any { it.isDigit() } || norm.contains("#"),
        )
    }

    @Test
    fun multiple_sms_accumulate_in_room() = runBlocking {
        val bodies = listOf(
            "Rs.350.00 debited from a/c **1234 to VPA swiggy@ybl on 20-03-26.",
            "Your a/c XXXX1234 is debited Rs 1200.00 for UPI txn to zomato@icici on 21-03-26.",
            "Rs.59.00 debited from a/c **5678 to VPA netflix@icici on 22-03-26.",
        )
        bodies.forEach { body -> ingestSms("HDFCBK", body) }

        val all = repository.allTransactions.first()
        assertEquals(3, all.size)
    }

    // ── Performance guard ─────────────────────────────────────────────────────

    /**
     * Verifies that UpiSmsParser runs in well under 100 ms per SMS
     * (the ModelManager classify() must also be < 100 ms, tested separately
     * with a real TFLite interpreter on device).
     */
    @Test
    fun sms_parser_runs_under_10ms_per_message() {
        val body = "Rs.350.00 debited from a/c **1234 to VPA swiggy@ybl on 20-03-26."
        val start = System.currentTimeMillis()
        repeat(100) {
            UpiSmsParser.parse("HDFCBK", body, LocalDateTime.now())
        }
        val elapsed = System.currentTimeMillis() - start
        val perCall = elapsed / 100.0
        assertTrue(
            "Parser avg ${perCall}ms per call should be < 10ms",
            perCall < 10.0,
        )
    }
}
