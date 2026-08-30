import { api } from "@/lib/http/client";

export type Modality = "IN_PERSON" | "REMOTE";

export type SessionStatus =
  | "PENDING"
  | "SCHEDULED"
  | "CONFIRMED"
  | "COMPLETED"
  | "NO_SHOW"
  | "CANCELLED"
  | "EXPIRED";

export type BookingStatus = "PROVISIONAL" | "CONVERTED" | "CANCELLED";

export type AgendaItem = {
  id: string;
  type: "SESSION" | "BOOKING";
  patient_id: string | null;
  patient_name: string;
  patient_phone: string | null;
  procedure_name: string;
  scheduled_at: string;
  modality: Modality;
  status: string;
  sequence_number: number | null;
  total_sessions: number | null;
  note: string | null;
};

export type OpenPackage = {
  sale_id: string;
  sale_item_id: string;
  patient_id: string;
  patient_name: string;
  patient_phone: string | null;
  procedure_id: string;
  procedure_name: string;
  total_sessions: number;
  used_sessions: number;
  pending_sessions: number;
  last_session_completed_at: string | null;
  next_pending_session_id: string | null;
};

export type SessionUpdateInput = {
  scheduled_at?: string | null;
  status?: SessionStatus | null;
  cost_override?: string | null;
  notes?: string | null;
};

export type BookingCreateInput = {
  patient_id?: string | null;
  patient_name_hint?: string | null;
  scheduled_at: string;
  modality?: Modality;
  note?: string | null;
};

export type BookingUpdateInput = {
  patient_id?: string | null;
  patient_name_hint?: string | null;
  scheduled_at?: string | null;
  modality?: Modality | null;
  note?: string | null;
  status?: BookingStatus | null;
};

export const sessionsApi = {
  getAgenda: (from: string, to: string) => {
    const qs = new URLSearchParams({ from, to });
    return api.get<AgendaItem[]>(`/sessions?${qs.toString()}`);
  },
  getOpenPackages: () => api.get<OpenPackage[]>("/packages/open"),
  updateSession: (id: string, payload: SessionUpdateInput) =>
    api.patch<void>(`/sessions/${id}`, payload),
};

export const bookingsApi = {
  create: (payload: BookingCreateInput) => api.post<void>("/bookings", payload),
  update: (id: string, payload: BookingUpdateInput) =>
    api.patch<void>(`/bookings/${id}`, payload),
};
