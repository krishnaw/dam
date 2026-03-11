import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AssetCard } from "../asset-grid/AssetCard";
import { useAssetStore } from "@/stores/assetStore";
import { useAuthStore } from "@/stores/authStore";
import type { Asset } from "@/types";

// --- Mocks ---

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("@/components/ui/badge", () => ({
  Badge: ({ children, ...props }: any) => (
    <span data-testid="badge" {...props}>
      {children}
    </span>
  ),
}));

vi.mock("@/components/ui/skeleton", () => ({
  Skeleton: (props: any) => <div data-testid="skeleton" {...props} />,
}));

vi.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div>{children}</div>,
  DropdownMenuItem: ({ children, ...props }: any) => (
    <div {...props}>{children}</div>
  ),
  DropdownMenuSeparator: () => <hr />,
  DropdownMenuTrigger: ({ children, ...props }: any) => (
    <button {...props}>{children}</button>
  ),
}));

// --- Helpers ---

function makeAsset(overrides: Partial<Asset> = {}): Asset {
  return {
    id: "asset-1",
    filename: "photo.jpg",
    original_filename: "vacation-photo.jpg",
    mime_type: "image/jpeg",
    file_size: 2048576,
    width: 1920,
    height: 1080,
    storage_path: "/uploads/photo.jpg",
    thumbnail_path: "/thumbs/photo.jpg",
    uploaded_by: "user-1",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    tags: [],
    metadata: {},
    ...overrides,
  };
}

// --- Tests ---

describe("AssetCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset zustand stores between tests
    useAssetStore.setState({ selectedAssets: new Set() });
    useAuthStore.setState({ token: "test-token" });
  });

  it("renders the asset filename", () => {
    render(<AssetCard asset={makeAsset()} />);
    expect(screen.getByText("vacation-photo.jpg")).toBeInTheDocument();
  });

  it("renders file size in bytes for small files", () => {
    render(<AssetCard asset={makeAsset({ file_size: 512 })} />);
    expect(screen.getByText("512 B")).toBeInTheDocument();
  });

  it("renders file size in KB for kilobyte-range files", () => {
    render(<AssetCard asset={makeAsset({ file_size: 5120 })} />);
    expect(screen.getByText("5.0 KB")).toBeInTheDocument();
  });

  it("renders file size in MB for megabyte-range files", () => {
    render(<AssetCard asset={makeAsset({ file_size: 2048576 })} />);
    expect(screen.getByText("2.0 MB")).toBeInTheDocument();
  });

  it("renders mime type badge with uppercase extension", () => {
    render(<AssetCard asset={makeAsset({ mime_type: "image/jpeg" })} />);
    const badge = screen.getByTestId("badge");
    expect(badge).toHaveTextContent("JPEG");
  });

  it("renders dimensions when width and height are present", () => {
    render(
      <AssetCard asset={makeAsset({ width: 1920, height: 1080 })} />
    );
    expect(screen.getByText("1920x1080")).toBeInTheDocument();
  });

  it("does not render dimensions when width and height are null", () => {
    render(
      <AssetCard asset={makeAsset({ width: null, height: null })} />
    );
    expect(screen.queryByText(/\d+x\d+/)).not.toBeInTheDocument();
  });

  it("shows thumbnail image with auth token when thumbnail_path is set", () => {
    render(<AssetCard asset={makeAsset({ thumbnail_path: "/thumbs/photo.jpg" })} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute(
      "src",
      expect.stringContaining("/api/assets/asset-1/thumbnail")
    );
    expect(img).toHaveAttribute("src", expect.stringContaining("token=test-token"));
  });

  it("shows file icon instead of image when thumbnail_path is null", () => {
    render(<AssetCard asset={makeAsset({ thumbnail_path: null })} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("navigates to asset detail page on click", () => {
    render(<AssetCard asset={makeAsset()} />);
    // Click on the thumbnail area
    const thumbnailArea = screen.getByAltText("vacation-photo.jpg");
    fireEvent.click(thumbnailArea);
    expect(mockNavigate).toHaveBeenCalledWith("/assets/asset-1");
  });

  it("toggles selection when checkbox is clicked", () => {
    render(<AssetCard asset={makeAsset()} />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(useAssetStore.getState().selectedAssets.has("asset-1")).toBe(true);

    fireEvent.click(checkbox);
    expect(useAssetStore.getState().selectedAssets.has("asset-1")).toBe(false);
  });

  it("shows checkbox as checked when asset is in selectedAssets", () => {
    useAssetStore.setState({ selectedAssets: new Set(["asset-1"]) });

    render(<AssetCard asset={makeAsset()} />);
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });
});
