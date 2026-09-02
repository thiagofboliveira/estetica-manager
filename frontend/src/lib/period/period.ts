export type Period = "today" | "last_7_days" | "this_month" | "last_month" | "custom";

export type PeriodParams = {
  period: Period;
  date_from?: string;
  date_to?: string;
};

export const PERIOD_OPTIONS: { value: Period; label: string }[] = [
  { value: "today", label: "Hoje" },
  { value: "last_7_days", label: "Últimos 7 dias" },
  { value: "this_month", label: "Este mês" },
  { value: "last_month", label: "Mês anterior" },
  { value: "custom", label: "Personalizado" },
];
