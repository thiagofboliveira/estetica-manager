import * as Sentry from "@sentry/react";

/**
 * Inicialização de telemetria de produção via Sentry (G-08).
 * Se VITE_SENTRY_DSN não estiver definido, permanece inativo sem efeito colateral.
 */
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) {
    return;
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
    sendDefaultPii: false, // Conformidade LGPD: não coleta dados pessoais automaticamente
  });
}
