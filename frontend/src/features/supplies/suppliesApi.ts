import { api } from "@/lib/http/client";

export type SupplyCategory =
  | "INJECTABLE"
  | "FILLER"
  | "THREAD"
  | "ANESTHETIC"
  | "CONSUMABLE"
  | "OTHER";

export type MovementType = "ENTRY" | "EXIT" | "ADJUSTMENT" | "LOSS";

export interface Supply {
  id: string;
  name: string;
  category: SupplyCategory;
  brand?: string | null;
  unit_measure: string;
  current_stock: number;
  min_stock_alert?: number | null;
  cost_price?: string | null;
  notes?: string | null;
  is_active: boolean;
  is_low_stock: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplyMovement {
  id: string;
  supply_id: string;
  movement_type: MovementType;
  quantity: number;
  unit_price?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface SupplyCreatePayload {
  name: string;
  category: SupplyCategory;
  brand?: string;
  unit_measure?: string;
  current_stock?: number;
  min_stock_alert?: number;
  cost_price?: number;
  notes?: string;
}

export interface SupplyUpdatePayload {
  name?: string;
  category?: SupplyCategory;
  brand?: string;
  unit_measure?: string;
  current_stock?: number;
  min_stock_alert?: number;
  cost_price?: number;
  notes?: string;
  is_active?: boolean;
}

export interface SupplyMovementPayload {
  movement_type: MovementType;
  quantity: number;
  unit_price?: number;
  notes?: string;
}

export async function getSupplies(params?: {
  category?: string;
  search?: string;
  low_stock_only?: boolean;
}): Promise<Supply[]> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.search) query.set("search", params.search);
  if (params?.low_stock_only) query.set("low_stock_only", "true");

  const qs = query.toString();
  return api.get<Supply[]>(`/v1/supplies${qs ? `?${qs}` : ""}`);
}

export async function createSupply(payload: SupplyCreatePayload): Promise<Supply> {
  return api.post<Supply>("/v1/supplies", payload);
}

export async function updateSupply(
  supplyId: string,
  payload: SupplyUpdatePayload
): Promise<Supply> {
  return api.patch<Supply>(`/v1/supplies/${supplyId}`, payload);
}

export async function deleteSupply(supplyId: string): Promise<void> {
  return api.del<void>(`/v1/supplies/${supplyId}`);
}

export async function recordSupplyMovement(
  supplyId: string,
  payload: SupplyMovementPayload
): Promise<SupplyMovement> {
  return api.post<SupplyMovement>(`/v1/supplies/${supplyId}/movements`, payload);
}

export async function getSupplyMovements(supplyId: string): Promise<SupplyMovement[]> {
  return api.get<SupplyMovement[]>(`/v1/supplies/${supplyId}/movements`);
}

export async function getRecentMovements(): Promise<SupplyMovement[]> {
  return api.get<SupplyMovement[]>("/v1/supplies/movements/recent");
}
