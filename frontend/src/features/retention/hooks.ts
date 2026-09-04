import { useMutation, useQuery } from "@tanstack/react-query";
import { CACHE, queryClient } from "@/lib/query/client";
import { qk } from "@/lib/query/keys";
import {
  retentionApi,
  type ReturnOpportunityUpdate,
} from "./api";

export function useRetentionCards(referenceDate?: string) {
  return useQuery({
    queryKey: [...qk.retention(), { referenceDate }],
    queryFn: () => retentionApi.getCards(referenceDate),
    ...CACHE.MONEY,
  });
}

export function useReengagement(inactiveDays: number, page: number, pageSize: number) {
  return useQuery({
    queryKey: qk.retentionReengagement(inactiveDays, page, pageSize),
    queryFn: () => retentionApi.getReengagement(inactiveDays, page, pageSize),
    ...CACHE.MONEY,
  });
}

export function useUpdateRetentionOpportunity() {
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReturnOpportunityUpdate }) =>
      retentionApi.updateOpportunity(id, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: qk.retention() });
    },
  });
}
