package com.xpenzo.ml.ensemble

import com.xpenzo.ml.core.ClassificationResult
import com.xpenzo.ml.core.ClassificationSource
import com.xpenzo.ml.core.ClassifierInput
import com.xpenzo.ml.models.CHTClassifier
import com.xpenzo.ml.models.HabitModel
import com.xpenzo.ml.models.RuleEngine
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.mockito.kotlin.any
import org.mockito.kotlin.doReturn
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever
import java.time.LocalDateTime

/**
 * Tests for adaptive ensemble weight progression across COLD → WARM → MATURE maturity.
 *
 * Three maturity levels (from [EnsembleClassifier.weightsForUser]):
 *  COLD   (< 10 habits):  chtWeight=0.60  rulesWeight=0.25  habitWeight=0 (ignored)
 *  WARM   (10–49 habits): chtWeight=0.45  rulesWeight=0.15  habitWeight=0.30
 *  MATURE (≥ 50 habits):  chtWeight=0.35  rulesWeight=0.10  habitWeight=0.50
 */
class EnsembleWeightingTest {

    private val testInput = ClassifierInput(
        merchantName = "swiggy",
        upiId = "swiggy@ybl",
        amount = 350.0,
        timestamp = LocalDateTime.now(),
    )

    // ── Mock helpers ──────────────────────────────────────────────────────────

    private fun makeResult(l1: String, conf: Float) = ClassificationResult(
        l1Category = l1,
        l1Confidence = conf,
        l2Category = "",
        l2Confidence = conf,
        l3Category = "",
        l3Confidence = conf,
        source = ClassificationSource.ML_MODEL,
    )

    /** CHTClassifier mock — always predicts [l1] with [conf]. */
    private fun chtMock(l1: String, conf: Float): CHTClassifier = mock {
        onBlocking { warmUp() } doReturn Unit
        onBlocking { classify(any()) } doReturn makeResult(l1, conf)
    }

    /** RuleEngine mock — always predicts [l1] with [conf]. */
    private fun ruleMock(l1: String, conf: Float): RuleEngine = mock {
        onBlocking { warmUp() } doReturn Unit
        onBlocking { classify(any()) } doReturn makeResult(l1, conf)
    }

    /** HabitModel mock — always predicts [l1] with [conf]. */
    private fun habitMock(l1: String, conf: Float): HabitModel = mock {
        onBlocking { warmUp() } doReturn Unit
        onBlocking { classify(any()) } doReturn makeResult(l1, conf)
    }

    // ── Tests ─────────────────────────────────────────────────────────────────

    /**
     * COLD phase: habit signal is ignored (habitWeight=0).
     * CHT says "Food & Dining" (0.70), Rules says "Food & Dining" (0.50),
     * Habit says "Shopping" (0.95).
     *
     * We use count=2 which is BELOW minimumHabitCount (3). This prevents the
     * early-return short-circuit (which fires when conf≥0.90 AND count≥3),
     * so the blending path is taken with habitWeight=0 for COLD.
     */
    @Test
    fun `COLD phase ignores habit signal`() = runTest {
        val ensemble = EnsembleClassifier(
            chtClassifier = chtMock("Food & Dining", 0.70f),
            ruleEngine = ruleMock("Food & Dining", 0.50f),
            habitModel = habitMock("Shopping", 0.95f),
            userTransactionCount = 2,  // < minimumHabitCount(3) → no early return; COLD weights apply
        )

        val result = ensemble.classify(testInput)
        assertEquals(
            "COLD: CHT+Rules should dominate over habit (habitWeight=0)",
            "Food & Dining", result.l1Category,
        )
    }

    /**
     * MATURE phase high-confidence habit short-circuits immediately.
     * When habitConfidence >= 0.90 AND userTransactionCount >= minimumHabitCount (3),
     * the habit result is returned directly without blending.
     */
    @Test
    fun `MATURE phase high-confidence habit overrides CHT and rules`() = runTest {
        val ensemble = EnsembleClassifier(
            chtClassifier = chtMock("Shopping", 0.80f),
            ruleEngine = ruleMock("Shopping", 0.70f),
            habitModel = habitMock("Food & Dining", 0.95f),
            userTransactionCount = 50,
        )

        val result = ensemble.classify(testInput)
        assertEquals(
            "MATURE + habit conf ≥ 0.90: habit must override",
            "Food & Dining", result.l1Category,
        )
    }

    /**
     * MATURE phase blending: when habit confidence is below the short-circuit threshold (0.90),
     * weighted blending applies. Habit weight (0.50) should push the habit prediction to win
     * even against a stronger CHT prediction.
     *
     * habitScore  = 0.85 * 0.50 = 0.425
     * chtScore    = 0.80 * 0.35 = 0.28
     * rulesScore  = 0.70 * 0.10 = 0.07
     *
     * "Food & Dining" (habit) total = 0.425 > "Shopping" total (0.28 + 0.07) = 0.35
     */
    @Test
    fun `MATURE phase blending favours habit below short-circuit threshold`() = runTest {
        val ensemble = EnsembleClassifier(
            chtClassifier = chtMock("Shopping", 0.80f),
            ruleEngine = ruleMock("Shopping", 0.70f),
            habitModel = habitMock("Food & Dining", 0.85f),  // < 0.90 → blending path
            userTransactionCount = 50,
        )

        val result = ensemble.classify(testInput)
        assertEquals(
            "MATURE blending: habit score (0.425) > CHT+Rules (0.35)",
            "Food & Dining", result.l1Category,
        )
    }

    /**
     * WARM phase blending: habit weight is 0.30 — less dominant than MATURE.
     * habitScore  = 0.85 * 0.30 = 0.255
     * chtScore    = 0.80 * 0.45 = 0.36
     * "Shopping" (CHT) wins over "Food & Dining" (habit).
     */
    @Test
    fun `WARM phase CHT still dominates over moderate habit`() = runTest {
        val ensemble = EnsembleClassifier(
            chtClassifier = chtMock("Shopping", 0.80f),
            ruleEngine = ruleMock("Shopping", 0.70f),
            habitModel = habitMock("Food & Dining", 0.85f),
            userTransactionCount = 20,
        )

        val result = ensemble.classify(testInput)
        assertEquals(
            "WARM: CHT score (0.36) > habit score (0.255)",
            "Shopping", result.l1Category,
        )
    }

    /**
     * Rules with ≥ 0.98 confidence and matching CHT cause a rule fast-path.
     * We use userTransactionCount = 2 (below minimumHabitCount=3) so the habit
     * short-circuit does NOT fire — even though habit confidence is 0.95.
     */
    @Test
    fun `rules fast-path triggers when rule conf above 0_98 and matches CHT`() = runTest {
        val ensemble = EnsembleClassifier(
            chtClassifier = chtMock("Bills & Utilities", 0.80f),
            ruleEngine = ruleMock("Bills & Utilities", 0.99f),
            // Habit says something different but count=2 < minimumHabitCount(3) → habit ignored
            habitModel = habitMock("Shopping", 0.95f),
            userTransactionCount = 2,
        )

        val result = ensemble.classify(testInput)
        assertEquals(
            "Rule fast-path: 0.99 conf rule + matching CHT should produce Bills & Utilities",
            "Bills & Utilities", result.l1Category,
        )
    }

    // ── Maturity threshold boundary tests ────────────────────────────────────

    @Test
    fun `maturity boundaries are at 10 and 50`() = runTest {
        // At count=9 habit is effectively ignored (weight=0)
        val cold = EnsembleClassifier(
            chtClassifier = chtMock("Transport", 0.75f),
            ruleEngine = ruleMock("Transport", 0.60f),
            habitModel = habitMock("Food & Dining", 0.80f),
            userTransactionCount = 9,
        )
        assertEquals("Transport", cold.classify(testInput).l1Category)

        // At count=10 habit weight becomes 0.30 but still not enough to overcome strong CHT
        val warm = EnsembleClassifier(
            chtClassifier = chtMock("Transport", 0.75f),
            ruleEngine = ruleMock("Transport", 0.60f),
            habitModel = habitMock("Food & Dining", 0.80f),
            userTransactionCount = 10,
        )
        // habitScore=0.24, chtScore=0.3375, rulesScore=0.09 → Transport wins at WARM
        assertEquals("Transport", warm.classify(testInput).l1Category)
    }

    @Test
    fun `updateTransactionCount shifts weights correctly`() = runTest {
        val cht = chtMock("Shopping", 0.70f)
        val rules = ruleMock("Shopping", 0.60f)
        val habit = habitMock("Food & Dining", 0.85f)  // conf < 0.90 → no early-return short-circuit

        // count=2 → below minimumHabitCount(3), COLD weights, CHT wins
        val ensemble = EnsembleClassifier(cht, rules, habit, userTransactionCount = 2)
        assertEquals("Shopping", ensemble.classify(testInput).l1Category)

        // Update to MATURE (habit conf 0.85 < 0.90 → blending path)
        // MATURE blending: habitScore=0.85*0.50=0.425, chtScore=0.70*0.35=0.245 → habit wins
        ensemble.updateTransactionCount(50)
        assertEquals("Food & Dining", ensemble.classify(testInput).l1Category)
    }
}
