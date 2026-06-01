/**
 * Join a group via a GRP-XXXXX invite code. Adds the caller as an ACTIVE member.
 *
 * data: { code: string }
 * returns: { groupId: string }
 */
import * as functions from 'firebase-functions/v1';
import * as admin from 'firebase-admin';

export const joinGroup = functions.https.onCall(async (data, context) => {
  const uid = context.auth?.uid;
  if (!uid) {
    throw new functions.https.HttpsError('unauthenticated', 'Sign in first.');
  }
  const code = (data?.code ?? '').toString().trim().toUpperCase();
  if (!/^GRP-[A-Z0-9]{5}$/.test(code)) {
    throw new functions.https.HttpsError('invalid-argument', 'Invalid invite code.');
  }

  const db = admin.firestore();
  const inviteRef = db.doc(`invitations/${code}`);
  const inviteSnap = await inviteRef.get();
  if (!inviteSnap.exists || inviteSnap.data()?.kind !== 'GROUP') {
    throw new functions.https.HttpsError('not-found', 'Invite code not found.');
  }
  const invite = inviteSnap.data()!;
  const expiresAt = invite.expires_at as admin.firestore.Timestamp | undefined;
  if (expiresAt && expiresAt.toMillis() < Date.now()) {
    throw new functions.https.HttpsError('deadline-exceeded', 'This invite has expired.');
  }

  const groupId = invite.group_id as string;
  const memberRef = db.doc(`groups/${groupId}/members/${uid}`);
  const infoRef = db.doc(`groups/${groupId}/info/info`);

  await db.runTransaction(async (tx) => {
    const existing = await tx.get(memberRef);
    if (existing.exists && existing.data()?.status === 'ACTIVE') {
      return; // idempotent — already a member
    }
    tx.set(memberRef, {
      uid,
      role: 'MEMBER',
      status: 'ACTIVE',
      joined_at: admin.firestore.FieldValue.serverTimestamp(),
    });
    tx.set(infoRef, { member_count: admin.firestore.FieldValue.increment(1) }, { merge: true });
  });

  return { groupId };
});
