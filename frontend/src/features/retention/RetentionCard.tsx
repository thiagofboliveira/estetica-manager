import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { Logger } from "@/lib/telemetry/logger";
import { MESSAGES, fillTemplate } from "@/lib/constants/messages";
import type { PatientRetentionCard } from "./api";
import { useUpdateRetentionOpportunity } from "./hooks";
import styles from "./RetentionCard.module.css";

type Props = {
  card: PatientRetentionCard;
};

export function RetentionCard({ card }: Props) {
  const updateOpportunity = useUpdateRetentionOpportunity();

  const cleanPhone = card.patient_phone ? card.patient_phone.replace(/\D/g, "") : null;
  const primaryOpp = card.primary_opportunity;

  const defaultMessage = fillTemplate(MESSAGES.RETENTION.WHATSAPP_DEFAULT, {
    patient_name: card.patient_name,
    procedure_name: primaryOpp.procedure_name,
  });

  const whatsappUrl =
    cleanPhone && card.whatsapp_enabled
      ? `https://wa.me/55${cleanPhone}?text=${encodeURIComponent(defaultMessage)}`
      : null;

  async function handleWhatsAppClick() {
    try {
      await updateOpportunity.mutateAsync({
        id: primaryOpp.id,
        payload: {
          status: "CONTACTED",
          contact_channel: "WHATSAPP",
          contacted_at: new Date().toISOString(),
        },
      });
    } catch (error) {
      Logger.captureException(error, { context: "WhatsApp Tracking Silent Fail", opportunityId: primaryOpp.id });
    }
  }

  function getTimingBadge(timing: string, daysDiff: number) {
    if (timing === "OVERDUE") {
      return (
        <span className="badge badge--danger">
          ⚠️ Atrasado ({Math.abs(daysDiff)} {Math.abs(daysDiff) === 1 ? "dia" : "dias"})
        </span>
      );
    }
    if (timing === "DUE") {
      return <span className="badge badge--accent">⏰ Na janela ideal</span>;
    }
    return <span className="badge badge--neutral">Em {daysDiff} dias</span>;
  }

  return (
    <article className={`card ${styles.card}`}>
      <div className={styles.header}>
        <div className={styles.avatar}>
          {card.patient_name.charAt(0).toUpperCase()}
        </div>
        <div className={styles.patient}>
          <div className={styles.titleRow}>
            <h3 className={styles.name}>{card.patient_name}</h3>
            {getTimingBadge(primaryOpp.timing, primaryOpp.days_diff)}
          </div>
          <p className={styles.contact}>
            {card.patient_phone || "Sem telefone"}
            {card.last_contacted_at && (
              <span className={styles.lastContact}>
                • Último contato: {new Date(card.last_contacted_at).toLocaleDateString("pt-BR")}
              </span>
            )}
          </p>
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.opp}>
          <div className={styles.oppMain}>
            <span className={styles.oppTitle}>{primaryOpp.procedure_name}</span>
            <span className={styles.oppDue}>
              Vencimento do retorno: {new Date(primaryOpp.due_date).toLocaleDateString("pt-BR")}
            </span>
          </div>
          <span className={styles.oppValue}>
            {formatBRL(money(primaryOpp.potential_value))}
          </span>
        </div>

        {card.secondary_opportunities.length > 0 && (
          <div className={styles.secondaries}>
            <span className={styles.secondariesLabel}>Outros procedimentos vencendo:</span>
            <ul className={styles.secondariesList}>
              {card.secondary_opportunities.map((opp) => (
                <li key={opp.id}>
                  <span>{opp.procedure_name}</span>
                  <span className="font-semibold">{formatBRL(money(opp.potential_value))}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className={styles.footer}>
        <div className={styles.total}>
          <span>Potencial estimado:</span>
          <strong>{formatBRL(money(card.total_potential_value))}</strong>
        </div>

        <div className={styles.actions}>
          {whatsappUrl ? (
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noreferrer"
              onClick={handleWhatsAppClick}
              className="button button--whatsapp tap-target"
            >
              💬 Chamar no WhatsApp
            </a>
          ) : (
            <button
              type="button"
              disabled
              className="button button--secondary tap-target"
              title={card.disabled_reason || "WhatsApp indisponível"}
            >
              💬 WhatsApp desabilitado ({card.disabled_reason || "Sem consentimento"})
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
