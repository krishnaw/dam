import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SearchFiltersValue {
  mime_type?: string;
  date_from?: string;
  date_to?: string;
}

interface SearchFiltersProps {
  filters: SearchFiltersValue;
  onChange: (filters: SearchFiltersValue) => void;
  onClear: () => void;
}

const fileTypeOptions = [
  { value: "image/", label: "Images" },
  { value: "video/", label: "Videos" },
  { value: "audio/", label: "Audio" },
  { value: "application/pdf", label: "Documents" },
];

export function SearchFilters({ filters, onChange, onClear }: SearchFiltersProps) {
  const [typeOpen, setTypeOpen] = useState(true);
  const [dateOpen, setDateOpen] = useState(true);

  return (
    <div className="space-y-4">
      <div>
        <button
          type="button"
          onClick={() => setTypeOpen(!typeOpen)}
          className="flex w-full items-center justify-between text-sm font-semibold"
        >
          File Type
          <span className="text-muted-foreground">{typeOpen ? "-" : "+"}</span>
        </button>
        {typeOpen && (
          <div className="mt-2 space-y-1">
            {fileTypeOptions.map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.mime_type === opt.value}
                  onChange={() =>
                    onChange({
                      ...filters,
                      mime_type: filters.mime_type === opt.value ? undefined : opt.value,
                    })
                  }
                  className="h-4 w-4 rounded border-border"
                />
                {opt.label}
              </label>
            ))}
          </div>
        )}
      </div>

      <div>
        <button
          type="button"
          onClick={() => setDateOpen(!dateOpen)}
          className="flex w-full items-center justify-between text-sm font-semibold"
        >
          Date Range
          <span className="text-muted-foreground">{dateOpen ? "-" : "+"}</span>
        </button>
        {dateOpen && (
          <div className="mt-2 space-y-2">
            <div>
              <label className="text-xs text-muted-foreground">From</label>
              <Input
                type="date"
                value={filters.date_from ?? ""}
                onChange={(e) => onChange({ ...filters, date_from: e.target.value || undefined })}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">To</label>
              <Input
                type="date"
                value={filters.date_to ?? ""}
                onChange={(e) => onChange({ ...filters, date_to: e.target.value || undefined })}
                className="h-8 text-sm"
              />
            </div>
          </div>
        )}
      </div>

      <Button variant="outline" size="sm" className="w-full" onClick={onClear}>
        Clear Filters
      </Button>
    </div>
  );
}
