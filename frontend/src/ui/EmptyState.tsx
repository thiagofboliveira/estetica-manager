import type { ReactNode } from "react";

/**
 * A primeira sessão dela é 100% tela vazia. "Nenhum resultado
 * encontrado" lê como produto quebrado. Distinguir os três tons é o
 * que evita isso — ver ENGENHARIA.md §6.
 */
type Tone = "first-run" | "good" | "filtered";

type Props = {
  title: string;
  body?: string;
  tone?: Tone;
  action?: ReactNode;
};

export function EmptyState({ title, body, tone = "good", action }: Props) {
  return (
    <div className={`empty-state empty-state--${tone}`}>
      <p className="empty-state__title">{title}</p>
      {body && <p className="empty-state__body">{body}</p>}
      {action}
    </div>
  );
}
