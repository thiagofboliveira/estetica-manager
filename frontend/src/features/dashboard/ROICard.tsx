import { Link } from "react-router-dom";
import { useROI } from "./hooks";
import type { DashboardParams } from "./api";
import { formatBRL } from "@/lib/money/format";
import type { Money } from "@/lib/money/money";
import { IconTrendingUp, IconArrowRight, IconSparkles, IconInfo } from "@/ui/icons";
import styles from "./ROICard.module.css";

const ATTRIBUTION_EXPLANATION =
  "Só contamos quando você registrou o contato E a paciente estava atrasada para o retorno E ela comprou em até 21 dias depois. Não contamos quem provavelmente voltaria sozinha.";

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
            <h3 className={styles.title}>
              Receita de pacientes contatadas {label}
              <span
                className={styles.infoIcon}
                title={ATTRIBUTION_EXPLANATION}
                aria-label={ATTRIBUTION_EXPLANATION}
              >
                <IconInfo width="14" height="14" />
              </span>
            </h3>
            <span className={styles.subtitle}>Retornos agendados via régua de WhatsApp (últimos 21 dias)</span>
          </div>
        </div>

        <div className={styles.badges}>
          {roi.is_estimated && (
            <span className={styles.estimatedBadge} title="Calculado com taxa estimada, ainda não confirmada por você">
              cálculo estimado
            </span>
          )}
          {roi.roi_ratio && (
            <div className={styles.ratioBadge}>
              <IconSparkles width="14" height="14" />
              <span>ROI: {roi.roi_ratio} sobre a mensalidade</span>
            </div>
          )}
        </div>
      </div>

      {hasData ? (
        <div className={styles.content}>
          <div className={styles.mainValue}>
            <span className={styles.amount}>{formatBRL(roi.attributed_revenue as Money)}</span>
            <span className={styles.subValue}>
              em {roi.attributed_sale_count} venda{roi.attributed_sale_count !== 1 ? "s" : ""}
            </span>
            <span className={styles.subValue}>
              {roi.patients_reactivated} paciente{roi.patients_reactivated !== 1 ? "s" : ""} reativada{roi.patients_reactivated !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      ) : (
        <div className={styles.emptyState}>
          <p className={styles.emptyText}>Nenhuma venda de paciente contatada pelo sistema neste período ainda.</p>
          <Link to="/retornos" className={styles.link}>
            <span>Acessar "Quem chamar hoje" para iniciar disparos</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>
      )}

      <Link to="/como-calculamos" className={styles.footerLink}>
        Como calculamos isso? →
      </Link>
    </section>
  );
}
