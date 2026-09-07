import { useState, useMemo } from "react";
import { useAuth } from "@/lib/auth/AuthContext";
import { ClinicScopeSelector, type ClinicScopeValue } from "@/features/clinic-management/ClinicScopeSelector";
import type { DashboardParams, DashboardPeriod } from "@/features/dashboard/api";
import {
  IconWallet,
  IconCalendar,
  IconTarget,
  IconSparkles,
} from "@/ui/icons";
import type { ReportCategory } from "./types";
import { resolvePeriodDateRange } from "./types";
import { FinancialReportTab } from "./FinancialReportTab";
import { AppointmentsReportTab } from "./AppointmentsReportTab";
import { RetentionReportTab } from "./RetentionReportTab";
import { ProceduresReportTab } from "./ProceduresReportTab";
import styles from "./ReportsPage.module.css";

const CATEGORIES: { id: ReportCategory; label: string; icon: typeof IconWallet }[] = [
  { id: "financial", label: "Financeiro", icon: IconWallet },
  { id: "appointments", label: "Agendamentos", icon: IconCalendar },
  { id: "retention", label: "Retornos & Fidelização", icon: IconTarget },
  { id: "procedures", label: "Procedimentos", icon: IconSparkles },
];

const PERIOD_OPTIONS: { value: DashboardPeriod; label: string }[] = [
  { value: "today", label: "Hoje" },
  { value: "last_7_days", label: "Últimos 7 dias" },
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Mês anterior" },
  { value: "custom", label: "Personalizado" },
];

export function ReportsPage() {
  const { user } = useAuth();
  const [clinicScope, setClinicScope] = useState<ClinicScopeValue>(() => ({
    scope: user?.role === "admin" && user?.clinic_id ? "clinic" : "me",
  }));
  const [category, setCategory] = useState<ReportCategory>("financial");
  const [period, setPeriod] = useState<DashboardPeriod>("this_month");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const isInvalidRange = period === "custom" && Boolean(dateFrom && dateTo && dateFrom > dateTo);

  const params: DashboardParams = useMemo(
    () => ({
      period,
      date_from: period === "custom" && !isInvalidRange ? dateFrom : undefined,
      date_to: period === "custom" && !isInvalidRange ? dateTo : undefined,
      scope: clinicScope.scope,
      professional_id: clinicScope.professional_id,
    }),
    [period, dateFrom, dateTo, isInvalidRange, clinicScope],
  );

  const dateRange = useMemo(
    () => resolvePeriodDateRange(period, dateFrom, dateTo),
    [period, dateFrom, dateTo],
  );

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <h1 className={styles.title}>Relatórios & Análises</h1>
          <p className={styles.subtitle}>
            Visão integrada da saúde financeira, ocupação da agenda, fidelização e desempenho do catálogo
          </p>
        </div>
        <ClinicScopeSelector
          value={clinicScope}
          onChange={setClinicScope}
        />
      </header>

      {/* Botões no topo segregando relatórios/dashboards por categoria */}
      <nav className={styles.categoryNav} role="tablist" aria-label="Categorias de relatórios">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const isActive = category === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={`${styles.categoryBtn} ${isActive ? styles.categoryBtnActive : ""}`}
              onClick={() => setCategory(cat.id)}
            >
              <span className={styles.categoryIcon}>
                <Icon width="16" height="16" />
              </span>
              <span>{cat.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Barra de Filtro de Período Compartilhada */}
      <div className={styles.toolbar}>
        <div className={styles.periodGroup} role="group" aria-label="Filtro de período">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`${styles.periodBtn} ${period === opt.value ? styles.periodBtnActive : ""}`}
              aria-pressed={period === opt.value}
              onClick={() => setPeriod(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {period === "custom" && (
          <div className={styles.customDateRow}>
            <label className={styles.dateInputGroup}>
              <span>De</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                aria-label="Data inicial"
              />
            </label>
            <label className={styles.dateInputGroup}>
              <span>Até</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                aria-label="Data final"
              />
            </label>
          </div>
        )}
      </div>

      {period === "custom" && isInvalidRange ? (
        <p className="form__error" style={{ color: "#ef4444" }}>
          A data final deve ser maior ou igual à data inicial.
        </p>
      ) : period === "custom" && !(dateFrom && dateTo) ? (
        <p style={{ color: "var(--text-muted)" }}>
          Escolha as duas datas para visualizar o relatório personalizado.
        </p>
      ) : (
        <main>
          {category === "financial" && <FinancialReportTab params={params} />}
          {category === "appointments" && (
            <AppointmentsReportTab dateRange={dateRange} />
          )}
          {category === "retention" && <RetentionReportTab params={params} />}
          {category === "procedures" && <ProceduresReportTab params={params} />}
        </main>
      )}
    </div>
  );
}
