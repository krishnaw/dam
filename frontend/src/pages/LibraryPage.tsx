import { useAssets, useDeleteAsset } from "@/api/useAssets";
import { AssetGrid } from "@/components/asset-grid/AssetGrid";
import { useAssetStore } from "@/stores/assetStore";
import { Button } from "@/components/ui/button";
import { Trash2, FolderPlus, Download } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

export function LibraryPage() {
  const navigate = useNavigate();
  const { data, isLoading, hasNextPage, isFetchingNextPage, fetchNextPage } =
    useAssets();
  const deleteMutation = useDeleteAsset();
  const { selectedAssets, clearSelection } = useAssetStore();

  const assets = data?.pages.flatMap((p) => p.items) ?? [];

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => toast.success("Asset deleted"),
    });
  };

  const handleBulkDelete = () => {
    selectedAssets.forEach((id) => deleteMutation.mutate(id));
    clearSelection();
    toast.success(`Deleted ${selectedAssets.size} assets`);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Library</h1>
        <Button size="sm" onClick={() => navigate("/upload")}>
          Upload
        </Button>
      </div>

      {selectedAssets.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border bg-muted/50 p-3">
          <span className="text-sm font-medium">
            {selectedAssets.size} selected
          </span>
          <Button variant="outline" size="sm" onClick={handleBulkDelete}>
            <Trash2 className="mr-1 h-4 w-4" />
            Delete
          </Button>
          <Button variant="outline" size="sm" disabled>
            <FolderPlus className="mr-1 h-4 w-4" />
            Add to Collection
          </Button>
          <Button variant="outline" size="sm" disabled>
            <Download className="mr-1 h-4 w-4" />
            Download
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={clearSelection}
          >
            Clear
          </Button>
        </div>
      )}

      <AssetGrid
        assets={assets}
        isLoading={isLoading}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        fetchNextPage={fetchNextPage}
        onDelete={handleDelete}
      />
    </div>
  );
}
