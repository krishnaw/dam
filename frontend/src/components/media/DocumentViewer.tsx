import { useState } from "react";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocumentPreview } from "@/api/useTransforms";
import { Skeleton } from "@/components/ui/skeleton";

interface DocumentViewerProps {
  assetId: string;
  totalPages?: number;
}

export function DocumentViewer({
  assetId,
  totalPages = 1,
}: DocumentViewerProps) {
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(100);
  const { data: pageUrl, isLoading } = useDocumentPreview(assetId, page);

  const handlePrev = () => setPage((p) => Math.max(1, p - 1));
  const handleNext = () => setPage((p) => Math.min(totalPages, p + 1));
  const handleZoomIn = () => setZoom((z) => Math.min(200, z + 25));
  const handleZoomOut = () => setZoom((z) => Math.max(50, z - 25));

  return (
    <div className="flex gap-4">
      {totalPages > 1 && (
        <aside className="hidden w-24 shrink-0 space-y-2 overflow-y-auto md:block">
          {Array.from({ length: Math.min(totalPages, 20) }, (_, i) => i + 1).map(
            (p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`w-full rounded border p-1 text-xs transition-colors ${
                  p === page
                    ? "border-primary bg-primary/10"
                    : "border-muted hover:border-primary/50"
                }`}
              >
                Page {p}
              </button>
            )
          )}
        </aside>
      )}

      <div className="flex-1 space-y-3">
        <div className="flex items-center justify-between rounded-lg border bg-card px-3 py-2">
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handlePrev}
              disabled={page <= 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleNext}
              disabled={page >= totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleZoomOut}
              disabled={zoom <= 50}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="text-xs text-muted-foreground">{zoom}%</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleZoomIn}
              disabled={zoom >= 200}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-center overflow-auto rounded-lg border bg-muted/30 p-4 min-h-[500px]">
          {isLoading ? (
            <Skeleton className="h-[500px] w-[350px]" />
          ) : pageUrl ? (
            <img
              src={pageUrl}
              alt={`Page ${page}`}
              className="max-w-full object-contain"
              style={{ width: `${zoom}%` }}
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              Preview not available for this page
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
