import { api } from "@/lib/http/client";

export type ProcedureType = "SERVICE" | "PRODUCT";

export type Procedure = {
  id: string;
  name: string;
  type: ProcedureType;
  price: string;
  estimated_cost: string;
  return_interval_days: number | null;
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
};

export type ProcedureUpdateInput = Partial<
  Pick<ProcedureCreateInput, "name" | "price" | "estimated_cost" | "return_interval_days">
> & {
  is_active?: boolean;
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
};
