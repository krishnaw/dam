import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { apiClient } from "./client";
import type { Collection, PaginatedResponse } from "@/types";

export function useCollections() {
  return useQuery({
    queryKey: ["collections"],
    queryFn: async () => {
      const res =
        await apiClient.get<PaginatedResponse<Collection>>("/collections");
      return res.data;
    },
  });
}

export function useCollection(id: string | undefined) {
  return useQuery({
    queryKey: ["collection", id],
    queryFn: async () => {
      const res = await apiClient.get<Collection>(`/collections/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; description?: string }) => {
      const res = await apiClient.post<Collection>("/collections", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useAddToCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      collectionId,
      assetIds,
    }: {
      collectionId: string;
      assetIds: string[];
    }) => {
      await apiClient.post(`/collections/${collectionId}/assets`, {
        asset_ids: assetIds,
      });
    },
    onSuccess: (_, { collectionId }) => {
      queryClient.invalidateQueries({
        queryKey: ["collection", collectionId],
      });
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}
