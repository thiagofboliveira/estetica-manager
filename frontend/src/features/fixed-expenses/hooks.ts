import { useMutation, useQuery } from "@tanstack/react-query";
import { CACHE, queryClient } from "@/lib/query/client";
import { qk } from "@/lib/query/keys";
import {
  fixedExpensesApi,
  type FixedExpenseCreateInput,
  type FixedExpenseUpdateInput,
} from "./api";

export function useFixedExpenses(activeOnly = true) {
  return useQuery({
    queryKey: [...qk.fixedExpenses(), { activeOnly }],
    queryFn: () => fixedExpensesApi.list(activeOnly),
    ...CACHE.SETTINGS,
  });
}

export function useCreateFixedExpense() {
  return useMutation({
    mutationFn: (payload: FixedExpenseCreateInput) => fixedExpensesApi.create(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: qk.financial() });
    },
  });
}

export function useUpdateFixedExpense() {
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: FixedExpenseUpdateInput }) =>
      fixedExpensesApi.update(id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: qk.financial() });
    },
  });
}

export function useArchiveFixedExpense() {
  return useMutation({
    mutationFn: (id: string) => fixedExpensesApi.archive(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: qk.financial() });
    },
  });
}
