import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Search, Sparkles, Image, Palette } from "lucide-react";

export type SearchMode = "keyword" | "nlp" | "visual" | "color";

interface SearchModeTabsProps {
  mode: SearchMode;
  onChange: (mode: SearchMode) => void;
}

const tabs: { mode: SearchMode; label: string; icon: React.ElementType }[] = [
  { mode: "keyword", label: "Keyword", icon: Search },
  { mode: "nlp", label: "Natural Language", icon: Sparkles },
  { mode: "visual", label: "Visual", icon: Image },
  { mode: "color", label: "Color", icon: Palette },
];

export function SearchModeTabs({ mode, onChange }: SearchModeTabsProps) {
  return (
    <div className="flex gap-1 rounded-lg border bg-muted/30 p-1">
      {tabs.map(({ mode: m, label, icon: Icon }) => (
        <Button
          key={m}
          variant={mode === m ? "default" : "ghost"}
          size="sm"
          className={cn("gap-2", mode !== m && "text-muted-foreground")}
          onClick={() => onChange(m)}
        >
          <Icon className="h-4 w-4" />
          {label}
        </Button>
      ))}
    </div>
  );
}
