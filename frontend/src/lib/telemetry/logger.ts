import * as Sentry from "@sentry/react";

/**
 * Cliente de telemetria e rastreamento de erros (G-08).
 * Envia para o Sentry quando inicializado em produção, e espelha no console para depuração local.
 */
export const Logger = {
  captureException: (error: unknown, context?: Record<string, unknown>) => {
    if (import.meta.env.VITE_SENTRY_DSN) {
      Sentry.captureException(error, { extra: context });
    }
    if (import.meta.env.DEV) {
      console.error("[TELEMETRY] Exceção capturada:", error);
      if (context) {
        console.error("[TELEMETRY] Contexto:", context);
      }
    }
  },
  captureMessage: (message: string, level: "info" | "warning" | "error" = "info") => {
    if (import.meta.env.VITE_SENTRY_DSN) {
      Sentry.captureMessage(message, level);
    }
    if (import.meta.env.DEV) {
      console.info(`[TELEMETRY][${level}] ${message}`);
    }
  },
};
