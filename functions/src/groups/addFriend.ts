/**
 * Add a friend. Writes BOTH sides of the friendship so each user sees the other —
 * clients can only write their own /users/{uid}/friends/* per security rules, so the
 * reciprocal record must be created here.
 *
 * For a "ghost" friend (someone not yet on Xpenzo) pass only a name/phone; no
 * reciprocal record is written until they sign up and are reconciled.
 *
 * data: { friendUid?: string, name: string, phone?: string }
 * returns: { friendUid: string | null, ghost: boolean }
 */
import * as functions from 'firebase-functions/v1';
import * as admin from 'firebase-admin';

export const addFriend = functions.https.onCall(async (data, context) => {
  const uid = context.auth?.uid;
  if (!uid) {
    throw new functions.https.HttpsError('unauthenticated', 'Sign in first.');
  }
  const name = (data?.name ?? '').toString().trim();
  if (!name) {
    throw new functions.https.HttpsError('invalid-argument', 'Friend name is required.');
  }
  const phone = data?.phone ? data.phone.toString().trim() : null;
  const friendUid: string | null = data?.friendUid ? data.friendUid.toString() : null;

  const db = admin.firestore();
  const now = admin.firestore.FieldValue.serverTimestamp();

  if (!friendUid) {
    // Ghost friend — local-only counterparty, no reciprocal record.
    const ghostRef = db.collection(`users/${uid}/friends`).doc();
    await ghostRef.set({
      friend_id: ghostRef.id,
      name,
      phone,
      is_ghost: true,
      created_at: now,
    });
    return { friendUid: null, ghost: true };
  }

  // Real user — write both directions.
  const batch = db.batch();
  batch.set(db.doc(`users/${uid}/friends/${friendUid}`), {
    friend_id: friendUid,
    name,
    phone,
    is_ghost: false,
    created_at: now,
  }, { merge: true });

  // Reciprocal: fetch the caller's display name for the other side.
  const me = await db.doc(`users/${uid}`).get();
  batch.set(db.doc(`users/${friendUid}/friends/${uid}`), {
    friend_id: uid,
    name: me.data()?.display_name ?? 'Xpenzo user',
    phone: me.data()?.phone ?? null,
    is_ghost: false,
    created_at: now,
  }, { merge: true });

  await batch.commit();
  return { friendUid, ghost: false };
});
