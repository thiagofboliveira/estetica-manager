import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
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
    queryKey: [...qk.expenses(), "detail", id] as const,
    queryFn: () => fixedExpensesApi.get(id),
    ...CACHE.SETTINGS,
  });
}

// Toda mutação invalida qk.financial() inteiro, não só qk.expenses(): uma
// despesa nova muda fixed_expenses_total e net_profit_after_fixed_expenses
// no dashboard, e ele não teria motivo pra saber disso sozinho.
export function useCreateFixedExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: FixedExpenseCreateInput) => fixedExpensesApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.financial() });
    },
  });
}

export function useUpdateFixedExpense(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: FixedExpenseUpdateInput) => fixedExpensesApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.financial() });
    },
  });
}

export function useArchiveFixedExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => fixedExpensesApi.archive(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.financial() });
    },
  });
}
