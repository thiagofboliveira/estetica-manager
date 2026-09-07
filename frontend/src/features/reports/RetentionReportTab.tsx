import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { useRetentionCards, useReengagement } from "@/features/retention/hooks";
import type { DashboardParams } from "@/features/dashboard/api";
import { ROICard } from "@/features/dashboard/ROICard";
import { IconTarget, IconDownload, IconArrowRight, IconUsers } from "@/ui/icons";
import { downloadCsv } from "./exportApi";
import styles from "./ReportsPage.module.css";

type Props = {
  params: DashboardParams;
};

export function RetentionReportTab({ params }: Props) {
  const cardsQuery = useRetentionCards();
  const reengagementQuery = useReengagement(60, 1, 10);
  const [exporting, setExporting] = useState(false);

  async function handleExportPatients() {
    try {
      setExporting(true);
      await downloadCsv("patients", "relatorio-pacientes.csv");
    } catch {
      alert("Não foi possível gerar a exportação de pacientes no momento.");
    } finally {
      setExporting(false);
    }
  }

  const cards = cardsQuery.data ?? [];

  const metrics = useMemo(() => {
    let totalPotential = 0;
    let overdueCount = 0;
    let dueCount = 0;
    let upcomingCount = 0;

    for (const card of cards) {
      totalPotential += Number(card.total_potential_value || 0);
      const timing = card.primary_opportunity?.timing;
      if (timing === "OVERDUE") overdueCount++;
      else if (timing === "DUE") dueCount++;
      else if (timing === "UPCOMING") upcomingCount++;
    }

    return {
      totalPotential,
      totalCards: cards.length,
      overdueCount,
      dueCount,
      upcomingCount,
    };
  }, [cards]);

  const inactiveCount = reengagementQuery.data?.inactive_total_count ?? 0;
  const neverTreatedCount = reengagementQuery.data?.never_treated_total_count ?? 0;

  return (
    <div className={styles.page}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTitleGroup}>
          <div className={styles.sectionIcon}>
            <IconTarget width="18" height="18" />
          </div>
          <div>
            <h2 className={styles.sectionTitle}>Relatório de Retornos e Fidelização</h2>
            <p className={styles.sectionSubtitle}>
              Métricas do motor de recorrência, valor em aberto e retorno sobre investimento
            </p>
          </div>
        </div>
        <button
          type="button"
          className={styles.exportBtn}
          onClick={handleExportPatients}
          disabled={exporting}
        >
          <IconDownload width="16" height="16" />
          <span>{exporting ? "Baixando…" : "Exportar Pacientes (CSV)"}</span>
        </button>
      </div>

      {/* Card Oficial de Retorno do Investimento (ROI) */}
      <ROICard params={params} />

      <AsyncBoundary
        query={cardsQuery}
        skeleton={<p>Carregando oportunidades de retorno…</p>}
        empty={<p>Nenhuma oportunidade de retorno encontrada no momento.</p>}
      >
        {() => (
          <>
            <div className={styles.metricGrid}>
              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Valor Potencial na Mesa</span>
                <strong className={styles.kpiValue} style={{ color: "var(--accent)" }}>
                  {formatBRL(money(metrics.totalPotential.toFixed(2)))}
                </strong>
                <span className={styles.kpiNote}>
                  Em {metrics.totalCards} {metrics.totalCards === 1 ? "paciente com retorno previsto" : "pacientes com retorno previsto"}
                </span>
              </div>

              <div className={`${styles.kpiCard} ${metrics.overdueCount > 0 ? styles.kpiCardAlert : ""}`}>
                <span className={styles.kpiLabel}>Retornos em Atraso</span>
                <strong className={styles.kpiValue} style={{ color: metrics.overdueCount > 0 ? "#ef4444" : undefined }}>
                  {metrics.overdueCount}
                </strong>
                <span className={styles.kpiNote}>
                  Pacientes que já ultrapassaram o tempo ideal de retoque
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Retornos para Esta Semana</span>
                <strong className={styles.kpiValue} style={{ color: "#f59e0b" }}>
                  {metrics.dueCount}
                </strong>
                <span className={styles.kpiNote}>
                  Janela ideal de contato nos próximos dias
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Próximos Retornos</span>
                <strong className={styles.kpiValue}>{metrics.upcomingCount}</strong>
                <span className={styles.kpiNote}>
                  Procedimentos que vencerão nas próximas semanas
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Pacientes Inativos (+60 dias)</span>
                <strong className={styles.kpiValue}>{inactiveCount}</strong>
                <span className={styles.kpiNote}>
                  Clientes sem nenhum atendimento recente
                </span>
              </div>

              <div className={styles.kpiCard}>
                <span className={styles.kpiLabel}>Nunca Atendidos</span>
                <strong className={styles.kpiValue}>{neverTreatedCount}</strong>
                <span className={styles.kpiNote}>
                  Cadastrados que ainda não realizaram procedimento
                </span>
              </div>
            </div>

            {/* Banner de Ação Rápida */}
            <div className={styles.actionBanner}>
              <div className={styles.actionBannerText}>
                <strong>Pronta para transformar essas oportunidades em faturamento?</strong>
                <span>
                  O motor de retorno seleciona as clientes ideais para contato hoje, já com sugestão de mensagem no WhatsApp.
                </span>
              </div>
              <Link to="/retornos" className={styles.actionBannerBtn}>
                <span>Quem chamar hoje?</span>
                <IconArrowRight width="16" height="16" />
              </Link>
            </div>

            {/* Pipeline de Retenção */}
            <div className={styles.sectionCard}>
              <div className={styles.sectionHeader}>
                <div>
                  <h3 className={styles.sectionTitle}>Pipeline da Carteira de Clientes</h3>
                  <p className={styles.sectionSubtitle}>
                    Status das oportunidades monitoradas pelo motor de retenção inteligente
                  </p>
                </div>
                <div className={styles.sectionIcon}>
                  <IconUsers width="18" height="18" />
                </div>
              </div>

              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Paciente</th>
                      <th>Procedimento Indicado</th>
                      <th>Previsão</th>
                      <th>Valor Estimado</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cards.slice(0, 8).map((card) => {
                      const opp = card.primary_opportunity;
                      return (
                        <tr key={card.patient_id}>
                          <td>
                            <strong>{card.patient_name}</strong>
                          </td>
                          <td>{opp?.procedure_name ?? "Procedimento"}</td>
                          <td>
                            {opp?.timing === "OVERDUE" ? (
                              <span className={`${styles.badge} ${styles.badgeDanger}`}>
                                Atrasado há {Math.abs(opp.days_diff)} dias
                              </span>
                            ) : opp?.timing === "DUE" ? (
                              <span className={`${styles.badge} ${styles.badgeWarning}`}>
                                No prazo ideal
                              </span>
                            ) : (
                              <span className={`${styles.badge} ${styles.badgeNeutral}`}>
                                Em {opp?.days_diff ?? 0} dias
                              </span>
                            )}
                          </td>
                          <td>
                            <strong>{formatBRL(money(card.total_potential_value))}</strong>
                          </td>
                          <td>{renderOpportunityStatus(opp?.status)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </AsyncBoundary>
    </div>
  );
}

function renderOpportunityStatus(status?: string) {
  switch (status) {
    case "BOOKED":
      return <span className={`${styles.badge} ${styles.badgeSuccess}`}>Agendado</span>;
    case "CONTACTED":
      return <span className={`${styles.badge} ${styles.badgeAccent}`}>Em contato</span>;
    case "OPEN":
      return <span className={`${styles.badge} ${styles.badgeWarning}`}>Pendente de contato</span>;
    case "DECLINED":
      return <span className={`${styles.badge} ${styles.badgeNeutral}`}>Recusado</span>;
    default:
      return <span className={`${styles.badge} ${styles.badgeNeutral}`}>Em aberto</span>;
  }
}
