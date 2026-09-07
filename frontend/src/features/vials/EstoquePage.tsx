import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  useSupplies,
  useRecentSupplyMovements,
} from "@/features/supplies/useSupplies";
import type {
  Supply,
  MovementType,
} from "@/features/supplies/suppliesApi";
import {
  CreateSupplyModal,
  RecordMovementModal,
  CATEGORY_SHORT_LABELS,
} from "@/features/supplies/SupplyModals";
import { useActiveVials, useFinishVial } from "./useVials";
import type { OpenVial } from "./vialsApi";
import { CreateVialModal, ConsumeVialModal } from "./VialModals";
import {
  IconDroplet,
  IconAlertTriangle,
  IconPlus,
  IconTarget,
  IconCheck,
  IconSparkles,
} from "@/ui/icons";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./EstoquePage.module.css";

export function EstoquePage() {
  const [activeTab, setActiveTab] = useState<"inventory" | "vials" | "movements">("inventory");

  // Filtros do Inventário
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [lowStockOnly, setLowStockOnly] = useState(false);

  // Modais de Insumos Gerais
  const [isCreateSupplyOpen, setIsCreateSupplyOpen] = useState(false);
  const [movementModalState, setMovementModalState] = useState<{
    supply: Supply;
    type: MovementType;
  } | null>(null);

  // Modais de Frascos Abertos (Perecíveis)
  const [isCreateVialOpen, setIsCreateVialOpen] = useState(false);
  const [selectedVialForConsume, setSelectedVialForConsume] = useState<OpenVial | null>(null);

  // Queries
  const suppliesQuery = useSupplies({
    category: categoryFilter !== "ALL" ? categoryFilter : undefined,
    search: searchQuery || undefined,
    low_stock_only: lowStockOnly || undefined,
  });
  const recentMovementsQuery = useRecentSupplyMovements();
  const activeVialsQuery = useActiveVials();

  const supplies = suppliesQuery.data ?? [];
  const activeVials = activeVialsQuery.data ?? [];
  const movements = recentMovementsQuery.data ?? [];

  // Cálculos de KPIs
  const lowStockCount = useMemo(() => {
    return supplies.filter((s) => s.is_low_stock).length;
  }, [supplies]);

  const totalRiskBrl = useMemo(() => {
    return activeVials.reduce(
      (sum, v) => sum + (v.estimated_loss_risk ? Number(v.estimated_loss_risk) : 0),
      0
    );
  }, [activeVials]);

  const isLoading = suppliesQuery.isLoading && activeVialsQuery.isLoading;

  if (isLoading) {
    return (
      <div className={styles.page}>
        <header className={styles.header}>
          <div className={styles.titleArea}>
            <h1 className={styles.title}>Estoque & Insumos da Clínica</h1>
          </div>
        </header>
        <p style={{ color: "var(--text-muted, #64748b)" }}>Carregando dados de estoque...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Header Superior */}
      <header className={styles.header}>
        <div className={styles.titleArea}>
          <h1 className={styles.title}>Estoque & Insumos Clínicos</h1>
          <p className={styles.subtitle}>
            Gestão completa de insumos: preenchedores, toxinas, fios de sustentação, descartáveis e controle de frascos abertos.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            className={styles.actionBtn}
            onClick={() => setIsCreateVialOpen(true)}
          >
            <IconDroplet width="15" height="15" color="var(--accent)" />
            <span>Abrir Frasco Multidose</span>
          </button>

          <button
            type="button"
            className={styles.primaryBtn}
            onClick={() => setIsCreateSupplyOpen(true)}
          >
            <IconPlus width="15" height="15" />
            <span>+ Novo Insumo</span>
          </button>
        </div>
      </header>

      {/* Top Metrics Grid */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Itens Cadastrados</span>
          <span className={styles.metricValue}>{supplies.length}</span>
          <span className={styles.metricNote}>Insumos em controle no catálogo</span>
        </div>

        <div className={`${styles.metricCard} ${lowStockCount > 0 ? styles.metricCardAlert : ""}`}>
          <span className={styles.metricLabel}>Alerta de Reposição</span>
          <span className={styles.metricValue} style={{ color: lowStockCount > 0 ? "#b45309" : undefined }}>
            {lowStockCount} {lowStockCount === 1 ? "insumo baixo" : "insumos baixos"}
          </span>
          <span className={styles.metricNote}>
            {lowStockCount > 0 ? "Abaixo do estoque mínimo configurado" : "Todos os níveis adequados"}
          </span>
        </div>

        <div className={styles.metricCard}>
          <span className={styles.metricLabel}>Frascos Abertos em Uso</span>
          <span className={styles.metricValue} style={{ color: "var(--accent, #6366f1)" }}>
            {activeVials.length}
          </span>
          <span className={styles.metricNote}>Toxinas / Bioestimuladores com validade</span>
        </div>

        <div className={`${styles.metricCard} ${totalRiskBrl > 0 ? styles.metricCardAlert : ""}`}>
          <span className={styles.metricLabel}>Risco de Desperdício</span>
          <span className={styles.metricValue} style={{ color: totalRiskBrl > 0 ? "#b45309" : undefined }}>
            {formatBRL(money(totalRiskBrl.toFixed(2)))}
          </span>
          <span className={styles.metricNote}>
            {totalRiskBrl > 0 ? "Valor em frascos abertos para aplicar a tempo" : "Nenhum valor em risco"}
          </span>
        </div>
      </div>

      {/* Navegação de Abas */}
      <div className={styles.tabGroup}>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "inventory" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("inventory")}
        >
          📦 Inventário Geral (Armário) ({supplies.length})
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "vials" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("vials")}
        >
          💧 Frascos Abertos ({activeVials.length})
        </button>
        <button
          type="button"
          className={`${styles.tabBtn} ${activeTab === "movements" ? styles.tabBtnActive : ""}`}
          onClick={() => setActiveTab("movements")}
        >
          📋 Histórico de Movimentações
        </button>
      </div>

      {/* ABA 1: INVENTÁRIO GERAL */}
      {activeTab === "inventory" && (
        <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Barra de Filtros e Busca */}
          <div className={styles.toolbar}>
            <div className={styles.filtersGroup}>
              <input
                type="text"
                className={styles.searchInput}
                placeholder="Buscar por nome ou marca..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />

              <select
                className={styles.selectInput}
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="ALL">Todas as Categorias</option>
                <option value="FILLER">Preenchedores (Ácido Hialurônico)</option>
                <option value="INJECTABLE">Injetáveis / Fracionados</option>
                <option value="THREAD">Fios de Sustentação</option>
                <option value="ANESTHETIC">Anestésicos</option>
                <option value="CONSUMABLE">Descartáveis & Consumíveis</option>
                <option value="OTHER">Outros Insumos</option>
              </select>

              <label className={styles.toggleLabel}>
                <input
                  type="checkbox"
                  checked={lowStockOnly}
                  onChange={(e) => setLowStockOnly(e.target.checked)}
                />
                <span>Apenas estoque baixo</span>
              </label>
            </div>
          </div>

          {supplies.length === 0 ? (
            <div className={styles.emptyState}>
              <IconSparkles width="36" height="36" color="var(--accent)" />
              <h3 className={styles.emptyTitle}>Nenhum insumo encontrado</h3>
              <p className={styles.emptyDesc}>
                {searchQuery || categoryFilter !== "ALL" || lowStockOnly
                  ? "Tente ajustar os filtros de busca para encontrar o item desejado."
                  : "Cadastre seus preenchedores, fios, toxinas e descartáveis para controlar entradas, saídas e alertas de compra."}
              </p>
              <button
                type="button"
                className={styles.primaryBtn}
                onClick={() => setIsCreateSupplyOpen(true)}
              >
                <IconPlus width="14" height="14" />
                <span>Cadastrar Primeiro Insumo</span>
              </button>
            </div>
          ) : (
            <div className={styles.vialsGrid}>
              {supplies.map((supply) => (
                <SupplyCardItem
                  key={supply.id}
                  supply={supply}
                  onRecordMovement={(type) => setMovementModalState({ supply, type })}
                  onOpenVial={() => setIsCreateVialOpen(true)}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* ABA 2: FRASCOS ABERTOS (USO CLÍNICO & VALIDADE CURTA) */}
      {activeTab === "vials" && (
        <section style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {activeVials.length === 0 ? (
            <div className={styles.emptyState}>
              <IconDroplet width="40" height="40" color="var(--accent)" />
              <h3 className={styles.emptyTitle}>Nenhum frasco aberto no momento</h3>
              <p className={styles.emptyDesc}>
                Ao reconstituir um frasco de Botox® ou bioestimulador, registre a abertura aqui para acompanhar as unidades restantes e evitar que o frasco vença na geladeira.
              </p>
              <button
                type="button"
                className={styles.primaryBtn}
                onClick={() => setIsCreateVialOpen(true)}
              >
                <IconPlus width="14" height="14" />
                <span>Registrar Abertura de Frasco</span>
              </button>
            </div>
          ) : (
            <div className={styles.vialsGrid}>
              {activeVials.map((vial) => (
                <ActiveVialCardItem
                  key={vial.id}
                  vial={vial}
                  onConsume={() => setSelectedVialForConsume(vial)}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* ABA 3: HISTÓRICO DE MOVIMENTAÇÕES */}
      {activeTab === "movements" && (
        <section className={styles.tableContainer}>
          {movements.length === 0 ? (
            <div className={styles.emptyState}>
              <h3 className={styles.emptyTitle}>Nenhuma movimentação recente registrada</h3>
              <p className={styles.emptyDesc}>
                Conforme você registrar entradas de compra, saídas de atendimento ou descartes, o log de auditoria aparecerá aqui.
              </p>
            </div>
          ) : (
            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th>Data / Hora</th>
                  <th>Tipo</th>
                  <th>Quantidade</th>
                  <th>Custo Unitário</th>
                  <th>Observações</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((mov) => {
                  let badgeBg = "rgba(34, 197, 94, 0.12)";
                  let badgeColor = "#15803d";
                  let label = "Entrada / Compra";

                  if (mov.movement_type === "EXIT") {
                    badgeBg = "rgba(59, 130, 246, 0.12)";
                    badgeColor = "#1d4ed8";
                    label = "Saída / Atendimento";
                  } else if (mov.movement_type === "LOSS") {
                    badgeBg = "rgba(239, 68, 68, 0.15)";
                    badgeColor = "#dc2626";
                    label = "Perda / Descarte";
                  } else if (mov.movement_type === "ADJUSTMENT") {
                    badgeBg = "rgba(245, 158, 11, 0.15)";
                    badgeColor = "#b45309";
                    label = "Ajuste de Balanço";
                  }

                  return (
                    <tr key={mov.id}>
                      <td>{new Date(mov.created_at).toLocaleString("pt-BR")}</td>
                      <td>
                        <span
                          className={styles.badge}
                          style={{ background: badgeBg, color: badgeColor }}
                        >
                          {label}
                        </span>
                      </td>
                      <td>
                        <strong>{mov.quantity}</strong>
                      </td>
                      <td>
                        {mov.unit_price ? formatBRL(money(mov.unit_price)) : "—"}
                      </td>
                      <td style={{ color: "var(--text-muted)" }}>
                        {mov.notes || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>
      )}

      {/* Modais de Insumos Gerais */}
      {isCreateSupplyOpen && (
        <CreateSupplyModal onClose={() => setIsCreateSupplyOpen(false)} />
      )}

      {movementModalState && (
        <RecordMovementModal
          supply={movementModalState.supply}
          defaultType={movementModalState.type}
          onClose={() => setMovementModalState(null)}
        />
      )}

      {/* Modais de Frascos Abertos */}
      {isCreateVialOpen && (
        <CreateVialModal onClose={() => setIsCreateVialOpen(false)} />
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

function SupplyCardItem({
  supply,
  onRecordMovement,
  onOpenVial,
}: {
  supply: Supply;
  onRecordMovement: (type: MovementType) => void;
  onOpenVial: () => void;
}) {
  let catClass = styles.catOther;
  if (supply.category === "FILLER") catClass = styles.catFiller;
  if (supply.category === "INJECTABLE") catClass = styles.catInjectable;
  if (supply.category === "THREAD") catClass = styles.catThread;
  if (supply.category === "ANESTHETIC") catClass = styles.catAnesthetic;
  if (supply.category === "CONSUMABLE") catClass = styles.catConsumable;

  return (
    <div className={styles.vialCard}>
      <div className={styles.vialCardHeader}>
        <div style={{ minWidth: 0, flex: 1, overflow: "hidden" }}>
          <span className={`${styles.categoryPill} ${catClass}`}>
            {CATEGORY_SHORT_LABELS[supply.category] || supply.category}
          </span>
          <h3 className={styles.vialName} style={{ marginTop: "6px", wordBreak: "break-word" }}>
            {supply.name}
          </h3>
          <div className={styles.vialMeta} style={{ wordBreak: "break-word" }}>
            {supply.brand ? `${supply.brand} • ` : ""}
            {supply.cost_price ? `Custo: ${formatBRL(money(supply.cost_price))}` : "Sem custo informado"}
          </div>
        </div>

        {supply.is_low_stock && (
          <span className={styles.stockLowAlert} style={{ flexShrink: 0 }}>
            <IconAlertTriangle width="12" height="12" />
            <span>Estoque Baixo</span>
          </span>
        )}
      </div>

      <div className={styles.stockLevel}>
        <span className={styles.stockNumber}>{supply.current_stock}</span>
        <span className={styles.stockUnit}>{supply.unit_measure} em armário</span>
      </div>

      {supply.min_stock_alert != null && (
        <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          Mínimo para alerta: {supply.min_stock_alert} {supply.unit_measure}
        </div>
      )}

      {supply.notes && (
        <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: 0 }}>
          {supply.notes}
        </p>
      )}

      <div className={styles.vialActions}>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.actionBtnPrimary}`}
          onClick={() => onRecordMovement("ENTRY")}
        >
          <IconPlus width="13" height="13" />
          <span>+ Entrada</span>
        </button>

        <button
          type="button"
          className={styles.actionBtn}
          onClick={() => onRecordMovement("EXIT")}
          disabled={supply.current_stock <= 0}
        >
          <span>- Baixa / Uso</span>
        </button>

        {supply.category === "INJECTABLE" && (
          <button
            type="button"
            className={styles.actionBtn}
            onClick={onOpenVial}
            title="Abrir e monitorar validade na geladeira"
          >
            <IconDroplet width="13" height="13" color="var(--accent)" />
            <span>Abrir Frasco</span>
          </button>
        )}
      </div>
    </div>
  );
}

function ActiveVialCardItem({
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
            <strong>{formatBRL(money(lossValue.toFixed(2)))}</strong> em risco caso vença.
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
