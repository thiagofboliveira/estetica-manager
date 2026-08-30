import { api } from "@/lib/http/client";

export type SaleType = "SINGLE" | "PACKAGE";
export type PaymentMethod = "PIX" | "DEBIT" | "CREDIT" | "CASH" | "TRANSFER";
export type SaleStatus = "ACTIVE" | "REFUNDED";
export type SplitBase = "GROSS" | "NET_OF_FEE";
export type FeePayer = "PROFESSIONAL" | "CLINIC" | "SPLIT_PRO_RATA";

export type SaleItemCreate = {
  procedure_id: string;
  quantity: number;
};

export type SaleCreateInput = {
  patient_id: string;
  type: SaleType;
  items: SaleItemCreate[];
  discount_amount: string;
  payment_method: PaymentMethod;
  installments: number;
  notes?: string | null;
  booking_id?: string | null;
};

export type SaleItemOut = {
  id: string;
  procedure_id: string;
  quantity: number;
  unit_price: string;
  unit_cost_estimated: string;
  return_interval_applied: number | null;
  discount_allocated: string;
};

export type SessionOut = {
  id: string;
  sale_item_id: string;
  sequence_number: number;
  scheduled_at: string | null;
  status: string;
  modality: string;
};

export type Sale = {
  id: string;
  patient_id: string;
  type: SaleType;
  sold_at: string;
  status: SaleStatus;

  payment_method: PaymentMethod;
  installments: number;

  items_total: string;
  discount_amount: string;
  gross_amount: string;

  split_applied: string;
  split_base_applied: SplitBase;
  fee_payer_applied: FeePayer;
  fee_applied: string;
  fee_amount_applied: string;

  cost_provisioned: string;
  cost_realized: string;

  net_profit: string;
  margin: string | null;
  expected_receipt_date: string | null;

  notes: string | null;
  created_at: string;
  updated_at: string;

  items: SaleItemOut[];
  sessions: SessionOut[];
};

export const salesApi = {
  create: (payload: SaleCreateInput, idempotencyKey: string) =>
    api.post<Sale>("/sales", payload, { headers: { "Idempotency-Key": idempotencyKey } }),
  get: (id: string) => api.get<Sale>(`/sales/${id}`),
};
