import type { KeyboardEvent } from "react";

/**
 * Acessibilidade mínima para modais feitos com overlay + conteúdo:
 *  - `ref={focusModal}`: leva o foco para dentro do modal ao abrir (referência
 *    estável, então não rouba o foco de um campo a cada re-render);
 *  - `onKeyDown={escapeToClose(fechar)}`: Esc fecha, como o usuário de teclado espera.
 * O conteúdo deve ter `role="dialog"` e `aria-modal="true"`.
 */
export function focusModal(el: HTMLElement | null): void {
  if (el && !el.contains(document.activeElement)) el.focus();
}

export function escapeToClose(close: () => void) {
  return (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      close();
    }
  };
}
