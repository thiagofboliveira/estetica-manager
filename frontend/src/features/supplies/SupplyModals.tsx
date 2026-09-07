import { useState } from "react";
import { useCreateSupply, useRecordSupplyMovement } from "./useSupplies";
import type { Supply, SupplyCategory, MovementType } from "./suppliesApi";
import { IconX } from "@/ui/icons";
import styles from "@/features/vials/BotoxVialCard.module.css";

export const CATEGORY_LABELS: Record<SupplyCategory, string> = {
  INJECTABLE: "Injetável / Fracionado (Toxinas, Bioestimuladores)",
  FILLER: "Preenchedor (Ácido Hialurônico)",
  THREAD: "Fios de Sustentação (PDO)",
  ANESTHETIC: "Anestésico (Tópico / Injetável)",
  CONSUMABLE: "Descartável & Consumível (Agulhas, luvas, etc.)",
  OTHER: "Outros Insumos",
};

export const CATEGORY_SHORT_LABELS: Record<SupplyCategory, string> = {
  INJECTABLE: "Injetável",
  FILLER: "Preenchedor",
  THREAD: "Fios",
  ANESTHETIC: "Anestésico",
  CONSUMABLE: "Descartável",
  OTHER: "Outro",
};

export function CreateSupplyModal({ onClose }: { onClose: () => void }) {
  const createMutation = useCreateSupply();

  const [name, setName] = useState("");
  const [category, setCategory] = useState<SupplyCategory>("FILLER");
  const [brand, setBrand] = useState("");
  const [unitMeasure, setUnitMeasure] = useState("SERINGA");
  const [currentStock, setCurrentStock] = useState("5");
  const [minStockAlert, setMinStockAlert] = useState("2");
  const [costPrice, setCostPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Informe o nome do insumo.");
      return;
    }

    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        category,
        brand: brand.trim() || undefined,
        unit_measure: unitMeasure.trim().toUpperCase() || "UN",
        current_stock: currentStock ? Number(currentStock) : 0,
        min_stock_alert: minStockAlert ? Number(minStockAlert) : undefined,
        cost_price: costPrice ? Number(costPrice) : undefined,
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao cadastrar insumo.");
    }
  };

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true">
      <div className={styles.modalContent} style={{ maxWidth: "500px" }}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Cadastrar Novo Insumo no Estoque</h3>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
            <IconX width="18" height="18" />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px", width: "100%" }}>
          {error && <div style={{ color: "var(--danger, #dc2626)", fontSize: "13px" }}>{error}</div>}

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Nome do Insumo / Produto</label>
            <input
              type="text"
              className={styles.formInput}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Restylane Defyne 1ml, Botox 100U, Agulha 30G 4mm"
              required
              autoFocus
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Categoria</label>
            <select
              className={styles.formInput}
              value={category}
              onChange={(e) => setCategory(e.target.value as SupplyCategory)}
            >
              <option value="FILLER">Preenchedores (Ácido Hialurônico)</option>
              <option value="INJECTABLE">Injetáveis / Fracionados (Toxina, Bioestimuladores)</option>
              <option value="THREAD">Fios de Sustentação (PDO)</option>
              <option value="ANESTHETIC">Anestésicos (Tópicos / Injetáveis)</option>
              <option value="CONSUMABLE">Descartáveis & Consumíveis (Agulhas, luvas)</option>
              <option value="OTHER">Outros Insumos Clínicos</option>
            </select>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Marca / Fabricante (Opcional)</label>
              <input
                type="text"
                className={styles.formInput}
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="Ex: Galderma, Allergan"
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Unidade de Medida</label>
              <select
                className={styles.formInput}
                value={unitMeasure}
                onChange={(e) => setUnitMeasure(e.target.value)}
              >
                <option value="SERINGA">Seringa</option>
                <option value="FRASCO">Frasco</option>
                <option value="UN">Unidade (UN)</option>
                <option value="CAIXA">Caixa</option>
                <option value="TUBO">Tubo / Bisnaga</option>
                <option value="ML">Mililitro (ml)</option>
                <option value="PACOTE">Pacote</option>
              </select>
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Estoque Atual Inicial</label>
              <input
                type="number"
                step="0.01"
                className={styles.formInput}
                value={currentStock}
                onChange={(e) => setCurrentStock(e.target.value)}
                min="0"
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Estoque Mínimo (Alerta)</label>
              <input
                type="number"
                step="0.01"
                className={styles.formInput}
                value={minStockAlert}
                onChange={(e) => setMinStockAlert(e.target.value)}
                min="0"
                placeholder="Aviso de compra"
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Custo Unitário Médio (R$)</label>
            <input
              type="number"
              step="0.01"
              className={styles.formInput}
              value={costPrice}
              onChange={(e) => setCostPrice(e.target.value)}
              placeholder="Ex: 450.00"
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Observações (Opcional)</label>
            <input
              type="text"
              className={styles.formInput}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Armazenar sob refrigeração de 2° a 8°C"
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
              {createMutation.isPending ? "Cadastrando..." : "Cadastrar Insumo"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function RecordMovementModal({
  supply,
  defaultType = "ENTRY",
  onClose,
}: {
  supply: Supply;
  defaultType?: MovementType;
  onClose: () => void;
}) {
  const movementMutation = useRecordSupplyMovement();

  const [type, setType] = useState<MovementType>(defaultType);
  const [quantity, setQuantity] = useState("1");
  const [unitPrice, setUnitPrice] = useState(
    supply.cost_price ? String(supply.cost_price) : ""
  );
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const qty = Number(quantity);
    if (!qty || qty <= 0) {
      setError("Informe uma quantidade válida maior que zero.");
      return;
    }

    try {
      await movementMutation.mutateAsync({
        supplyId: supply.id,
        payload: {
          movement_type: type,
          quantity: qty,
          unit_price: unitPrice ? Number(unitPrice) : undefined,
          notes: notes.trim() || undefined,
        },
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao registrar movimentação.");
    }
  };

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true">
      <div className={styles.modalContent} style={{ maxWidth: "480px" }}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Movimentar Estoque</h3>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Fechar">
            <IconX width="18" height="18" />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px", width: "100%" }}>
          {error && <div style={{ color: "var(--danger, #dc2626)", fontSize: "13px" }}>{error}</div>}

          <div style={{ background: "var(--surface-hover, #f8fafc)", padding: "10px 14px", borderRadius: "8px", width: "100%", boxSizing: "border-box", wordBreak: "break-word" }}>
            <p style={{ margin: 0, fontSize: "14px", fontWeight: 600, color: "var(--text)", wordBreak: "break-word" }}>
              {supply.name}
            </p>
            <span style={{ fontSize: "12.5px", color: "var(--text-muted)", wordBreak: "break-word" }}>
              Saldo atual: <strong>{supply.current_stock} {supply.unit_measure}</strong>
              {supply.brand ? ` • Marca: ${supply.brand}` : ""}
            </span>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Tipo de Movimentação</label>
            <select
              className={styles.formInput}
              value={type}
              onChange={(e) => setType(e.target.value as MovementType)}
            >
              <option value="ENTRY">➕ Entrada / Compra (Aumenta estoque)</option>
              <option value="EXIT">➖ Saída / Uso em Atendimento (Reduz estoque)</option>
              <option value="LOSS">⚠️ Perda / Descarte (Reduz estoque)</option>
              <option value="ADJUSTMENT">🔄 Ajuste de Balanço (Define saldo exato)</option>
            </select>
          </div>

          {type === "ENTRY" ? (
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>
                  Quantidade ({supply.unit_measure})
                </label>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  min="0.01"
                  required
                  autoFocus
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Preço Unitário (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  className={styles.formInput}
                  value={unitPrice}
                  onChange={(e) => setUnitPrice(e.target.value)}
                  placeholder="Ex: 450.00"
                />
              </div>
            </div>
          ) : (
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>
                {type === "ADJUSTMENT" ? "Novo Saldo Total" : "Quantidade a Abater"} ({supply.unit_measure})
              </label>
              <input
                type="number"
                step="0.01"
                className={styles.formInput}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                min="0.01"
                required
                autoFocus
              />
            </div>
          )}

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Observações / Motivo (Opcional)</label>
            <input
              type="text"
              className={styles.formInput}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Nota Fiscal, Uso em paciente, etc."
            />
          </div>

          <div className={styles.modalFooter}>
            <button
              type="button"
              className={styles.actionBtnSmall}
              onClick={onClose}
              disabled={movementMutation.isPending}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={`${styles.actionBtnSmall} ${styles.actionBtnPrimary}`}
              disabled={movementMutation.isPending}
            >
              {movementMutation.isPending ? "Gravando..." : "Confirmar Movimentação"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
