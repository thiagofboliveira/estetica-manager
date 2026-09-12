import { useState } from "react";
import {
  useCreateLoyaltyReward,
  useDeleteLoyaltyReward,
  useLoyaltyRewards,
  useUpdateLoyaltyReward,
} from "./useLoyalty";
import type { LoyaltyReward } from "./loyaltyApi";
import styles from "./LoyaltyRewardsManager.module.css";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";

export function LoyaltyRewardsManager() {
  const { data: rewards, isLoading, isError } = useLoyaltyRewards();
  const createMutation = useCreateLoyaltyReward();
  const updateMutation = useUpdateLoyaltyReward();
  const deleteMutation = useDeleteLoyaltyReward();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingReward, setEditingReward] = useState<LoyaltyReward | null>(null);

  // Form states
  const [title, setTitle] = useState("");
  const [pointsCost, setPointsCost] = useState(100);
  const [description, setDescription] = useState("");
  const [discountValue, setDiscountValue] = useState<string>("");
  const [orderIndex, setOrderIndex] = useState(1);
  const [isActive, setIsActive] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  function openCreateModal() {
    setEditingReward(null);
    setTitle("");
    setPointsCost(100);
    setDescription("");
    setDiscountValue("");
    setOrderIndex(rewards ? rewards.length + 1 : 1);
    setIsActive(true);
    setFormError(null);
    setIsModalOpen(true);
  }

  function openEditModal(reward: LoyaltyReward) {
    setEditingReward(reward);
    setTitle(reward.title);
    setPointsCost(reward.points_cost);
    setDescription(reward.description || "");
    setDiscountValue(reward.discount_value != null ? String(reward.discount_value) : "");
    setOrderIndex(reward.order_index ?? 1);
    setIsActive(reward.is_active);
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingReward(null);
    setFormError(null);
  }

  async function handleToggleActive(reward: LoyaltyReward) {
    try {
      await updateMutation.mutateAsync({
        id: reward.id,
        data: { is_active: !reward.is_active },
      });
    } catch (err: any) {
      alert(err?.message || "Erro ao alterar status da recompensa.");
    }
  }

  async function handleDelete(reward: LoyaltyReward) {
    if (!window.confirm(`Deseja realmente excluir a recompensa "${reward.title}"?`)) {
      return;
    }
    try {
      await deleteMutation.mutateAsync(reward.id);
    } catch (err: any) {
      alert(err?.message || "Erro ao excluir recompensa.");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);

    if (!title.trim()) {
      setFormError("Informe o nome do benefício ou recompensa.");
      return;
    }

    if (pointsCost < 1) {
      setFormError("A quantidade de pontos deve ser no mínimo 1.");
      return;
    }

    let parsedDiscount: number | null = null;
    if (discountValue.trim() !== "") {
      const cleanVal = discountValue.replace(",", ".");
      const num = parseFloat(cleanVal);
      if (isNaN(num) || num < 0) {
        setFormError("Informe um valor de desconto válido ou deixe em branco.");
        return;
      }
      parsedDiscount = num;
    }

    try {
      if (editingReward) {
        await updateMutation.mutateAsync({
          id: editingReward.id,
          data: {
            title: title.trim(),
            points_cost: pointsCost,
            description: description.trim(),
            discount_value: parsedDiscount,
            order_index: orderIndex,
            is_active: isActive,
          },
        });
      } else {
        await createMutation.mutateAsync({
          title: title.trim(),
          points_cost: pointsCost,
          description: description.trim(),
          discount_value: parsedDiscount,
          order_index: orderIndex,
          is_active: isActive,
        });
      }
      closeModal();
    } catch (err: any) {
      setFormError(err?.message || "Ocorreu um erro ao salvar a recompensa.");
    }
  }

  if (isLoading) {
    return <p>Carregando catálogo de recompensas…</p>;
  }

  if (isError) {
    return <p>Erro ao carregar catálogo VIP. Tente novamente mais tarde.</p>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.titleGroup}>
          <h3>Catálogo VIP &amp; Benefícios por Pontos</h3>
          <p>
            Defina quais procedimentos, mimos ou descontos em reais suas clientes podem resgatar
            ao acumular pontos de fidelidade no Clube VIP.
          </p>
        </div>
        <button type="button" className="button button--primary" onClick={openCreateModal}>
          + Nova Recompensa
        </button>
      </header>

      <div className={styles.infoNotice}>
        <span className={styles.infoNoticeIcon}>💡</span>
        <div>
          <strong>Exibição em tempo real no Cartão VIP da Cliente:</strong>
          {rewards && rewards.length > 0 ? (
            <span>
              {" "}Suas {rewards.filter((r) => r.is_active).length} recompensas ativas estão
              sendo exibidas no Cartão VIP digital e link de indicação das suas clientes.
            </span>
          ) : (
            <span>
              {" "}Você ainda não possui recompensas cadastradas. O Cartão VIP público está
              exibindo as 4 opções sugeridas por padrão (50, 100, 200 e 300 pts). Cadastre sua
              primeira recompensa para personalizar totalmente o seu catálogo!
            </span>
          )}
        </div>
      </div>

      {(!rewards || rewards.length === 0) ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🎁</div>
          <h4>Nenhuma recompensa personalizada cadastrada</h4>
          <p>
            Crie benefícios exclusivos para suas clientes, como descontos diretos, sessões cortesia
            ou massagens relaxantes para estimular indicações e fidelização!
          </p>
          <button type="button" className="button button--primary" onClick={openCreateModal}>
            Cadastrar Primeira Recompensa
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {rewards.map((reward) => {
            const hasDiscount = reward.discount_value != null && Number(reward.discount_value) > 0;
            const formattedVal = hasDiscount
              ? formatBRL(money(Number(reward.discount_value).toFixed(2)))
              : null;

            return (
              <div
                key={reward.id}
                className={`${styles.card} ${!reward.is_active ? styles.cardInactive : ""}`}
              >
                <div>
                  <div className={styles.cardTop}>
                    <span className={styles.pointsBadge}>
                      ★ {reward.points_cost} {reward.points_cost === 1 ? "ponto" : "pontos"}
                    </span>
                    <span
                      className={
                        reward.is_active ? styles.statusBadgeActive : styles.statusBadgeInactive
                      }
                    >
                      {reward.is_active ? "Ativa no Catálogo" : "Pausada"}
                    </span>
                  </div>

                  <h4 className={styles.cardTitle}>{reward.title}</h4>
                  <p className={styles.cardDescription}>
                    {reward.description || "Sem descrição informada."}
                  </p>

                  {formattedVal && (
                    <div className={styles.cardDiscount}>
                      <span>🏷️</span>
                      <span>Equivale a {formattedVal} de desconto</span>
                    </div>
                  )}
                </div>

                <div className={styles.cardActions}>
                  <button
                    type="button"
                    className={styles.btnAction}
                    onClick={() => handleToggleActive(reward)}
                    title={reward.is_active ? "Pausar recompensa" : "Ativar recompensa"}
                  >
                    {reward.is_active ? "Pausar" : "Ativar"}
                  </button>
                  <button
                    type="button"
                    className={styles.btnAction}
                    onClick={() => openEditModal(reward)}
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    className={`${styles.btnAction} ${styles.btnDanger}`}
                    onClick={() => handleDelete(reward)}
                  >
                    Excluir
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal de Criação / Edição */}
      {isModalOpen && (
        <div className={styles.modalBackdrop} onClick={closeModal}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>{editingReward ? "Editar Recompensa VIP" : "Nova Recompensa VIP"}</h3>
              <button type="button" className={styles.closeBtn} onClick={closeModal}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmit} className={styles.formGrid}>
              {formError && (
                <div style={{ color: "#dc2626", fontSize: "0.85rem", fontWeight: 500 }}>
                  {formError}
                </div>
              )}

              <div className={styles.formGroup}>
                <label htmlFor="reward-title">Título do Benefício *</label>
                <input
                  id="reward-title"
                  type="text"
                  placeholder="Ex: R$ 50 de Desconto ou Peeling de Diamante"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  maxLength={120}
                  required
                />
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="reward-points">Pontos Necessários *</label>
                  <input
                    id="reward-points"
                    type="number"
                    min={1}
                    value={pointsCost}
                    onChange={(e) => setPointsCost(Number(e.target.value))}
                    required
                  />
                </div>

                <div className={styles.formGroup}>
                  <label htmlFor="reward-discount">Valor de Desconto (R$)</label>
                  <input
                    id="reward-discount"
                    type="text"
                    inputMode="decimal"
                    placeholder="Ex: 50,00 (opcional)"
                    value={discountValue}
                    onChange={(e) => setDiscountValue(e.target.value)}
                  />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="reward-desc">Descrição Explicativa</label>
                <textarea
                  id="reward-desc"
                  rows={3}
                  placeholder="Explique como a cliente resgata ou os benefícios do procedimento..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  maxLength={255}
                />
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="reward-order">Ordem de Exibição</label>
                  <input
                    id="reward-order"
                    type="number"
                    min={0}
                    value={orderIndex}
                    onChange={(e) => setOrderIndex(Number(e.target.value))}
                  />
                </div>

                <div style={{ display: "flex", alignItems: "flex-end", paddingBottom: "0.5rem" }}>
                  <label className={styles.checkboxRow}>
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                    />
                    <span>Ativa no catálogo</span>
                  </label>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={closeModal}
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="button button--primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? "Salvando..."
                    : editingReward
                    ? "Atualizar Recompensa"
                    : "Criar Recompensa"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
