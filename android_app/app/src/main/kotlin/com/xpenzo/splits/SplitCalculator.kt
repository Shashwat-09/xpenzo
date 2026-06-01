package com.xpenzo.splits

import java.util.PriorityQueue
import kotlin.math.abs
import kotlin.math.roundToLong

/**
 * Split calculation engine — paise-exact, rounding errors go to the payer.
 *
 * Supports 4 split types per `docs/01 TRD §5.3`:
 *   - EQUAL    : amount divided equally among participants
 *   - EXACT    : caller supplies exact paise per user
 *   - PERCENT  : caller supplies percentages summing to 100
 *   - SHARES   : caller supplies relative integer share counts
 *
 * Also provides [simplifyDebts] which reduces N(N-1)/2 pairwise edges to at
 * most N-1 settlements using a min-cash-flow algorithm.
 */
object SplitCalculator {

    enum class SplitType { EQUAL, EXACT, PERCENT, SHARES }

    /** A single participant's input for the split form. */
    data class Participant(
        val userId: String,
        /** Used by EXACT (paise), PERCENT (0-100), SHARES (integer >= 0). Ignored for EQUAL. */
        val value: Double = 0.0,
    )

    /** Computed share per participant: how many paise this user owes the payer. */
    data class Share(val userId: String, val amountPaise: Long, val originalInput: Double)

    /**
     * Compute per-user shares for [totalPaise] using [type].
     *
     * Rounding rule: when paise leftovers can't be split evenly, they are
     * ATTRIBUTED TO THE PAYER. This is the standard Splitwise behaviour and
     * keeps every recipient row in nice round numbers.
     *
     * @throws IllegalArgumentException on invalid input (sums don't match, empty list, etc.)
     */
    fun split(
        type: SplitType,
        totalPaise: Long,
        payerUserId: String,
        participants: List<Participant>,
    ): List<Share> {
        require(participants.isNotEmpty()) { "Need at least one participant" }
        require(participants.any { it.userId == payerUserId }) {
            "Payer must be a participant"
        }
        require(totalPaise > 0) { "totalPaise must be > 0" }

        return when (type) {
            SplitType.EQUAL   -> splitEqual(totalPaise, payerUserId, participants)
            SplitType.EXACT   -> splitExact(totalPaise, payerUserId, participants)
            SplitType.PERCENT -> splitPercent(totalPaise, payerUserId, participants)
            SplitType.SHARES  -> splitShares(totalPaise, payerUserId, participants)
        }
    }

    private fun splitEqual(
        totalPaise: Long,
        payerUserId: String,
        participants: List<Participant>,
    ): List<Share> {
        val n = participants.size
        val basePerHead = totalPaise / n           // integer division
        val leftover = totalPaise - basePerHead * n   // 0..n-1 paise unaccounted

        return participants.map { p ->
            val owed = if (p.userId == payerUserId) basePerHead + leftover else basePerHead
            Share(p.userId, owed, basePerHead.toDouble())
        }
    }

    private fun splitExact(
        totalPaise: Long,
        payerUserId: String,
        participants: List<Participant>,
    ): List<Share> {
        val provided = participants.sumOf { it.value.roundToLong() }
        require(provided == totalPaise) {
            "EXACT shares ($provided) must equal totalPaise ($totalPaise)"
        }
        return participants.map { p ->
            Share(p.userId, p.value.roundToLong(), p.value)
        }
    }

    private fun splitPercent(
        totalPaise: Long,
        payerUserId: String,
        participants: List<Participant>,
    ): List<Share> {
        val pctSum = participants.sumOf { it.value }
        require(abs(pctSum - 100.0) < 0.01) {
            "PERCENT values must sum to 100 (got $pctSum)"
        }

        // Compute each share at full precision, round, then attribute leftover to payer
        val rawShares = participants.map { p ->
            val raw = (p.value / 100.0) * totalPaise
            Triple(p.userId, raw.roundToLong(), p.value)
        }
        val attributed = rawShares.sumOf { it.second }
        val leftover = totalPaise - attributed     // can be negative or positive

        return rawShares.map { (uid, amount, input) ->
            val finalAmount = if (uid == payerUserId) amount + leftover else amount
            Share(uid, finalAmount, input)
        }
    }

    private fun splitShares(
        totalPaise: Long,
        payerUserId: String,
        participants: List<Participant>,
    ): List<Share> {
        val totalShares = participants.sumOf { it.value }
        require(totalShares > 0) { "Total shares must be > 0" }

        val raw = participants.map { p ->
            val raw = p.value / totalShares * totalPaise
            Triple(p.userId, raw.roundToLong(), p.value)
        }
        val attributed = raw.sumOf { it.second }
        val leftover = totalPaise - attributed

        return raw.map { (uid, amount, input) ->
            val finalAmount = if (uid == payerUserId) amount + leftover else amount
            Share(uid, finalAmount, input)
        }
    }

    // ── Debt simplification ──────────────────────────────────────────────────

    /** Represents a single payment instruction "from → to". */
    data class Transfer(val from: String, val to: String, val amountPaise: Long)

    /**
     * Min-cash-flow debt simplification.
     *
     * Given a map of net balance per user (positive = is owed money, negative
     * = owes money), produces a minimal set of transfers (≤ N-1) that settle
     * everyone to zero.
     *
     * Greedy heap approach: at each step pair the largest creditor with the
     * largest debtor. Guaranteed to terminate in ≤ N-1 transfers when balances
     * sum to zero.
     */
    fun simplifyDebts(netBalances: Map<String, Long>): List<Transfer> {
        require(netBalances.values.sum() == 0L) {
            "Net balances must sum to zero (got ${netBalances.values.sum()})"
        }

        // Two max-heaps: creditors by balance desc, debtors by abs(balance) desc
        val creditors = PriorityQueue<Pair<String, Long>>(compareByDescending { it.second })
        val debtors = PriorityQueue<Pair<String, Long>>(compareByDescending { it.second })

        netBalances.forEach { (user, balance) ->
            when {
                balance > 0 -> creditors.add(user to balance)
                balance < 0 -> debtors.add(user to -balance)  // store as positive owed amount
                // balance == 0: nothing to do
            }
        }

        val transfers = mutableListOf<Transfer>()
        while (creditors.isNotEmpty() && debtors.isNotEmpty()) {
            val (creditor, owedAmount) = creditors.poll()
            val (debtor, owingAmount) = debtors.poll()

            val payment = minOf(owedAmount, owingAmount)
            transfers.add(Transfer(from = debtor, to = creditor, amountPaise = payment))

            if (owedAmount > payment) creditors.add(creditor to (owedAmount - payment))
            if (owingAmount > payment) debtors.add(debtor to (owingAmount - payment))
        }

        return transfers
    }

    /**
     * Convenience: given a list of expense-shares for a group, plus already-confirmed
     * settlements, compute the net balance map per user, then simplify.
     *
     * Each expense contributes:
     *  +amount to the payer (they fronted money)
     *  -share to each participant (they owe their share)
     *
     * Each confirmed settlement contributes:
     *  +amount to to_user (received money)
     *  -amount to from_user (paid money)
     */
    fun computeNetBalances(
        expensesPaidBy: Map<String, Long>,     // userId → total they paid (sum of expense.amountPaise)
        sharesOwed: Map<String, Long>,         // userId → total they owe (sum of share.amountPaise)
        confirmedSettlementsIn: Map<String, Long>,   // userId → total received via settlements
        confirmedSettlementsOut: Map<String, Long>,  // userId → total paid via settlements
    ): Map<String, Long> {
        val users = (expensesPaidBy.keys + sharesOwed.keys +
            confirmedSettlementsIn.keys + confirmedSettlementsOut.keys)
        return users.associateWith { uid ->
            (expensesPaidBy[uid] ?: 0L) -
                (sharesOwed[uid] ?: 0L) -
                (confirmedSettlementsIn[uid] ?: 0L) +
                (confirmedSettlementsOut[uid] ?: 0L)
        }
    }
}
