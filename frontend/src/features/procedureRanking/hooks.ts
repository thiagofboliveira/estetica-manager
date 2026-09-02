import { useQuery } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import { procedureRankingApi, type ProcedureRankingParams } from "./api";

export function useProcedureRanking(params: ProcedureRankingParams) {
  return useQuery({
    queryKey: qk.proceduresRanking(params),
    queryFn: () => procedureRankingApi.get(params),
    ...CACHE.MONEY,
    enabled: params.period !== "custom" || Boolean(params.date_from && params.date_to),
  });
}
