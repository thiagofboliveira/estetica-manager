import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { useFixedExpenses } from "./hooks";

const PERIODICITY_LABEL = { MONTHLY: "/mês", YEARLY: "/ano" } as const;

export function ExpensesPage() {
  const query = useFixedExpenses();
  const navigate = useNavigate();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Despesas fixas</h1>
        <button className="tap-target" onClick={() => navigate("nova")}>
          + Nova despesa
        </button>
      </header>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={
          <EmptyState
            tone="first-run"
            title="Nenhuma despesa fixa cadastrada ainda"
            body="Aluguel, assinaturas, o que sai do bolso todo mês — cadastre para ver o lucro real depois delas."
          />
        }
      >
        {(expenses) => (
          <ul className="list">
            {expenses.map((e) => (
              <li key={e.id} className="list__item">
                <button className="list__item-btn tap-target" onClick={() => navigate(e.id)}>
                  <span className="list__item-title">
                    {e.label}
                    {e.category && <span className="list__item-tag">{e.category}</span>}
                  </span>
                  <span className="list__item-sub">
                    {formatBRL(money(e.amount))} {PERIODICITY_LABEL[e.periodicity]}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </AsyncBoundary>
    </div>
  );
}
