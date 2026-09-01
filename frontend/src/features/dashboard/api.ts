import { api } from "@/lib/http/client";

export type DashboardPeriod = "today" | "last_7_days" | "this_month" | "last_month" | "custom";

export type DashboardParams = {
  period: DashboardPeriod;
  date_from?: string;
  date_to?: string;
};

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

export type ProcedureRankingRow = {
  procedure_id: string;
  procedure_name: string;
  gross_revenue: string;
  net_profit: string;
  margin: string | null;
};

export type ProcedureRanking = {
  period: string;
  date_from: string;
  date_to: string;
  rows: ProcedureRankingRow[];
};

export type ROI = {
  attributed_revenue: string;
  attributed_sale_count: number;
  patients_reactivated: number;
  roi_ratio: string | null;
  period: string;
  date_from: string;
  date_to: string;
  is_estimated: boolean;
};

export const dashboardApi = {
  get: (params: DashboardParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return api.get<Dashboard>(`/dashboard?${qs.toString()}`);
  },
  getProcedureRanking: (params: DashboardParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return api.get<ProcedureRanking>(`/reports/procedures?${qs.toString()}`);
  },
  getRoi: (params: DashboardParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return api.get<ROI>(`/dashboard/roi?${qs.toString()}`);
  },
};
