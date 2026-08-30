import { api } from "@/lib/http/client";

// MONTHLY | YEARLY — MVP v7.1 §12.5, T-021a/T-021b.
export type ExpensePeriodicity = "MONTHLY" | "YEARLY";

export type FixedExpense = {
  id: string;
  label: string;
  category: string | null;
  // Valor do CICLO (mensal se MONTHLY, anual se YEARLY) — não converter
  // para "por mês" no cliente, ver ENGENHARIA.md §1 (Money nunca no front).
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
};

export type FixedExpenseUpdateInput = Partial<
  Pick<FixedExpenseCreateInput, "label" | "category" | "amount" | "periodicity">
>;

export const fixedExpensesApi = {
  list: (params: { includeArchived?: boolean } = {}) => {
    const qs = params.includeArchived ? "?include_archived=true" : "";
    return api.get<FixedExpense[]>(`/fixed-expenses${qs}`);
  },
  get: (id: string) => api.get<FixedExpense>(`/fixed-expenses/${id}`),
  create: (payload: FixedExpenseCreateInput) => api.post<FixedExpense>("/fixed-expenses", payload),
  update: (id: string, payload: FixedExpenseUpdateInput) =>
    api.patch<FixedExpense>(`/fixed-expenses/${id}`, payload),
  // Backend nunca faz hard delete — fecha active_to=hoje (ver router do backend).
  archive: (id: string) => api.del<void>(`/fixed-expenses/${id}`),
};
