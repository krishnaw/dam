import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  apiUploadAsset,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

let token: string;

test.describe("Media Players - Asset Detail Preview", () => {
  test.afterEach(async () => {
    try {
      await cleanupTestData(token);
    } catch {
      // Ignore cleanup errors
    }
  });

  test("image asset shows ImageEditor with format select and quality slider", async ({ page }) => {
    token = await loginViaAPI(page);

    const png = createTestPNG();
    const asset = await apiUploadAsset(token, "editor-test.png", png, "image/png");

    await page.goto(`/assets/${asset.id}`);
    await page.waitForLoadState("networkidle");

    // Image preview should be visible
    const img = page.locator('img[alt="Preview"]');
    await expect(img).toBeVisible();

    // Format select with JPEG, PNG, WebP options
    const formatSelect = page.locator("select").filter({ has: page.locator('option[value="jpeg"]') });
    await expect(formatSelect).toBeVisible();

    const options = formatSelect.locator("option");
    await expect(options.nth(0)).toHaveText("JPEG");
    await expect(options.nth(1)).toHaveText("PNG");
    await expect(options.nth(2)).toHaveText("WebP");

    // Quality label and range input
    await expect(page.getByText("Quality")).toBeVisible();
    const rangeInput = page.locator('input[type="range"]');
    await expect(rangeInput).toBeVisible();
  });

  test("image editor has 'Save as New Version' button", async ({ page }) => {
    token = await loginViaAPI(page);

    const png = createTestPNG();
    const asset = await apiUploadAsset(token, "save-test.png", png, "image/png");

    await page.goto(`/assets/${asset.id}`);
    await page.waitForLoadState("networkidle");

    const saveBtn = page.getByRole("button", { name: "Save as New Version" });
    await expect(saveBtn).toBeVisible();
  });

  test("image editor has rotation buttons", async ({ page }) => {
    token = await loginViaAPI(page);

    const png = createTestPNG();
    const asset = await apiUploadAsset(token, "rotate-test.png", png, "image/png");

    await page.goto(`/assets/${asset.id}`);
    await page.waitForLoadState("networkidle");

    // Rotate buttons have title attributes
    const rotateCW = page.locator('button[title="Rotate CW"]');
    const rotateCCW = page.locator('button[title="Rotate CCW"]');
    await expect(rotateCW).toBeVisible();
    await expect(rotateCCW).toBeVisible();
  });

  test("non-previewable file shows 'Preview not available' message", async ({ page }) => {
    token = await loginViaAPI(page);

    // Upload a file with unrecognized mime type (not image/video/audio/pdf/document)
    const content = Buffer.from("fake file content");
    const asset = await apiUploadAsset(
      token,
      "report.xyz",
      content,
      "application/octet-stream"
    );

    await page.goto(`/assets/${asset.id}`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByText("Preview not available")).toBeVisible();
    await expect(page.getByText("Download the file to view it")).toBeVisible();
  });
});
