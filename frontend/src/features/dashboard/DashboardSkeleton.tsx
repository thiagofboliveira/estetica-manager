import s from "./DashboardSkeleton.module.css";

/**
 * DashboardSkeleton
 *
 * Exibido enquanto a query principal do dashboard (has_any_data) ainda não
 * resolveu. Replica o layout real com blocos animados (shimmer), evitando o
 * flash de onboarding falso que ocorria quando `dashboardQuery.data` era
 * undefined e `hasAnySale` era avaliado como false.
 */
export function DashboardSkeleton() {
  return (
    <div className={s.page} aria-busy="true" aria-label="Carregando painel de controle">
      {/* Header */}
      <header className={s.header}>
        <div>
          <div className={`${s.bone} ${s.headerTitle}`} />
          <div className={`${s.bone} ${s.headerSub}`} />
        </div>
        <div className={`${s.bone} ${s.headerChip}`} />
      </header>

      {/* Quick Actions */}
      <div className={s.quickActions}>
        {[140, 110, 130, 145, 120].map((w, i) => (
          <div key={i} className={`${s.bone} ${s.quickBtn}`} style={{ width: w }} />
        ))}
      </div>

      {/* Today Cards */}
      <div className={s.todayGrid}>
        {[0, 1].map((i) => (
          <div key={i} className={s.todayCard}>
            <div className={s.cardTopRow}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div className={`${s.bone} ${s.cardIcon}`} />
                <div className={`${s.bone} ${s.cardTitle}`} />
              </div>
              <div className={`${s.bone} ${s.cardBadge}`} />
            </div>
            <div className={`${s.bone} ${s.appointmentRow}`} />
            <div className={`${s.bone} ${s.appointmentRow}`} />
            <div className={`${s.bone} ${s.cardLink}`} />
          </div>
        ))}
      </div>

      {/* Financial Section */}
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div className={s.sectionHeader}>
          <div className={`${s.bone} ${s.sectionTitle}`} />
          <div className={`${s.bone} ${s.sectionLink}`} />
        </div>
        <div className={s.metricGrid}>
          {[0, 1, 2].map((i) => (
            <div key={i} className={s.kpiCard}>
              <div className={`${s.bone} ${s.kpiLabel}`} />
              <div className={`${s.bone} ${s.kpiValue}`} />
              <div className={`${s.bone} ${s.kpiNote}`} />
            </div>
          ))}
        </div>
      </div>

      {/* Opportunities */}
      <div className={s.opportunitiesGrid}>
        {[0, 1].map((i) => (
          <div key={i} className={s.opportunityCard}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div className={`${s.bone} ${s.oppTitle}`} />
              <div className={`${s.bone} ${s.oppDesc}`} />
              <div className={`${s.bone} ${s.oppDescSm}`} />
              <div className={`${s.bone} ${s.oppHighlight}`} />
              <div className={`${s.bone} ${s.oppSub}`} />
            </div>
            <div className={`${s.bone} ${s.oppLink}`} />
          </div>
        ))}
      </div>
    </div>
  );
}
