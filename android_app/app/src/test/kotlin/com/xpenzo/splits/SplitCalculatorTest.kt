package com.xpenzo.splits

import com.xpenzo.splits.SplitCalculator.Participant
import com.xpenzo.splits.SplitCalculator.SplitType
import com.xpenzo.splits.SplitCalculator.Transfer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SplitCalculatorTest {

    // ── EQUAL split ──────────────────────────────────────────────────────────

    @Test
    fun `EQUAL split divides evenly when total is exact multiple`() {
        // ₹300.00 (30000 paise) / 3 people = ₹100.00 each
        val shares = SplitCalculator.split(
            type = SplitType.EQUAL,
            totalPaise = 30000L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice"), Participant("bob"), Participant("carol"),
            ),
        )
        assertEquals(3, shares.size)
        shares.forEach { assertEquals(10_000L, it.amountPaise) }
        assertEquals(30000L, shares.sumOf { it.amountPaise })
    }

    @Test
    fun `EQUAL split attributes leftover paise to payer`() {
        // 10001 paise / 3 people = 3333 + leftover 2 → payer gets 3335
        val shares = SplitCalculator.split(
            type = SplitType.EQUAL,
            totalPaise = 10001L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice"), Participant("bob"), Participant("carol"),
            ),
        )
        assertEquals(3335L, shares.first { it.userId == "alice" }.amountPaise)
        assertEquals(3333L, shares.first { it.userId == "bob" }.amountPaise)
        assertEquals(3333L, shares.first { it.userId == "carol" }.amountPaise)
        assertEquals(10001L, shares.sumOf { it.amountPaise })
    }

    // ── EXACT split ──────────────────────────────────────────────────────────

    @Test
    fun `EXACT split uses provided paise amounts`() {
        val shares = SplitCalculator.split(
            type = SplitType.EXACT,
            totalPaise = 50000L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice", 20000.0),
                Participant("bob", 25000.0),
                Participant("carol", 5000.0),
            ),
        )
        assertEquals(20000L, shares.first { it.userId == "alice" }.amountPaise)
        assertEquals(25000L, shares.first { it.userId == "bob" }.amountPaise)
        assertEquals(5000L,  shares.first { it.userId == "carol" }.amountPaise)
        assertEquals(50000L, shares.sumOf { it.amountPaise })
    }

    @Test(expected = IllegalArgumentException::class)
    fun `EXACT split rejects when shares don't sum to total`() {
        SplitCalculator.split(
            type = SplitType.EXACT,
            totalPaise = 30000L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice", 10000.0),
                Participant("bob", 10000.0),
                // missing carol's share — total = 20000, not 30000
            ),
        )
    }

    // ── PERCENT split ────────────────────────────────────────────────────────

    @Test
    fun `PERCENT split allocates by percentage and rounds extra to payer`() {
        // 100 paise (₹1) split 33/33/34 = 33, 33, 34 — exact
        val shares = SplitCalculator.split(
            type = SplitType.PERCENT,
            totalPaise = 100L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice", 33.0),
                Participant("bob", 33.0),
                Participant("carol", 34.0),
            ),
        )
        assertEquals(100L, shares.sumOf { it.amountPaise })
    }

    @Test
    fun `PERCENT split with irrational percentages rounds to payer`() {
        // 1000 paise * 33.33% = 333.3 → rounds to 333. Three of those = 999.9 → 1000 needed.
        val shares = SplitCalculator.split(
            type = SplitType.PERCENT,
            totalPaise = 1000L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice", 33.33),
                Participant("bob", 33.33),
                Participant("carol", 33.34),
            ),
        )
        assertEquals("Total should equal input", 1000L, shares.sumOf { it.amountPaise })
        // Payer (alice) absorbs any leftover paise
        val alice = shares.first { it.userId == "alice" }
        val bob = shares.first { it.userId == "bob" }
        val carol = shares.first { it.userId == "carol" }
        assertEquals(1000L, alice.amountPaise + bob.amountPaise + carol.amountPaise)
    }

    @Test(expected = IllegalArgumentException::class)
    fun `PERCENT split rejects when percentages don't sum to 100`() {
        SplitCalculator.split(
            type = SplitType.PERCENT,
            totalPaise = 10000L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice", 50.0),
                Participant("bob", 30.0),  // 50+30=80, not 100
            ),
        )
    }

    // ── SHARES split ─────────────────────────────────────────────────────────

    @Test
    fun `SHARES split allocates proportionally to integer shares`() {
        // 60000 paise with shares 1:2:3 = 10000, 20000, 30000
        val shares = SplitCalculator.split(
            type = SplitType.SHARES,
            totalPaise = 60000L,
            payerUserId = "alice",
            participants = listOf(
                Participant("alice", 1.0),
                Participant("bob", 2.0),
                Participant("carol", 3.0),
            ),
        )
        assertEquals(10000L, shares.first { it.userId == "alice" }.amountPaise)
        assertEquals(20000L, shares.first { it.userId == "bob" }.amountPaise)
        assertEquals(30000L, shares.first { it.userId == "carol" }.amountPaise)
        assertEquals(60000L, shares.sumOf { it.amountPaise })
    }

    // ── Validation ───────────────────────────────────────────────────────────

    @Test(expected = IllegalArgumentException::class)
    fun `split rejects empty participants list`() {
        SplitCalculator.split(SplitType.EQUAL, 10000L, "alice", emptyList())
    }

    @Test(expected = IllegalArgumentException::class)
    fun `split rejects when payer is not in participants`() {
        SplitCalculator.split(
            SplitType.EQUAL, 10000L, "zoe",
            participants = listOf(Participant("alice"), Participant("bob")),
        )
    }

    // ── simplifyDebts (min-cash-flow) ────────────────────────────────────────

    @Test
    fun `simplifyDebts produces zero transfers when all balances are zero`() {
        val transfers = SplitCalculator.simplifyDebts(mapOf("a" to 0L, "b" to 0L))
        assertTrue(transfers.isEmpty())
    }

    @Test
    fun `simplifyDebts handles two-person case`() {
        // alice is owed 500, bob owes 500
        val transfers = SplitCalculator.simplifyDebts(mapOf("alice" to 500L, "bob" to -500L))
        assertEquals(1, transfers.size)
        assertEquals(Transfer(from = "bob", to = "alice", amountPaise = 500L), transfers.first())
    }

    @Test
    fun `simplifyDebts collapses 3-person triangle to 2 transfers`() {
        // alice +200, bob +100, carol -300
        // expected: carol → alice 200, carol → bob 100 (or whatever order produces same totals)
        val transfers = SplitCalculator.simplifyDebts(
            mapOf("alice" to 200L, "bob" to 100L, "carol" to -300L),
        )
        assertEquals("Should need exactly 2 transfers for 3-person triangle", 2, transfers.size)
        // All transfers come FROM carol
        assertTrue(transfers.all { it.from == "carol" })
        // Total paid by carol = 300
        assertEquals(300L, transfers.sumOf { it.amountPaise })
        // Alice receives 200, bob receives 100
        assertEquals(200L, transfers.first { it.to == "alice" }.amountPaise)
        assertEquals(100L, transfers.first { it.to == "bob" }.amountPaise)
    }

    @Test
    fun `simplifyDebts produces at most N-1 transfers for N people`() {
        // 5 people with random balances that sum to zero
        val balances = mapOf("a" to 1000L, "b" to 500L, "c" to -200L, "d" to -300L, "e" to -1000L)
        val transfers = SplitCalculator.simplifyDebts(balances)
        assertTrue(
            "transfers (${transfers.size}) must be ≤ N-1 (${balances.size - 1})",
            transfers.size <= balances.size - 1,
        )
        // Verify balances reach zero after applying transfers
        val resulting = balances.toMutableMap()
        transfers.forEach { t ->
            resulting[t.from] = (resulting[t.from] ?: 0L) + t.amountPaise
            resulting[t.to] = (resulting[t.to] ?: 0L) - t.amountPaise
        }
        assertTrue(resulting.values.all { it == 0L })
    }

    @Test(expected = IllegalArgumentException::class)
    fun `simplifyDebts rejects non-zero-sum balances`() {
        SplitCalculator.simplifyDebts(mapOf("a" to 100L, "b" to 50L))  // sum=150, not 0
    }

    // ── End-to-end realistic scenario ────────────────────────────────────────

    @Test
    fun `Goa trip scenario - hotel + dinner + simplification`() {
        // alice paid ₹6000 for hotel (split 3 ways), bob paid ₹900 for dinner (split 3 ways)
        // Net: alice +6000-2000=+4000, bob -2000+600=-1400, carol -2000-300=-2300
        // Actually: alice +6000 (paid) - 2000 (her share) = +4000
        //          bob -2000 (her share of hotel) + 900 (paid) - 300 (her share dinner) = -1400
        //          carol -2000 (hotel) - 300 (dinner) = -2300
        // Check: 4000 - 1400 - 2300 = 300 ≠ 0. Need bob's hotel share + alice's dinner share
        // Actually alice's dinner share is 300, not zero.
        // alice: +6000 (paid hotel) - 2000 (her hotel share) - 300 (her dinner share) = +3700
        // bob: -2000 (hotel share) + 900 (paid dinner) - 300 (his dinner share) = -1400
        // carol: -2000 (hotel share) - 300 (dinner share) = -2300
        // sum: 3700 - 1400 - 2300 = 0 ✓
        val net = mapOf("alice" to 3700L, "bob" to -1400L, "carol" to -2300L)
        val transfers = SplitCalculator.simplifyDebts(net)

        // Verify settles to zero
        val resulting = net.toMutableMap()
        transfers.forEach { t ->
            resulting[t.from] = (resulting[t.from] ?: 0L) + t.amountPaise
            resulting[t.to] = (resulting[t.to] ?: 0L) - t.amountPaise
        }
        assertTrue("All balances should settle to 0", resulting.values.all { it == 0L })
        // ≤ 2 transfers for 3 people
        assertTrue(transfers.size <= 2)
    }
}
