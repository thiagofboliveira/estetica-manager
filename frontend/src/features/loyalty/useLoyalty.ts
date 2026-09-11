import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CACHE } from "@/lib/query/client";
import { loyaltyApi, type LoyaltyAdjustRequest } from "./loyaltyApi";

export const loyaltyKeys = {
  all: ["loyalty"] as const,
  overview: () => [...loyaltyKeys.all, "overview"] as const,
  patient: (patientId: string) => [...loyaltyKeys.all, "patient", patientId] as const,
  referral: (patientId: string) => [...loyaltyKeys.all, "referral", patientId] as const,
  publicCard: (code: string) => [...loyaltyKeys.all, "public-card", code] as const,
};

export function usePatientLoyalty(patientId: string) {
  return useQuery({
    queryKey: loyaltyKeys.patient(patientId),
    queryFn: () => loyaltyApi.getPatientLoyalty(patientId),
    enabled: Boolean(patientId),
    ...CACHE.CATALOG,
  });
}

export function usePatientReferral(patientId: string) {
  return useQuery({
    queryKey: loyaltyKeys.referral(patientId),
    queryFn: () => loyaltyApi.getReferralInfo(patientId),
    enabled: Boolean(patientId),
    ...CACHE.CATALOG,
  });
}

export function useLoyaltyOverview() {
  return useQuery({
    queryKey: loyaltyKeys.overview(),
    queryFn: () => loyaltyApi.getOverview(),
    ...CACHE.CATALOG,
  });
}

export function usePublicVipCard(code: string) {
  return useQuery({
    queryKey: loyaltyKeys.publicCard(code),
    queryFn: () => loyaltyApi.getPublicVipCard(code),
    enabled: Boolean(code),
    ...CACHE.CATALOG,
  });
}

export function useSendVipCardEmail(patientId: string) {
  return useMutation({
    mutationFn: () => loyaltyApi.sendVipCardEmail(patientId),
  });
}

export function useAdjustLoyaltyPoints(patientId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LoyaltyAdjustRequest) =>
      loyaltyApi.adjustPoints(patientId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: loyaltyKeys.patient(patientId) });
      queryClient.invalidateQueries({ queryKey: loyaltyKeys.referral(patientId) });
      queryClient.invalidateQueries({ queryKey: loyaltyKeys.overview() });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });
}

