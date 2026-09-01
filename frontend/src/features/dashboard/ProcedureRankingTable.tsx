import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import type { DashboardParams } from "./api";
import { useProcedureRanking } from "./hooks";

type Props = {
  params: DashboardParams;
};

export function ProcedureRankingTable({ params }: Props) {
  const query = useProcedureRanking(params);

  return (
    <section className="dashboard__ranking">
      <div className="section-header">
        <h2>Ranking por Procedimento</h2>
        <p className="section-desc">
          Faturamento bruto, lucro real e margem obtida por serviço/produto no período selecionado.
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
        {(ranking) => (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Procedimento / Produto</th>
                  <th className="text-right">Faturamento</th>
                  <th className="text-right">Lucro Real</th>
                  <th className="text-right">Margem</th>
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </AsyncBoundary>
    </section>
  );
}
