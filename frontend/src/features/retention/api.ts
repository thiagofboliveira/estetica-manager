import { api } from "@/lib/http/client";

export type Timing = "UPCOMING" | "DUE" | "OVERDUE";

export type ReturnOpportunityStatus =
  | "OPEN"
  | "CONTACTED"
  | "BOOKED"
  | "DECLINED"
  | "NO_RESPONSE"
  | "DISMISSED"
  | "CLOSED";

export type ContactChannel = "WHATSAPP" | "PHONE" | "IN_PERSON" | "OTHER";

export type OpportunityItem = {
  id: string;
  procedure_id: string;
  procedure_name: string;
  due_date: string;
  timing: Timing;
  status: ReturnOpportunityStatus;
  potential_value: string;
  days_diff: number;
};

export type PatientRetentionCard = {
  patient_id: string;
  patient_name: string;
  patient_phone: string | null;
  consent_whatsapp: boolean;
  opted_out: boolean;
  is_suppressed: boolean;
  last_contacted_at: string | null;
  total_potential_value: string;
  primary_opportunity: OpportunityItem;
  secondary_opportunities: OpportunityItem[];
  whatsapp_enabled: boolean;
  disabled_reason: string | null;
};

export type ReturnOpportunityUpdate = {
  status?: ReturnOpportunityStatus | null;
  contact_channel?: ContactChannel | null;
  contact_status?: string | null;
  contacted_at?: string | null;
  dismissed?: boolean | null;
};

export type Gender = "FEMALE" | "MALE" | "OTHER" | "UNDISCLOSED";

// F4-04/E4: reengajamento (nunca tratou / parado há X dias) é fonte
// separada do motor de retorno real acima — não misturar os contadores
// (I6/I7: não é "oportunidade prevista", é captação de paciente frio).
export type ReengagementPatient = {
  patient_id: string;
  patient_name: string;
  patient_phone: string | null;
  gender: Gender | null;
  consent_whatsapp: boolean;
  last_treated_at: string | null;
};

export type ReengagementResponse = {
  never_treated: ReengagementPatient[];
  never_treated_total_count: number;
  inactive: ReengagementPatient[];
  inactive_total_count: number;
  inactive_days_threshold: number;
  page: number;
  page_size: number;
};

export const retentionApi = {
  getCards: (referenceDate?: string) => {
    const qs = new URLSearchParams({ view: "cards" });
    if (referenceDate) qs.set("reference_date", referenceDate);
    return api.get<PatientRetentionCard[]>(`/retention/opportunities?${qs.toString()}`);
  },
  updateOpportunity: (id: string, payload: ReturnOpportunityUpdate) =>
    api.patch<void>(`/retention/${id}`, payload),
  getReengagement: (inactiveDays: number, page: number, pageSize: number) => {
    const qs = new URLSearchParams({
      inactive_days: String(inactiveDays),
      page: String(page),
      page_size: String(pageSize),
    });
    return api.get<ReengagementResponse>(`/retention/reengagement?${qs.toString()}`);
  },
};
