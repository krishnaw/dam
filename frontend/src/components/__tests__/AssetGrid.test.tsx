import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { AssetGrid } from "../asset-grid/AssetGrid";
import { useAssetStore } from "@/stores/assetStore";
import type { Asset } from "@/types";

// --- Mocks ---

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({ useNavigate: () => mockNavigate }));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children }: any) => <span>{children}</span>,
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: (props: any) => <div data-testid="skeleton" {...props} />,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div>{children}</div>,
  DropdownMenuItem: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
  DropdownMenuTrigger: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

// AssetCard and AssetCardSkeleton are imported transitively; mock them so tests
// stay focused on AssetGrid behaviour.
vi.mock("../asset-grid/AssetCard", () => ({
  AssetCard: ({ asset }: { asset: Asset }) => (
    <div data-testid="asset-card" data-id={asset.id}>
      {asset.original_filename}
    </div>
  ),
  AssetCardSkeleton: () => <div data-testid="asset-card-skeleton" />,
}));

// --- Helpers ---

function makeAsset(overrides: Partial<Asset> = {}): Asset {
  return {
    id: "asset-1",
    filename: "test.jpg",
    original_filename: "test.jpg",
    mime_type: "image/jpeg",
    file_size: 1024,
    width: 800,
    height: 600,
    storage_path: "path/test.jpg",
    thumbnail_path: null,
    uploaded_by: "user-1",
    created_at: "2024-01-01",
    updated_at: "2024-01-01",
    tags: [],
    metadata: {},
    ...overrides,
  };
}

// --- Tests ---

describe("AssetGrid", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAssetStore.setState({ selectedAssets: new Set(), viewMode: "grid" });
  });

  it("shows skeleton loaders when isLoading is true", () => {
    render(<AssetGrid assets={[]} isLoading />);
    const skeletons = screen.getAllByTestId("asset-card-skeleton");
    expect(skeletons).toHaveLength(12);
  });

  it("shows the empty-state message when assets array is empty", () => {
    render(<AssetGrid assets={[]} />);
    expect(screen.getByText("No assets found")).toBeInTheDocument();
    expect(
      screen.getByText("Upload some files to get started")
    ).toBeInTheDocument();
  });

  it("does not show skeleton loaders in the empty state", () => {
    render(<AssetGrid assets={[]} />);
    expect(screen.queryByTestId("asset-card-skeleton")).not.toBeInTheDocument();
  });

  it("renders an AssetCard for each asset in the array", () => {
    const assets = [
      makeAsset({ id: "asset-1", original_filename: "alpha.jpg" }),
      makeAsset({ id: "asset-2", original_filename: "beta.jpg" }),
      makeAsset({ id: "asset-3", original_filename: "gamma.jpg" }),
    ];
    render(<AssetGrid assets={assets} />);

    const cards = screen.getAllByTestId("asset-card");
    expect(cards).toHaveLength(3);
    expect(screen.getByText("alpha.jpg")).toBeInTheDocument();
    expect(screen.getByText("beta.jpg")).toBeInTheDocument();
    expect(screen.getByText("gamma.jpg")).toBeInTheDocument();
  });

  it("shows 'Loading more...' when isFetchingNextPage is true", () => {
    render(<AssetGrid assets={[makeAsset()]} isFetchingNextPage />);
    expect(screen.getByText("Loading more...")).toBeInTheDocument();
  });

  it("does not show 'Loading more...' when isFetchingNextPage is false", () => {
    render(
      <AssetGrid assets={[makeAsset()]} isFetchingNextPage={false} />
    );
    expect(screen.queryByText("Loading more...")).not.toBeInTheDocument();
  });

  it("does not show 'Loading more...' when isFetchingNextPage is omitted", () => {
    render(<AssetGrid assets={[makeAsset()]} />);
    expect(screen.queryByText("Loading more...")).not.toBeInTheDocument();
  });
});
