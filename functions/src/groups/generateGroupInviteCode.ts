/**
 * Generate a unique GRP-XXXXX invite code for a group. Admin only.
 *
 * data: { groupId: string }
 * returns: { code: string, expiresAt: number }
 */
import * as functions from 'firebase-functions/v1';
import * as admin from 'firebase-admin';

const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no ambiguous chars (I/O/0/1)
const CODE_LEN = 5;
const TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function randomCode(): string {
  let s = '';
  for (let i = 0; i < CODE_LEN; i++) {
    s += ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
  }
  return `GRP-${s}`;
}

export const generateGroupInviteCode = functions.https.onCall(async (data, context) => {
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
  if (!memberDoc.exists || memberDoc.data()?.role !== 'ADMIN') {
    throw new functions.https.HttpsError('permission-denied', 'Only a group admin can invite.');
  }

  // Retry until a free code is found (collisions are astronomically rare).
  for (let attempt = 0; attempt < 5; attempt++) {
    const code = randomCode();
    const inviteRef = db.doc(`invitations/${code}`);
    const created = await db.runTransaction(async (tx) => {
      const existing = await tx.get(inviteRef);
      if (existing.exists) return false;
      tx.set(inviteRef, {
        code,
        kind: 'GROUP',
        group_id: groupId,
        created_by: uid,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        expires_at: admin.firestore.Timestamp.fromMillis(nowMs() + TTL_MS),
      });
      return true;
    });
    if (created) {
      return { code, expiresAt: nowMs() + TTL_MS };
    }
  }
  throw new functions.https.HttpsError('internal', 'Could not allocate an invite code, try again.');
});

// Wall-clock read isolated for testability.
function nowMs(): number {
  return Date.now();
}
