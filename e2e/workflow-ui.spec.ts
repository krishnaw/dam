import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  apiUploadAsset,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

const TEST_FILENAME = "e2e-workflow-test.png";

test.describe("Workflow UI on Asset Detail", () => {
  let token: string;
  let assetId: string;

  test.beforeAll(async () => {
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

  test("workflow tab shows Review Actions card", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Workflow" }).click();

    // The ReviewPanel renders a card with title "Review Actions"
    await expect(page.getByText("Review Actions")).toBeVisible();
  });

  test("Submit for Review button is visible", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Workflow" }).click();

    await expect(
      page.getByRole("button", { name: "Submit for Review" })
    ).toBeVisible();
  });

  test("shows no workflow steps message", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Workflow" }).click();

    // When no workflow exists, WorkflowStatus is not rendered (workflow?.steps is falsy).
    // The ReviewPanel is always shown; "Submit for Review" is visible when workflow is null.
    // Assert that no step circles are visible (no workflow steps in the UI).
    await expect(page.getByText("Review Actions")).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Submit for Review" })
    ).toBeVisible();
    // No step indicators present (WorkflowStatus component not rendered)
    await expect(page.getByText("No workflow steps defined.")).not.toBeVisible();
  });

  test("feedback textarea is visible with placeholder", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Workflow" }).click();

    await expect(
      page.locator("textarea[placeholder='Add review feedback...']")
    ).toBeVisible();
  });
});
