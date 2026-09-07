import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useActiveVials } from "./useVials";
import { CreateVialModal } from "./VialModals";
import {
  IconDroplet,
  IconAlertTriangle,
  IconPlus,
  IconArrowRight,
} from "@/ui/icons";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./BotoxVialCard.module.css";

export function BotoxVialCard() {
  const { data: vials = [], isLoading } = useActiveVials();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const totalRemainingUnits = useMemo(() => {
    return vials.reduce((sum, v) => sum + (v.remaining_units || 0), 0);
  }, [vials]);

  const totalRiskBrl = useMemo(() => {
    return vials.reduce(
      (sum, v) => sum + (v.estimated_loss_risk ? Number(v.estimated_loss_risk) : 0),
      0
    );
  }, [vials]);

  const criticalVials = useMemo(() => {
    return vials.filter((v) => v.days_remaining <= 5 || v.is_expired);
  }, [vials]);

  if (isLoading) {
    return null;
  }

  const hasVials = vials.length > 0;
  const isDanger = criticalVials.length > 0;

  return (
    <section className={styles.container} aria-label="Controle de Estoque de Insumos">
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <div
            className={`${styles.iconWrapper} ${
              isDanger ? styles.iconDanger : hasVials ? styles.iconWarning : ""
            }`}
          >
            <IconDroplet width="20" height="20" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
              <h2 className={styles.title}>Estoque & Insumos Críticos</h2>
              {isDanger && (
                <span className={`${styles.badge} ${styles.badgeDanger}`}>
                  {criticalVials.length} frasco(s) crítico(s)
                </span>
              )}
            </div>
            <p className={styles.subtitle}>
              {hasVials
                ? `${vials.length} frasco(s) aberto(s) • ${totalRemainingUnits} U restantes • Validade clínica de 30 dias`
                : "Nenhum frasco de Botox® ou insumo aberto no momento"}
            </p>
          </div>
        </div>

        <div className={styles.headerActions}>
          <button
            type="button"
            className={styles.actionBtnSmall}
            onClick={() => setIsCreateOpen(true)}
          >
            <IconPlus width="14" height="14" />
            <span>+ Abrir Frasco</span>
          </button>
          <Link
            to="/estoque"
            className={`${styles.actionBtnSmall} ${styles.actionBtnPrimary}`}
          >
            <span>Gerenciar Estoque</span>
            <IconArrowRight width="14" height="14" />
          </Link>
        </div>
      </div>

      {totalRiskBrl > 0 && (
        <div className={styles.riskBanner} style={{ marginTop: "4px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1 }}>
            <IconAlertTriangle width="16" height="16" color="#d97706" />
            <span className={styles.riskText}>
              Atenção: <strong>{formatBRL(money(totalRiskBrl.toFixed(2)))}</strong> em risco de desperdício caso os frascos não sejam aproveitados a tempo.
            </span>
          </div>
          <Link
            to="/retornos"
            className={styles.actionBtnSmall}
            style={{ borderColor: "#d97706", color: "#b45309", background: "rgba(245, 158, 11, 0.1)" }}
          >
            <span>Chamar Clientes para Retoque</span>
            <IconArrowRight width="12" height="12" />
          </Link>
        </div>
      )}

      {isCreateOpen && (
        <CreateVialModal onClose={() => setIsCreateOpen(false)} />
      )}
    </section>
  );
}
