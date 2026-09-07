import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import {
  getActiveVials,
  getAllVials,
  createVial,
  consumeVialUnits,
  finishVial,
  deleteVial,
  type OpenVialCreatePayload,
  type OpenVialConsumePayload,
} from "./vialsApi";

export function useActiveVials() {
  return useQuery({
    queryKey: qk.vialsActive(),
    queryFn: getActiveVials,
    staleTime: 60_000,
  });
}

export function useAllVials() {
  return useQuery({
    queryKey: qk.vials(),
    queryFn: getAllVials,
  });
}

export function useCreateVial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: OpenVialCreatePayload) => createVial(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.vials() });
    },
  });
}

export function useConsumeVial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ vialId, payload }: { vialId: string; payload: OpenVialConsumePayload }) =>
      consumeVialUnits(vialId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.vials() });
    },
  });
}

export function useFinishVial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vialId: string) => finishVial(vialId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.vials() });
    },
  });
}

export function useDeleteVial() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vialId: string) => deleteVial(vialId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.vials() });
    },
  });
}
