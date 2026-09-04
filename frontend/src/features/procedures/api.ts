import { api } from "@/lib/http/client";

export type ProcedureType = "SERVICE" | "PRODUCT";
export type Modality = "IN_PERSON" | "REMOTE";
export type SessionPlan = "SINGLE" | "MULTIPLE";

export type Procedure = {
  id: string;
  name: string;
  type: ProcedureType;
  price: string;
  estimated_cost: string;
  return_interval_days: number | null;
  default_modality: Modality;
  is_active: boolean;
  is_invasive: boolean;
  session_plan: SessionPlan;
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
  is_invasive?: boolean;
  session_plan?: SessionPlan;
};

export type ProcedureUpdateInput = Partial<
  Pick<
    ProcedureCreateInput,
    | "name"
    | "type"
    | "price"
    | "estimated_cost"
    | "return_interval_days"
    | "default_modality"
    | "is_invasive"
    | "session_plan"
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

export type ProcedureList = {
  items: Procedure[];
  total_count: number;
  page: number;
  page_size: number;
};

export type ProcedureListParams = {
  is_invasive?: boolean;
  session_plan?: SessionPlan;
  page?: number;
  page_size?: number;
};

export const proceduresApi = {
  list: (params: ProcedureListParams = {}) => {
    const qs = new URLSearchParams();
    if (params.is_invasive != null) qs.set("is_invasive", String(params.is_invasive));
    if (params.session_plan) qs.set("session_plan", params.session_plan);
    if (params.page) qs.set("page", String(params.page));
    if (params.page_size) qs.set("page_size", String(params.page_size));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return api.get<ProcedureList>(`/procedures${suffix}`);
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
