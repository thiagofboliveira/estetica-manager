import { useState, useMemo } from "react";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useAgenda, useOpenPackages } from "@/features/agenda/hooks";
import type { OpenPackage } from "@/features/agenda/api";
import type { DashboardParams } from "@/features/dashboard/api";
import { AppointmentsByServiceChart } from "@/features/dashboard/ProcedureChartsSection";
import { IconCalendar, IconDownload } from "@/ui/icons";
import { downloadCsv } from "./exportApi";
import type { PeriodDateRange } from "./types";
import styles from "./ReportsPage.module.css";

type Props = {
  dateRange: PeriodDateRange;
  params: DashboardParams;
};

export function AppointmentsReportTab({ dateRange, params }: Props) {
  const agendaQuery = useAgenda(dateRange.from, dateRange.to);
  const openPackagesQuery = useOpenPackages();
  const [exporting, setExporting] = useState(false);

  async function handleExportSessions() {
    try {
      setExporting(true);
      await downloadCsv("sessions", "relatorio-agendamentos.csv");
    } catch {
      alert("Não foi possível gerar a exportação de agendamentos no momento.");
    } finally {
      setExporting(false);
    }
  }

  const items = agendaQuery.data ?? [];

  const stats = useMemo(() => {
    let completed = 0;
    let scheduled = 0;
    let noShow = 0;
    let cancelled = 0;
    let publicBookings = 0;

    for (const item of items) {
      if (item.type === "BOOKING") {
        publicBookings++;
      }
      switch (item.status) {
        case "COMPLETED":
          completed++;
          break;
        case "SCHEDULED":
        case "CONFIRMED":
        case "PROVISIONAL":
          scheduled++;
          break;
        case "NO_SHOW":
          noShow++;
          break;
        case "CANCELLED":
          cancelled++;
          break;
      }
    }

    const total = items.length;
    const concludedOrMissed = completed + noShow;
    const attendanceRate = concludedOrMissed > 0 ? Math.round((completed / concludedOrMissed) * 100) : null;
    const noShowRate = concludedOrMissed > 0 ? Math.round((noShow / concludedOrMissed) * 100) : null;
    const cancelRate = total > 0 ? Math.round((cancelled / total) * 100) : null;

    return {
      total,
      completed,
      scheduled,
      noShow,
      cancelled,
      publicBookings,
      attendanceRate,
      noShowRate,
      cancelRate,
    };
  }, [agendaQuery.data]);

  const openPackages: OpenPackage[] = openPackagesQuery.data ?? [];

  return (
    <div className={styles.page}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTitleGroup}>
          <div className={styles.sectionIcon}>
            <IconCalendar width="18" height="18" />
          </div>
          <div>
            <h2 className={styles.sectionTitle}>Relatório de Agendamentos e Presença</h2>
            <p className={styles.sectionSubtitle}>
              Acompanhamento de sessões, taxa de comparecimento, faltas e reservas
            </p>
          </div>
        </div>
        <button
          type="button"
          className={styles.exportBtn}
          onClick={handleExportSessions}
          disabled={exporting}
        >
          <IconDownload width="16" height="16" />
          <span>{exporting ? "Baixando…" : "Exportar Atendimentos (CSV)"}</span>
        </button>
      </div>

      <AsyncBoundary
        query={agendaQuery}
        skeleton={<p>Carregando dados da agenda…</p>}
        empty={<p>Nenhum agendamento encontrado no período selecionado.</p>}
      >
        {() => (
          <>
            <div className={styles.metricGrid}>
              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Total na Agenda</span>
                <strong className={styles.kpiValue}>{stats.total}</strong>
                <span className={styles.kpiNote}>
                  Sessões e agendamentos previstos no período
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Realizados / Concluídos</span>
                <strong className={styles.kpiValue} style={{ color: "#10b981" }}>
                  {stats.completed}
                </strong>
                <span className={styles.kpiNote}>
                  Atendimentos com execução finalizada
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Agendados / Confirmados</span>
                <strong className={styles.kpiValue} style={{ color: "var(--accent)" }}>
                  {stats.scheduled}
                </strong>
                <span className={styles.kpiNote}>
                  Horários marcados aguardando atendimento
                </span>
              </div>

              <div className={`${styles.kpiCard} ${stats.noShow > 0 ? styles.kpiCardAlert : ""}`}>
                <span className={styles.kpiLabel}>Faltas (No-Show)</span>
                <strong className={styles.kpiValue} style={{ color: stats.noShow > 0 ? "#ef4444" : undefined }}>
                  {stats.noShow}
                </strong>
                <span className={styles.kpiNote}>
                  {stats.noShowRate !== null
                    ? `${stats.noShowRate}% de taxa de falta sobre agendamentos`
                    : "Nenhuma falta registrada no período"}
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Cancelamentos</span>
                <strong className={styles.kpiValue}>{stats.cancelled}</strong>
                <span className={styles.kpiNote}>
                  {stats.cancelRate !== null ? `${stats.cancelRate}% do total` : "Nenhum cancelamento"}
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Pelo Link Público</span>
                <strong className={styles.kpiValue}>{stats.publicBookings}</strong>
                <span className={styles.kpiNote}>
                  Originados da sua bio do Instagram ou WhatsApp
                </span>
              </div>
            </div>

            {/* Visualização de Eficiência da Agenda */}
            <div className={styles.sectionCard}>
              <h3 className={styles.sectionTitle}>Eficiência e Taxa de Comparecimento</h3>
              <p className={styles.sectionSubtitle}>
                Indicador direto de fidelidade e pontualidade da sua carteira de clientes
              </p>

              <div className={styles.rateBars}>
                <div className={styles.rateBarRow}>
                  <div className={styles.rateBarLabelRow}>
                    <span>Taxa de Comparecimento</span>
                    <strong>{stats.attendanceRate !== null ? `${stats.attendanceRate}%` : "—"}</strong>
                  </div>
                  <div className={styles.rateBarTrack}>
                    <div
                      className={styles.rateBarFill}
                      style={{
                        width: `${stats.attendanceRate ?? 0}%`,
                        background: "#10b981",
                      }}
                    />
                  </div>
                </div>

                <div className={styles.rateBarRow}>
                  <div className={styles.rateBarLabelRow}>
                    <span>Taxa de Faltas (No-Show)</span>
                    <strong style={{ color: stats.noShow > 0 ? "#ef4444" : undefined }}>
                      {stats.noShowRate !== null ? `${stats.noShowRate}%` : "0%"}
                    </strong>
                  </div>
                  <div className={styles.rateBarTrack}>
                    <div
                      className={styles.rateBarFill}
                      style={{
                        width: `${stats.noShowRate ?? 0}%`,
                        background: "#ef4444",
                      }}
                    />
                  </div>
                </div>

                <div className={styles.rateBarRow}>
                  <div className={styles.rateBarLabelRow}>
                    <span>Taxa de Cancelamentos</span>
                    <strong style={{ color: stats.cancelled > 0 ? "#f59e0b" : undefined }}>
                      {stats.cancelRate !== null ? `${stats.cancelRate}%` : "0%"}
                    </strong>
                  </div>
                  <div className={styles.rateBarTrack}>
                    <div
                      className={styles.rateBarFill}
                      style={{
                        width: `${stats.cancelRate ?? 0}%`,
                        background: "#f59e0b",
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Gráfico de procedimentos mais agendados */}
            <div className={styles.chartsGrid}>
              <AppointmentsByServiceChart params={params} />

              {/* Card de Pacotes em Aberto */}
              <div className={styles.sectionCard}>
                <div className={styles.sectionHeader}>
                  <div>
                    <h3 className={styles.sectionTitle}>Pacotes com Sessões em Aberto</h3>
                    <p className={styles.sectionSubtitle}>
                      Pacotes vendidos que ainda possuem sessões pendentes para agendar
                    </p>
                  </div>
                  <span className={`${styles.badge} ${styles.badgeAccent}`}>
                    {openPackages.length} {openPackages.length === 1 ? "pacote" : "pacotes"}
                  </span>
                </div>

                {openPackages.length === 0 ? (
                  <p className={styles.sectionSubtitle}>
                    Nenhum pacote com sessões pendentes no momento. Todos os atendimentos estão em dia!
                  </p>
                ) : (
                  <div className={styles.tableWrap}>
                    <table className={styles.table}>
                      <thead>
                        <tr>
                          <th>Paciente</th>
                          <th>Procedimento</th>
                          <th>Saldo de Sessões</th>
                        </tr>
                      </thead>
                      <tbody>
                        {openPackages.slice(0, 5).map((pkg) => (
                          <tr key={pkg.sale_item_id}>
                            <td>
                              <strong>{pkg.patient_name}</strong>
                            </td>
                            <td>{pkg.procedure_name}</td>
                            <td>
                              <span className={`${styles.badge} ${styles.badgeWarning}`}>
                                {pkg.pending_sessions} de {pkg.total_sessions} pendentes
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Tabela de Atendimentos no Período */}
            {items.length > 0 && (
              <div className={styles.sectionCard}>
                <div className={styles.sectionHeader}>
                  <h3 className={styles.sectionTitle}>Atendimentos no Período ({items.length})</h3>
                </div>
                <div className={styles.tableWrap}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Data/Hora</th>
                        <th>Paciente</th>
                        <th>Procedimento</th>
                        <th>Origem</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.slice(0, 10).map((item) => (
                        <tr key={item.id}>
                          <td>
                            {new Date(item.scheduled_at).toLocaleString("pt-BR", {
                              day: "2-digit",
                              month: "2-digit",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td>
                            <strong>{item.patient_name}</strong>
                          </td>
                          <td>{item.procedure_name}</td>
                          <td>
                            {item.type === "BOOKING" ? (
                              <span className={`${styles.badge} ${styles.badgeAccent}`}>Link Público</span>
                            ) : (
                              <span className={`${styles.badge} ${styles.badgeNeutral}`}>Direto</span>
                            )}
                          </td>
                          <td>{renderStatusBadge(item.status)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}

function renderStatusBadge(status: string) {
  switch (status) {
    case "COMPLETED":
      return <span className={`${styles.badge} ${styles.badgeSuccess}`}>Concluído</span>;
    case "CONFIRMED":
      return <span className={`${styles.badge} ${styles.badgeSuccess}`}>Confirmado</span>;
    case "SCHEDULED":
    case "PROVISIONAL":
      return <span className={`${styles.badge} ${styles.badgeAccent}`}>Agendado</span>;
    case "NO_SHOW":
      return <span className={`${styles.badge} ${styles.badgeDanger}`}>Falta (No-show)</span>;
    case "CANCELLED":
      return <span className={`${styles.badge} ${styles.badgeNeutral}`}>Cancelado</span>;
    default:
      return <span className={`${styles.badge} ${styles.badgeNeutral}`}>{status}</span>;
  }
}
