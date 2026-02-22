/**
 * @jest-environment node
 */
/**
 * CRIT-026: SSE Proxy resilience tests.
 *
 * AC5: Undici diagnostic logging
 * AC6: AbortSignal.timeout fallback (implicit — if undici fails, fetch still works)
 * AC7: Retry once on BodyTimeoutError before returning 504
 */

import { NextRequest } from "next/server";

const originalFetch = global.fetch;

describe("CRIT-026: SSE Proxy Retry + Observability", () => {
  const BACKEND_URL = "http://backend:8000";

  beforeEach(() => {
    process.env.BACKEND_URL = BACKEND_URL;
    jest.useFakeTimers({ advanceTimers: true });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  function makeRequest(searchId: string, token?: string): NextRequest {
    let url = `http://localhost/api/buscar-progress?search_id=${searchId}`;
    if (token) url += `&token=${token}`;
    return new NextRequest(new URL(url));
  }

  async function getHandler() {
    const routePath = require.resolve(
      "../../app/api/buscar-progress/route"
    );
    delete require.cache[routePath];
    const mod = await import("../../app/api/buscar-progress/route");
    return mod.GET;
  }

  // --------------------------------------------------------------------------
  // AC5: Undici diagnostic logging
  // --------------------------------------------------------------------------

  it("AC5: logs undici dispatcher status on each request", async () => {
    const consoleSpy = jest
      .spyOn(console, "log")
      .mockImplementation(() => {});

    const mockBody = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"stage":"complete"}\n\n')
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
    await GET(makeRequest("test-undici-log"));

    const undiciLogs = consoleSpy.mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("[SSE-PROXY]") &&
        call[0].includes("undici_dispatcher")
    );
    expect(undiciLogs.length).toBeGreaterThanOrEqual(1);

    consoleSpy.mockRestore();
  });

  // --------------------------------------------------------------------------
  // AC7: Retry once on BodyTimeoutError then succeed
  // --------------------------------------------------------------------------

  it("AC7: retries once and succeeds on second attempt", async () => {
    jest.useRealTimers(); // Need real timers for the 1s retry delay

    const bodyTimeoutError = new Error("body timeout");
    bodyTimeoutError.name = "BodyTimeoutError";

    const mockBody = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"stage":"complete"}\n\n')
        );
        controller.close();
      },
    });

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.reject(bodyTimeoutError);
      }
      return Promise.resolve({
        ok: true,
        body: mockBody,
        status: 200,
      });
    });

    const consoleSpy = jest
      .spyOn(console, "log")
      .mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-retry-success"));

    // Should succeed on retry
    expect(response.status).toBe(200);
    expect(callCount).toBe(2);

    // Should have logged a retry attempt
    const retryLogs = consoleSpy.mock.calls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].includes("Retrying")
    );
    expect(retryLogs.length).toBe(1);

    consoleSpy.mockRestore();
  });

  // --------------------------------------------------------------------------
  // AC7: Retry once on BodyTimeoutError, both fail → 504
  // --------------------------------------------------------------------------

  it("AC7: returns 504 after retry exhaustion", async () => {
    jest.useRealTimers();

    const bodyTimeoutError = new Error("body timeout");
    bodyTimeoutError.name = "BodyTimeoutError";

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      return Promise.reject(bodyTimeoutError);
    });

    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-retry-exhausted"));

    expect(response.status).toBe(504);
    expect(callCount).toBe(2); // Original + 1 retry
    const body = await response.json();
    expect(body.retries_exhausted).toBe(true);
    expect(body.error_type).toBe("BodyTimeoutError");
  });

  // --------------------------------------------------------------------------
  // AC7: TypeError terminated also triggers retry
  // --------------------------------------------------------------------------

  it("AC7: retries on TypeError: terminated", async () => {
    jest.useRealTimers();

    const terminatedError = new TypeError("terminated");

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      return Promise.reject(terminatedError);
    });

    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-retry-terminated"));

    expect(response.status).toBe(504);
    expect(callCount).toBe(2); // Original + 1 retry
  });

  // --------------------------------------------------------------------------
  // AbortError is NOT retried
  // --------------------------------------------------------------------------

  it("AbortError is not retried — returns 499 immediately", async () => {
    const abortError = new Error("The operation was aborted");
    abortError.name = "AbortError";

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      return Promise.reject(abortError);
    });

    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-abort-no-retry"));

    expect(response.status).toBe(499);
    expect(callCount).toBe(1); // No retry for AbortError
  });

  // --------------------------------------------------------------------------
  // Generic errors are NOT retried
  // --------------------------------------------------------------------------

  it("generic errors are not retried — returns 502 immediately", async () => {
    const networkError = new Error("ECONNREFUSED");

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      return Promise.reject(networkError);
    });

    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-generic-no-retry"));

    expect(response.status).toBe(502);
    expect(callCount).toBe(1); // No retry for generic errors
  });

  // --------------------------------------------------------------------------
  // AC9: Connection breadcrumb logging
  // --------------------------------------------------------------------------

  it("AC9: logs connection breadcrumb before fetch", async () => {
    const consoleSpy = jest
      .spyOn(console, "log")
      .mockImplementation(() => {});

    const mockBody = new ReadableStream({
      start(controller) {
        controller.close();
      },
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
      status: 200,
    });

    const GET = await getHandler();
    await GET(makeRequest("test-breadcrumb-123"));

    const breadcrumbLogs = consoleSpy.mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("[SSE-PROXY] Connecting") &&
        call[0].includes("test-breadcrumb-123")
    );
    expect(breadcrumbLogs.length).toBe(1);

    consoleSpy.mockRestore();
  });

  // --------------------------------------------------------------------------
  // AC7: Retry with "failed to pipe" error
  // --------------------------------------------------------------------------

  it("AC7: retries on 'failed to pipe response' error", async () => {
    jest.useRealTimers();

    const pipeError = new Error("failed to pipe response");

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      return Promise.reject(pipeError);
    });

    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-pipe-error"));

    expect(response.status).toBe(504);
    expect(callCount).toBe(2); // Original + 1 retry
  });
});
