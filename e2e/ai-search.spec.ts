import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  apiUploadAsset,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

let token: string;

test.describe("AI Search - Search Mode Tabs and Features", () => {
  test.beforeEach(async ({ page }) => {
    token = await loginViaAPI(page);

    // Upload a test asset so the app has data
    const png = createTestPNG();
    await apiUploadAsset(token, "ai-search-test.png", png, "image/png");

    await page.goto("/search");
    await page.waitForLoadState("networkidle");
  });

  test.afterEach(async () => {
    try {
      await cleanupTestData(token);
    } catch {
      // Ignore cleanup errors
    }
  });

  test("search mode tabs show all 4 modes", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Keyword" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Natural Language" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Visual" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Color" })).toBeVisible();
  });

  test("Visual search tab shows dropzone and disabled Find Similar button", async ({ page }) => {
    // Click Visual tab
    await page.getByRole("button", { name: "Visual" }).click();

    // Dropzone text
    await expect(page.getByText("Drop an image or click")).toBeVisible();

    // Find Similar button should be visible and disabled (no image selected)
    const findBtn = page.getByRole("button", { name: "Find Similar" });
    await expect(findBtn).toBeVisible();
    await expect(findBtn).toBeDisabled();
  });

  test("Color search tab shows color picker and preset swatches", async ({ page }) => {
    // Click Color tab
    await page.getByRole("button", { name: "Color" }).click();

    // Color picker input
    const colorInput = page.locator('input[type="color"]');
    await expect(colorInput).toBeVisible();

    // Search button
    const searchBtn = page.getByRole("button", { name: "Search" });
    await expect(searchBtn).toBeVisible();

    // Preset color swatch buttons (12 preset colors, each with title="#XXXXXX")
    const swatches = page.locator('button[title^="#"]');
    await expect(swatches).toHaveCount(12);
  });

  test("color picker shows hex value", async ({ page }) => {
    await page.getByRole("button", { name: "Color" }).click();

    // The default color hex value should be displayed
    await expect(page.getByText("#FF0000")).toBeVisible();
  });

  test("clicking a preset swatch updates the color", async ({ page }) => {
    await page.getByRole("button", { name: "Color" }).click();

    // Wait for color picker content to render
    await expect(page.getByText("#FF0000")).toBeVisible();

    // Click a preset swatch (e.g., blue #0066FF)
    const blueSwatch = page.locator('button[title="#0066FF"]');
    await expect(blueSwatch).toBeVisible();
    await blueSwatch.click();

    // Hex display should update (use exact to avoid matching search results text)
    await expect(page.getByText("#0066FF", { exact: true })).toBeVisible();
  });
});
