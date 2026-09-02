import { useMutation, useQuery } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import { invalidateAfterSettingsChange } from "@/lib/query/invalidation";
import { financialSettingsApi, type FinancialSettingsUpdateInput } from "./api";

export function useFinancialSettings() {
  return useQuery({
    queryKey: qk.settings(),
    queryFn: () => financialSettingsApi.get(),
    ...CACHE.SETTINGS,
  });
}

// Muda taxa/split: recalcula todo lucro histórico exibido (dashboard,
// ranking, vendas) — invalidateAfterSettingsChange cobre qk.financial()
// inteiro, não só qk.settings().
export function useUpdateFinancialSettings() {
  return useMutation({
    mutationFn: (payload: FinancialSettingsUpdateInput) => financialSettingsApi.update(payload),
    onSuccess: () => {
      void invalidateAfterSettingsChange();
    },
  });
}
