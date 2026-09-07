import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useActiveVials,
  useCreateVial,
  useConsumeVial,
  useFinishVial,
} from "./useVials";
import type { OpenVial } from "./vialsApi";
import {
  IconDroplet,
  IconAlertTriangle,
  IconPlus,
  IconX,
  IconTarget,
  IconCheck,
} from "@/ui/icons";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./BotoxVialCard.module.css";

export function BotoxVialCard() {
  const { data: vials = [], isLoading } = useActiveVials();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedVialForConsume, setSelectedVialForConsume] = useState<OpenVial | null>(null);

  if (isLoading) {
    return null;
  }

  const hasVials = vials.length > 0;

  return (
    <section className={styles.container} aria-label="Controle de Frascos Abertos">
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <div className={`${styles.iconWrapper} ${hasVials ? styles.iconWarning : ""}`}>
            <IconDroplet width="20" height="20" />
          </div>
          <div>
            <h2 className={styles.title}>Insumos Críticos & Toxina Botulínica</h2>
            <p className={styles.subtitle}>
              {hasVials
                ? `${vials.length} frasco(s) aberto(s) sob monitoramento de validade clínica (30 dias)`
                : "Nenhum frasco aberto no momento — evite desperdícios monitorando a reconstituição"}
            </p>
          </div>
        </div>

        <div className={styles.headerActions}>
          <button
            type="button"
            className={`${styles.actionBtnSmall} ${hasVials ? "" : styles.actionBtnPrimary}`}
            onClick={() => setIsCreateOpen(true)}
          >
            <IconPlus width="14" height="14" />
            <span>Abrir Frasco</span>
          </button>
        </div>
      </div>

      {!hasVials ? (
        <div className={styles.emptyStateCard}>
          <div className={styles.emptyText}>
            <span className={styles.emptyTitle}>Nenhum frasco em aberto</span>
            <span className={styles.emptySubtitle}>
              Abriu um frasco de Botox hoje? Registre aqui para receber alertas automáticos antes do vencimento.
            </span>
          </div>
          <button
            type="button"
            className={`${styles.actionBtnSmall} ${styles.actionBtnPrimary}`}
            onClick={() => setIsCreateOpen(true)}
          >
            <IconPlus width="14" height="14" />
            <span>Registrar Novo Frasco</span>
          </button>
        </div>
      ) : (
        <div className={styles.vialsList}>
          {vials.map((vial) => (
            <VialItem
              key={vial.id}
              vial={vial}
              onConsume={() => setSelectedVialForConsume(vial)}
            />
          ))}
        </div>
      )}

      {isCreateOpen && (
        <CreateVialModal onClose={() => setIsCreateOpen(false)} />
      )}

      {selectedVialForConsume && (
        <ConsumeVialModal
          vial={selectedVialForConsume}
          onClose={() => setSelectedVialForConsume(null)}
        />
      )}
    </section>
  );
}

function VialItem({
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

  let fillClass = styles.progressBarFill;
  if (isCritical || vial.is_expired) {
    fillClass = `${styles.progressBarFill} ${styles.progressBarFillDanger}`;
  } else if (isModerate) {
    fillClass = `${styles.progressBarFill} ${styles.progressBarFillWarning}`;
  }

  const handleFinish = async () => {
    if (confirm(`Deseja finalizar o frasco "${vial.medication_name}"?`)) {
      await finishMutation.mutateAsync(vial.id);
    }
  };

  const lossValue = vial.estimated_loss_risk ? Number(vial.estimated_loss_risk) : 0;

  return (
    <div className={styles.vialItem}>
      <div className={styles.vialItemHeader}>
        <div>
          <div className={styles.vialName}>
            {vial.medication_name}
            {vial.lot_number ? ` • Lote ${vial.lot_number}` : ""}
          </div>
          <div className={styles.vialMeta}>
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

      <div className={styles.progressBarContainer}>
        <div className={styles.progressBarTrack}>
          <div
            className={fillClass}
            style={{ width: `${percentageRemaining}%` }}
          />
        </div>
        <div className={styles.progressInfo}>
          <span className={styles.progressCurrent}>
            {vial.remaining_units} de {vial.total_units} {vial.unit_measure} restantes ({percentageRemaining}%)
          </span>
          <span>
            {vial.used_units} {vial.unit_measure} aplicadas
          </span>
        </div>
      </div>

      {lossValue > 0 && (
        <div className={styles.riskBanner}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <IconAlertTriangle width="16" height="16" color="#d97706" />
            <span className={styles.riskText}>
              <strong>{formatBRL(money(lossValue.toFixed(2)))}</strong> em risco de desperdício caso não seja utilizado a tempo.
            </span>
          </div>
          <Link
            to="/retornos"
            className={styles.actionBtnSmall}
            style={{ borderColor: "#d97706", color: "#b45309", background: "rgba(245, 158, 11, 0.1)" }}
          >
            <IconTarget width="14" height="14" />
            <span>Chamar Clientes para Retoque</span>
          </Link>
        </div>
      )}

      <div className={styles.vialItemActions}>
        <button
          type="button"
          className={`${styles.actionBtnSmall} ${styles.actionBtnPrimary}`}
          onClick={onConsume}
          disabled={vial.remaining_units <= 0}
        >
          <IconPlus width="14" height="14" />
          <span>Abater Aplicação</span>
        </button>

        <button
          type="button"
          className={styles.actionBtnSmall}
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

function CreateVialModal({ onClose }: { onClose: () => void }) {
  const createMutation = useCreateVial();
  const [medicationName, setMedicationName] = useState("Botox® Allergan");
  const [lotNumber, setLotNumber] = useState("");
  const [totalUnits, setTotalUnits] = useState("100");
  const [costPrice, setCostPrice] = useState("850.00");
  const [expirationDays, setExpirationDays] = useState("30");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const units = Number(totalUnits);
    if (!units || units <= 0) {
      setError("Informe a quantidade de unidades total.");
      return;
    }

    const days = Number(expirationDays) || 30;
    const expiresAtDate = new Date();
    expiresAtDate.setDate(expiresAtDate.getDate() + days);

    try {
      await createMutation.mutateAsync({
        medication_name: medicationName.trim(),
        lot_number: lotNumber.trim() || undefined,
        total_units: units,
        unit_measure: "U",
        cost_price: costPrice ? Number(costPrice) : undefined,
        expires_at: expiresAtDate.toISOString(),
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao abrir frasco.");
    }
  };

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true">
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Abrir Novo Frasco de Toxina / Insumo</h3>
          <button type="button" className={styles.closeBtn} onClick={onClose}>
            <IconX width="18" height="18" />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {error && <div style={{ color: "var(--danger, #dc2626)", fontSize: "13px" }}>{error}</div>}

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Medicamento / Produto</label>
            <input
              type="text"
              className={styles.formInput}
              value={medicationName}
              onChange={(e) => setMedicationName(e.target.value)}
              placeholder="Ex: Botox® Allergan 100U, Dysport®, Xeomin®"
              required
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Total de Unidades</label>
              <input
                type="number"
                className={styles.formInput}
                value={totalUnits}
                onChange={(e) => setTotalUnits(e.target.value)}
                min="1"
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Preço de Custo (R$)</label>
              <input
                type="number"
                step="0.01"
                className={styles.formInput}
                value={costPrice}
                onChange={(e) => setCostPrice(e.target.value)}
                placeholder="850.00"
              />
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Validade Clínica (Dias)</label>
              <input
                type="number"
                className={styles.formInput}
                value={expirationDays}
                onChange={(e) => setExpirationDays(e.target.value)}
                min="1"
                placeholder="30"
              />
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Padrão recomendado: 30 dias na geladeira
              </span>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Lote (Opcional)</label>
              <input
                type="text"
                className={styles.formInput}
                value={lotNumber}
                onChange={(e) => setLotNumber(e.target.value)}
                placeholder="Ex: C1234AB"
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Observações (Opcional)</label>
            <input
              type="text"
              className={styles.formInput}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Reconstituído com 2ml de soro estéril"
            />
          </div>

          <div className={styles.modalFooter}>
            <button
              type="button"
              className={styles.actionBtnSmall}
              onClick={onClose}
              disabled={createMutation.isPending}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={`${styles.actionBtnSmall} ${styles.actionBtnPrimary}`}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Cadastrando..." : "Registrar Frasco"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ConsumeVialModal({
  vial,
  onClose,
}: {
  vial: OpenVial;
  onClose: () => void;
}) {
  const consumeMutation = useConsumeVial();
  const [units, setUnits] = useState("20");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numUnits = Number(units);
    if (!numUnits || numUnits <= 0) {
      setError("Informe a quantidade de unidades aplicadas.");
      return;
    }
    if (numUnits > vial.remaining_units) {
      setError(`O frasco possui apenas ${vial.remaining_units} ${vial.unit_measure} disponíveis.`);
      return;
    }

    try {
      await consumeMutation.mutateAsync({
        vialId: vial.id,
        payload: {
          units: numUnits,
          notes: notes.trim() || undefined,
        },
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao abater unidades.");
    }
  };

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true">
      <div className={styles.modalContent}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Abater Unidades Utilizadas</h3>
          <button type="button" className={styles.closeBtn} onClick={onClose}>
            <IconX width="18" height="18" />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {error && <div style={{ color: "var(--danger, #dc2626)", fontSize: "13px" }}>{error}</div>}

          <p style={{ margin: 0, fontSize: "13px", color: "var(--text-muted)" }}>
            Frasco: <strong>{vial.medication_name}</strong> • Saldo atual:{" "}
            <strong>
              {vial.remaining_units} {vial.unit_measure}
            </strong>
          </p>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Unidades Aplicadas</label>
            <input
              type="number"
              className={styles.formInput}
              value={units}
              onChange={(e) => setUnits(e.target.value)}
              min="1"
              max={vial.remaining_units}
              required
              autoFocus
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Observação / Paciente (Opcional)</label>
            <input
              type="text"
              className={styles.formInput}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Aplicação terço superior - Maria Silva"
            />
          </div>

          <div className={styles.modalFooter}>
            <button
              type="button"
              className={styles.actionBtnSmall}
              onClick={onClose}
              disabled={consumeMutation.isPending}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={`${styles.actionBtnSmall} ${styles.actionBtnPrimary}`}
              disabled={consumeMutation.isPending}
            >
              {consumeMutation.isPending ? "Abatendo..." : "Confirmar Aplicação"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
