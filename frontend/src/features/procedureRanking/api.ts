import { api } from "@/lib/http/client";
import type { PeriodParams } from "@/lib/period/period";

export type ProcedureRankingParams = PeriodParams;

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

export const procedureRankingApi = {
  get: (params: ProcedureRankingParams) => {
    const qs = new URLSearchParams({ period: params.period });
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return api.get<ProcedureRanking>(`/reports/procedures?${qs.toString()}`);
  },
};
