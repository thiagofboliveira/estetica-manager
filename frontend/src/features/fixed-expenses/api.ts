import { api } from "@/lib/http/client";

export type ExpensePeriodicity = "MONTHLY" | "YEARLY";

export type FixedExpense = {
  id: string;
  label: string;
  category: string | null;
  amount: string;
  periodicity: ExpensePeriodicity;
  active_from: string;
  active_to: string | null;
  created_at: string;
  updated_at: string;
};

export type FixedExpenseCreateInput = {
  label: string;
  category?: string | null;
  amount: string;
  periodicity: ExpensePeriodicity;
  active_from?: string;
};

export type FixedExpenseUpdateInput = {
  label?: string | null;
  category?: string | null;
  amount?: string | null;
  periodicity?: ExpensePeriodicity | null;
};

export const fixedExpensesApi = {
  list: (activeOnly = true) => {
    const qs = activeOnly ? "?active_only=true" : "";
    return api.get<FixedExpense[]>(`/fixed-expenses${qs}`);
  },
  get: (id: string) => api.get<FixedExpense>(`/fixed-expenses/${id}`),
  create: (payload: FixedExpenseCreateInput) =>
    api.post<FixedExpense>("/fixed-expenses", payload),
  update: (id: string, payload: FixedExpenseUpdateInput) =>
    api.patch<FixedExpense>(`/fixed-expenses/${id}`, payload),
  archive: (id: string) => api.del<void>(`/fixed-expenses/${id}`),
};
