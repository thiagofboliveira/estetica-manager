import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { PeriodFilter } from "@/ui/PeriodFilter";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import type { Period } from "@/lib/period/period";
import { useProcedureRanking } from "./hooks";
import type { ProcedureRanking } from "./api";

/**
 * F-013c, ranking de procedimentos. GET /reports/procedures real
 * (T-024), linhas já vêm ordenadas por faturamento decrescente do
 * servidor. A API não sinaliza quais linhas dependem de estimativa de
 * parcelamento/custo variável (E4/E5, MVP §13) — por isso o aviso
 * abaixo da tabela é fixo, não por linha.
 */
export function ProcedureRankingPage() {
  const [period, setPeriod] = useState<Period>("this_month");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const query = useProcedureRanking({
    period,
    date_from: period === "custom" ? dateFrom : undefined,
    date_to: period === "custom" ? dateTo : undefined,
  });

  return (
    <div className="page">
      <header className="page__header">
        <h1>Ranking de procedimentos</h1>
      </header>

      <PeriodFilter
        period={period}
        onPeriodChange={setPeriod}
        dateFrom={dateFrom}
        onDateFromChange={setDateFrom}
        dateTo={dateTo}
        onDateToChange={setDateTo}
      />

      {period === "custom" && !(dateFrom && dateTo) ? (
        <p>Escolha as duas datas para ver o período.</p>
      ) : (
        <AsyncBoundary
          query={query}
          skeleton={<p>Carregando…</p>}
          empty={
            <EmptyState
              tone="first-run"
              title="Nenhuma venda registrada neste período"
              body="Registre vendas para ver o ranking de procedimentos."
            />
          }
          isEmpty={(d) => d.rows.length === 0}
        >
          {(ranking) => <RankingTable ranking={ranking} />}
        </AsyncBoundary>
      )}
    </div>
  );
}

function RankingTable({ ranking }: { ranking: ProcedureRanking }) {
  return (
    <>
      <table className="ranking-table">
        <thead>
          <tr>
            <th>Procedimento</th>
            <th>Faturamento</th>
            <th>Lucro</th>
            <th>Margem</th>
          </tr>
        </thead>
        <tbody>
          {ranking.rows.map((row) => (
            <tr key={row.procedure_id}>
              <td>{row.procedure_name}</td>
              <td>{formatBRL(money(row.gross_revenue))}</td>
              <td>{formatBRL(money(row.net_profit))}</td>
              <td>{row.margin != null ? formatRate(rate(row.margin)) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="ranking-table__note">
        Valores podem incluir estimativa de custo ou taxa de parcelamento não confirmada.
      </p>
    </>
  );
}
