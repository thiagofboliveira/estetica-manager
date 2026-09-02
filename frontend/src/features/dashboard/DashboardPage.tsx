import { useState } from "react";
import { Link } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { PeriodFilter } from "@/ui/PeriodFilter";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import type { Period } from "@/lib/period/period";
import { useDashboard } from "./hooks";
import type { Dashboard } from "./api";

/**
 * F-013, dashboard principal. GET /dashboard real (T-022). Cada
 * métrica tem base declarada (venda vs. sessão, MVP §13.1) — "3
 * vendas, 12 atendimentos" não é bug, é um pacote em andamento.
 * "Lucro real do mês" só existe em period=this_month|last_month
 * (fixed_expenses_total/net_profit_after_fixed_expenses vêm null fora
 * disso) — a linha some, nunca mostra "R$ 0,00" no lugar de null.
 */
export function DashboardPage() {
  const [period, setPeriod] = useState<Period>("this_month");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const query = useDashboard({
    period,
    date_from: period === "custom" ? dateFrom : undefined,
    date_to: period === "custom" ? dateTo : undefined,
  });

  return (
    <div className="page">
      <header className="page__header">
        <h1>Dashboard</h1>
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
              title="Nenhuma venda registrada ainda"
              body="Registre a primeira venda para ver o dashboard."
            />
          }
          isEmpty={(d) => !d.has_any_data}
        >
          {(dashboard) => <DashboardMetrics dashboard={dashboard} />}
        </AsyncBoundary>
      )}

      <p className="dashboard__ranking-link">
        <Link to="/relatorios/procedimentos">Ver ranking de procedimentos →</Link>
      </p>
    </div>
  );
}

function DashboardMetrics({ dashboard }: { dashboard: Dashboard }) {
  const { fixed_expenses_total, net_profit_after_fixed_expenses } = dashboard;
  const showFixedExpenses = fixed_expenses_total != null && net_profit_after_fixed_expenses != null;

  return (
    <dl className="dashboard__metrics">
      <div className="dashboard__metric">
        <dt>Faturamento</dt>
        <dd>{formatBRL(money(dashboard.gross_revenue))}</dd>
      </div>

      <div className="dashboard__metric">
        <dt>
          Lucro real
          {dashboard.has_provisional_profit && (
            <span className="chip chip--provisional" title="Tem sessão de pacote ainda não realizada neste período — o custo pode mudar quando ela acontecer">
              provisório
            </span>
          )}
        </dt>
        <dd>{formatBRL(money(dashboard.net_profit))}</dd>
      </div>

      {showFixedExpenses && (
        <div className="dashboard__metric">
          <dt>
            Lucro real do mês
            {dashboard.has_provisional_profit && (
              <span className="chip chip--provisional" title="Tem sessão de pacote ainda não realizada neste período — o custo pode mudar quando ela acontecer">
                provisório
              </span>
            )}
          </dt>
          <dd>
            {formatBRL(money(net_profit_after_fixed_expenses))}
            <span className="dashboard__metric-note">
              (após despesas fixas de {formatBRL(money(fixed_expenses_total))})
            </span>
          </dd>
        </div>
      )}

      <div className="dashboard__metric">
        <dt>A receber</dt>
        <dd>{formatBRL(money(dashboard.receivable_amount))}</dd>
      </div>

      <div className="dashboard__metric">
        <dt>Margem média</dt>
        <dd>{dashboard.average_margin != null ? formatRate(rate(dashboard.average_margin)) : "—"}</dd>
      </div>

      <div className="dashboard__metric">
        <dt>Ticket médio</dt>
        <dd>{dashboard.average_ticket != null ? formatBRL(money(dashboard.average_ticket)) : "—"}</dd>
      </div>

      <div className="dashboard__metric dashboard__metric--wide">
        <dt>Vendas e atendimentos</dt>
        <dd>
          {dashboard.sale_count} {dashboard.sale_count === 1 ? "venda" : "vendas"}, {dashboard.session_count}{" "}
          {dashboard.session_count === 1 ? "atendimento" : "atendimentos"}
        </dd>
      </div>
    </dl>
  );
}
