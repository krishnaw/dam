import { test, expect } from "@playwright/test";
import { loginViaAPI, TEST_USER } from "./helpers/api-helpers";

test.describe("Authentication", () => {
  test.describe("Login page UI", () => {
    test("displays sign-in form with email and password fields", async ({
      page,
    }) => {
      await page.goto("/login");

      // Card title says "Sign In"
      await expect(page.getByText("Sign In").first()).toBeVisible();

      // Email and password inputs are present
      await expect(page.locator("#email")).toBeVisible();
      await expect(page.locator("#password")).toBeVisible();

      // Submit button
      await expect(
        page.getByRole("button", { name: "Sign In" })
      ).toBeVisible();

      // Toggle to register
      await expect(
        page.getByRole("button", { name: "Register" })
      ).toBeVisible();
    });

    test("toggles to register form and back", async ({ page }) => {
      await page.goto("/login");

      // Switch to register mode
      await page.getByRole("button", { name: "Register" }).click();
      await expect(page.getByText("Create Account").first()).toBeVisible();
      await expect(page.locator("#fullName")).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Create Account" })
      ).toBeVisible();

      // Switch back to sign in
      await page.getByRole("button", { name: "Sign in" }).click();
      await expect(page.getByText("Sign In").first()).toBeVisible();
      await expect(page.locator("#fullName")).not.toBeVisible();
    });
  });

  test.describe("Login flow (real API)", () => {
    test("successful login redirects to library page", async ({ page }) => {
      await page.goto("/login");
      await page.locator("#email").fill(TEST_USER.email);
      await page.locator("#password").fill(TEST_USER.password);
      await page.getByRole("button", { name: "Sign In" }).click();

      // Should redirect to root (library page)
      await page.waitForURL("/", { timeout: 15000 });
      await expect(page.getByRole("heading", { name: "Library" })).toBeVisible();
    });

    test("failed login with wrong credentials shows error", async ({
      page,
    }) => {
      await page.goto("/login");
      await page.locator("#email").fill("wrong@example.com");
      await page.locator("#password").fill("wrongpassword");
      await page.getByRole("button", { name: "Sign In" }).click();

      // Error message appears in .text-destructive
      await expect(page.locator(".text-destructive")).toBeVisible({
        timeout: 10000,
      });
    });

    test("failed login with wrong password shows error", async ({ page }) => {
      await page.goto("/login");
      await page.locator("#email").fill(TEST_USER.email);
      await page.locator("#password").fill("definitelywrongpassword");
      await page.getByRole("button", { name: "Sign In" }).click();

      await expect(page.locator(".text-destructive")).toBeVisible({
        timeout: 10000,
      });
    });
  });

  test.describe("Logout (real API)", () => {
    test("logout clears token and redirects to login", async ({ page }) => {
      // Log in via API for speed, then navigate to library
      await loginViaAPI(page);
      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Library" })).toBeVisible({ timeout: 10000 });

      // Open user dropdown by clicking the avatar fallback in the header
      await page
        .locator("header")
        .locator("[class*='avatar'], [class*='Avatar']")
        .first()
        .click();

      // Click Logout in the dropdown menu
      await page.getByRole("menuitem", { name: "Logout" }).click();

      // Should redirect to login page
      await page.waitForURL("**/login", { timeout: 10000 });
      await expect(page.getByText("Sign In").first()).toBeVisible();

      // Token should be cleared from localStorage
      const token = await page.evaluate(() =>
        localStorage.getItem("dam_token")
      );
      expect(token).toBeNull();
    });
  });

  test.describe("Auth guard", () => {
    test("unauthenticated access to root redirects to login", async ({
      page,
    }) => {
      // Navigate to login first so we can clear localStorage
      await page.goto("/login");
      await page.evaluate(() => {
        localStorage.removeItem("dam_token");
        localStorage.removeItem("dam_user");
      });

      // Try to access protected route
      await page.goto("/");
      await page.waitForURL("**/login", { timeout: 10000 });
      await expect(page.getByText("Sign In").first()).toBeVisible();
    });

    test("unauthenticated access to collections redirects to login", async ({
      page,
    }) => {
      await page.goto("/login");
      await page.evaluate(() => {
        localStorage.removeItem("dam_token");
        localStorage.removeItem("dam_user");
      });

      await page.goto("/collections");
      await page.waitForURL("**/login", { timeout: 10000 });
      await expect(page.getByText("Sign In").first()).toBeVisible();
    });

    test("unauthenticated access to upload redirects to login", async ({
      page,
    }) => {
      await page.goto("/login");
      await page.evaluate(() => {
        localStorage.removeItem("dam_token");
        localStorage.removeItem("dam_user");
      });

      await page.goto("/upload");
      await page.waitForURL("**/login", { timeout: 10000 });
      await expect(page.getByText("Sign In").first()).toBeVisible();
    });
  });
});
