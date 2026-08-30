import { api } from "@/lib/http/client";

export type PaymentMethod = "PIX" | "DEBIT" | "CREDIT" | "CASH" | "TRANSFER";
export type SplitBase = "GROSS" | "NET_OF_FEE";
export type FeePayer = "PROFESSIONAL" | "CLINIC";

export type FinancialSettings = {
  id: string;
  split_clinic_percentage: string;
  split_base: SplitBase;
  fee_payer: FeePayer;
  pix_fee_percentage: string;
  debit_card_fee_percentage: string;
  default_payment_method: PaymentMethod;
  created_at: string;
  updated_at: string;
};

export type FinancialSettingsUpdate = {
  split_clinic_percentage?: string | null;
  split_base?: SplitBase | null;
  fee_payer?: FeePayer | null;
  pix_fee_percentage?: string | null;
  debit_card_fee_percentage?: string | null;
  default_payment_method?: PaymentMethod | null;
};

export type PaymentFeeRule = {
  id: string;
  payment_method: PaymentMethod;
  installments_min: number;
  installments_max: number;
  fee_percentage: string;
  fixed_fee: string;
  created_at: string;
  updated_at: string;
};

export type PaymentFeeRuleCreateInput = {
  payment_method: PaymentMethod;
  installments_min: number;
  installments_max: number;
  fee_percentage: string;
  fixed_fee?: string;
};

export type PaymentFeeRuleUpdateInput = {
  installments_min?: number;
  installments_max?: number;
  fee_percentage?: string;
  fixed_fee?: string;
};

export const financialSettingsApi = {
  get: () => api.get<FinancialSettings>("/financial-settings"),
  update: (payload: FinancialSettingsUpdate) =>
    api.patch<FinancialSettings>("/financial-settings", payload),
};

export const paymentFeeRulesApi = {
  list: () => api.get<PaymentFeeRule[]>("/payment-fee-rules"),
  create: (payload: PaymentFeeRuleCreateInput) =>
    api.post<PaymentFeeRule>("/payment-fee-rules", payload),
  update: (id: string, payload: PaymentFeeRuleUpdateInput) =>
    api.patch<PaymentFeeRule>(`/payment-fee-rules/${id}`, payload),
  delete: (id: string) => api.del<void>(`/payment-fee-rules/${id}`),
};
