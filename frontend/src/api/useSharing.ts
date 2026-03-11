import { useQuery, useMutation } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { ShareLink } from "@/types";

export function useCreateShare() {
  return useMutation({
    mutationFn: async (data: {
      asset_id?: string;
      collection_id?: string;
      expires_at?: string;
      password?: string;
      permissions?: string;
    }) => {
      const res = await apiClient.post<ShareLink>("/shares", data);
      return res.data;
    },
  });
}

export function useShareAccess(token: string | undefined) {
  return useQuery({
    queryKey: ["share", token],
    queryFn: async () => {
      const res = await apiClient.get<ShareLink & { asset?: { id: string; filename: string; mime_type: string; original_filename: string } }>(
        `/shares/${token}`
      );
      return res.data;
    },
    enabled: !!token,
    retry: false,
  });
}
