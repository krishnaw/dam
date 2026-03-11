import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { Workflow } from "@/types";

export function useAssetWorkflow(assetId: string | undefined) {
  return useQuery({
    queryKey: ["workflow", assetId],
    queryFn: async () => {
      const res = await apiClient.get<Workflow>("/workflows", {
        params: { asset_id: assetId },
      });
      return res.data;
    },
    enabled: !!assetId,
  });
}

export function useSubmitReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ assetId, comment }: { assetId: string; comment?: string }) => {
      const res = await apiClient.post<Workflow>(`/workflows`, {
        asset_id: assetId,
        comment,
      });
      return res.data;
    },
    onSuccess: (_, { assetId }) => {
      queryClient.invalidateQueries({ queryKey: ["workflow", assetId] });
    },
  });
}

export function useReviewAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      workflowId,
      stepId,
      action,
      comment,
    }: {
      workflowId: string;
      stepId: string;
      action: "approve" | "reject";
      comment?: string;
    }) => {
      const res = await apiClient.put<Workflow>(
        `/workflows/${workflowId}/steps/${stepId}`,
        { action, comment }
      );
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["workflow", data.assetId] });
    },
  });
}
