import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  apiUploadAsset,
  apiDeleteAsset,
  createTestPNG,
  cleanupTestData,
} from "./helpers/api-helpers";

const TEST_FILENAME = "e2e-comments-test.png";

test.describe("Comments on Assets", () => {
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

  test("comments tab shows empty state initially", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.waitForLoadState("networkidle");

    // Wait for asset to load, then click Comments tab
    await expect(page.locator("h1")).toBeVisible({ timeout: 10000 });
    await page.locator("button").filter({ hasText: "Comments" }).click();

    // Empty state message
    await expect(
      page.getByText("No comments yet. Start the conversation.")
    ).toBeVisible();
  });

  test("comment textarea is visible with placeholder", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Comments" }).click();

    await expect(
      page.locator("textarea[placeholder='Add a comment...']")
    ).toBeVisible();
  });

  test("add a comment and see it in the thread", async ({ page }) => {
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Comments" }).click();

    const commentText = `E2E test comment ${Date.now()}`;

    // Type the comment
    const textarea = page.locator("textarea[placeholder='Add a comment...']");
    await textarea.fill(commentText);

    // Click the send button (icon button adjacent to textarea)
    const sendBtn = textarea.locator("..").locator("..").locator("button").first();
    await sendBtn.click();

    // Comment should appear in the thread
    await expect(page.getByText(commentText)).toBeVisible({ timeout: 10000 });
  });

  test("reply button is visible on comments", async ({ page }) => {
    // First ensure there is at least one comment
    await page.goto(`/assets/${assetId}`);
    await page.locator("button").filter({ hasText: "Comments" }).click();

    // Wait for comments to load — there should be at least one from the previous test
    // (tests within a describe run sequentially by default in Playwright)
    await page.waitForTimeout(1000);

    // If no comment exists yet, add one
    const hasComments = await page.getByRole("button", { name: "Reply" }).count();
    if (hasComments === 0) {
      const textarea = page.locator("textarea[placeholder='Add a comment...']");
      await textarea.fill("Comment for reply test");
      const sendBtn = textarea.locator("..").locator("..").locator("button").first();
      await sendBtn.click();
      await expect(page.getByText("Comment for reply test")).toBeVisible({ timeout: 10000 });
    }

    // Reply button should be visible on at least one comment
    await expect(page.getByRole("button", { name: "Reply" }).first()).toBeVisible();
  });
});
