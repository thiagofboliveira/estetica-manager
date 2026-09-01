import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import styles from "./Toast.module.css";
import { IconCheck } from "./icons";

export type ToastType = "success" | "error" | "info";

export type ToastItem = {
  id: string;
  message: string;
  type: ToastType;
};

type ToastContextValue = {
  showToast: (message: string, type?: ToastType, durationMs?: number) => void;
  showSuccess: (message?: string, durationMs?: number) => void;
  showError: (message?: string, durationMs?: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

let globalShowToast: ((message: string, type?: ToastType, durationMs?: number) => void) | null = null;

/**
 * Função utilitária standalone para disparar toast de qualquer lugar do código.
 */
export const toast = {
  show: (message: string, type: ToastType = "success", durationMs = 3000) => {
    if (globalShowToast) {
      globalShowToast(message, type, durationMs);
    }
  },
  success: (message = "Salvo com sucesso!", durationMs = 3000) => {
    if (globalShowToast) {
      globalShowToast(message, "success", durationMs);
    }
  },
  error: (message = "Erro ao salvar.", durationMs = 4000) => {
    if (globalShowToast) {
      globalShowToast(message, "error", durationMs);
    }
  },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "success", durationMs = 3000) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      setToasts((prev) => [...prev, { id, message, type }]);

      setTimeout(() => {
        removeToast(id);
      }, durationMs);
    },
    [removeToast]
  );

  const showSuccess = useCallback(
    (message = "Salvo com sucesso!", durationMs = 3000) => {
      showToast(message, "success", durationMs);
    },
    [showToast]
  );

  const showError = useCallback(
    (message = "Não consegui salvar. Tenta de novo?", durationMs = 4000) => {
      showToast(message, "error", durationMs);
    },
    [showToast]
  );

  // Registra dispatch global
  globalShowToast = showToast;

  return (
    <ToastContext.Provider value={{ showToast, showSuccess, showError }}>
      {children}
      <div className={styles.toastContainer} aria-live="polite" aria-atomic="true">
        {toasts.map((t) => {
          const typeClass =
            t.type === "error"
              ? styles.toastError
              : t.type === "info"
              ? styles.toastInfo
              : styles.toastSuccess;

          return (
            <div key={t.id} className={`${styles.toast} ${typeClass}`} role="status">
              <div className={styles.icon}>
                {t.type === "success" && <IconCheck width="14" height="14" strokeWidth="2.5" />}
                {t.type === "error" && <span>✕</span>}
                {t.type === "info" && <span>ℹ</span>}
              </div>
              <div className={styles.message}>{t.message}</div>
              <button
                type="button"
                className={styles.closeBtn}
                onClick={() => removeToast(t.id)}
                aria-label="Fechar notificação"
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    return {
      showToast: toast.show,
      showSuccess: toast.success,
      showError: toast.error,
    };
  }
  return ctx;
}
