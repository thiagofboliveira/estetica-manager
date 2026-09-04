import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { Carousel } from "@/ui/Carousel";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import { useDashboard } from "./hooks";
import type { Dashboard, DashboardParams, DashboardPeriod } from "./api";

import { ProcedureRankingTable } from "./ProcedureRankingTable";
import { ProfitByServiceChart, AppointmentsByServiceChart } from "./ProcedureChartsSection";
import { ExpensesByCategoryChart } from "./ExpensesByCategoryChart";
import { OnboardingChecklist } from "@/features/onboarding/OnboardingChecklist";
import { ROICard } from "./ROICard";
import { MetricCard } from "./MetricCard";

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
 * F-013c: Ranking de procedimentos por faturamento e lucro real,
 * paginado (10/página) + gráficos de lucro e atendimentos (top 10) e
 * despesas fixas por categoria (GET /reports/expenses-by-category).
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
              <Carousel ariaLabel="Métricas do período" slidesPerView={3}>
                {buildMetricSlides(dashboard)}
              </Carousel>
              <Carousel ariaLabel="Gráficos financeiros" slidesPerView={1}>
                {[
                  <ExpensesByCategoryChart key="expenses" />,
                  <ProfitByServiceChart key="profit" params={params} />,
                  <AppointmentsByServiceChart key="appointments" params={params} />,
                ]}
              </Carousel>
              <ProcedureRankingTable params={params} />
            </>
          )}
        </AsyncBoundary>
      )}
    </div>
  );
}

// F5-02: cada métrica virou um slide do carrossel — mesma lógica
// condicional que existia no <dl> de grid (lucro do mês só com period
// this_month|last_month, ponto de equilíbrio só quando aplicável).
function buildMetricSlides(dashboard: Dashboard) {
  const { fixed_expenses_total, net_profit_after_fixed_expenses } = dashboard;
  const showFixedExpenses = fixed_expenses_total != null && net_profit_after_fixed_expenses != null;

  const slides = [
    <MetricCard key="revenue" label="Faturamento" value={formatBRL(money(dashboard.gross_revenue))} />,
    <MetricCard key="profit" label="Lucro real" value={formatBRL(money(dashboard.net_profit))} />,
  ];

  if (showFixedExpenses) {
    slides.push(
      <MetricCard
        key="profit-month"
        label="Lucro real do mês"
        value={formatBRL(money(net_profit_after_fixed_expenses))}
        note={`(após despesas fixas de ${formatBRL(money(fixed_expenses_total))})`}
      />,
    );
  }

  if (dashboard.breakeven_remaining_amount != null) {
    const covered = !(Number(dashboard.breakeven_remaining_amount) > 0);
    slides.push(
      <MetricCard
        key="breakeven"
        label="Ponto de equilíbrio do mês"
        alert={dashboard.breakeven_alert}
        value={
          covered ? (
            "Você já cobriu seus custos fixos este mês 🎉"
          ) : (
            <>Faltam {formatBRL(money(dashboard.breakeven_remaining_amount))} em vendas para cobrir seus custos fixos este mês</>
          )
        }
        note={
          !covered && dashboard.breakeven_remaining_sessions_estimate != null
            ? `~${dashboard.breakeven_remaining_sessions_estimate} ${
                dashboard.breakeven_remaining_sessions_estimate === 1 ? "atendimento" : "atendimentos"
              }, pelo seu ticket médio dos últimos meses`
            : undefined
        }
      />,
    );
  }

  slides.push(
    <MetricCard key="receivable" label="A receber" value={formatBRL(money(dashboard.receivable_amount))} />,
    <MetricCard
      key="margin"
      label="Margem média"
      value={dashboard.average_margin != null ? formatRate(rate(dashboard.average_margin)) : "—"}
    />,
    <MetricCard
      key="ticket"
      label="Ticket médio"
      value={dashboard.average_ticket != null ? formatBRL(money(dashboard.average_ticket)) : "—"}
    />,
    <MetricCard
      key="sales-sessions"
      label="Vendas e atendimentos"
      value={
        <>
          {dashboard.sale_count} {dashboard.sale_count === 1 ? "venda" : "vendas"}, {dashboard.session_count}{" "}
          {dashboard.session_count === 1 ? "atendimento" : "atendimentos"}
        </>
      }
    />,
  );

  return slides;
}
