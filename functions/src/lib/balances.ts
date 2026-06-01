/**
 * Shared balance math for Groups & Splits.
 *
 * Mirrors the on-device Kotlin `SplitCalculator` (android_app/.../splits/SplitCalculator.kt)
 * so server-recomputed balances always agree with what the client previewed.
 *
 * All amounts are in **paise** (integer) to stay exact. Clients NEVER write balances —
 * `onGroupExpenseWrite` / `onSettlementWrite` recompute them server-side from the
 * source-of-truth expenses + confirmed settlements.
 */

export interface ExpenseShare {
  user_id: string;
  owed_amount: number; // paise this user owes the payer for this expense
}

export interface GroupExpense {
  paid_by: string;
  total_amount: number; // paise
  shares: ExpenseShare[];
  is_active?: boolean; // soft-delete flag; absent → active
}

export interface Settlement {
  from_user: string;
  to_user: string;
  amount: number; // paise
  status: string; // PENDING | CONFIRMED | ...
}

export interface Transfer {
  from: string;
  to: string;
  amount: number; // paise
}

/**
 * Net balance per user: positive = is owed money, negative = owes money.
 * Σ over all users ≈ 0 (any rounding remainder already lives on the payer
 * because shares were computed leftover-to-payer on the client / in computeShares).
 */
export function recomputeGroupBalances(
  expenses: GroupExpense[],
  settlements: Settlement[],
): Record<string, number> {
  const net: Record<string, number> = {};
  const add = (uid: string, delta: number) => {
    net[uid] = (net[uid] ?? 0) + delta;
  };

  // 1) Expenses: the payer fronted total_amount; each participant owes their share.
  for (const exp of expenses) {
    if (exp.is_active === false) continue;
    add(exp.paid_by, exp.total_amount);
    for (const s of exp.shares) {
      add(s.user_id, -s.owed_amount);
    }
  }

  // 2) Confirmed settlements: from_user paid to_user, reducing what from_user owes.
  for (const st of settlements) {
    if (st.status !== 'CONFIRMED') continue;
    add(st.from_user, st.amount);
    add(st.to_user, -st.amount);
  }

  return net;
}

/**
 * Min-cash-flow debt simplification: reduces O(N²) pairwise debts to ≤ N-1 transfers.
 * Greedy: repeatedly settle the largest creditor against the largest debtor.
 *
 * Mirrors SplitCalculator.simplifyDebts() exactly. Input net must sum to ~0;
 * any single-paise remainder is ignored (below the settle threshold).
 */
export function simplifyDebts(net: Record<string, number>): Transfer[] {
  // Build (user, amount) lists. Creditors: amount > 0; debtors: amount < 0 (store positive owed).
  const creditors: Array<{ user: string; amount: number }> = [];
  const debtors: Array<{ user: string; amount: number }> = [];
  for (const [user, amount] of Object.entries(net)) {
    if (amount > 0) creditors.push({ user, amount });
    else if (amount < 0) debtors.push({ user, amount: -amount });
  }

  // Max-heap behaviour via sort-on-each-step (group sizes are tiny — N members).
  const byAmountDesc = (a: { amount: number }, b: { amount: number }) => b.amount - a.amount;
  const transfers: Transfer[] = [];

  while (creditors.length > 0 && debtors.length > 0) {
    creditors.sort(byAmountDesc);
    debtors.sort(byAmountDesc);
    const c = creditors[0];
    const d = debtors[0];

    const payment = Math.min(c.amount, d.amount);
    if (payment <= 0) break;
    transfers.push({ from: d.user, to: c.user, amount: payment });

    c.amount -= payment;
    d.amount -= payment;
    if (c.amount === 0) creditors.shift();
    if (d.amount === 0) debtors.shift();
  }

  return transfers;
}
