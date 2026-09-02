import { PERIOD_OPTIONS, type Period } from "@/lib/period/period";

type Props = {
  period: Period;
  onPeriodChange: (period: Period) => void;
  dateFrom: string;
  onDateFromChange: (value: string) => void;
  dateTo: string;
  onDateToChange: (value: string) => void;
};

/**
 * Extraído do Dashboard (F-013) para reuso em F-013c. O guard de
 * "período custom sem as duas datas" fica em quem consome — a query
 * fica `enabled: false` nesse caso e o AsyncBoundary não distingue
 * "desabilitada" de "carregando" (ver frontend/BACKLOG.md).
 */
export function PeriodFilter({ period, onPeriodChange, dateFrom, onDateFromChange, dateTo, onDateToChange }: Props) {
  return (
    <>
      <div className="dashboard__period" role="group" aria-label="Período">
        {PERIOD_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className="tap-target"
            aria-pressed={period === opt.value}
            onClick={() => onPeriodChange(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {period === "custom" && (
        <div className="dashboard__custom-range">
          <label>
            <span>De</span>
            <input type="date" value={dateFrom} onChange={(e) => onDateFromChange(e.target.value)} />
          </label>
          <label>
            <span>Até</span>
            <input type="date" value={dateTo} onChange={(e) => onDateToChange(e.target.value)} />
          </label>
        </div>
      )}
    </>
  );
}
