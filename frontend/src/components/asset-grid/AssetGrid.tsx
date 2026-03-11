import { useEffect, useRef, useCallback } from "react";
import { AssetCard, AssetCardSkeleton } from "./AssetCard";
import { useAssetStore } from "@/stores/assetStore";
import { Button } from "@/components/ui/button";
import { LayoutGrid, List } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Asset } from "@/types";

interface AssetGridProps {
  assets: Asset[];
  isLoading?: boolean;
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
  fetchNextPage?: () => void;
  onDelete?: (id: string) => void;
  onAddToCollection?: (id: string) => void;
}

export function AssetGrid({
  assets,
  isLoading,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  onDelete,
  onAddToCollection,
}: AssetGridProps) {
  const { viewMode, setViewMode } = useAssetStore();
  const observerRef = useRef<IntersectionObserver | null>(null);

  const lastElementRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (isFetchingNextPage) return;
      if (observerRef.current) observerRef.current.disconnect();
      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage && fetchNextPage) {
          fetchNextPage();
        }
      });
      if (node) observerRef.current.observe(node);
    },
    [isFetchingNextPage, hasNextPage, fetchNextPage]
  );

  useEffect(() => {
    return () => {
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, []);

  if (isLoading) {
    return (
      <div>
        <ViewToggle viewMode={viewMode} setViewMode={setViewMode} />
        <div
          className={cn(
            "mt-4",
            viewMode === "grid"
              ? "grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
              : "flex flex-col gap-2"
          )}
        >
          {Array.from({ length: 12 }).map((_, i) => (
            <AssetCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">No assets found</p>
        <p className="text-sm">Upload some files to get started</p>
      </div>
    );
  }

  return (
    <div>
      <ViewToggle viewMode={viewMode} setViewMode={setViewMode} />
      <div
        className={cn(
          "mt-4",
          viewMode === "grid"
            ? "grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
            : "flex flex-col gap-2"
        )}
      >
        {assets.map((asset, index) => (
          <div
            key={asset.id}
            ref={index === assets.length - 1 ? lastElementRef : undefined}
          >
            <AssetCard
              asset={asset}
              onDelete={onDelete}
              onAddToCollection={onAddToCollection}
            />
          </div>
        ))}
      </div>
      {isFetchingNextPage && (
        <div className="mt-4 flex justify-center">
          <p className="text-sm text-muted-foreground">Loading more...</p>
        </div>
      )}
    </div>
  );
}

function ViewToggle({
  viewMode,
  setViewMode,
}: {
  viewMode: "grid" | "list";
  setViewMode: (mode: "grid" | "list") => void;
}) {
  return (
    <div className="flex gap-1">
      <Button
        variant={viewMode === "grid" ? "default" : "ghost"}
        size="icon"
        className="h-8 w-8"
        onClick={() => setViewMode("grid")}
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>
      <Button
        variant={viewMode === "list" ? "default" : "ghost"}
        size="icon"
        className="h-8 w-8"
        onClick={() => setViewMode("list")}
      >
        <List className="h-4 w-4" />
      </Button>
    </div>
  );
}
