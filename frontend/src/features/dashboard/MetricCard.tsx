import type { ReactNode } from "react";

type Props = {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  alert?: boolean;
};

/**
 * Um slide do carrossel de métricas — mesma "chrome" visual que
 * .dashboard__metric já usava como card de grid, agora dentro do
 * Carousel genérico (F5-02).
 */
export function MetricCard({ label, value, note, alert }: Props) {
  return (
    <dl className={`dashboard__metric${alert ? " dashboard__metric--alert" : ""}`}>
      <dt>{label}</dt>
      <dd>{value}</dd>
      {note && <span className="dashboard__metric-note">{note}</span>}
    </dl>
  );
}
