/**
 * @jest-environment node
 */

/**
 * STORY-361: Tests for Google OAuth proxy routes.
 *
 * Covers:
 *   GET /api/auth/google       — initiate proxy  (AC1)
 *   GET /api/auth/google/callback — callback proxy (AC2)
 *   force-dynamic export                          (AC3)
 */

import { NextRequest } from "next/server";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockGetRefreshedToken = jest.fn();
jest.mock("../../lib/serverAuth", () => ({
  getRefreshedToken: (...args: unknown[]) => mockGetRefreshedToken(...args),
}));

global.fetch = jest.fn();

process.env.BACKEND_URL = "http://test-backend:8000";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeRequest(path: string, method = "GET"): NextRequest {
  return new NextRequest(`http://localhost:3000${path}`, { method });
}

function mockRedirectResponse(location: string, status = 302) {
  return {
    ok: false,
    status,
    headers: {
      get: (h: string) => (h.toLowerCase() === "location" ? location : null),
    },
  };
}

// ---------------------------------------------------------------------------
// GET /api/auth/google — initiate proxy
// ---------------------------------------------------------------------------

describe("GET /api/auth/google", () => {
  let GET: (req: NextRequest) => Promise<Response>;

  beforeAll(async () => {
    const mod = await import("@/app/api/auth/google/route");
    GET = mod.GET;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.BACKEND_URL = "http://test-backend:8000";
  });

  // AC3: force-dynamic
  it("exports dynamic = 'force-dynamic'", async () => {
    const mod = await import("@/app/api/auth/google/route");
    expect(mod.dynamic).toBe("force-dynamic");
  });

  it("returns 503 when BACKEND_URL is not configured", async () => {
    delete process.env.BACKEND_URL;
    const response = await GET(makeRequest("/api/auth/google?redirect=/buscar"));
    expect(response.status).toBe(503);
    const data = await response.json();
    expect(data.message).toContain("configurado");
  });

  it("redirects to /login when user has no auth token", async () => {
    mockGetRefreshedToken.mockResolvedValueOnce(null);
    const response = await GET(makeRequest("/api/auth/google?redirect=/buscar"));
    expect(response.status).toBe(307);
    const location = response.headers.get("location") || "";
    expect(location).toContain("/login");
    expect(location).toContain("redirect=%2Fbuscar");
  });

  it("proxies redirect param and relays backend 302 to Google", async () => {
    const googleConsentUrl =
      "https://accounts.google.com/o/oauth2/auth?client_id=xxx&scope=spreadsheets";
    mockGetRefreshedToken.mockResolvedValueOnce("valid-token");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockRedirectResponse(googleConsentUrl)
    );

    const response = await GET(
      makeRequest("/api/auth/google?redirect=/dashboard")
    );

    // Should relay the Google consent URL
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(googleConsentUrl);

    // Should have called backend with auth and redirect
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/auth/google?redirect=%2Fdashboard"),
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer valid-token" }),
        redirect: "manual",
      })
    );
  });

  it("defaults redirect to /buscar when not provided", async () => {
    mockGetRefreshedToken.mockResolvedValueOnce("valid-token");
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockRedirectResponse("https://accounts.google.com/o/oauth2/auth")
    );

    await GET(makeRequest("/api/auth/google"));

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("redirect=%2Fbuscar"),
      expect.anything()
    );
  });

  it("redirects to origin path with error on backend failure", async () => {
    mockGetRefreshedToken.mockResolvedValueOnce("valid-token");
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      headers: { get: () => null },
    });

    const response = await GET(
      makeRequest("/api/auth/google?redirect=/buscar")
    );

    expect(response.status).toBe(307);
    const location = response.headers.get("location") || "";
    expect(location).toContain("error=oauth_init_failed");
  });

  it("redirects with error on network failure", async () => {
    mockGetRefreshedToken.mockResolvedValueOnce("valid-token");
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Connection refused")
    );

    const response = await GET(
      makeRequest("/api/auth/google?redirect=/buscar")
    );

    expect(response.status).toBe(307);
    const location = response.headers.get("location") || "";
    expect(location).toContain("error=oauth_network_error");
  });
});

// ---------------------------------------------------------------------------
// GET /api/auth/google/callback — callback proxy
// ---------------------------------------------------------------------------

describe("GET /api/auth/google/callback", () => {
  let GET: (req: NextRequest) => Promise<Response>;

  beforeAll(async () => {
    const mod = await import("@/app/api/auth/google/callback/route");
    GET = mod.GET;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.BACKEND_URL = "http://test-backend:8000";
  });

  // AC3: force-dynamic
  it("exports dynamic = 'force-dynamic'", async () => {
    const mod = await import("@/app/api/auth/google/callback/route");
    expect(mod.dynamic).toBe("force-dynamic");
  });

  it("returns 503 when BACKEND_URL is not configured", async () => {
    delete process.env.BACKEND_URL;
    const response = await GET(
      makeRequest("/api/auth/google/callback?code=abc&state=xyz")
    );
    expect(response.status).toBe(503);
    const data = await response.json();
    expect(data.message).toContain("configurado");
  });

  it("forwards code and state params and relays backend redirect", async () => {
    const frontendRedirect = "http://smartlic.tech/buscar?google_oauth=success";
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockRedirectResponse(frontendRedirect)
    );

    const response = await GET(
      makeRequest("/api/auth/google/callback?code=4/auth-code&state=nonce123")
    );

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(frontendRedirect);

    // Verify backend was called with correct params
    const fetchUrl = (global.fetch as jest.Mock).mock.calls[0][0] as string;
    expect(fetchUrl).toContain("code=4%2Fauth-code");
    expect(fetchUrl).toContain("state=nonce123");
    expect(fetchUrl).toContain("test-backend:8000/api/auth/google/callback");
  });

  it("forwards error param when user denies OAuth", async () => {
    const errorRedirect = "http://smartlic.tech/buscar?error=oauth_denied";
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockRedirectResponse(errorRedirect)
    );

    const response = await GET(
      makeRequest(
        "/api/auth/google/callback?error=access_denied&state=nonce123"
      )
    );

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(errorRedirect);

    const fetchUrl = (global.fetch as jest.Mock).mock.calls[0][0] as string;
    expect(fetchUrl).toContain("error=access_denied");
  });

  it("redirects to /buscar with error on backend failure", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      headers: { get: () => null },
    });

    const response = await GET(
      makeRequest("/api/auth/google/callback?code=abc&state=xyz")
    );

    expect(response.status).toBe(307);
    const location = response.headers.get("location") || "";
    expect(location).toContain("error=oauth_callback_failed");
  });

  it("redirects with error on network failure", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Connection refused")
    );

    const response = await GET(
      makeRequest("/api/auth/google/callback?code=abc&state=xyz")
    );

    expect(response.status).toBe(307);
    const location = response.headers.get("location") || "";
    expect(location).toContain("error=oauth_network_error");
  });
});
