/**
 * @jest-environment node
 */
/**
 * CRIT-048: SSE Proxy Pipe Failure Regression Tests.
 *
 * AC2: Structured logging with upstream_status and upstream_error
 * AC6: Controlled pipe catches mid-stream errors and emits SSE error event
 * AC7: MAX_SSE_RETRIES increased from 1 to 2 (total 3 attempts)
 */

import { NextRequest } from "next/server";

const originalFetch = global.fetch;

describe("CRIT-048: SSE Proxy Pipe Failure Fix", () => {
  const BACKEND_URL = "http://backend:8000";

  beforeEach(() => {
    process.env.BACKEND_URL = BACKEND_URL;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
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
  // AC7: MAX_SSE_RETRIES is now 2 (total 3 attempts)
  // --------------------------------------------------------------------------

  it("AC7: retries up to 2 times (3 total attempts) before 504", async () => {
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
    const response = await GET(makeRequest("test-3-attempts"));

    expect(response.status).toBe(504);
    expect(callCount).toBe(3); // 1 original + 2 retries
  });

  it("AC7: succeeds on third attempt after two failures", async () => {
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
      if (callCount <= 2) {
        return Promise.reject(bodyTimeoutError);
      }
      return Promise.resolve({
        ok: true,
        body: mockBody,
        status: 200,
      });
    });

    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const GET = await getHandler();
    const response = await GET(makeRequest("test-succeed-3rd"));

    expect(response.status).toBe(200);
    expect(callCount).toBe(3);
  });

  // --------------------------------------------------------------------------
  // AC2: Structured logging with upstream_status and upstream_error
  // --------------------------------------------------------------------------

  it("AC2: logs upstream_status and upstream_error on non-ok response", async () => {
    const errorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      body: null,
    });

    const GET = await getHandler();
    const response = await GET(makeRequest("test-upstream-log", "token123"));

    expect(response.status).toBe(502);

    // Find the CRIT-048 upstream error log
    const upstreamLogs = errorSpy.mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("CRIT-048") &&
        call[0].includes("Upstream error")
    );
    expect(upstreamLogs.length).toBeGreaterThanOrEqual(1);

    // Verify structured JSON contains upstream fields
    const logJson = upstreamLogs[0][1];
    const parsed = JSON.parse(logJson);
    expect(parsed.upstream_status).toBe(502);
    expect(parsed.upstream_error).toBe("Bad Gateway");
    expect(parsed.search_id).toBe("test-upstream-log");

    errorSpy.mockRestore();
  });

  // --------------------------------------------------------------------------
  // AC6: Controlled pipe catches mid-stream errors
  // --------------------------------------------------------------------------

  it("AC6: pipe failure during streaming emits SSE error event", async () => {
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    // Create a body stream that fails mid-read
    const mockBody = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode('data: {"stage":"fetching","progress":10}\n\n')
        );
        // Simulate upstream disconnect
        controller.error(new Error("terminated"));
      },
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
      status: 200,
    });

    const GET = await getHandler();
    const response = await GET(makeRequest("test-pipe-error-48"));

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("text/event-stream");

    // Read the response body to get the SSE events
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let fullText = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        fullText += decoder.decode(value, { stream: true });
      }
    } catch {
      // Stream might error — that's expected in some environments
    }

    // Should contain the SSE error event with retry hint
    // Note: the first chunk may or may not be delivered depending on
    // ReadableStream timing — the key assertion is the error event
    expect(fullText).toContain("event: error");
    expect(fullText).toContain("retry: 5000");
    expect(fullText).toContain("upstream_error");
  });

  it("AC6: pipe failure logs structured error with upstream details", async () => {
    const errorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});

    const mockBody = new ReadableStream({
      start(controller) {
        controller.error(new Error("failed to pipe response"));
      },
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
      status: 200,
    });

    const GET = await getHandler();
    const response = await GET(makeRequest("test-pipe-log-48"));

    // Read response to trigger the pipe
    const reader = response.body!.getReader();
    try {
      while (true) {
        const { done } = await reader.read();
        if (done) break;
      }
    } catch {
      // Expected
    }

    // Verify structured logging
    const pipeErrorLogs = errorSpy.mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("CRIT-048") &&
        call[0].includes("Pipe failure")
    );
    expect(pipeErrorLogs.length).toBeGreaterThanOrEqual(1);

    const logJson = pipeErrorLogs[0][1];
    const parsed = JSON.parse(logJson);
    expect(parsed.upstream_status).toBe(200);
    expect(parsed.search_id).toBe("test-pipe-log-48");
    expect(parsed.error_type).toBeDefined();

    errorSpy.mockRestore();
  });

  // --------------------------------------------------------------------------
  // AC6: Successful stream piping still works
  // --------------------------------------------------------------------------

  it("AC6: successful stream pipes data correctly through controlled pipe", async () => {
    jest.spyOn(console, "log").mockImplementation(() => {});

    const encoder = new TextEncoder();
    const chunks = [
      'data: {"stage":"fetching","progress":10}\n\n',
      'data: {"stage":"complete","progress":100}\n\n',
    ];

    let chunkIndex = 0;
    const mockBody = new ReadableStream({
      pull(controller) {
        if (chunkIndex < chunks.length) {
          controller.enqueue(encoder.encode(chunks[chunkIndex++]));
        } else {
          controller.close();
        }
      },
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
      status: 200,
    });

    const GET = await getHandler();
    const response = await GET(makeRequest("test-normal-pipe"));

    expect(response.status).toBe(200);

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let fullText = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
    }

    expect(fullText).toContain("fetching");
    expect(fullText).toContain("complete");
    // Should NOT contain error events
    expect(fullText).not.toContain("event: error");
  });
});
