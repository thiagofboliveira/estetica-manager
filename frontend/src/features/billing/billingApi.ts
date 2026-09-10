import { api } from "@/lib/http/client";

export type BillingCycle = "MONTHLY" | "QUARTERLY" | "YEARLY";

export type PlanCycle = {
  cycle: BillingCycle;
  months: number;
  monthly_equivalent: string;
  total_amount: string;
  savings_percentage: string;
  badge: string | null;
  is_featured: boolean;
};

export type Plan = {
  id: string;
  name: string;
  description: string;
  trial_days: number;
  is_launch_promo: boolean;
  promo_headline: string;
  promo_badge: string;
  features: string[];
  cycles: PlanCycle[];
};

export type CouponValidation = {
  is_valid: boolean;
  code: string;
  discount_type: string | null;
  original_amount: string;
  discount_amount: string;
  final_amount: string;
  savings_percentage: string;
  message: string | null;
};

export type CheckoutPayload = {
  cycle: BillingCycle;
  coupon_code?: string;
  billing_type: "PIX" | "CREDIT_CARD" | "BOLETO" | "UNDEFINED";
  document?: string;
  phone?: string;
};

export type CheckoutResponse = {
  subscription_id: string;
  status: string;
  amount: string;
  cycle: BillingCycle;
  invoice_url: string | null;
  pix_qrcode_payload: string | null;
  first_due_date: string;
  is_trial_included: boolean;
};

export type SubscriptionStatus = {
  status: string;
  plan_id: string;
  cycle: BillingCycle;
  amount: string;
  trial_started_at: string;
  trial_ends_at: string;
  days_left_in_trial: number;
  is_trial_active: boolean;
  is_subscription_active: boolean;
  current_period_start?: string | null;
  current_period_end?: string | null;
  invoice_url?: string | null;
};

export async function getPlans(): Promise<Plan[]> {
  return api.get<Plan[]>("/billing/plans");
}

export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return api.get<SubscriptionStatus>("/billing/status");
}

export async function validateCoupon(code: string, cycle: BillingCycle): Promise<CouponValidation> {
  return api.post<CouponValidation>("/billing/coupons/validate", {
    code: code.trim().toUpperCase(),
    cycle,
  });
}

export async function createCheckout(payload: CheckoutPayload): Promise<CheckoutResponse> {
  return api.post<CheckoutResponse>("/billing/checkout", payload);
}
