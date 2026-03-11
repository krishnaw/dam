import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  apiUploadAsset,
  apiDeleteAsset,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

const TEST_FILENAME = "e2e-detail-test.png";

test.describe("Asset Detail Page", () => {
  let token: string;
  let assetId: string;

  test.beforeAll(async () => {
    // Login and upload a test asset once for the whole suite
    const { apiLogin } = await import("./helpers/api-helpers");
    const loginData = await apiLogin();
    token = loginData.access_token;

    const asset = await apiUploadAsset(token, TEST_FILENAME, createTestPNG(), "image/png");
    assetId = asset.id;
  });

  test.afterAll(async () => {
    if (token) {
      await cleanupTestData(token);
    }
  });

  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page);
  });

  test("shows asset filename as heading", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await expect(page.locator("h1").filter({ hasText: TEST_FILENAME })).toBeVisible();
  });

  test("download button is visible", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.waitForLoadState("networkidle");
    // Wait for the asset to finish loading before asserting
    await expect(page.locator("h1").filter({ hasText: TEST_FILENAME })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("button", { name: "Download" })).toBeVisible();
  });

  test("share button is visible", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await expect(page.getByRole("button", { name: /Share/ })).toBeVisible();
  });

  test("detail tabs are visible: Details, Comments, Workflow", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);

    const detailsTab = page.locator("button").filter({ hasText: "Details" });
    const commentsTab = page.locator("button").filter({ hasText: "Comments" });
    const workflowTab = page.locator("button").filter({ hasText: "Workflow" });

    await expect(detailsTab).toBeVisible();
    await expect(commentsTab).toBeVisible();
    await expect(workflowTab).toBeVisible();
  });

  test("metadata panel shows File Information with filename, type, and size", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.waitForLoadState("networkidle");

    // Wait for the asset to finish loading before asserting
    await expect(page.locator("h1").filter({ hasText: TEST_FILENAME })).toBeVisible({ timeout: 10000 });

    // File Information heading
    await expect(page.locator("h3").filter({ hasText: "File Information" })).toBeVisible();

    // Metadata labels
    await expect(page.getByText("Filename")).toBeVisible();
    await expect(page.getByText("Type")).toBeVisible();
    await expect(page.getByText("Size")).toBeVisible();
    await expect(page.getByText("Uploaded")).toBeVisible();
    await expect(page.getByText("Modified")).toBeVisible();

    // Filename value appears in the metadata section below "Filename" label
    const filenameValue = page.locator("main aside").getByText(TEST_FILENAME);
    await expect(filenameValue).toBeVisible();
  });

  test("back button navigates to previous page", async ({ page }) => {
    // Start at library, then navigate to asset detail
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Navigate to the asset detail page directly
    await page.goto(`/assets/${assetId}`);
    await expect(page.locator("h1").filter({ hasText: TEST_FILENAME })).toBeVisible();

    // Click the back button (usually an arrow-left icon button)
    const backBtn = page
      .locator("button")
      .filter({ has: page.locator("svg.lucide-arrow-left") })
      .first();
    await backBtn.click();

    // Should navigate away from the asset detail page
    await expect(page).not.toHaveURL(/\/assets\//);
  });
});
