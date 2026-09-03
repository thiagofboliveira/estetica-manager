import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import { useDashboard } from "./hooks";
import type { Dashboard, DashboardParams, DashboardPeriod } from "./api";

import { ProcedureRankingTable } from "./ProcedureRankingTable";
import { OnboardingChecklist } from "@/features/onboarding/OnboardingChecklist";
import { ROICard } from "./ROICard";

const PERIOD_OPTIONS: { value: DashboardPeriod; label: string }[] = [
  { value: "today", label: "Hoje" },
  { value: "last_7_days", label: "Últimos 7 dias" },
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Mês anterior" },
  { value: "custom", label: "Personalizado" },
];

/**
 * F-013, dashboard principal. GET /dashboard real (T-022). Cada
 * métrica tem base declarada (venda vs. sessão, MVP §13.1) — "3
 * vendas, 12 atendimentos" não é bug, é um pacote em andamento.
 * "Lucro real do mês" só existe em period=this_month|last_month
 * (fixed_expenses_total/net_profit_after_fixed_expenses vêm null fora
 * disso) — a linha some, nunca mostra "R$ 0,00" no lugar de null.
 * F-013b: Badges de estimativa/lucro provisório (I7).
 * F-013c: Ranking de procedimentos por faturamento e lucro real.
 * F-021: Checklist de primeiro acesso não-bloqueante.
 */
export function DashboardPage() {
  const [period, setPeriod] = useState<DashboardPeriod>("this_month");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const isInvalidRange = period === "custom" && Boolean(dateFrom && dateTo && dateFrom > dateTo);

  const params: DashboardParams = {
    period,
    date_from: period === "custom" && !isInvalidRange ? dateFrom : undefined,
    date_to: period === "custom" && !isInvalidRange ? dateTo : undefined,
  };

  const query = useDashboard(params);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Dashboard</h1>
      </header>

      <OnboardingChecklist hasAnySale={Boolean(query.data?.has_any_data)} />

      <div className="dashboard__period" role="group" aria-label="Período">
        {PERIOD_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className="tap-target"
            aria-pressed={period === opt.value}
            onClick={() => setPeriod(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {period === "custom" && (
        <div className="dashboard__custom-range">
          <label>
            <span>De</span>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label>
            <span>Até</span>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
        </div>
      )}

      {period === "custom" && isInvalidRange ? (
        <p className="form__error" style={{ marginTop: "12px", color: "#ef4444" }}>
          A data final deve ser maior ou igual à data inicial.
        </p>
      ) : period === "custom" && !(dateFrom && dateTo) ? (
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
          {(dashboard) => (
            <>
              <ROICard params={params} />
              <DashboardMetrics dashboard={dashboard} />
              <ProcedureRankingTable params={params} />
            </>
          )}
        </AsyncBoundary>
      )}
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
        <dt>Lucro real</dt>
        <dd>{formatBRL(money(dashboard.net_profit))}</dd>
      </div>

      {showFixedExpenses && (
        <div className="dashboard__metric">
          <dt>Lucro real do mês</dt>
          <dd>
            {formatBRL(money(net_profit_after_fixed_expenses))}
            <span className="dashboard__metric-note">
              (após despesas fixas de {formatBRL(money(fixed_expenses_total))})
            </span>
          </dd>
        </div>
      )}

      {dashboard.breakeven_remaining_amount != null && (
        <div
          className={`dashboard__metric dashboard__metric--wide${
            dashboard.breakeven_alert ? " dashboard__metric--alert" : ""
          }`}
        >
          <dt>Ponto de equilíbrio do mês</dt>
          <dd>
            {Number(dashboard.breakeven_remaining_amount) > 0 ? (
              <>
                Faltam {formatBRL(money(dashboard.breakeven_remaining_amount))} em vendas para cobrir seus custos fixos este mês
                {dashboard.breakeven_remaining_sessions_estimate != null && (
                  <span className="dashboard__metric-note">
                    ~{dashboard.breakeven_remaining_sessions_estimate}{" "}
                    {dashboard.breakeven_remaining_sessions_estimate === 1 ? "atendimento" : "atendimentos"}, pelo seu ticket médio dos últimos meses
                  </span>
                )}
              </>
            ) : (
              "Você já cobriu seus custos fixos este mês 🎉"
            )}
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
