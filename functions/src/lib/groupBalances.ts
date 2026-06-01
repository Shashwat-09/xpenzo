/**
 * Reads a group's source-of-truth expenses + settlements, recomputes net balances,
 * and persists them to /groups/{groupId}/balances/{uid}. Clients never write here.
 */
import * as admin from 'firebase-admin';
import {
  GroupExpense,
  Settlement,
  recomputeGroupBalances,
  simplifyDebts,
} from './balances';

export async function recomputeAndPersistBalances(groupId: string): Promise<void> {
  const db = admin.firestore();
  const groupRef = db.collection('groups').doc(groupId);

  const [expensesSnap, settlementsSnap] = await Promise.all([
    groupRef.collection('expenses').get(),
    groupRef.collection('settlements').get(),
  ]);

  const expenses = expensesSnap.docs.map((d) => d.data() as GroupExpense);
  const settlements = settlementsSnap.docs.map((d) => d.data() as Settlement);

  const net = recomputeGroupBalances(expenses, settlements);
  const transfers = simplifyDebts(net);

  // Collect every member uid so members who netted to exactly 0 still get a balances doc.
  const memberIds = new Set<string>(Object.keys(net));
  const membersSnap = await groupRef.collection('members').get();
  membersSnap.docs.forEach((d) => memberIds.add(d.id));

  const batch = db.batch();
  const now = admin.firestore.FieldValue.serverTimestamp();

  for (const uid of memberIds) {
    const balance = net[uid] ?? 0;
    // Suggested transfers that involve this user (what they should pay / will receive).
    const owes = transfers.filter((t) => t.from === uid).map((t) => ({ to: t.to, amount: t.amount }));
    const owedBy = transfers.filter((t) => t.to === uid).map((t) => ({ from: t.from, amount: t.amount }));

    batch.set(
      groupRef.collection('balances').doc(uid),
      {
        uid,
        net_paise: balance,
        owes,
        owed_by: owedBy,
        updated_at: now,
      },
      { merge: true },
    );
  }

  await batch.commit();
}
