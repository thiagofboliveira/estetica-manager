import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { useProcedures } from "./hooks";

export function ProceduresPage() {
  const query = useProcedures();
  const navigate = useNavigate();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Procedimentos</h1>
        <button className="tap-target" onClick={() => navigate("novo")}>
          + Novo procedimento
        </button>
      </header>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={
          <EmptyState
            tone="first-run"
            title="Nenhum procedimento cadastrado ainda"
            body="Cadastre os serviços e produtos que você oferece."
          />
        }
      >
        {(procedures) => (
          <ul className="list">
            {procedures.map((p) => (
              <li key={p.id} className="list__item">
                <button className="list__item-btn tap-target" onClick={() => navigate(p.id)}>
                  <div className="list__item-main">
                    <span className="list__item-title">{p.name}</span>
                    <span className="list__item-badge">
                      {p.type === "PRODUCT"
                        ? "📦 Produto"
                        : p.default_modality === "REMOTE"
                          ? "💻 Remoto"
                          : "📍 Presencial"}
                    </span>
                  </div>
                  <span className="list__item-sub">{formatBRL(money(p.price))}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </AsyncBoundary>
    </div>
  );
}
