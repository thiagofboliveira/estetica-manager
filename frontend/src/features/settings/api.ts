import { api } from "@/lib/http/client";

export type SplitBase = "GROSS" | "NET_OF_FEE";
export type FeePayer = "PROFESSIONAL" | "CLINIC" | "SPLIT_PRO_RATA";
export type DefaultPaymentMethod = "PIX" | "DEBIT" | "CREDIT" | "CASH" | "TRANSFER";

export type FinancialSettings = {
  id: string;
  // Percentuais chegam como MoneyOut (string, 2 casas) — não RateOut.
  split_clinic_percentage: string;
  split_base: SplitBase;
  fee_payer: FeePayer;
  pix_fee_percentage: string;
  debit_card_fee_percentage: string;
  default_payment_method: DefaultPaymentMethod;
  created_at: string;
  updated_at: string;
};

export type FinancialSettingsUpdateInput = Partial<
  Pick<
    FinancialSettings,
    | "split_clinic_percentage"
    | "split_base"
    | "fee_payer"
    | "pix_fee_percentage"
    | "debit_card_fee_percentage"
    | "default_payment_method"
  >
>;

export const financialSettingsApi = {
  // GET sempre retorna dado real: backend cria o singleton com
  // defaults de mercado no primeiro acesso (get_or_create_default).
  get: () => api.get<FinancialSettings>("/financial-settings"),
  update: (payload: FinancialSettingsUpdateInput) =>
    api.patch<FinancialSettings>("/financial-settings", payload),
};
