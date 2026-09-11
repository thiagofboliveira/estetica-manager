import { api } from "@/lib/http/client";

export interface PatientBirthday {
  patient_id: string;
  patient_name: string;
  patient_phone?: string | null;
  birth_date: string;
  day: number;
  month: number;
  days_until: number;
  is_today: boolean;
  formatted_date: string;
  whatsapp_url?: string | null;
}

export async function getBirthdays(month?: number): Promise<PatientBirthday[]> {
  const query = month ? `?month=${month}` : "";
  return api.get<PatientBirthday[]>(`/patients/birthdays${query}`);
}

export interface CampaignTemplate {
  id: string;
  professional_id?: string | null;
  clinic_id?: string | null;
  title: string;
  category: string;
  description?: string | null;
  message_text: string;
  is_system: boolean;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CampaignTemplateCreate {
  title: string;
  category: string;
  description?: string | null;
  message_text: string;
}

export interface CampaignTemplateUpdate {
  title?: string;
  category?: string;
  description?: string | null;
  message_text?: string;
  is_active?: boolean;
}

export async function getCampaignTemplates(category?: string): Promise<CampaignTemplate[]> {
  const query = category && category !== "all" ? `?category=${encodeURIComponent(category)}` : "";
  return api.get<CampaignTemplate[]>(`/campaigns/templates${query}`);
}

export async function createCampaignTemplate(data: CampaignTemplateCreate): Promise<CampaignTemplate> {
  return api.post<CampaignTemplate>("/campaigns/templates", data);
}

export async function updateCampaignTemplate(id: string, data: CampaignTemplateUpdate): Promise<CampaignTemplate> {
  return api.put<CampaignTemplate>(`/campaigns/templates/${id}`, data);
}

export async function deleteCampaignTemplate(id: string): Promise<void> {
  return api.del<void>(`/campaigns/templates/${id}`);
}

