import { UploadDropzone } from "@/components/upload/UploadDropzone";

export function UploadPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Upload</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload files to your asset library
        </p>
      </div>
      <UploadDropzone />
    </div>
  );
}
