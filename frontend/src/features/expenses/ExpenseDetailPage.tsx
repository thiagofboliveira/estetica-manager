import { useNavigate, useParams } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { ExpenseForm, type ExpenseFormValues } from "./ExpenseForm";
import { toExpensePayload } from "./mapper";
import { useArchiveFixedExpense, useFixedExpense, useUpdateFixedExpense } from "./hooks";

export function ExpenseDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const query = useFixedExpense(id);
  const update = useUpdateFixedExpense(id);
  const archive = useArchiveFixedExpense();

  async function handleSubmit(values: ExpenseFormValues) {
    await update.mutateAsync(toExpensePayload(values));
  }

  async function handleArchive() {
    // Backend nunca hard-deleta (fecha active_to=hoje) — mesmo assim
    // confirma, porque some da lista e do cálculo de lucro do mês.
    if (!window.confirm("Encerrar esta despesa? Ela para de entrar no cálculo do lucro.")) return;
    await archive.mutateAsync(id);
    navigate("/configuracoes/despesas");
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1>Despesa fixa</h1>
      </header>
      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={<p>Despesa não encontrada.</p>}
        isEmpty={(e) => e == null}
      >
        {(expense) => (
          <>
            <ExpenseForm initial={expense} onSubmit={handleSubmit} submitLabel="Salvar" />
            {expense.active_to == null && (
              <button
                className="tap-target danger"
                onClick={handleArchive}
                disabled={archive.isPending}
              >
                {archive.isPending ? "Encerrando…" : "Encerrar despesa"}
              </button>
            )}
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}
