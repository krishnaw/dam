import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { Asset } from "@/types";

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface MetadataPanelProps {
  asset: Asset;
}

export function MetadataPanel({ asset }: MetadataPanelProps) {
  const entries: [string, string][] = [
    ["Filename", asset.original_filename],
    ["Type", asset.mime_type],
    ["Size", formatFileSize(asset.file_size)],
    ...(asset.width && asset.height
      ? [["Dimensions", `${asset.width} x ${asset.height}`] as [string, string]]
      : []),
    ["Uploaded", formatDate(asset.created_at)],
    ["Modified", formatDate(asset.updated_at)],
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold">File Information</h3>
      <div className="space-y-2">
        {entries.map(([label, value]) => (
          <div key={label} className="flex justify-between text-sm">
            <span className="text-muted-foreground">{label}</span>
            <span className="text-right font-medium">{value}</span>
          </div>
        ))}
      </div>

      {asset.tags.length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="mb-2 text-sm font-semibold">Tags</h3>
            <div className="flex flex-wrap gap-1">
              {asset.tags.map((tag) => (
                <Badge key={tag.id} variant="secondary">
                  {tag.name}
                </Badge>
              ))}
            </div>
          </div>
        </>
      )}

      {Object.keys(asset.metadata).length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="mb-2 text-sm font-semibold">Metadata</h3>
            <div className="space-y-2">
              {Object.entries(asset.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{key}</span>
                  <span className="text-right font-medium">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
