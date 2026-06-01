/**
 * Xpenzo Cloud Functions entrypoint — Phase 10 (Groups & Splits).
 *
 * Deploy: `firebase deploy --only functions` (requires a Firebase project +
 * `firebase use <project>`). See docs/REMAINING_WORK.md §1 for project setup.
 */
import * as admin from 'firebase-admin';

admin.initializeApp();

// Callable functions
export { createGroup } from './groups/createGroup';
export { generateGroupInviteCode } from './groups/generateGroupInviteCode';
export { joinGroup } from './groups/joinGroup';
export { addFriend } from './groups/addFriend';
export { simplifyGroupDebts } from './groups/simplifyGroupDebts';

// Firestore triggers — keep cached balances authoritative
export { onGroupExpenseWrite } from './triggers/onGroupExpenseWrite';
export { onSettlementWrite } from './triggers/onSettlementWrite';
