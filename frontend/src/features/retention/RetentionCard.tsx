import { useState } from "react";
import { formatBRL } from "@/lib/money/format";
import { money } from "@/lib/money/money";
import { Logger } from "@/lib/telemetry/logger";
import { MESSAGES, fillTemplate } from "@/lib/constants/messages";
import { toWhatsAppUrl } from "@/lib/whatsapp";
import type { PatientRetentionCard } from "./api";
import { useDraftReturnMessage, useUpdateRetentionOpportunity } from "./hooks";
import { IconAlertTriangle, IconCalendar, IconWhatsApp, IconSparkles } from "@/ui/icons";
import styles from "./RetentionCard.module.css";

type Props = {
  card: PatientRetentionCard;
};

export function RetentionCard({ card }: Props) {
  const updateOpportunity = useUpdateRetentionOpportunity();
  const draftMessage = useDraftReturnMessage();
  const [feedback, setFeedback] = useState<string | null>(null);
  const [customMessage, setCustomMessage] = useState<string | null>(null);
  const [draftNotice, setDraftNotice] = useState<string | null>(null);

  const primaryOpp = card.primary_opportunity;

  const defaultMessage = fillTemplate(MESSAGES.RETENTION.WHATSAPP_DEFAULT, {
    patient_name: card.patient_name,
    procedure_name: primaryOpp.procedure_name,
  });

  const whatsappUrl = card.whatsapp_enabled
    ? toWhatsAppUrl(card.patient_phone, customMessage ?? defaultMessage)
    : null;

  async function handleSuggestMessage() {
    setDraftNotice(null);
    try {
      const draft = await draftMessage.mutateAsync(primaryOpp.id);
      setCustomMessage(draft.text);
      if (draft.source === "fallback") {
        setDraftNotice(
          draft.fallback_reason === "limit_reached"
            ? "Você usou todas as sugestões do mês. Este é o texto padrão."
            : "Texto padrão (a sugestão automática não está disponível agora).",
        );
      } else {
        setDraftNotice("Sugestão pronta. Revise e ajuste antes de enviar.");
      }
    } catch (error) {
      Logger.captureException(error, { context: "Draft message fail", opportunityId: primaryOpp.id });
      setDraftNotice("Não foi possível gerar a sugestão. Use a mensagem padrão.");
    }
  }

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
      setFeedback("Contato registrado!");
    } catch (error) {
      Logger.captureException(error, { context: "WhatsApp Tracking Fail", opportunityId: primaryOpp.id });
      setFeedback("Mensagem aberta, mas não foi possível sincronizar o status no servidor.");
    }
  }

  function getTimingBadge(timing: string, daysDiff: number) {
    if (timing === "OVERDUE") {
      return (
        <span className="badge badge--danger">
          <IconAlertTriangle width="12" height="12" />
          <span>Atrasado ({Math.abs(daysDiff)} {Math.abs(daysDiff) === 1 ? "dia" : "dias"})</span>
        </span>
      );
    }
    if (timing === "DUE") {
      return (
        <span className="badge badge--accent">
          <IconSparkles width="12" height="12" />
          <span>Na janela ideal</span>
        </span>
      );
    }
    return (
      <span className="badge badge--neutral">
        <IconCalendar width="12" height="12" />
        <span>Em {daysDiff} dias</span>
      </span>
    );
  }

  return (
    <article className={styles.card}>
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
          {card.whatsapp_enabled && (
            <>
              <button
                type="button"
                onClick={handleSuggestMessage}
                disabled={draftMessage.isPending}
                className="button button--secondary tap-target"
              >
                <IconSparkles width="16" height="16" />
                <span>{draftMessage.isPending ? "Gerando…" : "Sugerir mensagem"}</span>
              </button>
              {customMessage !== null && (
                <textarea
                  aria-label={`Mensagem para ${card.patient_name}`}
                  value={customMessage}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  rows={4}
                  style={{ width: "100%", fontSize: "16px", marginTop: "8px" }}
                />
              )}
              {draftNotice && (
                <span style={{ fontSize: "12px", display: "block", marginTop: "4px" }}>
                  {draftNotice}
                </span>
              )}
            </>
          )}
          {whatsappUrl ? (
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noreferrer"
              onClick={handleWhatsAppClick}
              className="button button--whatsapp tap-target"
            >
              <IconWhatsApp width="16" height="16" />
              <span>Chamar no WhatsApp</span>
            </a>
          ) : (
            <button
              type="button"
              disabled
              className="button button--secondary tap-target"
              title={card.disabled_reason || "WhatsApp indisponível"}
            >
              <IconWhatsApp width="16" height="16" />
              <span>WhatsApp indisponível ({card.disabled_reason || "Sem consentimento"})</span>
            </button>
          )}
          {feedback && (
            <span style={{ fontSize: "12px", color: feedback.includes("não") ? "#dc2626" : "#059669", marginTop: "4px", display: "block" }}>
              {feedback}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
