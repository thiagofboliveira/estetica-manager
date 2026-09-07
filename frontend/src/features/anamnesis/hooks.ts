import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  anamnesisApi,
  type CreateQuestionPayload,
  type PublicSubmitAnamnesisPayload,
  type UpdateQuestionPayload,
  type UpdateTemplatePayload,
} from "./api";

const ANAMNESIS_KEYS = {
  template: ["anamnesis", "template"] as const,
  submissions: ["anamnesis", "submissions"] as const,
  patient: (id: string) => ["anamnesis", "patient", id] as const,
  publicForm: (token: string) => ["anamnesis", "publicForm", token] as const,
  byBooking: (bookingId: string) => ["anamnesis", "byBooking", bookingId] as const,
};

export function useAnamnesisTemplate() {
  return useQuery({
    queryKey: ANAMNESIS_KEYS.template,
    queryFn: () => anamnesisApi.getTemplate(),
  });
}

export function useUpdateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateTemplatePayload) => anamnesisApi.updateTemplate(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ANAMNESIS_KEYS.template });
    },
  });
}

export function useCreateQuestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateQuestionPayload) => anamnesisApi.createQuestion(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ANAMNESIS_KEYS.template });
    },
  });
}

export function useUpdateQuestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateQuestionPayload }) =>
      anamnesisApi.updateQuestion(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ANAMNESIS_KEYS.template });
    },
  });
}

export function useDeleteQuestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => anamnesisApi.deleteQuestion(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ANAMNESIS_KEYS.template });
    },
  });
}

export function useReorderQuestions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (questions: { question_id: string; order_index: number }[]) =>
      anamnesisApi.reorderQuestions(questions),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ANAMNESIS_KEYS.template });
    },
  });
}

export function useAnamnesisSubmissions() {
  return useQuery({
    queryKey: ANAMNESIS_KEYS.submissions,
    queryFn: () => anamnesisApi.listSubmissions(),
  });
}

export function usePatientAnamnesis(patientId: string | undefined) {
  return useQuery({
    queryKey: ANAMNESIS_KEYS.patient(patientId ?? ""),
    queryFn: () => (patientId ? anamnesisApi.getPatientSubmissions(patientId) : Promise.resolve([])),
    enabled: Boolean(patientId),
  });
}

export function useGenerateSubmissionToken() {
  return useMutation({
    mutationFn: (params?: {
      patient_id?: string;
      booking_id?: string;
      patient_name?: string;
      patient_phone?: string;
    }) => anamnesisApi.generateSubmissionToken(params),
  });
}

export function usePublicAnamnesisForm(token: string | undefined) {
  return useQuery({
    queryKey: ANAMNESIS_KEYS.publicForm(token ?? ""),
    queryFn: () => (token ? anamnesisApi.getPublicForm(token) : Promise.reject("Token obrigatório")),
    enabled: Boolean(token),
  });
}

export function useSubmitPublicAnamnesis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ token, payload }: { token: string; payload: PublicSubmitAnamnesisPayload }) =>
      anamnesisApi.submitPublicForm(token, payload),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ANAMNESIS_KEYS.publicForm(variables.token) });
    },
  });
}

export function useBookingAnamnesis(bookingId: string | undefined, token: string | undefined) {
  return useQuery({
    queryKey: ANAMNESIS_KEYS.byBooking(bookingId ?? ""),
    queryFn: () =>
      bookingId && token ? anamnesisApi.getByBooking(bookingId, token) : Promise.reject("IDs obrigatórios"),
    enabled: Boolean(bookingId && token),
  });
}
