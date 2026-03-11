import { useState } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useColorSearch } from "@/api/useAISearch";
import { SearchResults } from "./SearchResults";

const presetColors = [
  "#FF0000", "#FF6600", "#FFCC00", "#33CC33",
  "#0066FF", "#6633CC", "#FF33CC", "#000000",
  "#FFFFFF", "#808080", "#8B4513", "#00CED1",
];

export function ColorSearch() {
  const [color, setColor] = useState("#FF0000");
  const [activeColor, setActiveColor] = useState("");
  const { data, isLoading } = useColorSearch(activeColor);

  const handleSearch = () => {
    setActiveColor(color);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="h-10 w-14 cursor-pointer border p-1"
          />
          <span className="text-sm font-mono text-muted-foreground">{color}</span>
        </div>
        <Button onClick={handleSearch} className="gap-2">
          <Search className="h-4 w-4" />
          Search
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {presetColors.map((c) => (
          <button
            key={c}
            onClick={() => {
              setColor(c);
              setActiveColor(c);
            }}
            className="h-8 w-8 rounded-md border-2 transition-transform hover:scale-110"
            style={{
              backgroundColor: c,
              borderColor: color === c ? "var(--primary)" : "transparent",
            }}
            title={c}
          />
        ))}
      </div>

      {activeColor && (
        <SearchResults
          query={`Color: ${activeColor}`}
          assets={data?.assets ?? []}
          total={data?.total ?? 0}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
