/**
 * Recompute cached group balances whenever an expense is created, edited, or deleted.
 * Balances are authoritative server-side; clients only read /groups/{id}/balances/*.
 */
import * as functions from 'firebase-functions/v1';
import { recomputeAndPersistBalances } from '../lib/groupBalances';

export const onGroupExpenseWrite = functions.firestore
  .document('groups/{groupId}/expenses/{expenseId}')
  .onWrite(async (_change, context) => {
    const { groupId } = context.params as { groupId: string };
    await recomputeAndPersistBalances(groupId);
  });
