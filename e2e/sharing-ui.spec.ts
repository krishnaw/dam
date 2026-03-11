import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  apiUploadAsset,
  apiDeleteAsset,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

let token: string;
let assetId: string;

test.describe("Sharing - Share Dialog on Asset Detail", () => {
  test.beforeEach(async ({ page }) => {
    token = await loginViaAPI(page);

    // Upload a test image asset
    const png = createTestPNG();
    const asset = await apiUploadAsset(token, "share-test.png", png, "image/png");
    assetId = asset.id;

    // Navigate to the asset detail page
    await page.goto(`/assets/${assetId}`);
    await page.waitForLoadState("networkidle");
  });

  test.afterEach(async () => {
    try {
      await cleanupTestData(token);
    } catch {
      // Ignore cleanup errors
    }
  });

  test("Share button opens dialog with 'Share Asset' title", async ({ page }) => {
    const shareBtn = page.getByRole("button", { name: "Share" });
    await expect(shareBtn).toBeVisible();
    await shareBtn.click();

    // DialogTitle should show "Share Asset"
    await expect(page.getByText("Share Asset")).toBeVisible();
  });

  test("dialog has expiry date, password, and permissions fields", async ({ page }) => {
    await page.getByRole("button", { name: "Share" }).click();
    await expect(page.getByText("Share Asset")).toBeVisible();

    // Expiry date input
    await expect(page.getByText("Expiry Date (optional)")).toBeVisible();
    const dateInput = page.locator('input[type="datetime-local"]');
    await expect(dateInput).toBeVisible();

    // Password input
    await expect(page.getByText("Password (optional)")).toBeVisible();
    const passwordInput = page.locator('input[placeholder="Leave empty for no password"]');
    await expect(passwordInput).toBeVisible();

    // Permissions select — scope to dialog to avoid matching the ImageEditor's format select
    await expect(page.getByText("Permissions")).toBeVisible();
    const dialog = page.getByRole("dialog");
    const permSelect = dialog.locator("select");
    await expect(permSelect).toBeVisible();
  });

  test("Create Link button is visible in the dialog", async ({ page }) => {
    await page.getByRole("button", { name: "Share" }).click();
    await expect(page.getByText("Share Asset")).toBeVisible();

    const createLinkBtn = page.getByRole("button", { name: "Create Link" });
    await expect(createLinkBtn).toBeVisible();
  });

  test("Permissions dropdown has 'View only' and 'View & Download' options", async ({ page }) => {
    await page.getByRole("button", { name: "Share" }).click();
    await expect(page.getByText("Share Asset")).toBeVisible();

    // Scope to dialog to avoid matching the ImageEditor's format select on the same page
    const dialog = page.getByRole("dialog");
    const permSelect = dialog.locator("select");
    await expect(permSelect).toBeVisible();

    // Check option values
    const options = permSelect.locator("option");
    await expect(options).toHaveCount(2);
    await expect(options.nth(0)).toHaveText("View only");
    await expect(options.nth(1)).toHaveText("View & Download");
  });
});
