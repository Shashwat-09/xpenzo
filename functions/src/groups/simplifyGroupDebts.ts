/**
 * Callable: return the min-cash-flow settle-up plan for a group (≤ N-1 transfers).
 * Read-only — does not mutate balances (the triggers own that).
 *
 * data: { groupId: string }
 * returns: { transfers: Array<{ from: string, to: string, amount: number }> }
 */
import * as functions from 'firebase-functions/v1';
import * as admin from 'firebase-admin';
import { GroupExpense, Settlement, recomputeGroupBalances, simplifyDebts } from '../lib/balances';

export const simplifyGroupDebts = functions.https.onCall(async (data, context) => {
  const uid = context.auth?.uid;
  if (!uid) {
    throw new functions.https.HttpsError('unauthenticated', 'Sign in first.');
  }
  const groupId = (data?.groupId ?? '').toString();
  if (!groupId) {
    throw new functions.https.HttpsError('invalid-argument', 'groupId is required.');
  }

  const db = admin.firestore();
  const memberDoc = await db.doc(`groups/${groupId}/members/${uid}`).get();
  if (!memberDoc.exists || memberDoc.data()?.status !== 'ACTIVE') {
    throw new functions.https.HttpsError('permission-denied', 'Not a member of this group.');
  }

  const groupRef = db.collection('groups').doc(groupId);
  const [expensesSnap, settlementsSnap] = await Promise.all([
    groupRef.collection('expenses').get(),
    groupRef.collection('settlements').get(),
  ]);
  const expenses = expensesSnap.docs.map((d) => d.data() as GroupExpense);
  const settlements = settlementsSnap.docs.map((d) => d.data() as Settlement);

  const net = recomputeGroupBalances(expenses, settlements);
  const transfers = simplifyDebts(net);
  return { transfers };
});
