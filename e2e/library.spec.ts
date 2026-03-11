import { test, expect } from "@playwright/test";
import {
  apiLogin,
  apiUploadAsset,
  apiDeleteAsset,
  loginViaAPI,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

// Track assets created during tests for cleanup
let authToken: string;
const createdAssetIds: string[] = [];

test.describe("Asset Library / Grid", () => {
  test.beforeAll(async () => {
    // Login and upload test assets via API
    const loginData = await apiLogin();
    authToken = loginData.access_token;

    // Upload two test assets so the library has content
    const png1 = await apiUploadAsset(
      authToken,
      "test-photo-alpha.png",
      createTestPNG(),
      "image/png"
    );
    createdAssetIds.push(png1.id);

    const png2 = await apiUploadAsset(
      authToken,
      "test-photo-beta.png",
      createTestPNG(),
      "image/png"
    );
    createdAssetIds.push(png2.id);
  });

  test.afterAll(async () => {
    // Clean up all test assets
    for (const id of createdAssetIds) {
      await apiDeleteAsset(authToken, id).catch(() => {});
    }
    createdAssetIds.length = 0;
  });

  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page);
  });

  test.describe("Library page basics", () => {
    test("shows Library heading", async ({ page }) => {
      await page.goto("/");
      await expect(
        page.getByRole("heading", { name: "Library" })
      ).toBeVisible();
    });

    test("shows Upload button in header area", async ({ page }) => {
      await page.goto("/");
      await expect(
        page.getByRole("button", { name: "Upload" })
      ).toBeVisible();
    });

    test("Upload button navigates to upload page", async ({ page }) => {
      await page.goto("/");
      await page.getByRole("button", { name: "Upload" }).click();
      await page.waitForURL("**/upload", { timeout: 10000 });
    });
  });

  test.describe("Asset grid display", () => {
    test("displays uploaded assets in grid", async ({ page }) => {
      await page.goto("/");

      // Wait for assets to load — look for our uploaded filenames
      await expect(
        page.getByText("test-photo-alpha.png")
      ).toBeVisible({ timeout: 15000 });
      await expect(page.getByText("test-photo-beta.png")).toBeVisible();
    });

    test("asset cards show filename", async ({ page }) => {
      await page.goto("/");
      // The filename appears in a <p class="truncate text-sm font-medium">
      const filenameEl = page
        .locator(".truncate.text-sm.font-medium")
        .filter({ hasText: "test-photo-alpha.png" });
      await expect(filenameEl).toBeVisible({ timeout: 15000 });
    });

    test("asset cards show type badge", async ({ page }) => {
      await page.goto("/");
      // Wait for assets to load
      await expect(
        page.getByText("test-photo-alpha.png")
      ).toBeVisible({ timeout: 15000 });

      // PNG type badge — the mime_type.split("/")[1].toUpperCase() = "PNG"
      const pngBadge = page.locator("[class*='badge'], [class*='Badge']", {
        hasText: "PNG",
      });
      await expect(pngBadge.first()).toBeVisible();
    });

    test("asset cards show file size", async ({ page }) => {
      await page.goto("/");
      await expect(
        page.getByText("test-photo-alpha.png")
      ).toBeVisible({ timeout: 15000 });

      // File size is displayed as "X B" or "X.X KB" next to the badge
      // A 1x1 PNG is ~68 bytes, so should show "XX B" or similar
      const sizeText = page.locator("text=/\\d+(\\.\\d+)?\\s*(B|KB|MB)/");
      await expect(sizeText.first()).toBeVisible();
    });
  });

  test.describe("View toggle", () => {
    test("can switch between grid and list view", async ({ page }) => {
      await page.goto("/");
      await expect(
        page.getByText("test-photo-alpha.png")
      ).toBeVisible({ timeout: 15000 });

      // Click list view button (List icon)
      const listBtn = page
        .locator("button")
        .filter({ has: page.locator("svg.lucide-list") });
      await listBtn.click();

      // The container should switch to flex-col layout
      const listContainer = page.locator("[class*='flex-col'][class*='gap-2']");
      await expect(listContainer).toBeVisible();

      // Switch back to grid
      const gridBtn = page
        .locator("button")
        .filter({ has: page.locator("svg.lucide-layout-grid") });
      await gridBtn.click();

      // Grid container with CSS grid classes
      const gridContainer = page.locator("[class*='grid'][class*='grid-cols']");
      await expect(gridContainer).toBeVisible();
    });

    test("grid view button is highlighted when active", async ({ page }) => {
      await page.goto("/");
      await expect(
        page.getByText("test-photo-alpha.png")
      ).toBeVisible({ timeout: 15000 });

      // Grid button should have "default" variant (not "ghost") by default
      const gridBtn = page
        .locator("button")
        .filter({ has: page.locator("svg.lucide-layout-grid") });
      // The active button uses variant="default" which does not have "ghost" in class
      const gridClass = await gridBtn.getAttribute("class");
      expect(gridClass).not.toContain("ghost");
    });
  });

  test.describe("Asset card interactions", () => {
    test("clicking an asset card navigates to detail page", async ({
      page,
    }) => {
      await page.goto("/");
      await expect(
        page.getByText("test-photo-alpha.png")
      ).toBeVisible({ timeout: 15000 });

      // Click on the asset filename area (which triggers navigate)
      // Use .first() in case multiple assets share the same filename across test runs
      await page.getByText("test-photo-alpha.png").first().click();

      // Should navigate to /assets/<uuid>
      await page.waitForURL(/\/assets\//, { timeout: 10000 });
      expect(page.url()).toMatch(/\/assets\/[a-f0-9-]+/);
    });
  });

  test.describe("Empty state", () => {
    test("shows 'No assets found' when library is empty", async ({ page }) => {
      // Delete only our tracked test assets to create empty state
      for (const id of [...createdAssetIds]) {
        await apiDeleteAsset(authToken, id).catch(() => {});
      }
      createdAssetIds.length = 0;

      await loginViaAPI(page);
      await page.goto("/");

      await expect(page.getByText("No assets found")).toBeVisible({
        timeout: 15000,
      });
      await expect(
        page.getByText("Upload some files to get started")
      ).toBeVisible();

      // Re-upload assets for other tests that might run after
      const png1 = await apiUploadAsset(
        authToken,
        "test-photo-alpha.png",
        createTestPNG(),
        "image/png"
      );
      createdAssetIds.push(png1.id);

      const png2 = await apiUploadAsset(
        authToken,
        "test-photo-beta.png",
        createTestPNG(),
        "image/png"
      );
      createdAssetIds.push(png2.id);
    });
  });
});
