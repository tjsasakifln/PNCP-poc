/**
 * @jest-environment node
 */
/**
 * CRIT-012 AC11: Frontend proxy SSE error handling tests.
 *
 * Tests that buscar-progress/route.ts correctly handles:
 * - BodyTimeoutError → 504
 * - TypeError: terminated → 504
 * - AbortError → 499
 * - Structured logging (AC7)
 */

import { NextRequest } from "next/server";

// Store original fetch
const originalFetch = global.fetch;

describe("CRIT-012: SSE Proxy Error Handling", () => {
  const BACKEND_URL = "http://backend:8000";

  beforeEach(() => {
    process.env.BACKEND_URL = BACKEND_URL;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  // Helper to create NextRequest with search_id
  function makeRequest(searchId: string, token?: string): NextRequest {
    let url = `http://localhost/api/buscar-progress?search_id=${searchId}`;
    if (token) url += `&token=${token}`;
    return new NextRequest(new URL(url));
  }

  // Dynamically import the route handler (after mocks are set up)
  async function getHandler() {
    // Clear module cache to pick up fresh mocks
    const routePath = require.resolve(
      "../../app/api/buscar-progress/route"
    );
    delete require.cache[routePath];
    const mod = await import("../../app/api/buscar-progress/route");
    return mod.GET;
  }

  // --------------------------------------------------------------------------
  // AC6: BodyTimeoutError → 504
  // --------------------------------------------------------------------------

  it("AC6/AC11: returns 504 for BodyTimeoutError", async () => {
    const bodyTimeoutError = new Error("body timeout");
    bodyTimeoutError.name = "BodyTimeoutError";
    global.fetch = jest.fn().mockRejectedValue(bodyTimeoutError);

    const GET = await getHandler();
    const response = await GET(makeRequest("test-bt-123", "token-abc"));

    expect(response.status).toBe(504);
    const body = await response.json();
    expect(body.error_type).toBe("BodyTimeoutError");
    expect(body.search_id).toBe("test-bt-123");
    expect(body.error).toBe("SSE stream timeout");
    expect(body.elapsed_ms).toBeGreaterThanOrEqual(0);
  });

  // --------------------------------------------------------------------------
  // AC6: TypeError: terminated → 504
  // --------------------------------------------------------------------------

  it("AC6/AC11: returns 504 for TypeError: terminated", async () => {
    const terminatedError = new TypeError("terminated");
    global.fetch = jest.fn().mockRejectedValue(terminatedError);

    const GET = await getHandler();
    const response = await GET(makeRequest("test-term-456", "token-def"));

    expect(response.status).toBe(504);
    const body = await response.json();
    expect(body.error_type).toBe("TypeError");
    expect(body.search_id).toBe("test-term-456");
  });

  // --------------------------------------------------------------------------
  // AC5: AbortError → 499
  // --------------------------------------------------------------------------

  it("AC5: returns 499 for AbortError (client disconnect)", async () => {
    const abortError = new Error("The operation was aborted");
    abortError.name = "AbortError";
    global.fetch = jest.fn().mockRejectedValue(abortError);

    const GET = await getHandler();
    const response = await GET(makeRequest("test-abort-789"));

    expect(response.status).toBe(499);
    const text = await response.text();
    expect(text).toBe("Client disconnected");
  });

  // --------------------------------------------------------------------------
  // AC7: Structured logging
  // --------------------------------------------------------------------------

  it("AC7: logs structured error data on failure", async () => {
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const error = new Error("body timeout");
    error.name = "BodyTimeoutError";
    global.fetch = jest.fn().mockRejectedValue(error);

    const GET = await getHandler();
    await GET(makeRequest("test-log-101"));

    expect(consoleSpy).toHaveBeenCalledWith(
      "SSE proxy error:",
      expect.stringContaining('"error_type":"BodyTimeoutError"')
    );
    expect(consoleSpy).toHaveBeenCalledWith(
      "SSE proxy error:",
      expect.stringContaining('"search_id":"test-log-101"')
    );

    consoleSpy.mockRestore();
  });

  // --------------------------------------------------------------------------
  // Generic errors → 502
  // --------------------------------------------------------------------------

  it("returns 502 for generic connection errors", async () => {
    const networkError = new Error("ECONNREFUSED");
    global.fetch = jest.fn().mockRejectedValue(networkError);

    const GET = await getHandler();
    const response = await GET(makeRequest("test-generic"));

    expect(response.status).toBe(502);
    const text = await response.text();
    expect(text).toBe("Failed to connect to backend");
  });

  // --------------------------------------------------------------------------
  // Happy path: proxies SSE stream
  // --------------------------------------------------------------------------

  it("proxies SSE stream with correct headers", async () => {
    const mockBody = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            'data: {"stage":"complete","progress":100}\n\n'
          )
        );
        controller.close();
      },
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
      status: 200,
    });

    const GET = await getHandler();
    const response = await GET(makeRequest("test-happy", "valid-token"));

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("text/event-stream");
    expect(response.headers.get("Cache-Control")).toBe("no-cache, no-transform");
    expect(response.headers.get("X-Accel-Buffering")).toBe("no");
  });

  // --------------------------------------------------------------------------
  // Validation
  // --------------------------------------------------------------------------

  it("returns 400 when search_id is missing", async () => {
    const GET = await getHandler();
    const request = new NextRequest(
      new URL("http://localhost/api/buscar-progress")
    );
    const response = await GET(request);
    expect(response.status).toBe(400);
  });

  it("returns 503 when BACKEND_URL not configured", async () => {
    delete process.env.BACKEND_URL;
    const GET = await getHandler();
    const response = await GET(makeRequest("test-no-backend"));
    expect(response.status).toBe(503);
  });
});
