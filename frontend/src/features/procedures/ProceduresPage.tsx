import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import type { SessionPlan } from "./api";
import { useProceduresPage } from "./hooks";

const PAGE_SIZE = 20;

// Três estados: indefinido (sem filtro), true, false.
type TriState = boolean | undefined;

function nextTriState(current: TriState): TriState {
  if (current === undefined) return true;
  if (current === true) return false;
  return undefined;
}

export function ProceduresPage() {
  const [isInvasive, setIsInvasive] = useState<TriState>(undefined);
  const [sessionPlan, setSessionPlan] = useState<SessionPlan | "">("");
  const [page, setPage] = useState(1);

  // Trocar qualquer filtro com a página > 1 deixaria a tela presa numa
  // página que pode nem existir mais no novo recorte filtrado.
  useEffect(() => setPage(1), [isInvasive, sessionPlan]);

  const hasActiveFilters = isInvasive !== undefined || Boolean(sessionPlan);

  const query = useProceduresPage(
    { is_invasive: isInvasive, session_plan: sessionPlan || undefined },
    page,
    PAGE_SIZE,
  );
  const navigate = useNavigate();

  return (
    <div className="page">
      <header className="page__header">
        <h1>Procedimentos</h1>
        <button className="tap-target" onClick={() => navigate("novo")}>
          + Novo procedimento
        </button>
      </header>

      <div className="filters-bar">
        <button
          type="button"
          className={
            isInvasive !== undefined
              ? "filters-bar__toggle filters-bar__toggle--active"
              : "filters-bar__toggle"
          }
          onClick={() => setIsInvasive((v) => nextTriState(v))}
          aria-pressed={isInvasive !== undefined}
        >
          ⚠️ Invasivo{isInvasive === true ? ": sim" : isInvasive === false ? ": não" : ""}
        </button>

        <select
          value={sessionPlan}
          onChange={(e) => setSessionPlan(e.target.value as SessionPlan | "")}
          aria-label="Filtrar por número de sessões"
        >
          <option value="">Sessões: todas</option>
          <option value="SINGLE">Sessão única</option>
          <option value="MULTIPLE">Múltiplas sessões</option>
        </select>
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando…</p>}
        empty={
          <EmptyState
            tone={hasActiveFilters ? "filtered" : "first-run"}
            title={hasActiveFilters ? "Nenhum procedimento encontrado" : "Nenhum procedimento cadastrado ainda"}
            body={
              hasActiveFilters
                ? "Ajuste os filtros para ver outros procedimentos."
                : "Cadastre os serviços e produtos que você oferece."
            }
          />
        }
        isEmpty={(data) => data.items.length === 0}
      >
        {(result) => {
          const totalPages = Math.max(1, Math.ceil(result.total_count / result.page_size));

          return (
            <>
              <ul className="list">
                {result.items.map((p) => (
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
                        {p.is_invasive && <span className="list__item-badge">⚠️ Invasivo</span>}
                        {p.session_plan === "MULTIPLE" && (
                          <span className="list__item-badge">🔁 Múltiplas sessões</span>
                        )}
                      </div>
                      <span className="list__item-sub">{formatBRL(money(p.price))}</span>
                    </button>
                  </li>
                ))}
              </ul>

              {totalPages > 1 && (
                <nav className="pagination" aria-label="Páginas de procedimentos">
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    ← Anterior
                  </button>
                  <span className="pagination__status">
                    Página {page} de {totalPages} · {result.total_count}{" "}
                    {result.total_count === 1 ? "procedimento" : "procedimentos"}
                  </span>
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Próxima →
                  </button>
                </nav>
              )}
            </>
          );
        }}
      </AsyncBoundary>
    </div>
  );
}
