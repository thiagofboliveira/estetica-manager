import { useNavigate } from "react-router-dom";
import { ExpenseForm, type ExpenseFormValues } from "./ExpenseForm";
import { toExpensePayload } from "./mapper";
import { useCreateFixedExpense } from "./hooks";

export function NewExpensePage() {
  const navigate = useNavigate();
  const create = useCreateFixedExpense();

  async function handleSubmit(values: ExpenseFormValues) {
    const expense = await create.mutateAsync(toExpensePayload(values));
    navigate(`/configuracoes/despesas/${expense.id}`);
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Nova despesa fixa</h1>
      </header>
      <ExpenseForm onSubmit={handleSubmit} submitLabel="Cadastrar" />
    </div>
  );
}
