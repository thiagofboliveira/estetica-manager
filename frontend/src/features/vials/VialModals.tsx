import { useState } from "react";
import { useCreateVial, useConsumeVial } from "./useVials";
import type { OpenVial } from "./vialsApi";
import { IconX } from "@/ui/icons";
import styles from "./BotoxVialCard.module.css";

export function CreateVialModal({ onClose }: { onClose: () => void }) {
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
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
            <IconX width="18" height="18" />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {error && <div style={{ color: "var(--danger, #dc2626)", fontSize: "13px" }}>{error}</div>}

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Medicamento / Insumo</label>
            <input
              type="text"
              className={styles.formInput}
              value={medicationName}
              onChange={(e) => setMedicationName(e.target.value)}
              placeholder="Ex: Botox® Allergan 100U, Dysport®, Sculptra®"
              required
              autoFocus
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

export function ConsumeVialModal({
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
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
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
