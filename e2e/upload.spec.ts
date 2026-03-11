import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  cleanupTestData,
  apiLogin,
} from "./helpers/api-helpers";

test.describe("File Upload", () => {
  let token: string;

  test.beforeEach(async ({ page }) => {
    token = await loginViaAPI(page);
  });

  test.afterAll(async () => {
    const data = await apiLogin();
    await cleanupTestData(data.access_token);
  });

  test("upload page shows heading and description", async ({ page }) => {
    await page.goto("/upload");
    await expect(
      page.getByRole("heading", { name: "Upload", level: 1 })
    ).toBeVisible();
    await expect(
      page.getByText("Upload files to your asset library")
    ).toBeVisible();
  });

  test("dropzone area is visible with instruction text", async ({ page }) => {
    await page.goto("/upload");
    await expect(
      page.getByText("Drag files here or click to browse")
    ).toBeVisible();
  });

  test("shows accepted file types", async ({ page }) => {
    await page.goto("/upload");
    await expect(
      page.getByText("Images, videos, audio, and documents")
    ).toBeVisible();
  });

  test("uploading a file shows progress and completes", async ({ page }) => {
    await page.goto("/upload");

    // Trigger the file chooser by clicking the dropzone
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.getByText("Drag files here or click to browse").click();
    const fileChooser = await fileChooserPromise;

    // Create a minimal valid PNG (1x1 red pixel)
    const testFilename = `test-upload-${Date.now()}.png`;
    const pngBuffer = Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
      "base64"
    );

    await fileChooser.setFiles({
      name: testFilename,
      mimeType: "image/png",
      buffer: pngBuffer,
    });

    // "Uploads" section heading should appear
    await expect(
      page.getByText("Uploads", { exact: true })
    ).toBeVisible();

    // The filename should be displayed
    await expect(page.getByText(testFilename)).toBeVisible();

    // Upload should complete with "Done" status
    await expect(page.getByText("Done")).toBeVisible({ timeout: 15000 });
  });

  test("uploads section heading only appears after a file is added", async ({ page }) => {
    await page.goto("/upload");

    // Before uploading, "Uploads" heading should not be visible
    await expect(
      page.getByText("Uploads", { exact: true })
    ).not.toBeVisible();

    // Upload a file via the hidden input
    const fileInput = page.locator("input[type='file']");
    await fileInput.setInputFiles({
      name: "verify-heading.png",
      mimeType: "image/png",
      buffer: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        "base64"
      ),
    });

    // Now the "Uploads" heading should be visible
    await expect(
      page.getByText("Uploads", { exact: true })
    ).toBeVisible();
  });
});
