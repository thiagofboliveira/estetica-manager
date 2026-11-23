import { useState } from "react";
import { Logger } from "@/lib/telemetry/logger";
import { retentionApi, type DraftMessage } from "./api";

/**
 * Rascunho de mensagem sugerido pela IA (AI-02/AI-06): gera, deixa a
 * profissional editar e, ao enviar, avisa o backend (só um contador, AI-05).
 * Nada é enviado por aqui: o envio é o link do WhatsApp.
 */
export function useDraftComposer(
  fetchDraft: () => Promise<DraftMessage>,
  logContext: Record<string, unknown>,
) {
  const [message, setMessage] = useState<string | null>(null);
  const [draft, setDraft] = useState<DraftMessage | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function generate() {
    setNotice(null);
    setPending(true);
    try {
      const result = await fetchDraft();
      setDraft(result);
      setMessage(result.text);
      if (result.source === "fallback") {
        setNotice(
          result.fallback_reason === "limit_reached"
            ? "Você usou todas as sugestões do mês. Este é o texto padrão."
            : "Texto padrão (a sugestão automática não está disponível agora).",
        );
      } else {
        setNotice("Sugestão pronta. Revise e ajuste antes de enviar.");
      }
    } catch (error) {
      Logger.captureException(error, { context: "Draft message fail", ...logContext });
      setNotice("Não foi possível gerar a sugestão. Use a mensagem padrão.");
    } finally {
      setPending(false);
    }
  }

  /** Chamar ao abrir o WhatsApp. Só conta rascunhos que vieram da IA. */
  function reportSent() {
    if (draft?.source !== "ai" || message === null) return;
    try {
      void Promise.resolve(retentionApi.reportDraftSent(message !== draft.text)).catch(
        () => undefined,
      );
    } catch {
      /* medição nunca atrapalha o envio */
    }
  }

  return { message, setMessage, notice, pending, generate, reportSent };
}
