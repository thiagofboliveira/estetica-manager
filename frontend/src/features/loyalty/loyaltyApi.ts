import { api } from "@/lib/http/client";

export type LoyaltyTransaction = {
  id: string;
  patient_id: string;
  sale_id: string | null;
  transaction_type: "EARNED" | "BONUS" | "REDEEMED" | "ADJUSTMENT";
  points: number;
  balance_after: number;
  description: string;
  created_at: string | null;
};

export type LoyaltyPatientOut = {
  patient_id: string;
  patient_name: string;
  loyalty_points: number;
  vip_tier: "BRONZE" | "SILVER" | "GOLD" | "DIAMOND";
  vip_badge: string;
  monetary_value: number;
  referral_code: string;
  referred_by_name: string | null;
  transactions: LoyaltyTransaction[];
};

export type LoyaltyAdjustRequest = {
  points: number;
  description: string;
  transaction_type?: "ADJUSTMENT" | "REDEEMED" | "BONUS";
};

export type ReferralFriend = {
  patient_id: string;
  patient_name: string;
  joined_at: string;
  has_completed_sale: boolean;
};

export type ReferralInfoOut = {
  referral_code: string;
  whatsapp_share_text: string;
  whatsapp_share_url: string;
  reward_points_per_friend: number;
  total_friends_referred: number;
  friends_converted_count: number;
  total_points_earned_from_referrals: number;
  friends: ReferralFriend[];
};

export type LoyaltyOverviewOut = {
  total_active_points: number;
  total_value_in_currency: number;
  tier_counts: Record<string, number>;
  total_referrals_count: number;
  total_converted_referrals: number;
};

export type PublicLoyaltyReward = {
  points_cost: number;
  title: string;
  description: string;
  discount_value: number | string | null;
};

export type PublicVipCardOut = {
  patient_first_name: string;
  patient_full_name: string;
  clinic_name: string;
  vip_tier: "BRONZE" | "SILVER" | "GOLD" | "DIAMOND" | string;
  vip_badge: string;
  loyalty_points: number;
  monetary_credit_value: number | string;
  next_tier: string | null;
  points_to_next_tier: number;
  next_tier_threshold: number | null;
  referral_code: string;
  referral_whatsapp_message: string;
  public_booking_slug: string | null;
  catalog_rewards: PublicLoyaltyReward[];
};

export type SendVipEmailResponse = {
  success: boolean;
  message: string;
  recipient_email: string;
};

export const loyaltyApi = {
  getPatientLoyalty: (patientId: string): Promise<LoyaltyPatientOut> =>
    api.get<LoyaltyPatientOut>(`/loyalty/patients/${patientId}`),

  adjustPoints: (patientId: string, payload: LoyaltyAdjustRequest): Promise<LoyaltyTransaction> =>
    api.post<LoyaltyTransaction>(`/loyalty/patients/${patientId}/adjust`, payload),

  getReferralInfo: (patientId: string): Promise<ReferralInfoOut> =>
    api.get<ReferralInfoOut>(`/loyalty/patients/${patientId}/referral`),

  getOverview: (): Promise<LoyaltyOverviewOut> =>
    api.get<LoyaltyOverviewOut>("/loyalty/overview"),

  getPublicVipCard: (code: string): Promise<PublicVipCardOut> =>
    api.get<PublicVipCardOut>(`/loyalty/public-card/${encodeURIComponent(code)}`, { public: true }),

  sendVipCardEmail: (patientId: string): Promise<SendVipEmailResponse> =>
    api.post<SendVipEmailResponse>(`/loyalty/patients/${patientId}/send-card-email`, {}),
};


