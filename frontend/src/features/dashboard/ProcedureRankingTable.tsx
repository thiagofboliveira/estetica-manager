import { useEffect, useState } from "react";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import type { DashboardParams } from "./api";
import { useProcedureRanking } from "./hooks";

const PAGE_SIZE = 10;

type Props = {
  params: DashboardParams;
};

export function ProcedureRankingTable({ params }: Props) {
  const [page, setPage] = useState(1);

  // Trocar o filtro de período com a página > 1 deixaria a tela presa
  // numa página que pode nem existir mais no novo recorte.
  useEffect(() => setPage(1), [params.period, params.date_from, params.date_to]);

  const query = useProcedureRanking({ ...params, page, page_size: PAGE_SIZE });

  return (
    <section className="dashboard__ranking">
      <div className="section-header">
        <h2>Ranking por Procedimento</h2>
        <p className="section-desc">
          Faturamento bruto, lucro real, margem e atendimentos concluídos por serviço/produto no período selecionado.
        </p>
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando ranking de procedimentos…</p>}
        empty={
          <EmptyState
            tone="filtered"
            title="Sem vendas no período"
            body="Nenhum procedimento foi registrado nas datas selecionadas."
          />
        }
        isEmpty={(data) => data.rows.length === 0}
      >
        {(ranking) => {
          const totalPages = Math.max(1, Math.ceil(ranking.total_count / ranking.page_size));

          return (
            <>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Procedimento / Produto</th>
                      <th className="text-right">Faturamento</th>
                      <th className="text-right">Lucro Real</th>
                      <th className="text-right">Margem</th>
                      <th className="text-right">Atendimentos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranking.rows.map((row) => (
                      <tr key={row.procedure_id}>
                        <td>
                          <span className="font-semibold">{row.procedure_name}</span>
                        </td>
                        <td className="text-right">{formatBRL(money(row.gross_revenue))}</td>
                        <td className="text-right font-semibold text-accent">
                          {formatBRL(money(row.net_profit))}
                        </td>
                        <td className="text-right">
                          {row.margin != null ? (
                            <span className="badge badge--neutral">
                              {formatRate(rate(row.margin))}
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="text-right">{row.session_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <nav className="pagination" aria-label="Páginas do ranking">
                  <button
                    type="button"
                    className="tap-target"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    ← Anterior
                  </button>
                  <span className="pagination__status">
                    Página {page} de {totalPages} · {ranking.total_count}{" "}
                    {ranking.total_count === 1 ? "procedimento" : "procedimentos"}
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
    </section>
  );
}
