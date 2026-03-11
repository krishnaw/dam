/**
 * Screenshot capture spec for PDF showcase document.
 * Takes screenshots of each key feature for the landscape PDF.
 */
import { test, expect, Page } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";
import {
  loginViaAPI,
  apiLogin,
  apiUploadAsset,
  apiCreateCollection,
  apiAddAssetToCollection,
  apiAddComment,
  cleanupTestData,
} from "./helpers/api-helpers";

const SCREENSHOT_DIR = "e2e/screenshots";

async function screenshot(page: Page, name: string) {
  await page.screenshot({
    path: `${SCREENSHOT_DIR}/${name}.png`,
    fullPage: false,
  });
}

test.describe("PDF Screenshots", () => {
  let token: string;
  const assetIds: string[] = [];
  let collectionId: string;

  test.beforeAll(async () => {
    const loginData = await apiLogin();
    token = loginData.access_token;

    // Upload real test images from generated files
    const imageDir = path.resolve(__dirname, "helpers/test-images");
    const files = [
      "sunset-beach.png",
      "mountain-landscape.png",
      "city-skyline.png",
      "product-photo.png",
      "team-meeting.png",
    ];
    for (const f of files) {
      const imgPath = path.join(imageDir, f);
      const imgBuffer = fs.readFileSync(imgPath);
      const asset = await apiUploadAsset(token, f, imgBuffer, "image/png");
      assetIds.push(asset.id);
    }

    // Create a collection and add assets
    const col = await apiCreateCollection(token, "Marketing Campaign 2026", "Brand assets for Q1 campaign");
    collectionId = col.id;
    await apiAddAssetToCollection(token, collectionId, assetIds[0]);
    await apiAddAssetToCollection(token, collectionId, assetIds[1]);

    // Add comments to first asset
    await apiAddComment(token, assetIds[0], "Great composition! The colors really pop.");
    await apiAddComment(token, assetIds[0], "Approved for use in the campaign.");
  });

  test.afterAll(async () => {
    if (token) await cleanupTestData(token);
  });

  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page);
  });

  test("01 - Login page", async ({ page }) => {
    // Clear auth to show login page
    await page.evaluate(() => {
      localStorage.removeItem("dam_token");
      localStorage.removeItem("dam_user");
    });
    await page.goto("/login");
    await expect(page.getByText("Sign In").first()).toBeVisible();
    await screenshot(page, "01-login");
  });

  test("02 - Library page with assets", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Library" })).toBeVisible();
    await expect(page.getByText("sunset-beach.png")).toBeVisible({ timeout: 10000 });
    // Wait for thumbnail images to load
    await page.waitForTimeout(2000);
    await screenshot(page, "02-library");
  });

  test("03 - Upload page", async ({ page }) => {
    await page.goto("/upload");
    await expect(page.getByRole("heading", { name: "Upload" })).toBeVisible();
    await screenshot(page, "03-upload");
  });

  test("04 - Asset detail page", async ({ page }) => {
    await page.goto(`/assets/${assetIds[0]}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1").filter({ hasText: "sunset-beach.png" })).toBeVisible({ timeout: 10000 });
    // Wait for preview image to load
    await page.waitForTimeout(2000);
    await screenshot(page, "04-asset-detail");
  });

  test("05 - Asset comments", async ({ page }) => {
    await page.goto(`/assets/${assetIds[0]}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible({ timeout: 10000 });
    await page.locator("button").filter({ hasText: "Comments" }).click();
    await expect(page.getByText("Great composition")).toBeVisible({ timeout: 10000 });
    await screenshot(page, "05-comments");
  });

  test("06 - Asset workflow", async ({ page }) => {
    await page.goto(`/assets/${assetIds[0]}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible({ timeout: 10000 });
    await page.locator("button").filter({ hasText: "Workflow" }).click();
    await expect(page.getByText("Review Actions")).toBeVisible();
    await screenshot(page, "06-workflow");
  });

  test("07 - Share dialog", async ({ page }) => {
    await page.goto(`/assets/${assetIds[0]}`);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: "Share" }).click();
    await expect(page.getByText("Share Asset")).toBeVisible();
    await screenshot(page, "07-share-dialog");
  });

  test("08 - Collections page", async ({ page }) => {
    await page.goto("/collections");
    await expect(page.getByRole("heading", { name: "Collections" })).toBeVisible();
    await screenshot(page, "08-collections");
  });

  test("09 - Search page", async ({ page }) => {
    await page.goto("/search");
    await expect(page.getByRole("heading", { name: "Search" })).toBeVisible();
    await screenshot(page, "09-search");
  });

  test("10 - Search with results", async ({ page }) => {
    await page.goto("/search?q=sunset");
    await expect(page.getByRole("heading", { name: "Search" })).toBeVisible();
    await page.waitForLoadState("networkidle");
    // Give search time to return results
    await page.waitForTimeout(2000);
    await screenshot(page, "10-search-results");
  });

  test("11 - AI Search modes", async ({ page }) => {
    await page.goto("/search");
    await expect(page.getByRole("heading", { name: "Search" })).toBeVisible();
    // Click Color tab
    await page.getByRole("button", { name: "Color" }).click();
    await expect(page.getByText("#FF0000")).toBeVisible();
    await screenshot(page, "11-ai-search-color");
  });

  test("12 - Settings page", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");
    await screenshot(page, "12-settings");
  });

  test("13 - Sidebar navigation", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("aside nav").getByText("Library")).toBeVisible();
    await screenshot(page, "13-navigation");
  });

  test("14 - Notification bell", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    // Click notification bell
    const bell = page.locator("header button").filter({ has: page.locator("svg.lucide-bell") });
    await bell.click();
    await expect(page.locator("h3").filter({ hasText: "Notifications" })).toBeVisible();
    await screenshot(page, "14-notifications");
  });
});
