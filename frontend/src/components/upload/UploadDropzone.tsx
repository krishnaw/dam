import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUploadAsset } from "@/api/useAssets";
import { UploadProgress, type UploadStatus } from "./UploadProgress";

interface UploadItem {
  id: string;
  filename: string;
  progress: number;
  status: UploadStatus;
  error?: string;
}

export function UploadDropzone() {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const uploadMutation = useUploadAsset();

  const updateUpload = (id: string, update: Partial<UploadItem>) => {
    setUploads((prev) =>
      prev.map((u) => (u.id === id ? { ...u, ...update } : u))
    );
  };

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newUploads: UploadItem[] = acceptedFiles.map((file) => ({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        filename: file.name,
        progress: 0,
        status: "pending" as UploadStatus,
      }));

      setUploads((prev) => [...newUploads, ...prev]);

      newUploads.forEach((item, index) => {
        const file = acceptedFiles[index];
        updateUpload(item.id, { status: "uploading" });

        uploadMutation.mutate(
          {
            file,
            onProgress: (pct) => updateUpload(item.id, { progress: pct }),
          },
          {
            onSuccess: () =>
              updateUpload(item.id, {
                status: "complete",
                progress: 100,
              }),
            onError: (err) =>
              updateUpload(item.id, {
                status: "error",
                error: err instanceof Error ? err.message : "Upload failed",
              }),
          }
        );
      });
    },
    [uploadMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [],
      "video/*": [],
      "audio/*": [],
      "application/pdf": [],
      "application/msword": [],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [],
    },
  });

  return (
    <div className="space-y-6">
      <div
        {...getRootProps()}
        className={cn(
          "flex min-h-[240px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
        <p className="text-sm font-medium">
          {isDragActive
            ? "Drop files here..."
            : "Drag files here or click to browse"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Images, videos, audio, and documents
        </p>
      </div>

      {uploads.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Uploads</h3>
          {uploads.map((item) => (
            <UploadProgress
              key={item.id}
              filename={item.filename}
              progress={item.progress}
              status={item.status}
              error={item.error}
            />
          ))}
        </div>
      )}
    </div>
  );
}
