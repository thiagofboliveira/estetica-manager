import { api } from "@/lib/http/client";
import type { PeriodParams } from "@/lib/period/period";

export type DashboardParams = PeriodParams;

export type Dashboard = {
  period: string;
  date_from: string;
  date_to: string;

  has_any_data: boolean;

  gross_revenue: string;
  net_profit: string;
  fixed_expenses_total: string | null;
  net_profit_after_fixed_expenses: string | null;
  receivable_amount: string;

  average_margin: string | null;
  sale_count: number;
  session_count: number;
  average_ticket: string | null;
};

export const dashboardApi = {
  get: (params: DashboardParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return api.get<Dashboard>(`/dashboard?${qs.toString()}`);
  },
};
