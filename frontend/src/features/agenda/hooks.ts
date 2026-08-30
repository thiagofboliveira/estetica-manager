import { useMutation, useQuery } from "@tanstack/react-query";
import { CACHE } from "@/lib/query/client";
import { invalidateAfterScheduling } from "@/lib/query/invalidation";
import { qk } from "@/lib/query/keys";
import {
  bookingsApi,
  sessionsApi,
  type BookingCreateInput,
  type BookingUpdateInput,
  type SessionUpdateInput,
} from "./api";

export function useAgenda(from: string, to: string) {
  return useQuery({
    queryKey: qk.sessionsRange(from, to),
    queryFn: () => sessionsApi.getAgenda(from, to),
    ...CACHE.MONEY,
    enabled: Boolean(from && to),
  });
}

export function useOpenPackages() {
  return useQuery({
    queryKey: qk.packagesOpen(),
    queryFn: () => sessionsApi.getOpenPackages(),
    ...CACHE.MONEY,
  });
}

export function useScheduleSession() {
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SessionUpdateInput }) =>
      sessionsApi.updateSession(id, payload),
    onSuccess: async () => {
      await invalidateAfterScheduling();
    },
  });
}

export function useCreateBooking() {
  return useMutation({
    mutationFn: (payload: BookingCreateInput) => bookingsApi.create(payload),
    onSuccess: async () => {
      await invalidateAfterScheduling();
    },
  });
}

export function useUpdateBooking() {
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: BookingUpdateInput }) =>
      bookingsApi.update(id, payload),
    onSuccess: async () => {
      await invalidateAfterScheduling();
    },
  });
}
