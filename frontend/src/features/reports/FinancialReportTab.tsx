import { useState } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatBRL, formatRate } from "@/lib/money/format";
import { money, rate } from "@/lib/money/money";
import { useDashboard } from "@/features/dashboard/hooks";
import type { Dashboard, DashboardParams } from "@/features/dashboard/api";
import { ExpensesByCategoryChart } from "@/features/dashboard/ExpensesByCategoryChart";
import { ProfitByServiceChart } from "@/features/dashboard/ProcedureChartsSection";
import { IconDownload, IconWallet } from "@/ui/icons";
import { downloadCsv } from "./exportApi";
import styles from "./ReportsPage.module.css";

type Props = {
  params: DashboardParams;
};

export function FinancialReportTab({ params }: Props) {
  const query = useDashboard(params);
  const [exporting, setExporting] = useState(false);

  async function handleExportSales() {
    try {
      setExporting(true);
      await downloadCsv("sales", "relatorio-vendas.csv");
    } catch {
      alert("Não foi possível gerar a exportação de vendas no momento.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className={styles.page}>
      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando dados financeiros…</p>}
        empty={<p>Nenhum dado financeiro registrado no período selecionado.</p>}
        isEmpty={(d) => !d.has_any_data}
      >
        {(dashboard) => (
          <>
            <div className={styles.sectionHeader}>
              <div className={styles.sectionTitleGroup}>
                <div className={styles.sectionIcon}>
                  <IconWallet width="18" height="18" />
                </div>
                <div>
                  <h2 className={styles.sectionTitle}>Indicadores Financeiros</h2>
                  <p className={styles.sectionSubtitle}>
                    Faturamento, lucratividade líquida e fluxo de caixa do período
                  </p>
                </div>
              </div>
              <button
                type="button"
                className={styles.exportBtn}
                onClick={handleExportSales}
                disabled={exporting}
              >
                <IconDownload width="16" height="16" />
                <span>{exporting ? "Baixando…" : "Exportar Vendas (CSV)"}</span>
              </button>
            </div>

            {renderFinancialKpis(dashboard)}

            <div className={styles.chartsGrid}>
              <ProfitByServiceChart params={params} />
              <ExpensesByCategoryChart />
            </div>
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}

function renderFinancialKpis(dashboard: Dashboard) {
  const { fixed_expenses_total, net_profit_after_fixed_expenses } = dashboard;
  const showFixedExpenses = fixed_expenses_total != null && net_profit_after_fixed_expenses != null;
  const breakevenCovered =
    dashboard.breakeven_remaining_amount != null
      ? !(Number(dashboard.breakeven_remaining_amount) > 0)
      : null;

  return (
    <div className={styles.metricGrid}>
      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Faturamento Bruto</span>
        <strong className={styles.kpiValue}>
          {formatBRL(money(dashboard.gross_revenue))}
        </strong>
        <span className={styles.kpiNote}>
          {dashboard.sale_count} {dashboard.sale_count === 1 ? "venda" : "vendas"} registradas
        </span>
      </div>

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Lucro Real</span>
        <strong className={styles.kpiValue} style={{ color: "var(--accent)" }}>
          {formatBRL(money(dashboard.net_profit))}
        </strong>
        <span className={styles.kpiNote}>
          Após abatimento dos custos de insumos e taxas
        </span>
      </div>

      {showFixedExpenses && (
        <div className={styles.kpiCard}>
          <span className={styles.kpiLabel}>Lucro Real do Mês</span>
          <strong className={styles.kpiValue}>
            {formatBRL(money(net_profit_after_fixed_expenses))}
          </strong>
          <span className={styles.kpiNote}>
            Após dedução de {formatBRL(money(fixed_expenses_total))} em despesas fixas
          </span>
        </div>
      )}

      {dashboard.breakeven_remaining_amount != null && (
        <div
          className={`${styles.kpiCard} ${
            breakevenCovered ? styles.kpiCardSuccess : styles.kpiCardAlert
          }`}
        >
          <span className={styles.kpiLabel}>Ponto de Equilíbrio</span>
          <strong className={styles.kpiValue} style={{ fontSize: "16px" }}>
            {breakevenCovered ? (
              "Custos cobertos! 🎉"
            ) : (
              <>Faltam {formatBRL(money(dashboard.breakeven_remaining_amount))}</>
            )}
          </strong>
          <span className={styles.kpiNote}>
            {breakevenCovered
              ? "Você já cobriu seus custos fixos deste mês"
              : dashboard.breakeven_remaining_sessions_estimate != null
                ? `Estimativa de ~${dashboard.breakeven_remaining_sessions_estimate} atendimentos para equilíbrio`
                : "Necessário para pagar despesas fixas"}
          </span>
        </div>
      )}

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Margem Média</span>
        <strong className={styles.kpiValue}>
          {dashboard.average_margin != null ? formatRate(rate(dashboard.average_margin)) : "—"}
        </strong>
        <span className={styles.kpiNote}>Retorno percentual sobre as vendas</span>
      </div>

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Ticket Médio</span>
        <strong className={styles.kpiValue}>
          {dashboard.average_ticket != null ? formatBRL(money(dashboard.average_ticket)) : "—"}
        </strong>
        <span className={styles.kpiNote}>Valor médio por venda realizada</span>
      </div>

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Valores a Receber</span>
        <strong className={styles.kpiValue}>
          {formatBRL(money(dashboard.receivable_amount))}
        </strong>
        <span className={styles.kpiNote}>Saldos pendentes ou parcelamentos futuros</span>
      </div>

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Atendimentos Realizados</span>
        <strong className={styles.kpiValue}>{dashboard.session_count}</strong>
        <span className={styles.kpiNote}>
          Sessões executadas e concluídas no período
        </span>
      </div>
    </div>
  );
}
