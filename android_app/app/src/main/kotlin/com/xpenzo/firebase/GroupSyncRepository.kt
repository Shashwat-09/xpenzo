package com.xpenzo.firebase

import android.util.Log
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.SetOptions
import com.xpenzo.data.db.dao.FriendDao
import com.xpenzo.data.db.dao.GroupDao
import com.xpenzo.data.db.dao.SplitDao
import com.xpenzo.data.db.entity.SettlementEntity
import com.xpenzo.data.db.entity.SplitExpenseEntity
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.tasks.await

/**
 * Mirrors Phase 10 (Groups & Splits) local Room state to Firestore so groups sync
 * across the members' devices.
 *
 * Field names mirror what the Cloud Functions expect (functions/src/lib/balances.ts):
 *   expense → { paid_by, total_amount, shares:[{user_id, owed_amount}], is_active }
 *   settlement → { from_user, to_user, amount, status }
 * so `onGroupExpenseWrite` / `onSettlementWrite` recompute the cached
 * balances docs under each group correctly. Clients never write balances.
 *
 * Only **group-scoped** expenses/settlements (group_id != null) sync here; 1:1 friend
 * splits stay local for now. Group + member creation is best done via the `createGroup`
 * callable in production — this direct mirror keeps offline-first devices consistent.
 *
 * 🔒 Privacy: this path is entirely separate from the ML loop. No split-partner identity,
 * group membership, or settlement data ever flows into `ml_corrections` (see
 * FirestoreSyncRepository.syncCorrections — only normalized merchant leaves the device).
 */
@Singleton
class GroupSyncRepository @Inject constructor(
    private val groupDao: GroupDao,
    private val splitDao: SplitDao,
    private val friendDao: FriendDao,
    private val auth: AuthRepository,
) {
    private val db = FirebaseFirestore.getInstance()

    suspend fun syncAll() {
        val uid = auth.currentUser?.uid ?: return
        syncGroups()
        syncExpenses()
        syncSettlements()
        syncFriends(uid)
    }

    private suspend fun syncGroups() {
        val groups = groupDao.getUnsyncedGroups()
        for (g in groups) {
            val groupRef = db.collection("groups").document(g.id)
            val members = groupDao.getMembers(g.id)

            val batch = db.batch()
            batch.set(
                groupRef.collection("info").document("info"),
                mapOf(
                    "group_id" to g.id,
                    "name" to g.name,
                    "emoji" to g.emoji,
                    "color_hex" to g.colorHex,
                    "currency" to g.currency,
                    "created_by" to g.createdBy,
                    "created_at" to g.createdAt,
                    "member_count" to members.size,
                ),
                SetOptions.merge(),
            )
            members.forEach { m ->
                batch.set(
                    groupRef.collection("members").document(m.userId),
                    mapOf(
                        "uid" to m.userId,
                        "display_name" to m.displayName,
                        "phone" to m.phoneE164,
                        "role" to m.role,
                        "status" to m.status,
                        "is_ghost" to m.isGhost,
                        "joined_at" to m.joinedAt,
                    ),
                    SetOptions.merge(),
                )
            }
            runCatching { batch.commit().await() }
                .onSuccess { groupDao.markGroupSynced(g.id) }
                .onFailure { Log.w(TAG, "Group ${g.id} sync failed", it) }
        }
    }

    private suspend fun syncExpenses() {
        val expenses = splitDao.getUnsyncedExpenses()
        for (e in expenses) {
            val groupId = e.groupId ?: continue
            val shares = splitDao.getSharesForExpense(e.id).map { s ->
                mapOf("user_id" to s.userId, "owed_amount" to s.amountPaise)
            }
            runCatching {
                db.collection("groups").document(groupId)
                    .collection("expenses").document(e.id)
                    .set(e.toFirestoreMap(shares), SetOptions.merge())
                    .await()
            }
                .onSuccess { splitDao.markExpenseSynced(e.id) }
                .onFailure { Log.w(TAG, "Expense ${e.id} sync failed", it) }
        }
    }

    private suspend fun syncSettlements() {
        val settlements = splitDao.getUnsyncedSettlements()
        for (s in settlements) {
            val groupId = s.groupId ?: continue
            runCatching {
                db.collection("groups").document(groupId)
                    .collection("settlements").document(s.id)
                    .set(s.toFirestoreMap(), SetOptions.merge())
                    .await()
            }
                .onSuccess { splitDao.markSettlementSynced(s.id) }
                .onFailure { Log.w(TAG, "Settlement ${s.id} sync failed", it) }
        }
    }

    private suspend fun syncFriends(uid: String) {
        val friends = friendDao.getUnsyncedFriends()
        for (f in friends) {
            runCatching {
                db.collection("users").document(uid)
                    .collection("friends").document(f.otherUserId)
                    .set(
                        mapOf(
                            "friend_id" to f.otherUserId,
                            "name" to f.displayName,
                            "phone" to f.phoneE164,
                            "is_ghost" to f.isGhost,
                            "created_at" to f.createdAt,
                        ),
                        SetOptions.merge(),
                    )
                    .await()
            }
                .onSuccess { friendDao.markFriendSynced(f.id) }
                .onFailure { Log.w(TAG, "Friend ${f.id} sync failed", it) }
        }
    }

    private fun SplitExpenseEntity.toFirestoreMap(shares: List<Map<String, Any?>>): Map<String, Any?> = mapOf(
        "id" to id,
        "group_id" to groupId,
        "title" to title,
        "total_amount" to amountPaise,
        "currency" to currency,
        "paid_by" to paidBy,
        "split_type" to splitType,
        "category_l1" to categoryL1,
        "created_by" to paidBy,
        "is_active" to !isDeleted,
        "shares" to shares,
        "created_at" to createdAt,
        "timestamp" to timestamp,
    )

    private fun SettlementEntity.toFirestoreMap(): Map<String, Any?> = mapOf(
        "id" to id,
        "group_id" to groupId,
        "from_user" to fromUser,
        "to_user" to toUser,
        "amount" to amountPaise,
        "currency" to currency,
        "method" to method,
        "status" to status,
        "created_at" to createdAt,
        "confirmed_at" to confirmedAt,
    )

    companion object {
        private const val TAG = "GroupSync"
    }
}
