import { api } from "@/lib/http/client";

export type DashboardPeriod = "today" | "last_7_days" | "this_month" | "last_month" | "custom";

export type DashboardParams = {
  period: DashboardPeriod;
  date_from?: string;
  date_to?: string;
  scope?: "me" | "clinic";
  professional_id?: string;
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

  breakeven_remaining_amount: string | null;
  breakeven_remaining_sessions_estimate: number | null;
  breakeven_alert: boolean;

  // Gamificação: Metas & Conquistas (Sprint 1)
  monthly_revenue_goal?: string | null;
  goal_progress_percentage?: string | null;
  breakeven_beaten?: boolean;
  breakeven_beaten_date?: string | null;

  public_booking_count?: number;
  scope?: string;
  professionals_count?: number;
};


export type ProcedureRankingRow = {
  procedure_id: string;
  procedure_name: string;
  gross_revenue: string;
  net_profit: string;
  margin: string | null;
  // Sessão COMPLETED no período (I5) — não é SaleItem.quantity, que
  // inclui sessão PENDING/SCHEDULED ainda não realizada.
  session_count: number;
};

export type ProcedureRanking = {
  period: string;
  date_from: string;
  date_to: string;
  rows: ProcedureRankingRow[];
  total_count: number;
  page: number;
  page_size: number;
  scope?: string;
  professionals_count?: number;
};

export type ProcedureRankingParams = DashboardParams & {
  page?: number;
  page_size?: number;
};

export type ExpenseByCategoryRow = {
  category: string;
  monthly_amount: string;
};

export type ExpensesByCategory = {
  rows: ExpenseByCategoryRow[];
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
    if (params.scope) qs.set("scope", params.scope);
    if (params.professional_id) qs.set("professional_id", params.professional_id);
    return api.get<Dashboard>(`/dashboard?${qs.toString()}`);
  },
  getProcedureRanking: (params: ProcedureRankingParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    if (params.scope) qs.set("scope", params.scope);
    if (params.professional_id) qs.set("professional_id", params.professional_id);
    return api.get<ProcedureRanking>(`/reports/procedures?${qs.toString()}`);
  },
  getExpensesByCategory: (params?: { scope?: "me" | "clinic"; professional_id?: string }) => {
    const qs = new URLSearchParams();
    if (params?.scope) qs.set("scope", params.scope);
    if (params?.professional_id) qs.set("professional_id", params.professional_id);
    const qStr = qs.toString() ? `?${qs.toString()}` : "";
    return api.get<ExpensesByCategory>(`/reports/expenses-by-category${qStr}`);
  },
  getRoi: (params: DashboardParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return api.get<ROI>(`/dashboard/roi?${qs.toString()}`);
  },
};
