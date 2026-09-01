import { Link } from "react-router-dom";
import { useROI } from "./hooks";
import type { DashboardParams } from "./api";
import { formatBRL } from "@/lib/money/format";
import type { Money } from "@/lib/money/money";
import { IconTrendingUp, IconArrowRight, IconSparkles } from "@/ui/icons";
import styles from "./ROICard.module.css";

type Props = {
  params: DashboardParams;
};

export function ROICard({ params }: Props) {
  const { data: roi, isLoading } = useROI(params);

  // Mostrar apenas para "this_month" ou "last_month"
  if (params.period !== "this_month" && params.period !== "last_month") {
    return null;
  }

  if (isLoading) {
    return (
      <div className={styles.cardLoading} aria-busy="true">
        <span className={styles.loadingPulse} />
        <span>Calculando receita recuperada...</span>
      </div>
    );
  }

  if (!roi) {
    return null;
  }

  const hasData = roi.attributed_sale_count > 0;
  const isThisMonth = params.period === "this_month";
  const label = isThisMonth ? "deste mês" : "do mês passado";

  return (
    <section className={styles.card} aria-label="Retorno sobre Investimento">
      <div className={styles.topRow}>
        <div className={styles.header}>
          <div className={styles.iconBadge}>
            <IconTrendingUp width="18" height="18" />
          </div>
          <div className={styles.headerTitles}>
            <h3 className={styles.title}>Receita Recuperada {label}</h3>
            <span className={styles.subtitle}>Retornos agendados via régua de WhatsApp (últimos 21 dias)</span>
          </div>
        </div>

        {roi.roi_ratio && (
          <div className={styles.ratioBadge}>
            <IconSparkles width="14" height="14" />
            <span>ROI: {roi.roi_ratio} sobre a mensalidade</span>
          </div>
        )}
      </div>

      {hasData ? (
        <div className={styles.content}>
          <div className={styles.mainValue}>
            <span className={styles.amount}>{formatBRL(roi.attributed_revenue as Money)}</span>
            <span className={styles.subValue}>
              {roi.patients_reactivated} paciente{roi.patients_reactivated !== 1 ? "s" : ""} reativada{roi.patients_reactivated !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      ) : (
        <div className={styles.emptyState}>
          <p className={styles.emptyText}>Nenhuma paciente reativada neste período ainda.</p>
          <Link to="/retornos" className={styles.link}>
            <span>Acessar "Quem chamar hoje" para iniciar disparos</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>
      )}
    </section>
  );
}
