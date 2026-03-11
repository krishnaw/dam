import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  cleanupTestData,
} from "./helpers/api-helpers";

let token: string;

test.describe("Notifications - Bell and Panel", () => {
  test.beforeEach(async ({ page }) => {
    token = await loginViaAPI(page);
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test.afterEach(async () => {
    try {
      await cleanupTestData(token);
    } catch {
      // Ignore cleanup errors
    }
  });

  test("notification bell icon is visible in the header", async ({ page }) => {
    // The NotificationBell renders a ghost Button with Bell icon inside the header
    const header = page.locator("header");
    const bellButton = header.locator("button").filter({
      has: page.locator("svg.lucide-bell"),
    });
    await expect(bellButton).toBeVisible();
  });

  test("clicking bell opens notification panel", async ({ page }) => {
    const header = page.locator("header");
    const bellButton = header.locator("button").filter({
      has: page.locator("svg.lucide-bell"),
    });
    await bellButton.click();

    // Panel should appear with "Notifications" heading
    const heading = page.locator("h3").filter({ hasText: "Notifications" });
    await expect(heading).toBeVisible();
  });

  test("panel shows 'Notifications' heading", async ({ page }) => {
    const header = page.locator("header");
    const bellButton = header.locator("button").filter({
      has: page.locator("svg.lucide-bell"),
    });
    await bellButton.click();

    // Use h3 to avoid matching other elements that contain "Notifications" text
    const heading = page.locator("h3").filter({ hasText: "Notifications" });
    await expect(heading).toBeVisible();
  });

  test("empty state shows 'No notifications'", async ({ page }) => {
    const header = page.locator("header");
    const bellButton = header.locator("button").filter({
      has: page.locator("svg.lucide-bell"),
    });
    await bellButton.click();

    await expect(page.getByText("No notifications")).toBeVisible();
  });
});
