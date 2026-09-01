import { useMutation, useQuery } from "@tanstack/react-query";
import { CACHE } from "@/lib/query/client";
import { invalidateAfterSettingsChange } from "@/lib/query/invalidation";
import { qk } from "@/lib/query/keys";
import {
  financialSettingsApi,
  paymentFeeRulesApi,
  type FinancialSettingsUpdate,
  type PaymentFeeRuleCreateInput,
  type PaymentFeeRuleUpdateInput,
} from "./api";

export function useFinancialSettings() {
  return useQuery({
    queryKey: qk.financialSettings(),
    queryFn: () => financialSettingsApi.get(),
    ...CACHE.SETTINGS,
  });
}

export function useUpdateFinancialSettings() {
  return useMutation({
    mutationFn: (payload: FinancialSettingsUpdate) => financialSettingsApi.update(payload),
    onSuccess: async () => {
      await invalidateAfterSettingsChange();
    },
  });
}

export function usePaymentFeeRules() {
  return useQuery({
    queryKey: qk.paymentFeeRules(),
    queryFn: () => paymentFeeRulesApi.list(),
    ...CACHE.SETTINGS,
  });
}

export function useCreatePaymentFeeRule() {
  return useMutation({
    mutationFn: (payload: PaymentFeeRuleCreateInput) => paymentFeeRulesApi.create(payload),
    onSuccess: async () => {
      await invalidateAfterSettingsChange();
    },
  });
}

export function useUpdatePaymentFeeRule() {
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: PaymentFeeRuleUpdateInput }) =>
      paymentFeeRulesApi.update(id, payload),
    onSuccess: async () => {
      await invalidateAfterSettingsChange();
    },
  });
}

export function useDeletePaymentFeeRule() {
  return useMutation({
    mutationFn: (id: string) => paymentFeeRulesApi.delete(id),
    onSuccess: async () => {
      await invalidateAfterSettingsChange();
    },
  });
}
