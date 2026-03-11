import { useParams } from "react-router-dom";
import { useAsset } from "@/api/useAssets";
import { AssetDetail } from "@/components/asset-detail/AssetDetail";
import { Skeleton } from "@/components/ui/skeleton";

export function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: asset, isLoading, error } = useAsset(id);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="flex-1 space-y-4">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-[400px] w-full rounded-lg" />
        </div>
        <div className="w-full lg:w-80 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    );
  }

  if (error || !asset) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">Asset not found</p>
      </div>
    );
  }

  return <AssetDetail asset={asset} />;
}
