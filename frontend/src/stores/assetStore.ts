import { create } from "zustand";

type ViewMode = "grid" | "list";

interface AssetState {
  selectedAssets: Set<string>;
  viewMode: ViewMode;
  toggleAsset: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelection: () => void;
  setViewMode: (mode: ViewMode) => void;
}

export const useAssetStore = create<AssetState>((set) => ({
  selectedAssets: new Set(),
  viewMode: "grid",
  toggleAsset: (id) =>
    set((state) => {
      const next = new Set(state.selectedAssets);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { selectedAssets: next };
    }),
  selectAll: (ids) => set({ selectedAssets: new Set(ids) }),
  clearSelection: () => set({ selectedAssets: new Set() }),
  setViewMode: (mode) => set({ viewMode: mode }),
}));
