import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { Comment } from "@/types";

export function useComments(assetId: string | undefined) {
  return useQuery({
    queryKey: ["comments", assetId],
    queryFn: async () => {
      const res = await apiClient.get<Comment[]>(`/assets/${assetId}/comments`);
      return res.data;
    },
    enabled: !!assetId,
  });
}

export function useAddComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      assetId,
      content,
      parentId,
    }: {
      assetId: string;
      content: string;
      parentId?: string | null;
    }) => {
      const res = await apiClient.post<Comment>(`/assets/${assetId}/comments`, {
        content,
        parent_id: parentId ?? null,
      });
      return res.data;
    },
    onSuccess: (_, { assetId }) => {
      queryClient.invalidateQueries({ queryKey: ["comments", assetId] });
    },
  });
}
