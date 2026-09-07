import { api } from "@/lib/http/client";

export type QuestionFieldType = "yes_no" | "text" | "long_text" | "select";

export interface AnamnesisQuestion {
  id: string;
  template_id: string;
  title: string;
  description: string | null;
  field_type: QuestionFieldType;
  options: string[] | null;
  is_required: boolean;
  is_risk_alert: boolean;
  risk_trigger_value: string | null;
  order_index: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnamnesisTemplate {
  id: string;
  title: string;
  description: string | null;
  is_default: boolean;
  is_active: boolean;
  auto_request_on_booking: boolean;
  created_at: string;
  updated_at: string;
  questions: AnamnesisQuestion[];
}

export interface AnamnesisSubmission {
  id: string;
  template_id: string;
  patient_id: string | null;
  booking_id: string | null;
  public_token: string;
  patient_name: string;
  patient_phone: string | null;
  answers: Record<string, any>;
  has_risk_alerts: boolean;
  risk_alerts_summary: string[];
  signature_name: string | null;
  submitted_at: string | null;
  created_at: string;
}

export interface PublicAnamnesisForm {
  token: string;
  clinic_name: string | null;
  professional_name: string;
  professional_slug: string | null;
  template_title: string;
  template_description: string | null;
  patient_name: string | null;
  patient_phone: string | null;
  is_submitted: boolean;
  submitted_at: string | null;
  questions: AnamnesisQuestion[];
}

export interface CreateQuestionPayload {
  title: string;
  description?: string | null;
  field_type: QuestionFieldType;
  options?: string[] | null;
  is_required: boolean;
  is_risk_alert: boolean;
  risk_trigger_value?: string | null;
  order_index?: number;
}

export interface UpdateQuestionPayload {
  title?: string;
  description?: string | null;
  field_type?: QuestionFieldType;
  options?: string[] | null;
  is_required?: boolean;
  is_risk_alert?: boolean;
  risk_trigger_value?: string | null;
  order_index?: number;
  is_active?: boolean;
}

export interface UpdateTemplatePayload {
  title?: string;
  description?: string | null;
  auto_request_on_booking?: boolean;
}

export interface PublicSubmitAnamnesisPayload {
  patient_name: string;
  patient_phone?: string | null;
  answers: Record<string, any>;
  signature_name?: string | null;
}

export const anamnesisApi = {
  getTemplate: () => api.get<AnamnesisTemplate>("/anamnesis/template"),
  updateTemplate: (payload: UpdateTemplatePayload) =>
    api.put<AnamnesisTemplate>("/anamnesis/template", payload),
  createQuestion: (payload: CreateQuestionPayload) =>
    api.post<AnamnesisQuestion>("/anamnesis/questions", payload),
  updateQuestion: (id: string, payload: UpdateQuestionPayload) =>
    api.put<AnamnesisQuestion>(`/anamnesis/questions/${id}`, payload),
  deleteQuestion: (id: string) => api.del<void>(`/anamnesis/questions/${id}`),
  reorderQuestions: (questions: { question_id: string; order_index: number }[]) =>
    api.post<AnamnesisQuestion[]>("/anamnesis/questions/reorder", { questions }),
  listSubmissions: () => api.get<AnamnesisSubmission[]>("/anamnesis/submissions"),
  getPatientSubmissions: (patientId: string) =>
    api.get<AnamnesisSubmission[]>(`/anamnesis/patient/${patientId}`),
  generateSubmissionToken: (params?: {
    patient_id?: string;
    booking_id?: string;
    patient_name?: string;
    patient_phone?: string;
  }) => api.post<AnamnesisSubmission>("/anamnesis/submissions/token", params),

  // Public APIs
  getPublicForm: (token: string) =>
    api.get<PublicAnamnesisForm>(`/public/anamnesis/${token}`),
  submitPublicForm: (token: string, payload: PublicSubmitAnamnesisPayload) =>
    api.post<AnamnesisSubmission>(`/public/anamnesis/${token}`, payload),
  getByBooking: (bookingId: string, token: string) =>
    api.get<AnamnesisSubmission>(`/public/anamnesis/by-booking/${bookingId}?token=${token}`),
};
