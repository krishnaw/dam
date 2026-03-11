import { AssetGrid } from "@/components/asset-grid/AssetGrid";
import type { Asset } from "@/types";

interface SearchResultsProps {
  query: string;
  assets: Asset[];
  total: number;
  isLoading: boolean;
  onDelete?: (id: string) => void;
}

export function SearchResults({
  query,
  assets,
  total,
  isLoading,
  onDelete,
}: SearchResultsProps) {
  return (
    <div>
      {query && !isLoading && (
        <p className="mb-4 text-sm text-muted-foreground">
          Found {total} asset{total !== 1 ? "s" : ""} for &quot;{query}&quot;
        </p>
      )}
      <AssetGrid assets={assets} isLoading={isLoading} onDelete={onDelete} />
    </div>
  );
}
