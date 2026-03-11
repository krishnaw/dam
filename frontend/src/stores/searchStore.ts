import { create } from "zustand";

interface SearchFilters {
  mime_type?: string;
  date_from?: string;
  date_to?: string;
  min_width?: number;
  min_height?: number;
  tags?: string[];
}

interface SearchState {
  query: string;
  filters: SearchFilters;
  setQuery: (query: string) => void;
  setFilters: (filters: Partial<SearchFilters>) => void;
  resetFilters: () => void;
}

const defaultFilters: SearchFilters = {};

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  filters: { ...defaultFilters },
  setQuery: (query) => set({ query }),
  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),
  resetFilters: () => set({ filters: { ...defaultFilters } }),
}));
