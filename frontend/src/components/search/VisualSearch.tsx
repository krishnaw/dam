import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVisualSearch } from "@/api/useAISearch";
import { SearchResults } from "./SearchResults";

export function VisualSearch() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const visualSearch = useVisualSearch();

  const onDrop = useCallback((accepted: File[]) => {
    const f = accepted[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [] },
    maxFiles: 1,
  });

  const handleSearch = () => {
    if (file) {
      visualSearch.mutate(file);
    }
  };

  const handleClear = () => {
    setFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    visualSearch.reset();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-4">
        {!preview ? (
          <div
            {...getRootProps()}
            className={`flex h-32 w-48 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
              isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary/50"
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mb-2 h-6 w-6 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">Drop an image or click</p>
          </div>
        ) : (
          <div className="relative h-32 w-48">
            <img
              src={preview}
              alt="Reference"
              className="h-full w-full rounded-lg border object-cover"
            />
            <button
              onClick={handleClear}
              className="absolute -right-2 -top-2 rounded-full bg-destructive p-1 text-destructive-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        )}
        <Button onClick={handleSearch} disabled={!file || visualSearch.isPending} className="gap-2">
          <Search className="h-4 w-4" />
          Find Similar
        </Button>
      </div>

      {visualSearch.data && (
        <SearchResults
          query="Visual search"
          assets={visualSearch.data.assets}
          total={visualSearch.data.total}
          isLoading={false}
        />
      )}
    </div>
  );
}
