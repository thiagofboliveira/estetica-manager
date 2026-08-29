import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import {
  proceduresApi,
  type ProcedureCreateInput,
  type ProcedureUpdateInput,
} from "./api";

export function useProcedures() {
  return useQuery({
    queryKey: qk.procedures(),
    queryFn: () => proceduresApi.list({ limit: 200 }),
    ...CACHE.CATALOG,
  });
}

export function useProcedure(id: string) {
  return useQuery({
    queryKey: [...qk.procedures(), "detail", id] as const,
    queryFn: () => proceduresApi.get(id),
    ...CACHE.CATALOG,
  });
}

export function useCreateProcedure() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProcedureCreateInput) => proceduresApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.procedures() });
    },
  });
}

export function useUpdateProcedure(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProcedureUpdateInput) => proceduresApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.procedures() });
    },
  });
}

export function useDeactivateProcedure() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => proceduresApi.deactivate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.procedures() });
    },
  });
}
