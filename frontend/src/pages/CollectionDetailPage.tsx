import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useCollection } from "@/api/useCollections";
import { useAssets, useDeleteAsset } from "@/api/useAssets";
import { AssetGrid } from "@/components/asset-grid/AssetGrid";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

export function CollectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: collection, isLoading: collLoading } = useCollection(id);
  const { data: assetsData, isLoading: assetsLoading, hasNextPage, isFetchingNextPage, fetchNextPage } =
    useAssets({ collection_id: id });
  const deleteMutation = useDeleteAsset();

  const assets = assetsData?.pages.flatMap((p) => p.items) ?? [];

  const handleDelete = (assetId: string) => {
    deleteMutation.mutate(assetId, {
      onSuccess: () => toast.success("Asset removed"),
    });
  };

  if (collLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">Collection not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/collections")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{collection.name}</h1>
          {collection.description && (
            <p className="text-sm text-muted-foreground">{collection.description}</p>
          )}
        </div>
      </div>

      <AssetGrid
        assets={assets}
        isLoading={assetsLoading}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        fetchNextPage={fetchNextPage}
        onDelete={handleDelete}
      />
    </div>
  );
}
