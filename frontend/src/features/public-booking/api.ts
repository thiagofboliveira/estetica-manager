import { api } from "@/lib/http/client";

export type PublicProcedure = {
  id: string;
  name: string;
  price: string;
  return_interval_days: number | null;
  session_plan: string;
  image_url?: string | null;
};

export type PublicProfessionalInfo = {
  name: string;
  slug: string;
  bio: string | null;
  avatar_url?: string | null;
  specialty?: string | null;
  procedures: PublicProcedure[];
};

export type PublicBookingCreateInput = {
  procedure_id: string;
  scheduled_at: string;
  patient_name: string;
  patient_phone: string;
  note?: string | null;
  patient_consent_whatsapp?: boolean;
};

export type PublicBookingRescheduleInput = {
  scheduled_at?: string;
  procedure_id?: string;
  note?: string | null;
};

export type PublicBooking = {
  id: string;
  professional_name: string;
  professional_slug: string | null;
  patient_name: string;
  patient_phone: string | null;
  procedure_id: string | null;
  procedure_name: string | null;
  procedure_price: string | null;
  scheduled_at: string;
  status: "SCHEDULED" | "COMPLETED" | "CANCELLED" | "NO_SHOW";
  note: string | null;
  management_token: string;
};

export const publicBookingApi = {
  getAgendaInfo: (slug: string) =>
    api.get<PublicProfessionalInfo>(`/public/agenda/${encodeURIComponent(slug)}`),

  getSlots: (slug: string, date: string) =>
    api.get<string[]>(`/public/agenda/${encodeURIComponent(slug)}/slots?date=${date}`),

  createBooking: (slug: string, payload: PublicBookingCreateInput) =>
    api.post<PublicBooking>(`/public/agenda/${encodeURIComponent(slug)}/bookings`, payload),

  getBooking: (id: string, token: string) =>
    api.get<PublicBooking>(`/public/bookings/${id}?token=${encodeURIComponent(token)}`),

  rescheduleBooking: (id: string, token: string, payload: PublicBookingRescheduleInput) =>
    api.patch<PublicBooking>(
      `/public/bookings/${id}/reschedule?token=${encodeURIComponent(token)}`,
      payload
    ),

  cancelBooking: (id: string, token: string) =>
    api.post<PublicBooking>(
      `/public/bookings/${id}/cancel?token=${encodeURIComponent(token)}`,
      {}
    ),
};
