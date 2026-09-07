import { api } from "@/lib/http/client";

export type PhotoType = "BEFORE" | "AFTER" | "GENERAL";

export type PatientPhoto = {
  id: string;
  patient_id: string;
  procedure_id: string | null;
  procedure_name: string | null;
  photo_type: PhotoType;
  image_url: string;
  caption: string | null;
  captured_at: string;
  authorized_social_media: boolean;
  created_at: string;
};

export type PatientPhotoCreateInput = {
  photo_type: PhotoType;
  procedure_id?: string | null;
  image_url: string;
  caption?: string | null;
  captured_at?: string | null;
  authorized_social_media?: boolean;
};

export type PatientPhotoUpdateInput = {
  photo_type?: PhotoType;
  procedure_id?: string | null;
  caption?: string | null;
  captured_at?: string | null;
  authorized_social_media?: boolean;
};

export const photosApi = {
  list(
    patientId: string,
    params?: { procedure_id?: string; photo_type?: PhotoType }
  ): Promise<PatientPhoto[]> {
    const searchParams = new URLSearchParams();
    if (params?.procedure_id) searchParams.set("procedure_id", params.procedure_id);
    if (params?.photo_type) searchParams.set("photo_type", params.photo_type);
    const qs = searchParams.toString();
    return api.get<PatientPhoto[]>(
      `/patients/${patientId}/photos${qs ? `?${qs}` : ""}`
    );
  },

  get(patientId: string, photoId: string): Promise<PatientPhoto> {
    return api.get<PatientPhoto>(`/patients/${patientId}/photos/${photoId}`);
  },

  create(patientId: string, input: PatientPhotoCreateInput): Promise<PatientPhoto> {
    return api.post<PatientPhoto>(`/patients/${patientId}/photos`, input);
  },

  update(
    patientId: string,
    photoId: string,
    input: PatientPhotoUpdateInput
  ): Promise<PatientPhoto> {
    return api.patch<PatientPhoto>(
      `/patients/${patientId}/photos/${photoId}`,
      input
    );
  },

  delete(patientId: string, photoId: string): Promise<void> {
    return api.del<void>(`/patients/${patientId}/photos/${photoId}`);
  },
};
