import { test, expect } from "@playwright/test";
import { loginViaAPI } from "./helpers/api-helpers";

test.describe("App Navigation & Layout", () => {
  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page);
  });

  test.describe("Sidebar navigation links", () => {
    test("sidebar shows all navigation links", async ({ page }) => {
      await page.goto("/");
      const nav = page.locator("aside nav");

      await expect(nav.getByText("Library")).toBeVisible();
      await expect(nav.getByText("Collections")).toBeVisible();
      await expect(nav.getByText("Upload")).toBeVisible();
      await expect(nav.getByText("Search")).toBeVisible();
      // Settings is only visible to admin role — may or may not appear
      // depending on test user's role, so we don't assert it here
    });

    test("sidebar shows DAM logo text", async ({ page }) => {
      await page.goto("/");
      await expect(page.locator("aside").getByText("DAM")).toBeVisible();
    });
  });

  test.describe("Navigation routing", () => {
    test("clicking Library link navigates to root", async ({ page }) => {
      await page.goto("/collections");
      await page.waitForURL("**/collections", { timeout: 10000 });

      const nav = page.locator("aside nav");
      await nav.getByText("Library").click();
      await page.waitForURL("/", { timeout: 10000 });
      await expect(
        page.getByRole("heading", { name: "Library" })
      ).toBeVisible();
    });

    test("clicking Collections link navigates correctly", async ({ page }) => {
      await page.goto("/");
      const nav = page.locator("aside nav");
      await nav.getByText("Collections").click();
      await page.waitForURL("**/collections", { timeout: 10000 });
      await expect(
        page.getByRole("heading", { name: "Collections" })
      ).toBeVisible();
    });

    test("clicking Upload link navigates correctly", async ({ page }) => {
      await page.goto("/");
      const nav = page.locator("aside nav");
      await nav.getByText("Upload").click();
      await page.waitForURL("**/upload", { timeout: 10000 });
      await expect(
        page.getByRole("heading", { name: "Upload" })
      ).toBeVisible();
    });

    test("clicking Search link navigates correctly", async ({ page }) => {
      await page.goto("/");
      const nav = page.locator("aside nav");
      await nav.getByText("Search").click();
      await page.waitForURL("**/search", { timeout: 10000 });
      await expect(
        page.getByRole("heading", { name: "Search" })
      ).toBeVisible();
    });
  });

  test.describe("Active link highlighting", () => {
    test("Library link is active on root page", async ({ page }) => {
      await page.goto("/");
      // NavLink with end={true} at "/" gets bg-sidebar-accent when active
      const libraryLink = page.locator("aside nav a[href='/']");
      await expect(libraryLink).toHaveClass(/bg-sidebar-accent/);
    });

    test("Collections link is active on collections page", async ({
      page,
    }) => {
      await page.goto("/collections");
      const collectionsLink = page.locator(
        "aside nav a[href='/collections']"
      );
      await expect(collectionsLink).toHaveClass(/bg-sidebar-accent/);
    });
  });

  test.describe("Sidebar collapse/expand", () => {
    test("sidebar collapses when chevron button is clicked", async ({
      page,
    }) => {
      await page.goto("/");

      // DAM text and nav labels should be visible
      await expect(page.locator("aside").getByText("DAM")).toBeVisible();
      await expect(
        page.locator("aside nav").getByText("Library")
      ).toBeVisible();

      // Click the collapse button (the only button in the aside header)
      // The button toggles between ChevronLeft (expanded) and ChevronRight (collapsed)
      const collapseBtn = page.locator("aside button").first();
      await collapseBtn.click();

      // DAM text and labels should be hidden after collapse
      await expect(
        page.locator("aside").getByText("DAM")
      ).not.toBeVisible();
      await expect(
        page.locator("aside nav").getByText("Library")
      ).not.toBeVisible();

      // Wait for CSS transition (duration-300 = 300ms) then check width
      await page.waitForTimeout(500);
      const aside = page.locator("aside");
      const box = await aside.boundingBox();
      expect(box).toBeTruthy();
      expect(box!.width).toBeLessThanOrEqual(80);
    });

    test("collapsed sidebar expands when chevron button is clicked", async ({
      page,
    }) => {
      await page.goto("/");

      // Collapse first using the only button in the aside header
      const collapseBtn = page.locator("aside button").first();
      await collapseBtn.click();
      await expect(
        page.locator("aside").getByText("DAM")
      ).not.toBeVisible();

      // Expand: same button now shows ChevronRight, click it again
      const expandBtn = page.locator("aside button").first();
      await expandBtn.click();

      // DAM text and labels should be visible again
      await expect(page.locator("aside").getByText("DAM")).toBeVisible();
      await expect(
        page.locator("aside nav").getByText("Library")
      ).toBeVisible();
    });
  });

  test.describe("Header", () => {
    test("header search bar is visible on all pages", async ({ page }) => {
      await page.goto("/");
      await expect(
        page.locator("header input[placeholder='Search assets...']")
      ).toBeVisible();

      await page.goto("/collections");
      await expect(
        page.locator("header input[placeholder='Search assets...']")
      ).toBeVisible();
    });

    test("header search navigates to search page with query", async ({
      page,
    }) => {
      await page.goto("/");
      const searchInput = page.locator(
        "header input[placeholder='Search assets...']"
      );
      await searchInput.fill("test query");
      await searchInput.press("Enter");

      await page.waitForURL(/\/search\?q=test%20query/, { timeout: 10000 });
    });

    test("header shows user avatar", async ({ page }) => {
      await page.goto("/");
      // Avatar with AvatarFallback should be visible in header
      const avatar = page
        .locator("header")
        .locator("[class*='avatar'], [class*='Avatar']")
        .first();
      await expect(avatar).toBeVisible();
    });

    test("user dropdown shows Profile, Settings, and Logout", async ({
      page,
    }) => {
      await page.goto("/");

      // Open the avatar dropdown
      await page
        .locator("header")
        .locator("[class*='avatar'], [class*='Avatar']")
        .first()
        .click();

      await expect(
        page.getByRole("menuitem", { name: "Profile" })
      ).toBeVisible();
      await expect(
        page.getByRole("menuitem", { name: "Settings" })
      ).toBeVisible();
      await expect(
        page.getByRole("menuitem", { name: "Logout" })
      ).toBeVisible();
    });
  });
});
