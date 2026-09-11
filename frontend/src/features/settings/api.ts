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
  monthly_revenue_goal?: string | null;
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
  monthly_revenue_goal?: string | null;
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
  payment_method?: PaymentMethod;
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

export type WeeklySummary = {
  professional_name: string;
  period_start: string;
  period_end: string;
  gross_revenue: string;
  net_profit: string;
  sales_count: number;
  pending_opportunities_count: number;
  weekly_summary_enabled: boolean;
  whatsapp_message: string;
  whatsapp_url?: string | null;
  unsubscribe_url: string;
};

export const weeklySummaryApi = {
  get: (useCurrentWeek = false) =>
    api.get<WeeklySummary>(`/weekly-summary?use_current_week=${useCurrentWeek}`),
  updateSettings: (enabled: boolean) =>
    api.patch<{ weekly_summary_enabled: boolean }>("/weekly-summary/settings", {
      weekly_summary_enabled: enabled,
    }),
};

