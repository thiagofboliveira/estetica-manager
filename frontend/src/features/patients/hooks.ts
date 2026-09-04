import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import { CACHE } from "@/lib/query/client";
import {
  patientsApi,
  type PatientCreateInput,
  type PatientListParams,
  type PatientUpdateInput,
} from "./api";

// Usado por PatientPicker/OnboardingChecklist, que precisam de uma
// lista simples (não paginada) para montar um <select> ou checar
// "existe pelo menos uma paciente cadastrada".
export function usePatientsSearch(search: string) {
  return useQuery({
    queryKey: qk.patientsSearch(search),
    queryFn: () =>
      patientsApi.list({ search: search || undefined, page: 1, page_size: 50 }).then((r) => r.items),
    ...CACHE.SEARCH,
  });
}

export function usePatients(search = "") {
  return usePatientsSearch(search);
}

// Usado pela tela de listagem paginada (PatientsPage).
export function usePatientsPage(
  filters: Omit<PatientListParams, "page" | "page_size">,
  page: number,
  pageSize: number,
) {
  return useQuery({
    queryKey: [...qk.patients(), "page", filters, page, pageSize] as const,
    queryFn: () => patientsApi.list({ ...filters, page, page_size: pageSize }),
    ...CACHE.SEARCH,
  });
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: qk.patientDetail(id),
    queryFn: () => patientsApi.get(id),
    ...CACHE.CATALOG,
  });
}

export function useCreatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: PatientCreateInput) => patientsApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patients() });
    },
  });
}

export function useUpdatePatient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: PatientUpdateInput) => patientsApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patients() });
    },
  });
}

export function useArchivePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => patientsApi.archive(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patients() });
    },
  });
}

export function useAnonymizePatient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => patientsApi.anonymize(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patientDetail(id) });
      qc.invalidateQueries({ queryKey: qk.patients() });
    },
  });
}

export function useOptOutPatient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => patientsApi.optOut(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patientDetail(id) });
      qc.invalidateQueries({ queryKey: qk.patients() });
    },
  });
}

export function usePatientImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { patients: { name: string; phone?: string | null }[] }) => 
      patientsApi.batchImport(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patients() });
    },
  });
}
