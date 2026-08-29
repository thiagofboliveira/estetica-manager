import { money } from "@/lib/money/money";
import type { ExpenseFormValues } from "./ExpenseForm";

export function toExpensePayload(values: ExpenseFormValues) {
  return {
    label: values.label,
    category: values.category?.trim() ? values.category.trim() : null,
    amount: money(values.amount),
    periodicity: values.periodicity,
  };
}
