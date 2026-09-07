import { api } from "@/lib/http/client";

export interface OpenVial {
  id: string;
  medication_name: string;
  lot_number?: string | null;
  total_units: number;
  used_units: number;
  remaining_units: number;
  unit_measure: string;
  cost_price?: string | null;
  cost_per_unit?: string | null;
  estimated_loss_risk?: string | null;
  opened_at: string;
  expires_at: string;
  days_remaining: number;
  is_expired: boolean;
  status: "active" | "finished" | "discarded";
  procedure_id?: string | null;
  procedure_name?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface OpenVialCreatePayload {
  medication_name: string;
  lot_number?: string;
  total_units: number;
  unit_measure?: string;
  cost_price?: number;
  opened_at?: string;
  expires_at: string;
  procedure_id?: string;
  notes?: string;
}

export interface OpenVialConsumePayload {
  units: number;
  notes?: string;
}

export async function getActiveVials(): Promise<OpenVial[]> {
  return api.get<OpenVial[]>("/v1/vials");
}

export async function getAllVials(): Promise<OpenVial[]> {
  return api.get<OpenVial[]>("/v1/vials?include_all=true");
}

export async function createVial(payload: OpenVialCreatePayload): Promise<OpenVial> {
  return api.post<OpenVial>("/v1/vials", payload);
}

export async function consumeVialUnits(vialId: string, payload: OpenVialConsumePayload): Promise<OpenVial> {
  return api.post<OpenVial>(`/v1/vials/${vialId}/consume`, payload);
}

export async function finishVial(vialId: string): Promise<OpenVial> {
  return api.post<OpenVial>(`/v1/vials/${vialId}/finish`, {});
}

export async function deleteVial(vialId: string): Promise<void> {
  return api.del<void>(`/v1/vials/${vialId}`);
}
