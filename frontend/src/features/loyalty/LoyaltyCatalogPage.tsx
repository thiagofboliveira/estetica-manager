import { Link } from "react-router-dom";
import { useLoyaltyOverview } from "./useLoyalty";
import { LoyaltyRewardsManager } from "./LoyaltyRewardsManager";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./LoyaltyCatalogPage.module.css";

export function LoyaltyCatalogPage() {
  const { data: overview } = useLoyaltyOverview();

  const totalPoints = overview?.total_active_points ?? 0;
  const totalValue = overview?.total_value_in_currency
    ? formatBRL(money(Number(overview.total_value_in_currency).toFixed(2)))
    : "R$ 0,00";

  const totalMembers = overview?.tier_counts
    ? Object.values(overview.tier_counts).reduce((acc, curr) => acc + curr, 0)
    : 0;

  const totalReferrals = overview?.total_referrals_count ?? 0;
  const convertedReferrals = overview?.total_converted_referrals ?? 0;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Clube VIP &amp; Catálogo de Recompensas</h1>
          <p className={styles.subtitle}>
            Gerencie seu catálogo de benefícios resgatáveis por pontos, acompanhe a circulação de
            pontos e estimule a fidelização e indicações das suas clientes.
          </p>
        </div>
        <div>
          <Link
            to="/financeiro?tab=loyalty"
            className="button button--secondary"
            style={{ fontSize: "0.84rem", display: "inline-flex", alignItems: "center", gap: "6px" }}
          >
            <span>⚙️ Regras Financeiras do VIP &rarr;</span>
          </Link>
        </div>
      </header>

      {/* Visão Geral Rápida do Programa */}
      <section className={styles.statsGrid} aria-label="Métricas do Clube VIP">
        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Pontos em Circulação</span>
            <span className={styles.statIcon}>⭐</span>
          </div>
          <div className={styles.statValue}>{totalPoints.toLocaleString("pt-BR")} pts</div>
          <span className={styles.statHint}>
            Equivale a <strong>{totalValue}</strong> em créditos potenciais
          </span>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Membros no Clube VIP</span>
            <span className={styles.statIcon}>👑</span>
          </div>
          <div className={styles.statValue}>{totalMembers} clientes</div>
          <div className={styles.tiersList}>
            <span className={styles.tierTag}>🥉 {overview?.tier_counts?.BRONZE ?? 0}</span>
            <span className={styles.tierTag}>🥈 {overview?.tier_counts?.SILVER ?? 0}</span>
            <span className={styles.tierTag}>🥇 {overview?.tier_counts?.GOLD ?? 0}</span>
            <span className={styles.tierTag}>💎 {overview?.tier_counts?.DIAMOND ?? 0}</span>
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statHeader}>
            <span className={styles.statLabel}>Traga uma Amiga</span>
            <span className={styles.statIcon}>👭</span>
          </div>
          <div className={styles.statValue}>{convertedReferrals} convertidas</div>
          <span className={styles.statHint}>
            de {totalReferrals} amigas indicadas pelas clientes
          </span>
        </div>
      </section>

      {/* Seção Principal: Gestor do Catálogo de Recompensas */}
      <main className={styles.catalogSection}>
        <LoyaltyRewardsManager />
      </main>
    </div>
  );
}
