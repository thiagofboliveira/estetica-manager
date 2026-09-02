import { useMutation, useQuery } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import { invalidateAfterRetentionChange } from "@/lib/query/invalidation";
import { retentionApi, type RetentionUpdateInput } from "./api";

export function useRetentionOpportunities() {
  return useQuery({
    queryKey: qk.retentionList(),
    queryFn: () => retentionApi.list(),
    ...CACHE.MONEY,
  });
}

export function useUpdateOpportunity() {
  return useMutation({
    mutationFn: ({ opportunityId, payload }: { opportunityId: string; payload: RetentionUpdateInput }) =>
      retentionApi.updateOpportunity(opportunityId, payload),
    onSuccess: () => {
      void invalidateAfterRetentionChange();
    },
  });
}
