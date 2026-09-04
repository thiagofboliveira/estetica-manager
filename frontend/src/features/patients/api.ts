import { api } from "@/lib/http/client";

export type Gender = "FEMALE" | "MALE" | "OTHER" | "UNDISCLOSED";

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
  gender: Gender | null;
  created_at: string;
  updated_at: string;
};

export type PatientCreateInput = {
  name: string;
  phone?: string | null;
  email?: string | null;
  birth_date?: string | null;
  notes?: string | null;
  consent_whatsapp?: boolean;
  gender?: Gender | null;
};

export type PatientUpdateInput = Partial<PatientCreateInput> & {
  consent_whatsapp?: boolean;
};

export type BatchImportResult = {
  created_count: number;
  skipped_count: number;
  errors: { line: number; reason: string }[];
  patients: Patient[];
};

export type PatientList = {
  items: Patient[];
  total_count: number;
  page: number;
  page_size: number;
};

export type PatientListParams = {
  search?: string;
  gender?: Gender;
  has_upcoming_booking?: boolean;
  has_completed_treatment?: boolean;
  page?: number;
  page_size?: number;
};

export const patientsApi = {
  list: (params: PatientListParams = {}) => {
    const qs = new URLSearchParams();
    if (params.search) qs.set("search", params.search);
    if (params.gender) qs.set("gender", params.gender);
    if (params.has_upcoming_booking != null) {
      qs.set("has_upcoming_booking", String(params.has_upcoming_booking));
    }
    if (params.has_completed_treatment != null) {
      qs.set("has_completed_treatment", String(params.has_completed_treatment));
    }
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return api.get<PatientList>(`/patients${suffix}`);
  },
  get: (id: string) => api.get<Patient>(`/patients/${id}`),
  create: (payload: PatientCreateInput) => api.post<Patient>("/patients", payload),
  update: (id: string, payload: PatientUpdateInput) =>
    api.patch<Patient>(`/patients/${id}`, payload),
  archive: (id: string) => api.del<void>(`/patients/${id}`),
  anonymize: (id: string) => api.post<Patient>(`/patients/${id}/anonymize`, {}),
  optOut: (id: string) => api.post<Patient>(`/patients/${id}/opt-out`, {}),
  exportData: (id: string) => api.get<Record<string, unknown>>(`/patients/${id}/export`),
  batchImport: (payload: { patients: { name: string; phone?: string | null }[] }) => 
    api.post<BatchImportResult>("/patients/import", payload),
};
