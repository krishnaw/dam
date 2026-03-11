/**
 * E2E test helpers for real API interactions.
 * No mocking — all data is created via the actual backend API
 * and cleaned up after tests.
 */
import { Page, expect } from "@playwright/test";

const API_BASE = "http://localhost:8000";

// ── Test user credentials ──────────────────────────────────────────
export const TEST_USER = {
  email: "e2etest@example.com",
  password: "testpass123",
  full_name: "E2E Test User",
};

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
    created_at: string;
  };
}

// ── Auth helpers ───────────────────────────────────────────────────

/** Register a new user via API. Returns token + user. */
export async function apiRegister(
  email: string,
  password: string,
  fullName: string
): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Register failed (${res.status}): ${text}`);
  }
  return res.json();
}

/** Login via API. Returns token + user. */
export async function apiLogin(
  email: string = TEST_USER.email,
  password: string = TEST_USER.password
): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Login failed (${res.status}): ${text}`);
  }
  return res.json();
}

/** Set up browser auth state by logging in and setting localStorage. */
export async function loginViaUI(page: Page): Promise<void> {
  await page.goto("/login");
  await page.locator("#email").fill(TEST_USER.email);
  await page.locator("#password").fill(TEST_USER.password);
  await page.getByRole("button", { name: "Sign In" }).click();
  await page.waitForURL("/", { timeout: 10000 });
}

/** Set auth token in localStorage (skip UI login for faster tests). */
export async function loginViaAPI(page: Page): Promise<string> {
  const data = await apiLogin();
  // Go to login page first to get access to localStorage
  await page.goto("/login");
  await page.evaluate(
    ({ token }) => {
      localStorage.setItem("dam_token", token);
    },
    { token: data.access_token }
  );
  // Reload so the Zustand store re-initializes with the token from localStorage
  await page.reload({ waitUntil: "networkidle" });
  return data.access_token;
}

// ── Asset helpers ──────────────────────────────────────────────────

/** Upload a test file via API. Returns asset data. */
export async function apiUploadAsset(
  token: string,
  filename: string,
  content: Buffer | Uint8Array,
  contentType: string = "image/png"
): Promise<any> {
  const formData = new FormData();
  const blob = new Blob([content], { type: contentType });
  formData.append("file", blob, filename);

  const res = await fetch(`${API_BASE}/api/assets/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload failed (${res.status}): ${text}`);
  }
  return res.json();
}

/** Delete an asset via API. */
export async function apiDeleteAsset(
  token: string,
  assetId: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/assets/${assetId}?hard=true`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  // 204 = success, 404 = already gone — both OK for cleanup
  if (!res.ok && res.status !== 404) {
    const text = await res.text();
    throw new Error(`Delete asset failed (${res.status}): ${text}`);
  }
}

/** List assets via API. */
export async function apiListAssets(
  token: string
): Promise<{ items: any[]; total: number }> {
  const res = await fetch(`${API_BASE}/api/assets/?page=1&page_size=50`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`List assets failed: ${res.status}`);
  return res.json();
}

// ── Collection helpers ─────────────────────────────────────────────

/** Create a collection via API. */
export async function apiCreateCollection(
  token: string,
  name: string,
  description?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/collections/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Create collection failed (${res.status}): ${text}`);
  }
  return res.json();
}

/** Delete a collection via API. */
export async function apiDeleteCollection(
  token: string,
  collectionId: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/collections/${collectionId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 404) {
    throw new Error(`Delete collection failed: ${res.status}`);
  }
}

/** Add asset to collection. */
export async function apiAddAssetToCollection(
  token: string,
  collectionId: string,
  assetId: string
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/api/collections/${collectionId}/assets`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ asset_id: assetId }),
    }
  );
  if (!res.ok) throw new Error(`Add to collection failed: ${res.status}`);
}

// ── Comment helpers ────────────────────────────────────────────────

/** Add a comment to an asset. */
export async function apiAddComment(
  token: string,
  assetId: string,
  content: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/assets/${assetId}/comments`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Add comment failed (${res.status}): ${text}`);
  }
  return res.json();
}

// ── Search helpers ─────────────────────────────────────────────────

/** Search assets via keyword API. */
export async function apiSearch(
  token: string,
  query: string
): Promise<any> {
  const res = await fetch(
    `${API_BASE}/api/search/?q=${encodeURIComponent(query)}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

// ── Utility: generate a 1x1 PNG buffer ─────────────────────────────

/** Generates a minimal valid PNG file as a Buffer. */
export function createTestPNG(): Buffer {
  // 1x1 red pixel PNG
  return Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
    "base64"
  );
}

/** Generates a minimal test PDF. */
export function createTestPDF(): Buffer {
  const content = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer << /Size 4 /Root 1 0 R >>
startxref
206
%%EOF`;
  return Buffer.from(content);
}

// ── Cleanup helpers ────────────────────────────────────────────────

/** Delete all test assets and collections for cleanup. */
export async function cleanupTestData(token: string): Promise<void> {
  try {
    // Delete all assets
    const assets = await apiListAssets(token);
    for (const asset of assets.items) {
      await apiDeleteAsset(token, asset.id);
    }
  } catch {
    // Ignore cleanup errors
  }
  try {
    // Delete all collections
    const res = await fetch(`${API_BASE}/api/collections/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const collections = await res.json();
      for (const col of collections) {
        await apiDeleteCollection(token, col.id);
      }
    }
  } catch {
    // Ignore cleanup errors
  }
}
