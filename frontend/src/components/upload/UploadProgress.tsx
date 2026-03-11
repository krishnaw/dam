import { CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export type UploadStatus = "pending" | "uploading" | "processing" | "complete" | "error";

interface UploadProgressProps {
  filename: string;
  progress: number;
  status: UploadStatus;
  error?: string;
}

export function UploadProgress({
  filename,
  progress,
  status,
  error,
}: UploadProgressProps) {
  return (
    <div className="flex items-center gap-3 rounded-md border p-3">
      <div className="shrink-0">
        {status === "complete" && (
          <CheckCircle className="h-5 w-5 text-green-500" />
        )}
        {status === "error" && (
          <AlertCircle className="h-5 w-5 text-destructive" />
        )}
        {(status === "uploading" || status === "processing") && (
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
        )}
        {status === "pending" && (
          <div className="h-5 w-5 rounded-full border-2 border-muted-foreground" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium">{filename}</p>
        <div className="mt-1 flex items-center gap-2">
          <div className="h-1.5 flex-1 rounded-full bg-muted">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                status === "error" ? "bg-destructive" : "bg-primary"
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground">
            {status === "complete"
              ? "Done"
              : status === "error"
                ? "Failed"
                : status === "processing"
                  ? "Processing"
                  : `${progress}%`}
          </span>
        </div>
        {error && (
          <p className="mt-1 text-xs text-destructive">{error}</p>
        )}
      </div>
    </div>
  );
}
