package com.xpenzo.splits

import com.xpenzo.data.db.dao.FriendDao
import com.xpenzo.data.db.dao.GroupDao
import com.xpenzo.data.db.dao.SplitDao
import com.xpenzo.data.db.entity.FriendEntity
import com.xpenzo.data.db.entity.GroupEntity
import com.xpenzo.data.db.entity.GroupMemberEntity
import com.xpenzo.data.db.entity.SettlementEntity
import com.xpenzo.data.db.entity.SplitExpenseEntity
import com.xpenzo.data.db.entity.SplitShareEntity
import com.xpenzo.splits.SplitCalculator.SplitType
import com.xpenzo.splits.SplitCalculator.Transfer
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Coordinates groups, members, split expenses, settlements, and friends.
 *
 * UI ViewModels should depend on this repository (NOT raw DAOs) so that
 * computation rules (balance derivation, simplification, transaction linkage)
 * stay in one place.
 */
@Singleton
class SplitsRepository @Inject constructor(
    private val groupDao: GroupDao,
    private val splitDao: SplitDao,
    private val friendDao: FriendDao,
) {

    // ── Groups ────────────────────────────────────────────────────────────────

    val activeGroups: Flow<List<GroupEntity>> = groupDao.flowActiveGroups()

    fun groupById(id: String): Flow<GroupEntity?> = groupDao.flowById(id)

    fun groupMembers(groupId: String): Flow<List<GroupMemberEntity>> =
        groupDao.flowMembers(groupId)

    suspend fun createGroup(
        name: String,
        emoji: String,
        creatorUserId: String,
        creatorDisplayName: String,
        otherMembers: List<Pair<String, String>>,  // (userId, displayName)
    ): String {
        val id = UUID.randomUUID().toString()
        val group = GroupEntity(
            id = id,
            name = name,
            emoji = emoji,
            createdBy = creatorUserId,
        )
        groupDao.upsertGroup(group)

        val members = buildList {
            add(GroupMemberEntity(
                groupId = id,
                userId = creatorUserId,
                displayName = creatorDisplayName,
                role = "ADMIN",
            ))
            otherMembers.forEach { (userId, name) ->
                add(GroupMemberEntity(
                    groupId = id,
                    userId = userId,
                    displayName = name,
                    role = "MEMBER",
                ))
            }
        }
        groupDao.upsertMembers(members)
        return id
    }

    suspend fun archiveGroup(groupId: String) {
        groupDao.getById(groupId)?.let {
            groupDao.updateGroup(it.copy(isArchived = true, synced = false))
        }
    }

    // ── Expenses ──────────────────────────────────────────────────────────────

    fun groupExpenses(groupId: String): Flow<List<SplitExpenseEntity>> =
        splitDao.flowGroupExpenses(groupId)

    fun expenseShares(expenseId: String): Flow<List<SplitShareEntity>> =
        splitDao.flowSharesForExpense(expenseId)

    /**
     * Create a split expense and atomically write its per-user shares.
     * Returns the new expense id.
     */
    suspend fun createExpense(
        groupId: String?,
        title: String,
        amountPaise: Long,
        payerUserId: String,
        splitType: SplitType,
        participants: List<SplitCalculator.Participant>,
        categoryL1: String = "Food & Dining",
        notes: String = "",
        linkedTransactionId: String? = null,
    ): String {
        val expenseId = UUID.randomUUID().toString()
        val shares = SplitCalculator.split(
            type = splitType,
            totalPaise = amountPaise,
            payerUserId = payerUserId,
            participants = participants,
        )

        val expense = SplitExpenseEntity(
            id = expenseId,
            groupId = groupId,
            title = title,
            amountPaise = amountPaise,
            paidBy = payerUserId,
            splitType = splitType.name,
            categoryL1 = categoryL1,
            notes = notes,
            linkedTransactionId = linkedTransactionId,
        )

        val shareRows = shares.map { s ->
            SplitShareEntity(
                expenseId = expenseId,
                userId = s.userId,
                amountPaise = s.amountPaise,
                shareInput = s.originalInput,
            )
        }

        splitDao.saveExpenseWithShares(expense, shareRows)
        return expenseId
    }

    suspend fun deleteExpense(id: String) = splitDao.softDelete(id)

    // ── Balances + simplification ─────────────────────────────────────────────

    /**
     * Reactive net balances for [groupId]: who owes whom (positive = owed to user,
     * negative = user owes). Recomputes on every expense or settlement change.
     */
    fun groupNetBalances(groupId: String): Flow<Map<String, Long>> = combine(
        splitDao.flowGroupExpenses(groupId),
        splitDao.flowAllSharesForGroup(groupId),
        splitDao.flowGroupSettlements(groupId),
    ) { expenses, shares, settlements ->
        computeBalances(expenses, shares, settlements)
    }

    /** Synchronous one-shot net balance computation (for share/export). */
    suspend fun groupNetBalancesOnce(groupId: String): Map<String, Long> {
        val expenses = splitDao.flowGroupExpenses(groupId).let { /* unused — get directly */
            // We need a non-flow version. Add a one-shot in DAO? Use shares directly via
            // computed paid totals below.
            emptyList<SplitExpenseEntity>()
        }
        // Easier: use the joined-shares helper we already have:
        val sharesAll = splitDao.getAllSharesForGroup(groupId)
        val settlements = splitDao.getConfirmedSettlements(groupId)
        // We still need expense-level payment totals — re-fetch via group_id query:
        // Walk shares grouped by expense to derive who paid what would require another helper.
        // For now we re-create the helper by reading each unique expense.
        val expenseIds = sharesAll.map { it.expenseId }.distinct()
        val expensesResolved = expenseIds.mapNotNull { splitDao.getExpense(it) }
        return computeBalances(expensesResolved, sharesAll, settlements)
    }

    private fun computeBalances(
        expenses: List<SplitExpenseEntity>,
        shares: List<SplitShareEntity>,
        settlements: List<SettlementEntity>,
    ): Map<String, Long> {
        val paidBy = expenses
            .filterNot { it.isDeleted }
            .groupBy { it.paidBy }
            .mapValues { (_, list) -> list.sumOf { it.amountPaise } }

        val owedBy = shares
            .groupBy { it.userId }
            .mapValues { (_, list) -> list.sumOf { it.amountPaise } }

        val confirmed = settlements.filter { it.status == "CONFIRMED" }
        val settIn = confirmed.groupBy { it.toUser }.mapValues { (_, l) -> l.sumOf { it.amountPaise } }
        val settOut = confirmed.groupBy { it.fromUser }.mapValues { (_, l) -> l.sumOf { it.amountPaise } }

        return SplitCalculator.computeNetBalances(paidBy, owedBy, settIn, settOut)
    }

    /** Convenience: balances already simplified to ≤ N-1 transfers. */
    fun groupSimplifiedTransfers(groupId: String): Flow<List<Transfer>> =
        groupNetBalances(groupId).map { SplitCalculator.simplifyDebts(it) }

    // ── Settlements ───────────────────────────────────────────────────────────

    fun groupSettlements(groupId: String): Flow<List<SettlementEntity>> =
        splitDao.flowGroupSettlements(groupId)

    suspend fun recordSettlement(
        groupId: String?,
        fromUser: String,
        toUser: String,
        amountPaise: Long,
        method: String,
        notes: String = "",
    ): String {
        val id = UUID.randomUUID().toString()
        splitDao.upsertSettlement(
            SettlementEntity(
                id = id,
                groupId = groupId,
                fromUser = fromUser,
                toUser = toUser,
                amountPaise = amountPaise,
                method = method,
                status = "PENDING",
                notes = notes,
            ),
        )
        return id
    }

    suspend fun confirmSettlement(id: String) {
        splitDao.updateSettlementStatus(id, "CONFIRMED", System.currentTimeMillis())
    }

    suspend fun cancelSettlement(id: String) {
        splitDao.updateSettlementStatus(id, "CANCELLED", null)
    }

    // ── Friends (1:1 splits) ──────────────────────────────────────────────────

    val friends: Flow<List<FriendEntity>> = friendDao.flowAll()

    suspend fun addFriend(
        displayName: String,
        phoneE164: String?,
        otherUserId: String? = null,
    ): String {
        val id = UUID.randomUUID().toString()
        val isGhost = otherUserId == null
        val effectiveId = otherUserId ?: "ghost_$id"
        friendDao.upsert(
            FriendEntity(
                id = id,
                otherUserId = effectiveId,
                displayName = displayName,
                phoneE164 = phoneE164,
                isGhost = isGhost,
            ),
        )
        return id
    }

    suspend fun removeFriend(id: String) = friendDao.delete(id)
}
