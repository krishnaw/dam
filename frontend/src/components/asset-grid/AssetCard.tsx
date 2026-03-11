import { useNavigate } from "react-router-dom";
import { FileImage, FileVideo, FileText, File, Download, Trash2, FolderPlus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useAssetStore } from "@/stores/assetStore";
import { useAuthStore } from "@/stores/authStore";
import type { Asset } from "@/types";

function getFileIcon(mimeType: string) {
  if (mimeType.startsWith("image/")) return FileImage;
  if (mimeType.startsWith("video/")) return FileVideo;
  if (mimeType === "application/pdf") return FileText;
  return File;
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface AssetCardProps {
  asset: Asset;
  onDelete?: (id: string) => void;
  onAddToCollection?: (id: string) => void;
}

export function AssetCard({ asset, onDelete, onAddToCollection }: AssetCardProps) {
  const navigate = useNavigate();
  const { selectedAssets, toggleAsset } = useAssetStore();
  const authToken = useAuthStore((s) => s.token);
  const isSelected = selectedAssets.has(asset.id);
  const Icon = getFileIcon(asset.mime_type);

  return (
    <div
      className={cn(
        "group relative cursor-pointer overflow-hidden rounded-lg border bg-card transition-all hover:shadow-md",
        isSelected && "ring-2 ring-primary"
      )}
    >
      <div
        className="absolute top-2 left-2 z-10"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => toggleAsset(asset.id)}
          className="h-4 w-4 rounded border-border opacity-0 group-hover:opacity-100 transition-opacity data-[state=checked]:opacity-100"
          style={{ opacity: isSelected ? 1 : undefined }}
        />
      </div>
      <div
        className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => e.stopPropagation()}
      >
        <DropdownMenu>
          <DropdownMenuTrigger className="flex h-7 w-7 items-center justify-center rounded-md bg-background/80 backdrop-blur-sm hover:bg-background">
            <span className="text-xs font-bold">...</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => window.open(`/api/assets/${asset.id}/download`)}
            >
              <Download className="mr-2 h-4 w-4" />
              Download
            </DropdownMenuItem>
            {onAddToCollection && (
              <DropdownMenuItem onClick={() => onAddToCollection(asset.id)}>
                <FolderPlus className="mr-2 h-4 w-4" />
                Add to Collection
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            {onDelete && (
              <DropdownMenuItem
                onClick={() => onDelete(asset.id)}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div
        className="aspect-square bg-muted flex items-center justify-center"
        onClick={() => navigate(`/assets/${asset.id}`)}
      >
        {asset.thumbnail_path ? (
          <img
            src={`/api/assets/${asset.id}/thumbnail${authToken ? `?token=${authToken}` : ''}`}
            alt={asset.original_filename}
            className="h-full w-full object-cover"
          />
        ) : (
          <Icon className="h-12 w-12 text-muted-foreground" />
        )}
      </div>
      <div className="p-3" onClick={() => navigate(`/assets/${asset.id}`)}>
        <p className="truncate text-sm font-medium">{asset.original_filename}</p>
        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="secondary" className="text-xs">
            {asset.mime_type.split("/")[1]?.toUpperCase()}
          </Badge>
          <span>{formatFileSize(asset.file_size)}</span>
          {asset.width && asset.height && (
            <span>
              {asset.width}x{asset.height}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export function AssetCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <Skeleton className="aspect-square w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}
