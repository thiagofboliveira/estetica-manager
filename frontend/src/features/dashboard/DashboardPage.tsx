import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { formatLocalDate } from "@/lib/format/date";
import { useAuth } from "@/lib/auth/AuthContext";
import { ClinicScopeSelector, type ClinicScopeValue } from "@/features/clinic-management/ClinicScopeSelector";
import { useDashboard } from "./hooks";
import type { Dashboard } from "./api";
import { useAgenda, useUnconfirmedSessions, useOpenPackages } from "@/features/agenda/hooks";
import { useRetentionCards } from "@/features/retention/hooks";
import { OnboardingChecklist } from "@/features/onboarding/OnboardingChecklist";
import { ROICard } from "./ROICard";
import {
  IconCalendar,
  IconPlus,
  IconSparkles,
  IconWhatsApp,
  IconTarget,
  IconArrowRight,
  IconWallet,
  IconBarChart,
  IconCheck,
} from "@/ui/icons";
import styles from "./DashboardPage.module.css";

export function DashboardPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.role === "superadmin" || Boolean(user?.is_superuser);
  const [clinicScope, setClinicScope] = useState<ClinicScopeValue>(() => ({
    scope: isAdmin && user?.clinic_id ? "clinic" : "me",
  }));

  const todayStr = useMemo(() => formatLocalDate(new Date()), []);
  const todayDateFormatted = useMemo(() => {
    return new Date().toLocaleDateString("pt-BR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }, []);

  const dashboardParams = useMemo(
    () => ({
      period: "this_month" as const,
      scope: clinicScope.scope,
      professional_id: clinicScope.professional_id,
    }),
    [clinicScope],
  );
  const dashboardQuery = useDashboard(dashboardParams);
  const todayAgendaQuery = useAgenda(todayStr, todayStr, {
    scope: clinicScope.scope,
    professional_id: clinicScope.professional_id,
  });
  const unconfirmedQuery = useUnconfirmedSessions();
  const retentionQuery = useRetentionCards();
  const openPackagesQuery = useOpenPackages();

  const todaySessions = todayAgendaQuery.data ?? [];
  const unconfirmedSessions = unconfirmedQuery.data ?? [];
  const retentionCards = retentionQuery.data ?? [];
  const openPackages = openPackagesQuery.data ?? [];

  // Cálculos de oportunidades quentes
  const retentionStats = useMemo(() => {
    let totalPotential = 0;
    let dueCount = 0;
    for (const card of retentionCards) {
      totalPotential += Number(card.total_potential_value || 0);
      const timing = card.primary_opportunity?.timing;
      if (timing === "DUE" || timing === "OVERDUE") {
        dueCount++;
      }
    }
    return { totalPotential, dueCount, totalCards: retentionCards.length };
  }, [retentionCards]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.greetingGroup}>
          <h1 className={styles.greeting}>Painel de Controle</h1>
          <p className={styles.dateSubtitle}>{todayDateFormatted}</p>
        </div>
        <ClinicScopeSelector
          value={clinicScope}
          onChange={setClinicScope}
          professionalsCount={dashboardQuery.data?.professionals_count}
        />
      </header>

      {/* Checklist de primeiro acesso (não bloqueante) */}
      <OnboardingChecklist hasAnySale={Boolean(dashboardQuery.data?.has_any_data)} />

      {/* Barra de Ações Rápidas em 1 Clique */}
      <section className={styles.quickActions} aria-label="Ações rápidas">
        <Link to="/vendas/nova" className={`${styles.quickActionBtn} ${styles.quickActionBtnPrimary}`}>
          <IconPlus width="16" height="16" />
          <span>Nova Venda</span>
        </Link>
        <Link to="/vendas/nova-pacote" className={styles.quickActionBtn}>
          <IconSparkles width="16" height="16" />
          <span>Vender Pacote</span>
        </Link>
        <Link to="/agenda" className={styles.quickActionBtn}>
          <IconCalendar width="16" height="16" />
          <span>Novo Agendamento</span>
        </Link>
        <Link to="/agenda/rapido" className={styles.quickActionBtn}>
          <IconWhatsApp width="16" height="16" />
          <span>Modo Ocupado (Horários)</span>
        </Link>
        <Link to="/retornos" className={styles.quickActionBtn}>
          <IconTarget width="16" height="16" />
          <span>Quem Chamar Hoje</span>
        </Link>
      </section>

      {/* Foco Operacional de Hoje */}
      <div className={styles.todayGrid}>
        {/* Card 1: Atendimentos de Hoje */}
        <div className={styles.todayCard}>
          <div className={styles.cardHeader}>
            <div className={styles.cardHeaderTitle}>
              <div className={styles.cardIcon}>
                <IconCalendar width="18" height="18" />
              </div>
              <h2 className={styles.cardTitle}>Atendimentos de Hoje</h2>
            </div>
            <span className={styles.countBadge}>
              {todaySessions.length} {todaySessions.length === 1 ? "cliente" : "clientes"}
            </span>
          </div>

          {todaySessions.length === 0 ? (
            <div className={styles.cardEmpty}>
              <p>Nenhum atendimento marcado para hoje.</p>
              <p style={{ fontSize: "12.5px" }}>
                Aproveite para divulgar horários livres pelo WhatsApp ou chamar clientes com retorno previsto!
              </p>
            </div>
          ) : (
            <div className={styles.appointmentList}>
              {todaySessions.slice(0, 3).map((session) => (
                <div key={session.id} className={styles.appointmentItem}>
                  <div className={styles.appointmentInfo}>
                    <span className={styles.appointmentPatient}>{session.patient_name}</span>
                    <span className={styles.appointmentProcedure}>
                      {session.procedure_name}
                      {session.professional_name ? ` • ${session.professional_name}` : ""}
                    </span>
                  </div>
                  <span className={styles.appointmentTime}>
                    {new Date(session.scheduled_at).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              ))}
              {todaySessions.length > 3 && (
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  + {todaySessions.length - 3} outros atendimentos hoje
                </span>
              )}
            </div>
          )}

          <Link to="/agenda" className={styles.cardLink}>
            <span>Ver agenda completa</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>

        {/* Card 2: Confirmações de Presença (Anti-No-Show) */}
        <div className={styles.todayCard}>
          <div className={styles.cardHeader}>
            <div className={styles.cardHeaderTitle}>
              <div
                className={styles.cardIcon}
                style={{
                  background: unconfirmedSessions.length > 0 ? "rgba(245, 158, 11, 0.12)" : undefined,
                  color: unconfirmedSessions.length > 0 ? "#d97706" : undefined,
                }}
              >
                {unconfirmedSessions.length > 0 ? (
                  <IconWhatsApp width="18" height="18" />
                ) : (
                  <IconCheck width="18" height="18" />
                )}
              </div>
              <h2 className={styles.cardTitle}>Confirmações de Presença</h2>
            </div>
            {unconfirmedSessions.length > 0 && (
              <span
                className={styles.countBadge}
                style={{ background: "rgba(245, 158, 11, 0.15)", color: "#d97706" }}
              >
                {unconfirmedSessions.length} pendente{unconfirmedSessions.length === 1 ? "" : "s"}
              </span>
            )}
          </div>

          {unconfirmedSessions.length === 0 ? (
            <div className={styles.cardEmpty}>
              <p>Tudo em dia! 🎉</p>
              <p style={{ fontSize: "12.5px" }}>
                Não há confirmações pendentes para amanhã. Suas clientes agendadas já estão confirmadas.
              </p>
            </div>
          ) : (
            <div className={styles.appointmentList}>
              <p style={{ fontSize: "13px", color: "var(--text)", margin: 0 }}>
                Você tem <strong>{unconfirmedSessions.length}</strong> atendimento
                {unconfirmedSessions.length === 1 ? "" : "s"} agendado
                {unconfirmedSessions.length === 1 ? "" : "s"} para amanhã aguardando confirmação no WhatsApp para evitar faltas.
              </p>
              {unconfirmedSessions.slice(0, 2).map((item) => (
                <div key={item.session_id} className={styles.appointmentItem}>
                  <div className={styles.appointmentInfo}>
                    <span className={styles.appointmentPatient}>{item.patient_name}</span>
                    <span className={styles.appointmentProcedure}>{item.procedure_name}</span>
                  </div>
                  <a
                    href={item.whatsapp_link}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      color: "#16a34a",
                      fontWeight: 600,
                      fontSize: "12.5px",
                    }}
                  >
                    Confirmar
                  </a>
                </div>
              ))}
            </div>
          )}

          <Link to="/agenda" className={styles.cardLink}>
            <span>Gerenciar na agenda</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>
      </div>

      {/* Resumo Financeiro do Mês (Visão Executiva) */}
      <AsyncBoundary
        query={dashboardQuery}
        skeleton={<p>Carregando resumo do mês…</p>}
        empty={
          <EmptyState
            tone="first-run"
            title="Nenhuma venda registrada ainda"
            body="Registre sua primeira venda para ver o faturamento e lucro do mês."
          />
        }
        isEmpty={(d) => !d.has_any_data}
      >
        {(dashboard) => (
          <section className={styles.section} aria-label="Resumo Financeiro do Mês">
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Resumo Financeiro deste Mês</h2>
              <Link to="/relatorios" className={styles.sectionLink}>
                <span>Ver relatórios detalhados</span>
                <IconArrowRight width="14" height="14" />
              </Link>
            </div>

            {renderMonthlyKpis(dashboard)}

            {/* ROI do Motor de Retenção */}
            <ROICard params={dashboardParams} />
          </section>
        )}
      </AsyncBoundary>

      {/* Oportunidades & Pacotes em Aberto */}
      <div className={styles.opportunitiesGrid}>
        {/* Card de Oportunidades de Retorno */}
        <div className={styles.opportunityCard}>
          <div className={styles.opportunityContent}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--accent)" }}>
              <IconTarget width="18" height="18" />
              <h3 className={styles.opportunityTitle}>Oportunidades de Retorno</h3>
            </div>
            <p className={styles.opportunityDesc}>
              Clientes na janela ideal para retoque ou novas sessões esta semana.
            </p>
            <div className={styles.opportunityHighlight}>
              {formatBRL(money(retentionStats.totalPotential.toFixed(2)))}
            </div>
            <span style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
              {retentionStats.dueCount} {retentionStats.dueCount === 1 ? "cliente pronta" : "clientes prontas"} para contato hoje
            </span>
          </div>
          <Link to="/retornos" className={styles.cardLink}>
            <span>Chamar clientes no WhatsApp</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>

        {/* Card de Pacotes em Aberto */}
        <div className={styles.opportunityCard}>
          <div className={styles.opportunityContent}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--accent)" }}>
              <IconSparkles width="18" height="18" />
              <h3 className={styles.opportunityTitle}>Pacotes com Sessões em Aberto</h3>
            </div>
            <p className={styles.opportunityDesc}>
              Pacotes já comercializados que possuem créditos de sessões aguardando agendamento.
            </p>
            <div className={styles.opportunityHighlight}>
              {openPackages.length} {openPackages.length === 1 ? "pacote ativo" : "pacotes ativos"}
            </div>
            <span style={{ fontSize: "12.5px", color: "var(--text-muted)" }}>
              Incentive suas clientes a agendarem para manter a frequência
            </span>
          </div>
          <Link to="/agenda" className={styles.cardLink}>
            <span>Agendar sessões pendentes</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>
      </div>

      {/* Atalhos Rápidos para a Central de Relatórios */}
      <section className={styles.section} aria-label="Acesso Rápido a Relatórios">
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Central de Relatórios</h2>
          <Link to="/relatorios" className={styles.sectionLink}>
            <span>Abrir todos</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>

        <div className={styles.reportsHub}>
          <Link to="/relatorios" className={styles.reportShortcut}>
            <div className={styles.reportShortcutIcon}>
              <IconWallet width="16" height="16" />
            </div>
            <div className={styles.reportShortcutText}>
              <span className={styles.reportShortcutTitle}>Financeiro</span>
              <span className={styles.reportShortcutDesc}>Despesas e ticket médio</span>
            </div>
          </Link>

          <Link to="/relatorios" className={styles.reportShortcut}>
            <div className={styles.reportShortcutIcon}>
              <IconCalendar width="16" height="16" />
            </div>
            <div className={styles.reportShortcutText}>
              <span className={styles.reportShortcutTitle}>Agendamentos</span>
              <span className={styles.reportShortcutDesc}>Presença e no-show</span>
            </div>
          </Link>

          <Link to="/relatorios" className={styles.reportShortcut}>
            <div className={styles.reportShortcutIcon}>
              <IconTarget width="16" height="16" />
            </div>
            <div className={styles.reportShortcutText}>
              <span className={styles.reportShortcutTitle}>Fidelização</span>
              <span className={styles.reportShortcutDesc}>Retornos e reativação</span>
            </div>
          </Link>

          <Link to="/relatorios" className={styles.reportShortcut}>
            <div className={styles.reportShortcutIcon}>
              <IconBarChart width="16" height="16" />
            </div>
            <div className={styles.reportShortcutText}>
              <span className={styles.reportShortcutTitle}>Procedimentos</span>
              <span className={styles.reportShortcutDesc}>Ranking de lucratividade</span>
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}

function renderMonthlyKpis(dashboard: Dashboard) {
  const { fixed_expenses_total, net_profit_after_fixed_expenses } = dashboard;
  const breakevenCovered =
    dashboard.breakeven_remaining_amount != null
      ? !(Number(dashboard.breakeven_remaining_amount) > 0)
      : null;

  return (
    <div className={styles.metricGrid}>
      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Faturamento do Mês</span>
        <strong className={styles.kpiValue}>
          {formatBRL(money(dashboard.gross_revenue))}
        </strong>
        <span className={styles.kpiNote}>
          {dashboard.sale_count} {dashboard.sale_count === 1 ? "venda" : "vendas"} realizadas
        </span>
      </div>

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>Lucro Real do Mês</span>
        <strong className={styles.kpiValue} style={{ color: "var(--accent)" }}>
          {net_profit_after_fixed_expenses != null
            ? formatBRL(money(net_profit_after_fixed_expenses))
            : formatBRL(money(dashboard.net_profit))}
        </strong>
        <span className={styles.kpiNote}>
          {fixed_expenses_total != null
            ? `Após deduzir ${formatBRL(money(fixed_expenses_total))} em despesas fixas`
            : "Após custos de insumos e taxas"}
        </span>
      </div>

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
              ? "Você já cobriu suas despesas fixas este mês"
              : dashboard.breakeven_remaining_sessions_estimate != null
                ? `Estimativa de ~${dashboard.breakeven_remaining_sessions_estimate} atendimentos para equilíbrio`
                : "Necessário para pagar despesas fixas"}
          </span>
        </div>
      )}

      <div className={styles.kpiCard}>
        <span className={styles.kpiLabel}>A Receber</span>
        <strong className={styles.kpiValue}>
          {formatBRL(money(dashboard.receivable_amount))}
        </strong>
        <span className={styles.kpiNote}>Saldos pendentes ou parcelamentos</span>
      </div>
    </div>
  );
}
