import { useMutation, useQuery } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import { invalidateAfterFixedExpenseChange } from "@/lib/query/invalidation";
import {
  fixedExpensesApi,
  type FixedExpenseCreateInput,
  type FixedExpenseUpdateInput,
} from "./api";

export function useFixedExpenses() {
  return useQuery({
    queryKey: qk.expenses(),
    queryFn: () => fixedExpensesApi.list(),
    ...CACHE.SETTINGS,
  });
}

export function useFixedExpense(id: string) {
  return useQuery({
    queryKey: qk.expenseDetail(id),
    queryFn: () => fixedExpensesApi.get(id),
    enabled: !!id,
    ...CACHE.SETTINGS,
  });
}

// Despesa fixa só afeta a lista/detalhe dela e o dashboard
// (fixed_expenses_total/net_profit_after_fixed_expenses) — não o resto
// de qk.financial() (retenção, pacotes, sessões, vendas).
export function useCreateFixedExpense() {
  return useMutation({
    mutationFn: (payload: FixedExpenseCreateInput) => fixedExpensesApi.create(payload),
    onSuccess: () => {
      void invalidateAfterFixedExpenseChange();
    },
  });
}

export function useUpdateFixedExpense(id: string) {
  return useMutation({
    mutationFn: (payload: FixedExpenseUpdateInput) => fixedExpensesApi.update(id, payload),
    onSuccess: () => {
      void invalidateAfterFixedExpenseChange();
    },
  });
}

export function useArchiveFixedExpense() {
  return useMutation({
    mutationFn: (id: string) => fixedExpensesApi.archive(id),
    onSuccess: () => {
      void invalidateAfterFixedExpenseChange();
    },
  });
}
