import { Link } from "react-router-dom";
import type { DashboardParams } from "@/features/dashboard/api";
import { ProcedureRankingTable } from "@/features/dashboard/ProcedureRankingTable";
import { ProfitByServiceChart, AppointmentsByServiceChart } from "@/features/dashboard/ProcedureChartsSection";
import { IconSparkles, IconTrendingUp, IconArrowRight } from "@/ui/icons";
import styles from "./ReportsPage.module.css";

type Props = {
  params: DashboardParams;
};

export function ProceduresReportTab({ params }: Props) {
  return (
    <div className={styles.page}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTitleGroup}>
          <div className={styles.sectionIcon}>
            <IconSparkles width="18" height="18" />
          </div>
          <div>
            <h2 className={styles.sectionTitle}>Relatório de Procedimentos e Lucratividade</h2>
            <p className={styles.sectionSubtitle}>
              Ranking detalhado de procedimentos por faturamento, margem e volume de atendimentos
            </p>
          </div>
        </div>
      </div>

      <div className={styles.chartsGrid}>
        <ProfitByServiceChart params={params} />
        <AppointmentsByServiceChart params={params} />
      </div>

      <div className={styles.actionBanner}>
        <div className={styles.actionBannerText}>
          <strong>Deseja testar novos valores ou ajustar sua margem de lucro?</strong>
          <span>
            Simule preços considerando custos de insumos, taxas de cartão e impostos antes de precificar.
          </span>
        </div>
        <Link to="/simulador" className={styles.actionBannerBtn}>
          <IconTrendingUp width="16" height="16" />
          <span>Abrir Simulador de Preço</span>
          <IconArrowRight width="16" height="16" />
        </Link>
      </div>

      <ProcedureRankingTable params={params} />
    </div>
  );
}
