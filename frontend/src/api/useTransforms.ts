import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";
import { useAuthStore } from "@/stores/authStore";
import type { TransformOptions } from "@/types";

export function buildTransformUrl(assetId: string, options: TransformOptions, token?: string | null): string {
  const params = new URLSearchParams();
  if (options.width) params.set("w", String(options.width));
  if (options.height) params.set("h", String(options.height));
  if (options.fit) params.set("fit", options.fit);
  if (options.format) params.set("fmt", options.format);
  if (options.quality) params.set("q", String(options.quality));
  if (options.rotate) params.set("rotate", String(options.rotate));
  if (token) params.set("token", token);
  return `/api/assets/${assetId}/transform?${params.toString()}`;
}

export function useQueueTranscode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      assetId,
      options,
    }: {
      assetId: string;
      options: TransformOptions;
    }) => {
      const res = await apiClient.post(`/assets/${assetId}/transcode`, options);
      return res.data;
    },
    onSuccess: (_, { assetId }) => {
      queryClient.invalidateQueries({ queryKey: ["asset", assetId] });
    },
  });
}

export function useDocumentPreview(assetId: string | undefined, page: number) {
  return useQuery({
    queryKey: ["document-preview", assetId, page],
    queryFn: async () => {
      const res = await apiClient.get(`/assets/${assetId}/preview`, {
        params: { page },
        responseType: "blob",
      });
      return URL.createObjectURL(res.data as Blob);
    },
    enabled: !!assetId,
  });
}
