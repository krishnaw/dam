import { useQuery, useMutation } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { SearchResult } from "@/types";

export function useNLPSearch(query: string) {
  return useQuery({
    queryKey: ["search", "nlp", query],
    queryFn: async () => {
      const res = await apiClient.post<SearchResult>("/search/nlp", { query });
      return res.data;
    },
    enabled: query.length > 0,
  });
}

export function useVisualSearch() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("image", file);
      const res = await apiClient.post<SearchResult>("/search/similar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
  });
}

export function useColorSearch(color: string) {
  return useQuery({
    queryKey: ["search", "color", color],
    queryFn: async () => {
      const res = await apiClient.post<SearchResult>("/search/color", { color });
      return res.data;
    },
    enabled: color.length > 0,
  });
}
