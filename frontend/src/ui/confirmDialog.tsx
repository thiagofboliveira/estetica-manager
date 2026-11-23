import { useEffect, useId, useRef } from "react";
import { createRoot } from "react-dom/client";
import styles from "./ConfirmDialog.module.css";

export type ConfirmOptions = {
  title?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Destaca o botão em vermelho. Por padrão é inferido de "excluir/remover…". */
  danger?: boolean;
};

const DESTRUCTIVE = /exclu|remov|irrevers|cancelar este/i;

type DialogProps = {
  message: string;
  options: ConfirmOptions;
  onResolve: (value: boolean) => void;
};

function Dialog({ message, options, onResolve }: DialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const messageId = useId();
  const danger = options.danger ?? DESTRUCTIVE.test(message);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    // Foco no "Cancelar": Enter por engano nunca confirma uma ação destrutiva.
    cancelRef.current?.focus();
    return () => previous?.focus?.();
  }, []);

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.stopPropagation();
      onResolve(false);
    } else if (e.key === "Tab") {
      // Prende o foco entre os dois botões.
      const first = cancelRef.current;
      const last = confirmRef.current;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    }
  }

  return (
    <div
      className={styles.backdrop}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onResolve(false);
      }}
    >
      <div
        className={styles.dialog}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={messageId}
        onKeyDown={onKeyDown}
      >
        <h2 id={titleId} className={styles.title}>
          {options.title ?? "Confirmar ação"}
        </h2>
        <p id={messageId} className={styles.message}>
          {message}
        </p>
        <div className={styles.actions}>
          <button
            ref={cancelRef}
            type="button"
            className={styles.btn}
            onClick={() => onResolve(false)}
          >
            {options.cancelLabel ?? "Cancelar"}
          </button>
          <button
            ref={confirmRef}
            type="button"
            className={`${styles.btn} ${danger ? styles.danger : styles.confirm}`}
            onClick={() => onResolve(true)}
          >
            {options.confirmLabel ?? "Confirmar"}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Substituto assíncrono de `window.confirm()`: `if (await confirmDialog("…"))`.
 * Imperativo (como o `toast`), então não exige provider na árvore.
 */
export function confirmDialog(
  message: string,
  options: ConfirmOptions = {},
): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    const host = document.createElement("div");
    document.body.appendChild(host);
    const root = createRoot(host);
    let settled = false;

    const onResolve = (value: boolean) => {
      if (settled) return;
      settled = true;
      resolve(value);
      // Desmonta fora do ciclo do evento que acabou de disparar.
      setTimeout(() => {
        root.unmount();
        host.remove();
      }, 0);
    };

    root.render(<Dialog message={message} options={options} onResolve={onResolve} />);
  });
}
