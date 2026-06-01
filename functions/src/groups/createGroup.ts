/**
 * Create a group. The caller becomes its ADMIN member.
 *
 * data: { name: string, emoji?: string, type?: 'TRIP'|'FLATMATES'|'COUPLE'|'OTHER' }
 * returns: { groupId: string }
 */
import * as functions from 'firebase-functions/v1';
import * as admin from 'firebase-admin';

export const createGroup = functions.https.onCall(async (data, context) => {
  const uid = context.auth?.uid;
  if (!uid) {
    throw new functions.https.HttpsError('unauthenticated', 'Sign in to create a group.');
  }

  const name = (data?.name ?? '').toString().trim();
  if (name.length < 1 || name.length > 60) {
    throw new functions.https.HttpsError('invalid-argument', 'Group name must be 1–60 chars.');
  }
  const emoji = (data?.emoji ?? '👥').toString().slice(0, 8);
  const type = (data?.type ?? 'OTHER').toString();

  const db = admin.firestore();
  const groupRef = db.collection('groups').doc();
  const now = admin.firestore.FieldValue.serverTimestamp();

  const batch = db.batch();
  batch.set(groupRef.collection('info').doc('info'), {
    group_id: groupRef.id,
    name,
    emoji,
    type,
    created_by: uid,
    created_at: now,
    member_count: 1,
  });
  batch.set(groupRef.collection('members').doc(uid), {
    uid,
    role: 'ADMIN',
    status: 'ACTIVE',
    joined_at: now,
  });
  await batch.commit();

  return { groupId: groupRef.id };
});
