import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery,
} from "@tanstack/react-query";
import { apiClient } from "./client";
import type { Asset, PaginatedResponse } from "@/types";

interface AssetFilters {
  mime_type?: string;
  tag?: string;
  collection_id?: string;
  sort_by?: string;
  order?: "asc" | "desc";
}

export function useAssets(filters: AssetFilters = {}) {
  return useInfiniteQuery({
    queryKey: ["assets", filters],
    queryFn: async ({ pageParam = 1 }) => {
      const res = await apiClient.get<PaginatedResponse<Asset>>("/assets", {
        params: { ...filters, page: pageParam, per_page: 30 },
      });
      return res.data;
    },
    getNextPageParam: (lastPage) => {
      const totalPages = Math.ceil(lastPage.total / lastPage.per_page);
      return lastPage.page < totalPages ? lastPage.page + 1 : undefined;
    },
    initialPageParam: 1,
  });
}

export function useAsset(id: string | undefined) {
  return useQuery({
    queryKey: ["asset", id],
    queryFn: async () => {
      const res = await apiClient.get<Asset>(`/assets/${id}`);
      return res.data;
    },
    enabled: !!id,
  });
}

export function useUploadAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      file,
      onProgress,
    }: {
      file: File;
      onProgress?: (pct: number) => void;
    }) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await apiClient.post<Asset>("/assets/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total && onProgress) {
            onProgress(Math.round((e.loaded * 100) / e.total));
          }
        },
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/assets/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useUpdateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Pick<Asset, "filename" | "metadata" | "tags">>;
    }) => {
      const res = await apiClient.patch<Asset>(`/assets/${id}`, data);
      return res.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["asset", id] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}
