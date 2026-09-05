import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import {
  proceduresApi,
  type ProcedureCreateInput,
  type ProcedureListParams,
  type ProcedureUpdateInput,
} from "./api";

// Usado por formulários/pickers que precisam do catálogo inteiro para
// montar um <select> (SaleForm, PackageSaleForm, OnboardingChecklist) —
// não pagina, só lê a página grande o bastante para cobrir o catálogo.
export function useProcedures() {
  return useQuery({
    queryKey: qk.procedures(),
    queryFn: () => proceduresApi.list({ page: 1, page_size: 200 }).then((r) => r.items),
    ...CACHE.CATALOG,
  });
}

// Usado pela tela de listagem paginada (ProceduresPage).
export function useProceduresPage(
  filters: Omit<ProcedureListParams, "page" | "page_size">,
  page: number,
  pageSize: number,
) {
  return useQuery({
    queryKey: [...qk.procedures(), "page", filters, page, pageSize] as const,
    queryFn: () => proceduresApi.list({ ...filters, page, page_size: pageSize }),
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
