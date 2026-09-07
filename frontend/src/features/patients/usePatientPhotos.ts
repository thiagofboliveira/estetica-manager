import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/query/keys";
import {
  photosApi,
  type PatientPhotoCreateInput,
  type PatientPhotoUpdateInput,
  type PhotoType,
} from "./photosApi";

export function usePatientPhotos(
  patientId: string,
  params?: { procedure_id?: string; photo_type?: PhotoType }
) {
  return useQuery({
    queryKey: [...qk.patientPhotos(patientId), params] as const,
    queryFn: () => photosApi.list(patientId, params),
    enabled: Boolean(patientId),
  });
}

export function useCreatePatientPhoto(patientId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: PatientPhotoCreateInput) =>
      photosApi.create(patientId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patientPhotos(patientId) });
    },
  });
}

export function useUpdatePatientPhoto(patientId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      photoId,
      input,
    }: {
      photoId: string;
      input: PatientPhotoUpdateInput;
    }) => photosApi.update(patientId, photoId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patientPhotos(patientId) });
    },
  });
}

export function useDeletePatientPhoto(patientId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (photoId: string) => photosApi.delete(patientId, photoId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.patientPhotos(patientId) });
    },
  });
}
