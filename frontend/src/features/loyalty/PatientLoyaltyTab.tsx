import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useAdjustLoyaltyPoints,
  usePatientLoyalty,
  usePatientReferral,
  useSendVipCardEmail,
} from "./useLoyalty";

import type { LoyaltyPatientOut, ReferralInfoOut } from "./loyaltyApi";
import styles from "./PatientLoyaltyTab.module.css";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";

interface PatientLoyaltyTabProps {
  patientId: string;
  patientPhone: string | null;
  patientConsentWhatsapp: boolean;
}

export function PatientLoyaltyTab({
  patientId,
  patientPhone,
  patientConsentWhatsapp,
}: PatientLoyaltyTabProps) {
  const loyaltyQuery = usePatientLoyalty(patientId);
  const referralQuery = usePatientReferral(patientId);
  const adjustMutation = useAdjustLoyaltyPoints(patientId);
  const sendEmailMutation = useSendVipCardEmail(patientId);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [adjustType, setAdjustType] = useState<"BONUS" | "REDEEMED">("BONUS");
  const [pointsInput, setPointsInput] = useState<string>("50");
  const [reasonInput, setReasonInput] = useState<string>("");
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedVipUrl, setCopiedVipUrl] = useState(false);
  const [emailSuccessMsg, setEmailSuccessMsg] = useState<string | null>(null);


  if (loyaltyQuery.isLoading || referralQuery.isLoading) {
    return <p>Carregando dados de fidelidade e indicação…</p>;
  }

  const loyalty: LoyaltyPatientOut | undefined = loyaltyQuery.data;
  const referral: ReferralInfoOut | undefined = referralQuery.data;

  if (!loyalty) {
    return <p>Não foi possível carregar as informações do Clube VIP.</p>;
  }

  const tierClass =
    loyalty.vip_tier === "DIAMOND"
      ? styles.vipBannerDiamond
      : loyalty.vip_tier === "GOLD"
      ? styles.vipBannerGold
      : loyalty.vip_tier === "SILVER"
      ? styles.vipBannerSilver
      : styles.vipBannerBronze;

  const badgeClass =
    loyalty.vip_tier === "DIAMOND"
      ? styles.badgeDiamond
      : loyalty.vip_tier === "GOLD"
      ? styles.badgeGold
      : loyalty.vip_tier === "SILVER"
      ? styles.badgeSilver
      : styles.badgeBronze;

  const cleanPhone = patientPhone ? patientPhone.replace(/\D/g, "") : null;
  const formattedVal = formatBRL(money(Number(loyalty.monetary_value || 0).toFixed(2)));
  const patientWhatsappBalanceMsg = `Olá, ${loyalty.patient_name}! ✨ Seu saldo no nosso Clube VIP é de *${loyalty.loyalty_points} pontos* (equivalente a ${formattedVal} em benefícios). Você está no nível *${loyalty.vip_badge} ${loyalty.vip_tier}*!`;
  const whatsappBalanceUrl =
    cleanPhone && patientConsentWhatsapp
      ? `https://wa.me/55${cleanPhone}?text=${encodeURIComponent(patientWhatsappBalanceMsg)}`
      : null;

  async function handleCopyReferralMessage() {
    if (!referral) return;
    try {
      await navigator.clipboard.writeText(referral.whatsapp_share_text);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2500);
    } catch {
      // Fallback
    }
  }

  async function handleSendVipEmail() {
    setEmailSuccessMsg(null);
    try {
      const res = await sendEmailMutation.mutateAsync();
      setEmailSuccessMsg(`✓ Cartão VIP enviado com sucesso para ${res.recipient_email}!`);
      setTimeout(() => setEmailSuccessMsg(null), 5000);
    } catch (err: any) {
      alert(err?.response?.data?.detail || err?.message || "Erro ao enviar e-mail com Cartão VIP.");
    }
  }

  async function handleCopyVipLink() {
    if (!loyalty) return;
    const vipUrl = `${window.location.origin}/clube-vip/${loyalty.referral_code}`;
    try {
      await navigator.clipboard.writeText(vipUrl);
      setCopiedVipUrl(true);
      setTimeout(() => setCopiedVipUrl(false), 2500);
    } catch {
      // Fallback
    }
  }

  async function handleAdjustSubmit(e: React.FormEvent) {
    e.preventDefault();
    const pts = parseInt(pointsInput, 10);
    if (isNaN(pts) || pts <= 0) {
      alert("Informe uma quantidade válida de pontos.");
      return;
    }

    const finalPoints = adjustType === "REDEEMED" ? -pts : pts;
    const finalReason =
      reasonInput.trim() ||
      (adjustType === "REDEEMED" ? "Resgate em procedimento" : "Bônus especial de fidelidade");

    try {
      await adjustMutation.mutateAsync({
        points: finalPoints,
        description: finalReason,
        transaction_type: adjustType,
      });
      setIsModalOpen(false);
      setPointsInput("50");
      setReasonInput("");
    } catch (err: any) {
      alert(err?.message || "Erro ao atualizar pontos.");
    }
  }

  return (
    <div className={styles.container}>
      {/* Banner Principal do Clube VIP */}
      <section className={`${styles.vipBanner} ${tierClass}`}>
        <div className={styles.vipInfo}>
          <div className={styles.vipBadgeRow}>
            <span className={`${styles.vipBadge} ${badgeClass}`}>
              {loyalty.vip_badge} Categoria {loyalty.vip_tier}
            </span>
            {loyalty.referred_by_name && (
              <span style={{ fontSize: "0.82rem", color: "#64748b" }}>
                Indicada por: <strong>{loyalty.referred_by_name}</strong>
              </span>
            )}
          </div>

          <div className={styles.pointsDisplay}>
            {loyalty.loyalty_points} <span style={{ fontSize: "1.2rem", fontWeight: 500 }}>pontos</span>
          </div>

          <p className={styles.pointsSub}>
            Equivalente a{" "}
            <span className={styles.pointsEquiv}>{formattedVal}</span> de desconto ou
            crédito para resgate.
          </p>
        </div>

        <div className={styles.vipActions}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            {whatsappBalanceUrl ? (
              <a
                href={whatsappBalanceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.whatsappButton}
              >
                💬 Enviar Saldo por WhatsApp
              </a>
            ) : (
              <button
                type="button"
                disabled
                className={styles.whatsappButton}
                style={{ opacity: 0.6, cursor: "not-allowed" }}
                title="Paciente sem WhatsApp cadastrado ou sem consentimento LGPD"
              >
                💬 WhatsApp desabilitado
              </button>
            )}

            <button
              type="button"
              className={styles.emailButton}
              onClick={handleSendVipEmail}
              disabled={sendEmailMutation.isPending}
              title="Disparar Cartão VIP Digital por e-mail para a paciente"
            >
              {sendEmailMutation.isPending ? "📧 Enviando E-mail..." : "📧 Disparar Cartão VIP por E-mail"}
            </button>
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            <a
              href={`/clube-vip/${loyalty.referral_code}`}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.vipLinkButton}
              title="Abrir página pública do Cartão VIP desta paciente"
            >
              💳 Abrir Cartão VIP ↗
            </a>

            <button
              type="button"
              className={styles.vipLinkButton}
              onClick={handleCopyVipLink}
              title="Copiar link seguro do Cartão VIP"
            >
              {copiedVipUrl ? "✓ Link Copiado!" : "🔗 Copiar Link do Cartão"}
            </button>

            <button
              type="button"
              className={styles.adjustButton}
              onClick={() => setIsModalOpen(true)}
            >
              ⚖️ Resgatar / Ajustar Pontos
            </button>

            <Link
              to="/catalogo-vip"
              className={styles.vipLinkButton}
              title="Configurar catálogo de pontos e recompensas VIP"
            >
              🎁 Catálogo VIP
            </Link>
          </div>



          {emailSuccessMsg && (
            <div style={{ fontSize: "0.85rem", color: "#16a34a", fontWeight: 600, width: "100%", textAlign: "right" }}>
              {emailSuccessMsg}
            </div>
          )}
        </div>
      </section>

      {/* Seção Traga uma Amiga */}
      {referral && (
        <section className={styles.referralSection}>
          <div className={styles.referralHeader}>
            <div>
              <h3 className={styles.referralTitle}>🎁 Motor de Indicação: "Traga uma Amiga"</h3>
              <p style={{ margin: "4px 0 0", fontSize: "0.88rem", color: "#64748b" }}>
                Cada amiga que utilizar o código desta paciente ganha benefício na 1ª sessão, e a
                paciente recebe <strong>+{referral.reward_points_per_friend} pontos</strong>!
              </p>
            </div>

            <div className={styles.codeBox}>
              <span>Código:</span>
              <span className={styles.codeText}>{referral.referral_code}</span>
              <button
                type="button"
                onClick={handleCopyReferralMessage}
                className={styles.copyCodeBtn}
              >
                {copiedCode ? "✓ Copiado!" : "📋 Copiar Convite"}
              </button>
            </div>
          </div>

          <div className={styles.referralStatsGrid}>
            <div className={styles.statCard}>
              <p className={styles.statVal}>{referral.total_friends_referred}</p>
              <p className={styles.statLabel}>Amigas Indicadas</p>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statVal} style={{ color: "#16a34a" }}>
                {referral.friends_converted_count}
              </p>
              <p className={styles.statLabel}>Sessões Realizadas</p>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statVal} style={{ color: "#0284c7" }}>
                +{referral.total_points_earned_from_referrals} pts
              </p>
              <p className={styles.statLabel}>Pontos Ganhos por Indicação</p>
            </div>
          </div>

          {referral.friends.length > 0 && (
            <div>
              <h4 style={{ fontSize: "0.92rem", fontWeight: 700, margin: "14px 0 8px" }}>
                Amigas que se cadastraram ({referral.friends.length}):
              </h4>
              <div className={styles.friendsList}>
                {referral.friends.map((f) => (
                  <div key={f.patient_id} className={styles.friendItem}>
                    <span className={styles.friendName}>{f.patient_name}</span>
                    {f.has_completed_sale ? (
                      <span className={styles.badgeConverted}>✓ Procedimento Realizado</span>
                    ) : (
                      <span className={styles.badgePending}>Aguardando 1ª sessão</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Extrato de Transações */}
      <section className={styles.historySection}>
        <h3 className={styles.historyTitle}>📜 Extrato de Pontos de Fidelidade</h3>

        {loyalty.transactions.length === 0 ? (
          <p style={{ color: "#64748b", fontSize: "0.9rem", margin: 0 }}>
            Nenhuma movimentação registrada ainda. Pontos serão acumulados automaticamente na
            conclusão de vendas ou por indicação de amigas.
          </p>
        ) : (
          <table className={styles.historyTable}>
            <thead>
              <tr>
                <th>Data</th>
                <th>Operação</th>
                <th>Descrição</th>
                <th style={{ textAlign: "right" }}>Pontos</th>
                <th style={{ textAlign: "right" }}>Saldo Final</th>
              </tr>
            </thead>
            <tbody>
              {loyalty.transactions.map((tx) => {
                const isPositive = tx.points > 0;
                return (
                  <tr key={tx.id}>
                    <td>
                      {tx.created_at
                        ? new Date(tx.created_at).toLocaleDateString("pt-BR")
                        : "—"}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: "0.78rem",
                          fontWeight: 700,
                          padding: "2px 8px",
                          borderRadius: "10px",
                          background:
                            tx.transaction_type === "EARNED"
                              ? "#dcfce7"
                              : tx.transaction_type === "BONUS"
                              ? "#e0f2fe"
                              : "#fee2e2",
                          color:
                            tx.transaction_type === "EARNED"
                              ? "#15803d"
                              : tx.transaction_type === "BONUS"
                              ? "#0369a1"
                              : "#b91c1c",
                        }}
                      >
                        {tx.transaction_type === "EARNED"
                          ? "COMPRA"
                          : tx.transaction_type === "BONUS"
                          ? "BÔNUS INDICAÇÃO"
                          : tx.transaction_type === "REDEEMED"
                          ? "RESGATE"
                          : "AJUSTE"}
                      </span>
                    </td>
                    <td>{tx.description}</td>
                    <td
                      style={{ textAlign: "right" }}
                      className={isPositive ? styles.pointsEarned : styles.pointsRedeemed}
                    >
                      {isPositive ? `+${tx.points}` : tx.points}
                    </td>
                    <td style={{ textAlign: "right", fontWeight: 600 }}>
                      {tx.balance_after} pts
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      {/* Modal de Ajuste / Resgate */}
      {isModalOpen && (
        <div className={styles.modalOverlay} onClick={() => setIsModalOpen(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>⚖️ Resgate ou Crédito de Pontos</h3>

            <form onSubmit={handleAdjustSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div className={styles.formGroup}>
                <label>Tipo de Movimentação</label>
                <select
                  value={adjustType}
                  onChange={(e) => setAdjustType(e.target.value as "BONUS" | "REDEEMED")}
                >
                  <option value="BONUS">🎁 Creditar Bônus / Cortesia</option>
                  <option value="REDEEMED">🏷️ Resgatar Pontos (Desconto em Procedimento)</option>
                </select>
              </div>

              <div className={styles.formGroup}>
                <label>Quantidade de Pontos</label>
                <input
                  type="number"
                  min="1"
                  max={adjustType === "REDEEMED" ? loyalty.loyalty_points : 10000}
                  value={pointsInput}
                  onChange={(e) => setPointsInput(e.target.value)}
                  required
                />
                {adjustType === "REDEEMED" && (
                  <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                    Saldo disponível para resgate: <strong>{loyalty.loyalty_points} pts</strong>
                  </span>
                )}
              </div>

              <div className={styles.formGroup}>
                <label>Motivo ou Observação</label>
                <input
                  type="text"
                  placeholder={
                    adjustType === "REDEEMED"
                      ? "Ex: Desconto na sessão de Limpeza de Pele"
                      : "Ex: Bonificação especial de aniversário"
                  }
                  value={reasonInput}
                  onChange={(e) => setReasonInput(e.target.value)}
                />
              </div>

              <div className={styles.modalActions}>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="button button--ghost"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={adjustMutation.isPending}
                  className="button button--primary"
                >
                  {adjustMutation.isPending ? "Processando…" : "Confirmar Movimentação"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
