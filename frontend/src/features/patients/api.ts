import { api } from "@/lib/http/client";

export type Patient = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  birth_date: string | null;
  notes: string | null;
  consent_whatsapp: boolean;
  consent_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type PatientCreateInput = {
  name: string;
  phone?: string | null;
  email?: string | null;
  birth_date?: string | null;
  notes?: string | null;
};

export type PatientUpdateInput = Partial<PatientCreateInput> & {
  consent_whatsapp?: boolean;
};

export const patientsApi = {
  list: (params: { search?: string; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.search) qs.set("search", params.search);
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.offset) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return api.get<Patient[]>(`/patients${suffix}`);
  },
  get: (id: string) => api.get<Patient>(`/patients/${id}`),
  create: (payload: PatientCreateInput) => api.post<Patient>("/patients", payload),
  update: (id: string, payload: PatientUpdateInput) =>
    api.patch<Patient>(`/patients/${id}`, payload),
  archive: (id: string) => api.del<void>(`/patients/${id}`),
};
