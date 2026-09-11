import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCampaignTemplates,
  createCampaignTemplate,
  updateCampaignTemplate,
  deleteCampaignTemplate,
  type CampaignTemplateCreate,
  type CampaignTemplateUpdate,
} from "./campaignsApi";

export const CAMPAIGN_TEMPLATES_KEY = ["campaign-templates"];

export function useCampaignTemplates(category?: string) {
  return useQuery({
    queryKey: [...CAMPAIGN_TEMPLATES_KEY, category || "all"],
    queryFn: () => getCampaignTemplates(category),
  });
}

export function useCreateCampaignTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignTemplateCreate) => createCampaignTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CAMPAIGN_TEMPLATES_KEY });
    },
  });
}

export function useUpdateCampaignTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CampaignTemplateUpdate }) =>
      updateCampaignTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CAMPAIGN_TEMPLATES_KEY });
    },
  });
}

export function useDeleteCampaignTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteCampaignTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CAMPAIGN_TEMPLATES_KEY });
    },
  });
}
