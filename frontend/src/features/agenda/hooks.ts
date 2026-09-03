import { useMutation, useQuery } from "@tanstack/react-query";
import { CACHE, queryClient } from "@/lib/query/client";
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

export function useFreeSlots(date: string) {
  return useQuery({
    queryKey: qk.freeSlots(date),
    queryFn: () => sessionsApi.getFreeSlots(date),
    ...CACHE.MONEY,
    enabled: Boolean(date),
  });
}

export function useUnconfirmedSessions() {
  return useQuery({
    queryKey: [...qk.sessions(), "unconfirmed"],
    queryFn: () => sessionsApi.getUnconfirmed(),
    refetchInterval: 5 * 60 * 1000,
    ...CACHE.MONEY,
  });
}

export function useConfirmSession() {
  return useMutation({
    mutationFn: (id: string) => sessionsApi.confirmSession(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: [...qk.sessions(), "unconfirmed"] });
      const previousData = queryClient.getQueryData([...qk.sessions(), "unconfirmed"]);
      queryClient.setQueryData(
        [...qk.sessions(), "unconfirmed"],
        (old: any[] | undefined) =>
          old?.map(s =>
            s.session_id === id
              ? { ...s, confirmed_at: new Date().toISOString() }
              : s
          )
      );
      return { previousData };
    },
    onError: (_err, _id, context) => {
      if (context?.previousData) {
        queryClient.setQueryData([...qk.sessions(), "unconfirmed"], context.previousData);
      }
    },
    onSettled: async () => {
      await invalidateAfterScheduling();
    },
  });
}
