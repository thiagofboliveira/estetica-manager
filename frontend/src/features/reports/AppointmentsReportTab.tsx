import { useState, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { useAgenda, useOpenPackages } from "@/features/agenda/hooks";
import type { AgendaItem, OpenPackage } from "@/features/agenda/api";
import { IconCalendar, IconDownload } from "@/ui/icons";
import { downloadCsv } from "./exportApi";
import type { PeriodDateRange } from "./types";
import chartStyles from "@/features/dashboard/charts.module.css";
import styles from "./ReportsPage.module.css";

type Props = {
  dateRange: PeriodDateRange;
};

export function AppointmentsReportTab({ dateRange }: Props) {
  // Permite que a profissional alterne rapidamente para ver os próximos 30 dias caso tenha agendado no futuro
  const [scope, setScope] = useState<"period" | "next_30_days">("period");
  const [exporting, setExporting] = useState(false);

  const effectiveRange = useMemo(() => {
    if (scope === "next_30_days") {
      const now = new Date();
      const in30Days = new Date();
      in30Days.setDate(in30Days.getDate() + 30);
      const pad = (n: number) => n.toString().padStart(2, "0");
      const fmt = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
      return { from: fmt(now), to: fmt(in30Days) };
    }
    return dateRange;
  }, [scope, dateRange]);

  const agendaQuery = useAgenda(effectiveRange.from, effectiveRange.to);
  const openPackagesQuery = useOpenPackages();

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
    const list = agendaQuery.data ?? [];
    let completed = 0;
    let scheduled = 0;
    let noShow = 0;
    let cancelled = 0;
    let publicBookings = 0;

    for (const item of list) {
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
        default:
          scheduled++;
          break;
      }
    }

    const total = list.length;
    const concludedOrMissed = completed + noShow;
    const attendanceRate =
      concludedOrMissed > 0 ? Math.round((completed / concludedOrMissed) * 100) : null;
    const noShowRate =
      concludedOrMissed > 0 ? Math.round((noShow / concludedOrMissed) * 100) : null;
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

  // Formata as datas para exibição visual amigável
  const rangeDisplay = useMemo(() => {
    const parse = (s: string) => {
      const [y, m, d] = s.split("-");
      return `${d}/${m}/${y}`;
    };
    return `${parse(effectiveRange.from)} até ${parse(effectiveRange.to)}`;
  }, [effectiveRange]);

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
              Exibindo agendamentos de <strong>{rangeDisplay}</strong> ({items.length} registro{items.length === 1 ? "" : "s"})
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Alternador rápido de escopo */}
          <div style={{ display: "inline-flex", background: "var(--bg-subtle)", padding: "3px", borderRadius: "8px", border: "1px solid var(--border)" }}>
            <button
              type="button"
              onClick={() => setScope("period")}
              style={{
                border: "none",
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "12.5px",
                fontWeight: 600,
                cursor: "pointer",
                background: scope === "period" ? "var(--bg-card)" : "transparent",
                color: scope === "period" ? "var(--text-h)" : "var(--text-muted)",
                boxShadow: scope === "period" ? "var(--shadow-sm)" : "none",
              }}
            >
              Filtro Selecionado
            </button>
            <button
              type="button"
              onClick={() => setScope("next_30_days")}
              style={{
                border: "none",
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "12.5px",
                fontWeight: 600,
                cursor: "pointer",
                background: scope === "next_30_days" ? "var(--bg-card)" : "transparent",
                color: scope === "next_30_days" ? "var(--text-h)" : "var(--text-muted)",
                boxShadow: scope === "next_30_days" ? "var(--shadow-sm)" : "none",
              }}
            >
              Próximos 30 dias
            </button>
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
      </div>

      <AsyncBoundary
        query={agendaQuery}
        skeleton={<p>Carregando dados da agenda…</p>}
        empty={<p>Nenhum agendamento encontrado no período selecionado.</p>}
        isEmpty={() => false}
      >
        {() => (
          <>
            <div className={styles.metricGrid}>
              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Total na Agenda</span>
                <strong className={styles.kpiValue}>{stats.total}</strong>
                <span className={styles.kpiNote}>
                  Sessões e agendamentos no intervalo selecionado
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

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Realizados / Concluídos</span>
                <strong className={styles.kpiValue} style={{ color: "#10b981" }}>
                  {stats.completed}
                </strong>
                <span className={styles.kpiNote}>
                  Atendimentos com execução finalizada
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
                    : "Nenhuma falta registrada"}
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
                Indicador de assiduidade das clientes no período analisado
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

            {/* Gráficos e Pacotes em Aberto */}
            <div className={styles.chartsGrid}>
              {/* Gráfico Real com os Procedimentos dos Agendamentos da Agenda */}
              <div className={chartStyles.card}>
                <div className={chartStyles.header}>
                  <div className={chartStyles.iconBadge}>
                    <IconCalendar width="16" height="16" />
                  </div>
                  <h3 className={chartStyles.title}>Procedimentos Mais Agendados</h3>
                </div>
                <p className={chartStyles.subtitle}>
                  Volume de sessões marcadas ou atendidas no período.
                </p>
                <ScheduledAppointmentsBarChart items={items} />
              </div>

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
            <div className={styles.sectionCard}>
              <div className={styles.sectionHeader}>
                <h3 className={styles.sectionTitle}>Atendimentos no Período ({items.length})</h3>
              </div>

              {items.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "13.5px", padding: "12px 0" }}>
                  Nenhum agendamento encontrado para o intervalo de <strong>{rangeDisplay}</strong>. Caso tenha agendado para outra data, alterne para <em>"Próximos 30 dias"</em> ou ajuste o filtro de período no topo.
                </p>
              ) : (
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
                      {items.map((item) => (
                        <tr key={item.id}>
                          <td>
                            {new Date(item.scheduled_at).toLocaleString("pt-BR", {
                              day: "2-digit",
                              month: "2-digit",
                              year: "numeric",
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
              )}
            </div>
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}

function ScheduledAppointmentsBarChart({ items }: { items: AgendaItem[] }) {
  const chartData = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of items) {
      const name = item.procedure_name || "Agendamento";
      counts.set(name, (counts.get(name) || 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
  }, [items]);

  if (chartData.length === 0) {
    return (
      <div className={chartStyles.emptyChart}>
        Nenhum agendamento registrado no período selecionado.
      </div>
    );
  }

  return (
    <div className={chartStyles.chartWrap}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
          <XAxis
            type="number"
            allowDecimals={false}
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            stroke="var(--border)"
          />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            tick={{ fill: "var(--text)", fontSize: 12 }}
            stroke="var(--border)"
          />
          <Tooltip
            cursor={{ fill: "var(--bg-subtle)" }}
            contentStyle={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
              color: "var(--text-h)",
            }}
            formatter={(value: any) => [
              `${value} agendamento${value === 1 ? "" : "s"}`,
              "Volume",
            ]}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
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
