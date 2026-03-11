import { useState } from "react";
import {
  RotateCw,
  RotateCcw,
  Link2,
  Link2Off,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { buildTransformUrl, useQueueTranscode } from "@/api/useTransforms";
import { useAuthStore } from "@/stores/authStore";
import type { TransformOptions } from "@/types";
import { toast } from "sonner";

interface ImageEditorProps {
  assetId: string;
  originalWidth: number | null;
  originalHeight: number | null;
}

export function ImageEditor({
  assetId,
  originalWidth,
  originalHeight,
}: ImageEditorProps) {
  const [width, setWidth] = useState(originalWidth ?? 0);
  const [height, setHeight] = useState(originalHeight ?? 0);
  const [locked, setLocked] = useState(true);
  const [rotation, setRotation] = useState(0);
  const [format, setFormat] = useState<"jpeg" | "png" | "webp">("jpeg");
  const [quality, setQuality] = useState(85);
  const transcode = useQueueTranscode();
  const authToken = useAuthStore((s) => s.token);

  const aspectRatio =
    originalWidth && originalHeight ? originalWidth / originalHeight : 1;

  const handleWidthChange = (w: number) => {
    setWidth(w);
    if (locked) setHeight(Math.round(w / aspectRatio));
  };

  const handleHeightChange = (h: number) => {
    setHeight(h);
    if (locked) setWidth(Math.round(h * aspectRatio));
  };

  const options: TransformOptions = {
    width: width || undefined,
    height: height || undefined,
    format,
    quality,
    rotate: rotation || undefined,
  };

  const previewUrl = buildTransformUrl(assetId, options, authToken);

  const handleSave = () => {
    transcode.mutate(
      { assetId, options },
      { onSuccess: () => toast.success("Saved as new version") }
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-3">
        <div className="flex items-center gap-1">
          <label className="text-xs text-muted-foreground">W</label>
          <Input
            type="number"
            value={width}
            onChange={(e) => handleWidthChange(Number(e.target.value))}
            className="h-8 w-20 text-sm"
          />
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setLocked(!locked)}
          title={locked ? "Unlock aspect ratio" : "Lock aspect ratio"}
        >
          {locked ? <Link2 className="h-4 w-4" /> : <Link2Off className="h-4 w-4" />}
        </Button>
        <div className="flex items-center gap-1">
          <label className="text-xs text-muted-foreground">H</label>
          <Input
            type="number"
            value={height}
            onChange={(e) => handleHeightChange(Number(e.target.value))}
            className="h-8 w-20 text-sm"
          />
        </div>

        <div className="h-6 w-px bg-border" />

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setRotation((r) => (r - 90 + 360) % 360)}
          title="Rotate CCW"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setRotation((r) => (r + 90) % 360)}
          title="Rotate CW"
        >
          <RotateCw className="h-4 w-4" />
        </Button>

        <div className="h-6 w-px bg-border" />

        <select
          value={format}
          onChange={(e) => setFormat(e.target.value as "jpeg" | "png" | "webp")}
          className="h-8 rounded-md border bg-transparent px-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="jpeg">JPEG</option>
          <option value="png">PNG</option>
          <option value="webp">WebP</option>
        </select>

        <div className="flex items-center gap-1">
          <label className="text-xs text-muted-foreground">Quality</label>
          <input
            type="range"
            min={1}
            max={100}
            value={quality}
            onChange={(e) => setQuality(Number(e.target.value))}
            className="h-1 w-20 cursor-pointer accent-primary"
          />
          <span className="text-xs text-muted-foreground">{quality}</span>
        </div>

        <Button
          size="sm"
          className="ml-auto gap-2"
          onClick={handleSave}
          disabled={transcode.isPending}
        >
          <Save className="h-4 w-4" />
          Save as New Version
        </Button>
      </div>

      <div className="flex items-center justify-center rounded-lg border bg-muted/30 p-4 min-h-[400px]">
        <img
          src={previewUrl}
          alt="Preview"
          className="max-h-[600px] max-w-full object-contain"
          style={{ transform: `rotate(${rotation}deg)` }}
        />
      </div>
    </div>
  );
}
