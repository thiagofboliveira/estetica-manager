import { api } from "@/lib/http/client";

export type ReturnOpportunityStatus =
  | "OPEN"
  | "CONTACTED"
  | "BOOKED"
  | "DECLINED"
  | "NO_RESPONSE"
  | "DISMISSED"
  | "CLOSED";

export type ContactChannel = "WHATSAPP" | "PHONE" | "IN_PERSON" | "OTHER";

export type OpportunityLine = {
  id: string;
  procedure: string;
  due_date: string;
  timing: "UPCOMING" | "DUE" | "OVERDUE";
  status: ReturnOpportunityStatus;
  // Valor potencial chega como string (MoneyOut) — nunca number, ver
  // frontend/BACKLOG.md "Valores monetários chegam como string".
  potential_value: string;
};

export type PatientRetention = {
  patient_id: string;
  patient_name: string;
  patient_phone: string | null;
  can_contact: boolean;
  cannot_contact_reason: string | null;
  total_potential_value: string;
  opportunities: OpportunityLine[];
};

export type RetentionUpdateInput = {
  status: ReturnOpportunityStatus;
  contact_channel?: ContactChannel;
};

export const retentionApi = {
  // Sem query params — o backend já agrupa por paciente, aplica
  // supressão de 14d e ordena por valor potencial decrescente (F-015a).
  list: () => api.get<PatientRetention[]>("/retention/opportunities"),
  updateOpportunity: (opportunityId: string, payload: RetentionUpdateInput) =>
    api.patch(`/retention/opportunities/${opportunityId}`, payload),
};
