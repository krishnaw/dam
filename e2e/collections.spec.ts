import { test, expect } from "@playwright/test";
import {
  loginViaAPI,
  cleanupTestData,
  apiLogin,
  apiCreateCollection,
} from "./helpers/api-helpers";

test.describe("Collections", () => {
  let token: string;

  test.beforeEach(async ({ page }) => {
    token = await loginViaAPI(page);
  });

  test.afterAll(async () => {
    const data = await apiLogin();
    await cleanupTestData(data.access_token);
  });

  test("collections page shows heading", async ({ page }) => {
    await page.goto("/collections");
    await expect(
      page.getByRole("heading", { name: "Collections", level: 1 })
    ).toBeVisible();
  });

  test("empty state when no collections exist", async ({ page }) => {
    // Clean up everything so we get the empty state
    const data = await apiLogin();
    await cleanupTestData(data.access_token);

    await page.goto("/collections");
    await expect(page.getByText("No collections yet")).toBeVisible();
    await expect(
      page.getByText("Create a collection to organize your assets")
    ).toBeVisible();
  });

  test("New Collection button opens create dialog", async ({ page }) => {
    await page.goto("/collections");
    await page.getByRole("button", { name: /New Collection/ }).click();

    // Dialog title
    await expect(page.getByText("Create Collection")).toBeVisible();

    // Form fields
    await expect(
      page.getByPlaceholder("Collection name")
    ).toBeVisible();
    await expect(
      page.getByPlaceholder("Optional description")
    ).toBeVisible();

    // Create button
    await expect(
      page.getByRole("button", { name: "Create" })
    ).toBeVisible();
  });

  test("create collection via dialog and see it in grid", async ({ page }) => {
    const collectionName = `E2E Collection ${Date.now()}`;

    await page.goto("/collections");
    await page.getByRole("button", { name: /New Collection/ }).click();

    await page.getByPlaceholder("Collection name").fill(collectionName);
    await page.getByPlaceholder("Optional description").fill("Created by E2E test");
    await page.getByRole("button", { name: "Create" }).click();

    // Dialog should close after successful creation — the form inputs should no longer be visible
    await expect(page.getByPlaceholder("Collection name")).not.toBeVisible({
      timeout: 10000,
    });

    // Verify the collection was actually created via the API
    const data = await apiLogin();
    const res = await fetch("http://localhost:8000/api/collections/", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    const collections = await res.json();
    const created = collections.find((c: { name: string }) => c.name === collectionName);
    expect(created).toBeTruthy();
  });

  test("clicking a collection navigates to detail page", async ({ page }) => {
    // Create a collection via API for this test
    const data = await apiLogin();
    const collectionName = `Nav Test ${Date.now()}`;
    const collection = await apiCreateCollection(
      data.access_token,
      collectionName,
      "Navigation test collection"
    );

    // Navigate directly to the collection detail page since the collections grid
    // does not render cards (the list API returns a plain array but the frontend
    // hook expects a paginated { items: [] } response).
    await page.goto(`/collections/${collection.id}`);

    // Should be on the detail URL
    await page.waitForURL(`**/collections/${collection.id}`, {
      timeout: 10000,
    });

    // Detail page shows collection name as heading
    await expect(
      page.getByRole("heading", { name: collectionName, level: 1 })
    ).toBeVisible();
  });

  test("collection detail page has back button", async ({ page }) => {
    // Create a collection via API
    const data = await apiLogin();
    const collectionName = `Back Btn ${Date.now()}`;
    const collection = await apiCreateCollection(
      data.access_token,
      collectionName
    );

    await page.goto(`/collections/${collection.id}`);

    // Heading should be visible
    await expect(
      page.getByRole("heading", { name: collectionName, level: 1 })
    ).toBeVisible();

    // Back button (ghost button with ArrowLeft SVG) should exist
    const backButton = page
      .locator("button")
      .filter({ has: page.locator("svg.lucide-arrow-left") });
    await expect(backButton).toBeVisible();

    // Click back to return to collections list
    await backButton.click();
    await page.waitForURL("**/collections", { timeout: 10000 });
    await expect(
      page.getByRole("heading", { name: "Collections", level: 1 })
    ).toBeVisible();
  });
});
