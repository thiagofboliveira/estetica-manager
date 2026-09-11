import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { usePublicVipCard } from "./useLoyalty";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import styles from "./PublicVipCardPage.module.css";

export function PublicVipCardPage() {
  const { code } = useParams<{ code: string }>();
  const cleanCode = code ? decodeURIComponent(code).trim() : "";
  const { data: card, isLoading, isError, refetch } = usePublicVipCard(cleanCode);

  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedMessage, setCopiedMessage] = useState(false);

  async function handleCopyCode() {
    if (!card) return;
    try {
      await navigator.clipboard.writeText(card.referral_code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } catch {
      // Fallback
    }
  }

  async function handleCopyInviteMessage() {
    if (!card) return;
    try {
      await navigator.clipboard.writeText(card.referral_whatsapp_message);
      setCopiedMessage(true);
      setTimeout(() => setCopiedMessage(false), 2000);
    } catch {
      // Fallback
    }
  }

  if (!cleanCode) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.centerBox}>
          <h2 style={{ color: "#f87171", fontSize: "1.4rem" }}>Link Inválido</h2>
          <p style={{ color: "#94a3b8", maxWidth: "380px" }}>
            Nenhum código de Cartão VIP foi informado. Verifique o link e tente novamente.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.centerBox}>
          <div className={styles.spinner} />
          <p style={{ color: "#94a3b8" }}>Carregando seu Cartão VIP...</p>
        </div>
      </div>
    );
  }

  if (isError || !card) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.centerBox}>
          <h2 style={{ color: "#f87171", fontSize: "1.4rem" }}>Cartão VIP não encontrado</h2>
          <p style={{ color: "#94a3b8", maxWidth: "380px" }}>
            Não encontramos nenhum cartão vinculado ao código <strong>{cleanCode}</strong>.
            Verifique o link enviado pela clínica ou solicite um novo acesso.
          </p>
          <button
            type="button"
            onClick={() => refetch()}
            className={styles.copyCodeBtn}
            style={{ marginTop: "16px", padding: "8px 16px" }}
          >
            🔄 Tentar Novamente
          </button>
        </div>
      </div>
    );
  }


  const tierClass =
    card.vip_tier === "DIAMOND"
      ? styles.cardDiamond
      : card.vip_tier === "GOLD"
      ? styles.cardGold
      : card.vip_tier === "SILVER"
      ? styles.cardSilver
      : styles.cardBronze;

  const creditFormatted = formatBRL(
    money(Number(card.monetary_credit_value || 0).toFixed(2))
  );

  const progressPercent = card.next_tier_threshold
    ? Math.min(100, Math.max(0, Math.round((card.loyalty_points / card.next_tier_threshold) * 100)))
    : 100;

  const whatsappShareUrl = `https://wa.me/?text=${encodeURIComponent(
    card.referral_whatsapp_message
  )}`;

  return (
    <div className={styles.wrapper}>
      <main className={styles.container}>
        {/* Header Institucional */}
        <header className={styles.header}>
          <div className={styles.clinicBadge}>
            <span>✨</span> {card.clinic_name}
          </div>
          <h1 className={styles.title}>Cartão Fidelidade VIP</h1>
          <p className={styles.subtitle}>
            Olá, {card.patient_first_name}! Acompanhe seus benefícios exclusivos.
          </p>
        </header>

        {/* Cartão VIP Interativo */}
        <div className={styles.cardWrapper}>
          <div className={`${styles.vipCard} ${tierClass}`}>
            <div className={styles.cardShimmer} />

            <div className={styles.cardTopRow}>
              <span className={styles.cardClinicName}>{card.clinic_name}</span>
              <div className={styles.cardChip}>
                <div className={styles.chipSim} />
                <span className={styles.tierPill}>
                  {card.vip_badge} {card.vip_tier}
                </span>
              </div>
            </div>

            <div className={styles.cardMiddleRow}>
              <span className={styles.patientLabel}>Membro VIP</span>
              <h2 className={styles.patientName}>{card.patient_full_name}</h2>
            </div>

            <div className={styles.cardBottomRow}>
              <div className={styles.pointsBlock}>
                <span className={styles.pointsValue}>{card.loyalty_points}</span>
                <span className={styles.pointsLabel}>Pontos Acumulados</span>
              </div>

              <div className={styles.creditValue}>
                <span className={styles.creditAmount}>{creditFormatted}</span>
                <span className={styles.creditLabel}>em créditos / descontos</span>
              </div>
            </div>
          </div>
        </div>

        {/* Barra de Progresso do Nível VIP */}
        <div className={styles.progressCard}>
          <div className={styles.progressHeader}>
            <span style={{ fontWeight: 600 }}>Nível {card.vip_tier}</span>
            {card.next_tier ? (
              <span style={{ color: "#38bdf8", fontWeight: 700 }}>
                Próximo: {card.next_tier}
              </span>
            ) : (
              <span style={{ color: "#38bdf8", fontWeight: 700 }}>Nível Máximo ✨</span>
            )}
          </div>

          <div className={styles.progressBarBg}>
            <div
              className={styles.progressBarFill}
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <div className={styles.progressFooter}>
            {card.next_tier ? (
              <>
                Faltam apenas <strong>{card.points_to_next_tier} pontos</strong> para você atingir a
                categoria <strong>{card.next_tier}</strong> e desbloquear mais vantagens!
              </>
            ) : (
              <>
                Parabéns! Você alcançou nossa categoria máxima Diamante, com benefícios e
                atendimento prioritário exclusivo.
              </>
            )}
          </div>
        </div>

        {/* Motor Traga uma Amiga */}
        <section className={styles.referralCard}>
          <div className={styles.referralHeader}>
            <div className={styles.referralIcon}>🎁</div>
            <div>
              <h3 className={styles.referralTitle}>Traga uma Amiga e Ganhe Pontos</h3>
              <p className={styles.referralSub}>
                Compartilhe seu código com amigas. Quando elas realizarem a 1ª sessão, ambas
                ganham bônus especiais!
              </p>
            </div>
          </div>

          <div className={styles.codeBox}>
            <div>
              <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase" }}>
                Seu Código de Indicação
              </div>
              <span className={styles.codeText}>{card.referral_code}</span>
            </div>

            <button
              type="button"
              onClick={handleCopyCode}
              className={styles.copyCodeBtn}
            >
              {copiedCode ? "✓ Copiado!" : "Copiar Código"}
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <a
              href={whatsappShareUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.whatsappShareBtn}
            >
              <span>💬 Convidar Amiga no WhatsApp</span>
            </a>

            <button
              type="button"
              onClick={handleCopyInviteMessage}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                fontSize: "0.82rem",
                cursor: "pointer",
                textDecoration: "underline",
                padding: "4px",
              }}
            >
              {copiedMessage ? "✓ Mensagem completa copiada!" : "Ou copiar texto completo do convite"}
            </button>
          </div>
        </section>

        {/* Catálogo de Vantagens e Resgates */}
        {card.catalog_rewards && card.catalog_rewards.length > 0 && (
          <section className={styles.rewardsSection}>
            <div className={styles.sectionHeading}>
              <span>Catálogo de Resgates VIP</span>
              <span style={{ fontSize: "0.82rem", color: "#94a3b8", fontWeight: 400 }}>
                {card.loyalty_points} pts disponíveis
              </span>
            </div>

            <div className={styles.rewardsList}>
              {card.catalog_rewards.map((reward, index) => {
                const canRedeem = card.loyalty_points >= reward.points_cost;
                const pointsMissing = reward.points_cost - card.loyalty_points;

                return (
                  <div
                    key={index}
                    className={`${styles.rewardItem} ${canRedeem ? styles.rewardItemActive : ""}`}
                  >
                    <div className={styles.rewardContent}>
                      <div className={styles.rewardTitle}>{reward.title}</div>
                      <div className={styles.rewardDesc}>{reward.description}</div>
                    </div>

                    <div className={styles.rewardStatusCol}>
                      <span className={styles.pointsBadge}>
                        {reward.points_cost} pts
                      </span>
                      {canRedeem ? (
                        <span className={styles.availTag}>✓ Disponível</span>
                      ) : (
                        <span className={styles.needTag}>Faltam {pointsMissing} pts</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* CTA Agendamento Público */}
        {card.public_booking_slug && (
          <div className={styles.bookingCtaCard}>
            <div style={{ fontSize: "1.02rem", fontWeight: 700, color: "#f8fafc" }}>
              Deseja agendar sua próxima sessão?
            </div>
            <p style={{ margin: 0, fontSize: "0.84rem", color: "#94a3b8", maxWidth: "360px" }}>
              Escolha o melhor dia e horário diretamente na agenda online da clínica.
            </p>
            <Link
              to={`/agendar/${card.public_booking_slug}`}
              className={styles.bookingBtn}
            >
              📅 Agendar meu Horário
            </Link>
          </div>
        )}

        {/* Rodapé Seguro */}
        <footer className={styles.footer}>
          <p>
            🔒 Cartão pessoal e intransferível • {card.clinic_name}
            <br />
            Para resgatar pontos ou tirar dúvidas, informe seu código na recepção.
          </p>
        </footer>
      </main>
    </div>
  );
}
