import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";
import type { SearchResult } from "@/types";

interface SearchFilters {
  mime_type?: string;
  date_from?: string;
  date_to?: string;
  min_width?: number;
  min_height?: number;
  tags?: string[];
}

export function useSearch(query: string, filters: SearchFilters = {}) {
  return useQuery({
    queryKey: ["search", query, filters],
    queryFn: async () => {
      const res = await apiClient.get<SearchResult>("/search", {
        params: { q: query, ...filters },
      });
      return res.data;
    },
    enabled: query.length > 0,
  });
}
