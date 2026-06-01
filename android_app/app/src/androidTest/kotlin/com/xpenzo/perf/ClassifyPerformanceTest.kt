package com.xpenzo.perf

import androidx.test.ext.junit.runners.AndroidJUnit4
import com.xpenzo.sms.UpiSmsParser
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.time.LocalDateTime

/**
 * On-device performance benchmarks.
 *
 * These tests DO NOT require a TFLite model (which needs real assets).
 * Model inference performance (< 100 ms) must be verified manually on a
 * mid-range device (e.g. Snapdragon 680) by profiling via Android Studio
 * Profiler or the following adb command:
 *
 *   adb shell am start -n com.xpenzo/.MainActivity
 *   # trigger an SMS and observe Logcat "CHTClassifier" timing output
 *
 * The targets per docs/09 §6.1:
 *   SMS parsing:      < 10 ms per message
 *   ML inference:     < 100 ms (TFLite FP16 on mid-range)
 *   Full ingestion:   < 150 ms total (parsing + classify + Room write)
 */
@RunWith(AndroidJUnit4::class)
class ClassifyPerformanceTest {

    private val realSmsFixtures = listOf(
        "HDFCBK" to "Rs.350.00 debited from a/c **1234 to VPA swiggy@ybl on 20-03-26.",
        "SBIINB" to "Your a/c XXXX5678 is debited Rs 1200.00 for UPI txn to zomato@icici on 21-03-26.",
        "ICICIB" to "ICICI Bank: Rs 59.00 debited from account XX789. UPI/netflix@icici.",
        "HDFCBK" to "Rs.5000.00 debited from a/c **9999 to VPA phonepe@ybl on 22-03-26.",
        "AXISBK" to "INR 299.00 debited from your Axis Bank a/c XX123 for UPI ref 123. Merchant: Spotify.",
    )

    @Test
    fun sms_parsing_stays_under_10ms_per_message_on_device() {
        val now = LocalDateTime.now()
        val iterations = 200

        val start = System.currentTimeMillis()
        repeat(iterations) { i ->
            val fixture = realSmsFixtures[i % realSmsFixtures.size]
            UpiSmsParser.parse(fixture.first, fixture.second, now)
        }
        val totalMs = System.currentTimeMillis() - start
        val perCallMs = totalMs.toDouble() / iterations

        assertTrue(
            "Parser avg ${perCallMs}ms per call must be < 10ms. " +
                "Actual: ${perCallMs}ms over $iterations iterations.",
            perCallMs < 10.0,
        )
    }

    @Test
    fun normalization_is_idempotent_and_fast() {
        val merchants = listOf("Swiggy123", "ZOMATO", "Netflix India", "Pay#123@ybl", "")
        val iterations = 1_000

        val start = System.currentTimeMillis()
        repeat(iterations) {
            merchants.forEach { UpiSmsParser.normalizeMerchant(it) }
        }
        val totalMs = System.currentTimeMillis() - start
        val perCallMs = totalMs.toDouble() / (iterations * merchants.size)

        assertTrue(
            "normalizeMerchant avg ${perCallMs}ms per call must be < 1ms.",
            perCallMs < 1.0,
        )

        // Idempotency: normalizing twice gives the same result
        merchants.forEach { m ->
            val once = UpiSmsParser.normalizeMerchant(m)
            val twice = UpiSmsParser.normalizeMerchant(once)
            assertTrue(
                "normalizeMerchant should be idempotent for '$m': '$once' != '$twice'",
                once == twice,
            )
        }
    }
}
