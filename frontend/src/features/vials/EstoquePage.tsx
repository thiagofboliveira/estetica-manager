import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  useActiveVials,
  useAllVials,
  useFinishVial,
} from "./useVials";
import type { OpenVial } from "./vialsApi";
import { CreateVialModal, ConsumeVialModal } from "./VialModals";
import {
  IconDroplet,
  IconAlertTriangle,
  IconPlus,
  IconTarget,
  IconCheck,
} from "@/ui/icons";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./EstoquePage.module.css";

export function EstoquePage() {
  const { data: activeVials = [], isLoading: loadingActive } = useActiveVials();
  const { data: allVials = [], isLoading: loadingAll } = useAllVials();

  const [activeTab, setActiveTab] = useState<"active" | "history">("active");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedVialForConsume, setSelectedVialForConsume] = useState<OpenVial | null>(null);

  const finishedVials = useMemo(() => {
    return allVials.filter((v) => v.status !== "active");
  }, [allVials]);

  const totalRemainingUnits = useMemo(() => {
    return activeVials.reduce((sum, v) => sum + (v.remaining_units || 0), 0);
  }, [activeVials]);

  const totalRiskBrl = useMemo(() => {
    return activeVials.reduce((sum, v) => sum + (v.estimated_loss_risk ? Number(v.estimated_loss_risk) : 0), 0);
  }, [activeVials]);

  const isLoading = loadingActive || loadingAll;

  if (isLoading) {
    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.titleArea}>
            <h1 className={styles.title}>Estoque & Insumos Críticos</h1>
          </div>
        </header>
        <p style={{ color: "var(--text-muted, #64748b)" }}>Carregando insumos e frascos...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.titleArea}>
          <h1 className={styles.title}>Estoque & Insumos Críticos</h1>
          <p className={styles.subtitle}>
            Monitore a validade de frascos de toxina botulínica e bioestimuladores abertos para zerar desperdícios.
          </p>
        </div>

        <button
          type="button"
          className={styles.primaryBtn}
          onClick={() => setIsCreateOpen(true)}
        >
          <IconPlus width="16" height="16" />
          <span>+ Abrir Novo Frasco</span>
        </button>
      </header>

      {/* Top Metrics */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Frascos em Aberto</span>
          <span className={styles.metricValue}>{activeVials.length}</span>
          <span className={styles.metricNote}>Em refrigeração / uso clínico</span>
        </div>

        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Unidades Disponíveis</span>
          <span className={styles.metricValue} style={{ color: "var(--accent, #6366f1)" }}>
            {totalRemainingUnits} U
          </span>
          <span className={styles.metricNote}>Saldo total para procedimentos</span>
        </div>

        <div className={`${styles.metricCard} ${totalRiskBrl > 0 ? styles.metricCardAlert : ""}`}>
          <span className={styles.metricLabel}>Risco de Desperdício</span>
          <span className={styles.metricValue} style={{ color: totalRiskBrl > 0 ? "#b45309" : undefined }}>
            {formatBRL(money(totalRiskBrl.toFixed(2)))}
          </span>
          <span className={styles.metricNote}>
            {totalRiskBrl > 0 ? "Em frascos abertos com validade correndo" : "Nenhum valor em risco"}
          </span>
        </div>

        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Frascos Finalizados</span>
          <span className={styles.metricValue}>{finishedVials.length}</span>
          <span className={styles.metricNote}>Histórico de consumo concluído</span>
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabGroup}>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "active" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("active")}
        >
          Frascos Abertos ({activeVials.length})
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "history" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("history")}
        >
          Histórico ({finishedVials.length})
        </button>
      </div>

      {/* Tab 1: Frascos Abertos */}
      {activeTab === "active" && (
        <>
          {activeVials.length === 0 ? (
            <div className={styles.emptyState}>
              <div style={{ color: "var(--text-muted)", marginBottom: "4px" }}>
                <IconDroplet width="40" height="40" />
              </div>
              <h3 className={styles.emptyTitle}>Nenhum frasco aberto no momento</h3>
              <p className={styles.emptyDesc}>
                Abriu um novo frasco de Botox® ou bioestimulador hoje? Registre aqui para monitorar o saldo de unidades e receber alertas automáticos de validade clínica.
              </p>
              <button
                type="button"
                className={styles.primaryBtn}
                onClick={() => setIsCreateOpen(true)}
              >
                <IconPlus width="16" height="16" />
                <span>Registrar Novo Frasco</span>
              </button>
            </div>
          ) : (
            <div className={styles.vialsGrid}>
              {activeVials.map((vial) => (
                <ActiveVialCard
                  key={vial.id}
                  vial={vial}
                  onConsume={() => setSelectedVialForConsume(vial)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Tab 2: Histórico */}
      {activeTab === "history" && (
        <>
          {finishedVials.length === 0 ? (
            <div className={styles.emptyState}>
              <h3 className={styles.emptyTitle}>Nenhum frasco finalizado ainda</h3>
              <p className={styles.emptyDesc}>
                Conforme você consumir ou finalizar frascos em aberto, o registro histórico completo ficará armazenado aqui para auditoria de custos.
              </p>
            </div>
          ) : (
            <div className={styles.vialsGrid}>
              {finishedVials.map((vial) => (
                <HistoryVialCard key={vial.id} vial={vial} />
              ))}
            </div>
          )}
        </>
      )}

      {/* Modais */}
      {isCreateOpen && (
        <CreateVialModal onClose={() => setIsCreateOpen(false)} />
      )}

      {selectedVialForConsume && (
        <ConsumeVialModal
          vial={selectedVialForConsume}
          onClose={() => setSelectedVialForConsume(null)}
        />
      )}
    </div>
  );
}

function ActiveVialCard({
  vial,
  onConsume,
}: {
  vial: OpenVial;
  onConsume: () => void;
}) {
  const finishMutation = useFinishVial();
  const percentageRemaining = Math.max(
    0,
    Math.min(100, Math.round((vial.remaining_units / vial.total_units) * 100))
  );

  const isCritical = vial.days_remaining <= 5 || vial.is_expired;
  const isModerate = vial.days_remaining <= 10 && !isCritical;

  let badgeClass = styles.badgeNormal;
  if (vial.is_expired) {
    badgeClass = styles.badgeDanger;
  } else if (isCritical) {
    badgeClass = styles.badgeDanger;
  } else if (isModerate) {
    badgeClass = styles.badgeWarning;
  }

  const handleFinish = async () => {
    if (confirm(`Deseja finalizar o frasco "${vial.medication_name}"?`)) {
      await finishMutation.mutateAsync(vial.id);
    }
  };

  const lossValue = vial.estimated_loss_risk ? Number(vial.estimated_loss_risk) : 0;

  return (
    <div className={styles.vialCard}>
      <div className={styles.vialCardHeader}>
        <div>
          <h3 className={styles.vialName}>{vial.medication_name}</h3>
          <div className={styles.vialMeta}>
            {vial.lot_number ? `Lote: ${vial.lot_number} • ` : ""}
            Aberto em {new Date(vial.opened_at).toLocaleDateString("pt-BR")}
            {vial.cost_price ? ` • Custo: ${formatBRL(money(vial.cost_price))}` : ""}
          </div>
        </div>
        <span className={`${styles.badge} ${badgeClass}`}>
          {vial.is_expired
            ? "Vencido"
            : vial.days_remaining === 0
            ? "Vence hoje!"
            : `${vial.days_remaining} dia(s) restante(s)`}
        </span>
      </div>

      <div className={styles.progressArea}>
        <div className={styles.progressTrack}>
          <div
            className={styles.progressFill}
            style={{
              width: `${percentageRemaining}%`,
              background:
                isCritical || vial.is_expired
                  ? "var(--danger, #dc2626)"
                  : isModerate
                  ? "#d97706"
                  : undefined,
            }}
          />
        </div>
        <div className={styles.progressInfo}>
          <span className={styles.progressCurrent}>
            {vial.remaining_units} de {vial.total_units} {vial.unit_measure} ({percentageRemaining}%)
          </span>
          <span>
            {vial.used_units} {vial.unit_measure} aplicadas
          </span>
        </div>
      </div>

      {lossValue > 0 && (
        <div className={styles.riskBanner}>
          <IconAlertTriangle width="16" height="16" color="#d97706" />
          <span>
            <strong>{formatBRL(money(lossValue.toFixed(2)))}</strong> em risco de desperdício caso vença.
          </span>
          <Link
            to="/retornos"
            className={styles.actionBtn}
            style={{ marginLeft: "auto", borderColor: "#d97706", color: "#b45309", background: "rgba(245, 158, 11, 0.1)" }}
          >
            <IconTarget width="12" height="12" />
            <span>Chamar Retoque</span>
          </Link>
        </div>
      )}

      <div className={styles.vialActions}>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.actionBtnPrimary}`}
          onClick={onConsume}
          disabled={vial.remaining_units <= 0}
        >
          <IconPlus width="14" height="14" />
          <span>Abater Aplicação</span>
        </button>

        <button
          type="button"
          className={styles.actionBtn}
          onClick={handleFinish}
          disabled={finishMutation.isPending}
        >
          <IconCheck width="14" height="14" />
          <span>Finalizar Frasco</span>
        </button>
      </div>
    </div>
  );
}

function HistoryVialCard({ vial }: { vial: OpenVial }) {
  return (
    <div className={styles.vialCard} style={{ opacity: 0.85 }}>
      <div className={styles.vialCardHeader}>
        <div>
          <h3 className={styles.vialName}>{vial.medication_name}</h3>
          <div className={styles.vialMeta}>
            {vial.lot_number ? `Lote: ${vial.lot_number} • ` : ""}
            Aberto em {new Date(vial.opened_at).toLocaleDateString("pt-BR")}
            {vial.cost_price ? ` • Custo: ${formatBRL(money(vial.cost_price))}` : ""}
          </div>
        </div>
        <span
          className={styles.badge}
          style={{
            background: vial.status === "finished" ? "rgba(100, 116, 139, 0.15)" : "rgba(239, 68, 68, 0.15)",
            color: vial.status === "finished" ? "#475569" : "#dc2626",
          }}
        >
          {vial.status === "finished" ? "Finalizado" : "Descartado"}
        </span>
      </div>

      <div className={styles.progressArea}>
        <div className={styles.progressInfo}>
          <span>
            Total aproveitado: <strong>{vial.used_units}</strong> de {vial.total_units} {vial.unit_measure}
          </span>
          {vial.remaining_units > 0 && (
            <span style={{ color: "#dc2626" }}>
              Descarte: {vial.remaining_units} {vial.unit_measure}
            </span>
          )}
        </div>
      </div>

      {vial.notes && (
        <p style={{ fontSize: "12.5px", color: "var(--text-muted)", margin: 0 }}>
          {vial.notes}
        </p>
      )}
    </div>
  );
}
