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
