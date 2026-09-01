import { api } from "@/lib/http/client";

export type ProcedureType = "SERVICE" | "PRODUCT";
export type Modality = "IN_PERSON" | "REMOTE";

export type Procedure = {
  id: string;
  name: string;
  type: ProcedureType;
  price: string;
  estimated_cost: string;
  return_interval_days: number | null;
  default_modality: Modality;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProcedureCreateInput = {
  name: string;
  type: ProcedureType;
  price: string;
  estimated_cost: string;
  return_interval_days?: number | null;
  default_modality?: Modality;
};

export type ProcedureUpdateInput = Partial<
  Pick<
    ProcedureCreateInput,
    "name" | "type" | "price" | "estimated_cost" | "return_interval_days" | "default_modality"
  >
> & {
  is_active?: boolean;
};

export type ProcedureTemplate = {
  template_id: string;
  name: string;
  type: ProcedureType;
  suggested_price: string;
  suggested_cost: string;
  suggested_return_interval_days: number | null;
  category: string;
};

export const proceduresApi = {
  list: (params: { limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.offset) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return api.get<Procedure[]>(`/procedures${suffix}`);
  },
  get: (id: string) => api.get<Procedure>(`/procedures/${id}`),
  create: (payload: ProcedureCreateInput) => api.post<Procedure>("/procedures", payload),
  update: (id: string, payload: ProcedureUpdateInput) =>
    api.patch<Procedure>(`/procedures/${id}`, payload),
  deactivate: (id: string) => api.del<void>(`/procedures/${id}`),
  getTemplates: () => api.get<ProcedureTemplate[]>("/procedures/templates"),
  createFromTemplate: (templateId: string, payload: ProcedureCreateInput) => 
    api.post<Procedure>("/procedures/from-template", { template_id: templateId, ...payload }),
};
