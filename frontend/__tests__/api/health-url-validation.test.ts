/**
 * @jest-environment node
 */
// CRIT-006: BACKEND_URL validation tests
import { GET } from "@/app/api/health/route";

// Mock fetch
global.fetch = jest.fn();

describe("CRIT-006: BACKEND_URL validation", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    jest.clearAllMocks();
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  test("AC5: DNS failure returns backend_url_valid: false", async () => {
    process.env.BACKEND_URL = "https://nonexistent.invalid";
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error("getaddrinfo ENOTFOUND nonexistent.invalid")
    );

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend_url_valid).toBe(false);
    expect(body.backend).toBe("unreachable");
    expect(body.warning).toContain("BACKEND_URL may be misconfigured");
    expect(body.warning).toContain("dns_resolution_failed");
  });

  test("AC5: ENOTFOUND error returns backend_url_valid: false", async () => {
    process.env.BACKEND_URL = "https://bad-domain.test";
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error("ENOTFOUND bad-domain.test")
    );

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend_url_valid).toBe(false);
    expect(body.backend).toBe("unreachable");
  });

  test("AC5: Connection refused returns backend_url_valid: false", async () => {
    process.env.BACKEND_URL = "https://localhost:9999";
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error("connect ECONNREFUSED 127.0.0.1:9999")
    );

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend_url_valid).toBe(false);
    expect(body.backend).toBe("unreachable");
    expect(body.warning).toContain("connection_refused");
  });

  test("AC6: timeout returns backend_url_valid: true", async () => {
    process.env.BACKEND_URL = "https://slow-backend.example.com";
    const abortError = new Error("AbortError: The operation was aborted");
    abortError.name = "AbortError";
    (global.fetch as jest.Mock).mockRejectedValue(abortError);

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend_url_valid).toBe(true);
    expect(body.backend).toBe("unreachable");
    expect(body.warning).toBeUndefined(); // No warning for temporary failures
  });

  test("AC6: ETIMEDOUT returns backend_url_valid: true", async () => {
    process.env.BACKEND_URL = "https://slow-backend.example.com";
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error("ETIMEDOUT: Connection timed out")
    );

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend_url_valid).toBe(true);
    expect(body.backend).toBe("unreachable");
  });

  test("AC6: unknown errors default to backend_url_valid: true", async () => {
    process.env.BACKEND_URL = "https://backend.example.com";
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error("Some other network error")
    );

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend_url_valid).toBe(true);
    expect(body.backend).toBe("unreachable");
  });

  test("AC7: backend healthy does not include backend_url_valid", async () => {
    process.env.BACKEND_URL = "https://good-backend.example.com";
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: "healthy", ready: true }),
    });

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend).toBe("healthy");
    expect(body.backend_url_valid).toBeUndefined();
  });

  test("AC7: backend unhealthy does not include backend_url_valid", async () => {
    process.env.BACKEND_URL = "https://good-backend.example.com";
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
    });

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.backend).toBe("unhealthy");
    expect(body.backend_url_valid).toBeUndefined();
  });

  test("AC4: DNS failure logs with CRITICAL severity", async () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    process.env.BACKEND_URL = "https://nonexistent.invalid";
    (global.fetch as jest.Mock).mockRejectedValue(
      new Error("getaddrinfo ENOTFOUND nonexistent.invalid")
    );

    await GET();

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("[HEALTH] CRITICAL: BACKEND_URL")
    );
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("dns_resolution_failed")
    );

    consoleErrorSpy.mockRestore();
  });

  test("AC4: timeout logs with WARNING severity", async () => {
    const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

    process.env.BACKEND_URL = "https://slow-backend.example.com";
    const abortError = new Error("AbortError: The operation was aborted");
    (global.fetch as jest.Mock).mockRejectedValue(abortError);

    await GET();

    expect(consoleWarnSpy).toHaveBeenCalledWith(
      expect.stringContaining("[HEALTH] WARNING: BACKEND_URL")
    );
    expect(consoleWarnSpy).toHaveBeenCalledWith(
      expect.stringContaining("timeout")
    );

    consoleWarnSpy.mockRestore();
  });
});
