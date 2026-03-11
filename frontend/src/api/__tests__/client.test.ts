import { describe, it, expect, beforeAll, beforeEach, vi } from "vitest";
import { apiClient } from "@/api/client";
import { useAuthStore } from "@/stores/authStore";

// ── types ─────────────────────────────────────────────────────────────────────

type RequestConfig = {
  headers: Record<string, string>;
  url?: string;
};

type AxiosError = {
  config?: { url?: string };
  response?: { status: number };
};

// ── location mock ─────────────────────────────────────────────────────────────
//
// jsdom's window.location.href is non-configurable once the page is created, so
// we replace the entire window.location object once before any tests run.

const mockLocation = { href: "" };

beforeAll(() => {
  Object.defineProperty(window, "location", {
    configurable: true,
    value: mockLocation,
    writable: true,
  });
});

// ── helpers ───────────────────────────────────────────────────────────────────

/**
 * Pull interceptor callbacks directly from the live axios instance.
 * axios stores them in `.interceptors.{request,response}.handlers`.
 */
function getInterceptors() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const client = apiClient as any;
  const reqHandler = client.interceptors.request.handlers[0];
  const resHandler = client.interceptors.response.handlers[0];
  return {
    requestFulfilled: reqHandler.fulfilled as (cfg: RequestConfig) => RequestConfig,
    responseFulfilled: resHandler.fulfilled as (res: unknown) => unknown,
    responseRejected: resHandler.rejected as (err: AxiosError) => Promise<never>,
  };
}

/** Restore authStore and localStorage state between tests. */
function resetAuth() {
  localStorage.clear();
  useAuthStore.setState({ token: null, user: null });
}

// ── tests ─────────────────────────────────────────────────────────────────────

describe("apiClient", () => {
  // A single logout mock shared across the suite.
  // We patch useAuthStore.getState so the interceptor always gets this mock.
  const logoutMock = vi.fn();

  beforeEach(() => {
    resetAuth();
    mockLocation.href = "";
    logoutMock.mockClear();

    // Make getState() return our controlled logout mock while keeping
    // token reads working through the real store.
    vi.spyOn(useAuthStore, "getState").mockImplementation(() => ({
      ...useAuthStore.getState.wrappedStore?.getState?.() ?? { token: null, user: null },
      token: useAuthStore.getState["_realToken"] as string | null ?? null,
      user: null,
      setAuth: vi.fn(),
      logout: logoutMock,
    }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. Base URL
  it("is created with baseURL /api", () => {
    expect(apiClient.defaults.baseURL).toBe("/api");
  });

  // 2. Request interceptor — token present
  it("request interceptor attaches Authorization header when token is set", () => {
    // The request interceptor reads token via useAuthStore.getState().token.
    // Override the mock to return a token for this test.
    vi.mocked(useAuthStore.getState).mockReturnValue({
      token: "test-token-abc",
      user: null,
      setAuth: vi.fn(),
      logout: logoutMock,
    });

    const { requestFulfilled } = getInterceptors();
    const config: RequestConfig = { headers: {} };
    const result = requestFulfilled(config);

    expect(result.headers.Authorization).toBe("Bearer test-token-abc");
  });

  // 3. Request interceptor — no token
  it("request interceptor does NOT add Authorization header when no token", () => {
    vi.mocked(useAuthStore.getState).mockReturnValue({
      token: null,
      user: null,
      setAuth: vi.fn(),
      logout: logoutMock,
    });

    const { requestFulfilled } = getInterceptors();
    const config: RequestConfig = { headers: {} };
    const result = requestFulfilled(config);

    expect(result.headers.Authorization).toBeUndefined();
  });

  // 4. Response interceptor — pass-through on success
  it("response interceptor passes successful responses through unchanged", () => {
    const { responseFulfilled } = getInterceptors();
    const fakeResponse = { status: 200, data: { id: 1 } };

    expect(responseFulfilled(fakeResponse)).toBe(fakeResponse);
  });

  // 5. Response interceptor — 401 on non-auth endpoint → logout + redirect
  it("response interceptor calls logout and redirects to /login on 401 for non-auth endpoints", async () => {
    const { responseRejected } = getInterceptors();
    const error: AxiosError = {
      config: { url: "/assets/" },
      response: { status: 401 },
    };

    await responseRejected(error).catch(() => {});

    expect(logoutMock).toHaveBeenCalledOnce();
    expect(mockLocation.href).toBe("/login");
  });

  // 6. Response interceptor — 401 on /auth/ endpoint → NO logout, NO redirect
  it("response interceptor does NOT logout on 401 for /auth/ endpoints", async () => {
    const { responseRejected } = getInterceptors();
    const error: AxiosError = {
      config: { url: "/auth/login" },
      response: { status: 401 },
    };

    await responseRejected(error).catch(() => {});

    expect(logoutMock).not.toHaveBeenCalled();
    expect(mockLocation.href).toBe("");
  });

  // 7. Response interceptor — non-401 error re-rejected without side effects
  it("response interceptor re-rejects non-401 errors without calling logout", async () => {
    const { responseRejected } = getInterceptors();
    const error: AxiosError = {
      config: { url: "/assets/" },
      response: { status: 500 },
    };

    await expect(responseRejected(error)).rejects.toBe(error);
    expect(logoutMock).not.toHaveBeenCalled();
  });

  // 8. Response interceptor — missing config (no url) still triggers logout on 401
  it("response interceptor handles missing config.url and still logs out on 401", async () => {
    const { responseRejected } = getInterceptors();
    const error: AxiosError = {
      config: undefined,
      response: { status: 401 },
    };

    await responseRejected(error).catch(() => {});

    expect(logoutMock).toHaveBeenCalledOnce();
    expect(mockLocation.href).toBe("/login");
  });
});
