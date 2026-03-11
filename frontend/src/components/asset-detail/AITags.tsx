import { useNavigate } from "react-router-dom";
import { Sparkles, Check, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Asset } from "@/types";

interface AITagsProps {
  asset: Asset;
  onAcceptTag?: (tag: string) => void;
  onRejectTag?: (tag: string) => void;
}

export function AITags({ asset, onAcceptTag, onRejectTag }: AITagsProps) {
  const navigate = useNavigate();

  const aiTags = asset.tags.filter((t) => {
    const meta = asset.metadata as Record<string, unknown>;
    const tagSources = meta?.tag_sources as Record<string, string> | undefined;
    return tagSources?.[t.name] === "auto";
  });

  const manualTags = asset.tags.filter((t) => !aiTags.includes(t));

  if (aiTags.length === 0 && manualTags.length === 0) return null;

  return (
    <div className="space-y-2">
      {aiTags.length > 0 && (
        <div>
          <div className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold">
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            AI-Generated Tags
          </div>
          <div className="flex flex-wrap gap-1.5">
            {aiTags.map((tag) => (
              <div key={tag.id} className="group flex items-center gap-0.5">
                <Badge
                  variant="secondary"
                  className="cursor-pointer gap-1 pr-1"
                  onClick={() => navigate(`/search?q=${encodeURIComponent(tag.name)}`)}
                >
                  <Sparkles className="h-3 w-3 text-amber-500" />
                  {tag.name}
                </Badge>
                <div className="flex opacity-0 transition-opacity group-hover:opacity-100">
                  {onAcceptTag && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5 text-green-600"
                      onClick={() => onAcceptTag(tag.name)}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                  )}
                  {onRejectTag && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5 text-red-600"
                      onClick={() => onRejectTag(tag.name)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
