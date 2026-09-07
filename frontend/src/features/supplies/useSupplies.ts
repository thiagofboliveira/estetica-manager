import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getSupplies,
  createSupply,
  updateSupply,
  deleteSupply,
  recordSupplyMovement,
  getRecentMovements,
  type SupplyCreatePayload,
  type SupplyUpdatePayload,
  type SupplyMovementPayload,
} from "./suppliesApi";

export const SUPPLIES_KEY = ["supplies"] as const;
export const MOVEMENTS_KEY = ["supply_movements"] as const;

export function useSupplies(params?: {
  category?: string;
  search?: string;
  low_stock_only?: boolean;
}) {
  return useQuery({
    queryKey: [...SUPPLIES_KEY, params],
    queryFn: () => getSupplies(params),
    staleTime: 1000 * 60, // 1 min
  });
}

export function useCreateSupply() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SupplyCreatePayload) => createSupply(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIES_KEY });
      queryClient.invalidateQueries({ queryKey: MOVEMENTS_KEY });
    },
  });
}

export function useUpdateSupply() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ supplyId, payload }: { supplyId: string; payload: SupplyUpdatePayload }) =>
      updateSupply(supplyId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIES_KEY });
    },
  });
}

export function useDeleteSupply() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (supplyId: string) => deleteSupply(supplyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIES_KEY });
    },
  });
}

export function useRecordSupplyMovement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      supplyId,
      payload,
    }: {
      supplyId: string;
      payload: SupplyMovementPayload;
    }) => recordSupplyMovement(supplyId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIES_KEY });
      queryClient.invalidateQueries({ queryKey: MOVEMENTS_KEY });
    },
  });
}

export function useRecentSupplyMovements() {
  return useQuery({
    queryKey: MOVEMENTS_KEY,
    queryFn: () => getRecentMovements(),
    staleTime: 1000 * 30, // 30s
  });
}
