/**
 * Mock de telemetria / Sentry para falhas silenciosas
 */
export const Logger = {
  captureException: (error: unknown, context?: Record<string, unknown>) => {
    // Em produção, isso seria enviado ao Sentry, Datadog, etc.
    console.error("[TELEMETRY] Exceção capturada:", error);
    if (context) {
      console.error("[TELEMETRY] Contexto:", context);
    }
  },
  captureMessage: (message: string, level: "info" | "warning" | "error" = "info") => {
    console.info(`[TELEMETRY][${level}] ${message}`);
  },
};
