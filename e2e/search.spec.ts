import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  cleanupTestData,
  apiLogin,
  apiUploadAsset,
  createTestPNG,
} from "./helpers/api-helpers";

test.describe("Search Functionality", () => {
  let token: string;

  test.beforeAll(async () => {
    // Upload test assets so search has data to find
    const data = await apiLogin();
    token = data.access_token;

    await apiUploadAsset(token, "sunset-photo.png", createTestPNG(), "image/png");
    await apiUploadAsset(token, "mountain-landscape.png", createTestPNG(), "image/png");
    await apiUploadAsset(token, "ocean-waves.png", createTestPNG(), "image/png");

    // Give Meilisearch time to index the new assets
    await new Promise((r) => setTimeout(r, 2000));
  });

  test.beforeEach(async ({ page }) => {
    token = await loginViaAPI(page);
  });

  test.afterAll(async () => {
    const data = await apiLogin();
    await cleanupTestData(data.access_token);
  });

  test("search page shows heading", async ({ page }) => {
    await page.goto("/search");
    await expect(
      page.getByRole("heading", { name: "Search", level: 1 })
    ).toBeVisible();
  });

  test("search mode tabs are visible", async ({ page }) => {
    await page.goto("/search");
    await expect(page.getByRole("button", { name: "Keyword" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Natural Language" })
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Visual" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Color" })).toBeVisible();
  });

  test("keyword mode shows search bar and filters", async ({ page }) => {
    await page.goto("/search");

    // Search bar elements — scope to main to avoid the header's duplicate input
    const main = page.locator("main");
    await expect(main.getByPlaceholder("Search assets...")).toBeVisible();
    await expect(
      main.getByRole("button", { name: "Search" })
    ).toBeVisible();

    // File type filter section — the toggle button is "File Type -" so use partial match
    await expect(
      page.getByRole("button", { name: /File Type/ })
    ).toBeVisible();
    await expect(page.getByLabel("Images")).toBeVisible();
    await expect(page.getByLabel("Videos")).toBeVisible();
    await expect(page.getByLabel("Audio")).toBeVisible();
    await expect(page.getByLabel("Documents")).toBeVisible();

    // Clear filters button
    await expect(
      page.getByRole("button", { name: "Clear Filters" })
    ).toBeVisible();
  });

  test("keyword search shows results with count", async ({ page }) => {
    await page.goto("/search");

    // Scope to main to avoid filling the header's duplicate "Search assets..." input
    const main = page.locator("main");
    await main.getByPlaceholder("Search assets...").fill("sunset");
    await main.getByRole("button", { name: "Search" }).click();

    // URL should include the query param
    await expect(page).toHaveURL(/[?&]q=sunset/);

    // Should show "Found N asset(s) for" text
    await expect(
      page.getByText(/Found \d+ assets? for/)
    ).toBeVisible({ timeout: 10000 });
  });

  test("header search input navigates to search page with query", async ({ page }) => {
    // Start on a non-search page
    await page.goto("/upload");

    // The header contains its own search input
    const headerSearch = page
      .locator("header")
      .getByPlaceholder("Search assets...");
    await expect(headerSearch).toBeVisible();

    // Type and press Enter to submit
    await headerSearch.fill("mountain");
    await headerSearch.press("Enter");

    // Should navigate to the search page with the query param
    await page.waitForURL(/\/search\?q=mountain/, { timeout: 10000 });

    // Search page heading should be present
    await expect(
      page.getByRole("heading", { name: "Search", level: 1 })
    ).toBeVisible();
  });

  test("switching tabs hides keyword-specific UI", async ({ page }) => {
    await page.goto("/search");

    // In keyword mode, filters are visible
    await expect(
      page.getByRole("button", { name: "Clear Filters" })
    ).toBeVisible();

    // Switch to Visual tab
    await page.getByRole("button", { name: "Visual" }).click();

    // Keyword search bar and filters should disappear
    await expect(
      page.getByRole("button", { name: "Clear Filters" })
    ).not.toBeVisible();
  });

  test("search button submits the query from search page", async ({ page }) => {
    await page.goto("/search");

    // Use the search page's own SearchBar (not the header)
    const searchInput = page
      .locator("main, [class*='space-y']")
      .getByPlaceholder("Search assets...")
      .last();
    await searchInput.fill("landscape");
    await page.getByRole("button", { name: "Search" }).click();

    await expect(page).toHaveURL(/[?&]q=landscape/);
  });
});
