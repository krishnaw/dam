import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useSearch } from "@/api/useSearch";
import { useNLPSearch } from "@/api/useAISearch";
import { useDeleteAsset } from "@/api/useAssets";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchFilters } from "@/components/search/SearchFilters";
import { SearchResults } from "@/components/search/SearchResults";
import { SearchModeTabs, type SearchMode } from "@/components/search/SearchModeTabs";
import { VisualSearch } from "@/components/search/VisualSearch";
import { ColorSearch } from "@/components/search/ColorSearch";
import { useSearchStore } from "@/stores/searchStore";
import { toast } from "sonner";

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<SearchMode>("keyword");
  const urlQuery = searchParams.get("q") ?? "";
  const { filters, setFilters, resetFilters } = useSearchStore();
  const { data: keywordData, isLoading: keywordLoading } = useSearch(
    mode === "keyword" ? urlQuery : "",
    filters
  );
  const { data: nlpData, isLoading: nlpLoading } = useNLPSearch(
    mode === "nlp" ? urlQuery : ""
  );
  const deleteMutation = useDeleteAsset();

  const handleSearch = (q: string) => {
    if (q) {
      setSearchParams({ q });
    } else {
      setSearchParams({});
    }
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => toast.success("Asset deleted"),
    });
  };

  const isKeywordOrNlp = mode === "keyword" || mode === "nlp";
  const data = mode === "keyword" ? keywordData : nlpData;
  const isLoading = mode === "keyword" ? keywordLoading : nlpLoading;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Search</h1>
      <SearchModeTabs mode={mode} onChange={setMode} />

      {isKeywordOrNlp && (
        <SearchBar
          initialQuery={urlQuery}
          onSearch={handleSearch}
        />
      )}

      {mode === "visual" && <VisualSearch />}
      {mode === "color" && <ColorSearch />}

      {isKeywordOrNlp && (
        <div className="flex gap-6">
          <aside className="hidden w-56 shrink-0 md:block">
            <SearchFilters
              filters={filters}
              onChange={(f) => setFilters(f)}
              onClear={resetFilters}
            />
          </aside>
          <div className="flex-1">
            <SearchResults
              query={urlQuery}
              assets={data?.assets ?? []}
              total={data?.total ?? 0}
              isLoading={isLoading}
              onDelete={handleDelete}
            />
          </div>
        </div>
      )}
    </div>
  );
}
