/**
 * Recompute cached group balances whenever a settlement is created, confirmed,
 * or cancelled. Only CONFIRMED settlements affect balances (see recomputeGroupBalances).
 */
import * as functions from 'firebase-functions/v1';
import { recomputeAndPersistBalances } from '../lib/groupBalances';

export const onSettlementWrite = functions.firestore
  .document('groups/{groupId}/settlements/{settlementId}')
  .onWrite(async (_change, context) => {
    const { groupId } = context.params as { groupId: string };
    await recomputeAndPersistBalances(groupId);
  });
