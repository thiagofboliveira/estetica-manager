import { useQuery } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import { dashboardApi, type DashboardParams } from "./api";

export function useDashboard(params: DashboardParams) {
  return useQuery({
    queryKey: qk.dashboard(params),
    queryFn: () => dashboardApi.get(params),
    ...CACHE.MONEY,
    enabled: params.period !== "custom" || Boolean(params.date_from && params.date_to),
  });
}

export function useProcedureRanking(params: DashboardParams) {
  return useQuery({
    queryKey: qk.procedureRanking(params),
    queryFn: () => dashboardApi.getProcedureRanking(params),
    ...CACHE.MONEY,
    enabled: params.period !== "custom" || Boolean(params.date_from && params.date_to),
  });
}
