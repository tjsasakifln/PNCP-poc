/**
 * @jest-environment node
 */
/**
 * CRIT-082 AC10: buscar proxy — Retry simplification tests.
 *
 * Verifies:
 * - MAX_RETRIES = 2 → exactly 2 fetch attempts on retryable failure (not 3)
 * - Non-retryable status (400) makes only 1 fetch attempt
 * - Proxy timeout is 60s (not 90s)
 * - Succeeds on second attempt after 502
 *
 * Pattern follows buscar-auth-refresh.test.ts (same mocks, same import style).
 */

import { NextRequest } from "next/server";

// Mock getRefreshedToken via closure so jest.mock hoisting works
const mockGetRefreshedToken = jest.fn();
jest.mock("../../lib/serverAuth", () => ({
  getRefreshedToken: (...args: unknown[]) => mockGetRefreshedToken(...args),
}));

// Mock proxy-error-handler to return null (not a special infra error)
jest.mock("../../lib/proxy-error-handler", () => ({
  sanitizeProxyError: () => null,
  sanitizeNetworkError: (error: unknown) => {
    const { NextResponse } = require("next/server");
    return NextResponse.json({ message: "Erro de conexão" }, { status: 502 });
  },
}));

// Import AFTER mocks
import { POST } from "../../app/api/buscar/route";

function makeRequest(): NextRequest {
  return new NextRequest("http://localhost:3000/api/buscar", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer test-token",
    },
    body: JSON.stringify({
      ufs: ["SP"],
      data_inicial: "2026-01-01",
      data_final: "2026-01-10",
    }),
  });
}

describe("CRIT-082 AC10: buscar proxy retry simplification", () => {
  beforeEach(() => {
    process.env.BACKEND_URL = "http://test-backend:8000";
    // getRefreshedToken returns null → route falls back to Authorization header
    mockGetRefreshedToken.mockResolvedValue(null);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // AC1: MAX_RETRIES = 2 → only 2 fetch calls (not 3) on persistent 502
  // ---------------------------------------------------------------------------

  it("AC1: makes exactly 2 fetch attempts on retryable 502 (not 3)", async () => {
    let callCount = 0;
    jest.spyOn(global, "fetch").mockImplementation(() => {
      callCount++;
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "bad gateway" }), {
          status: 502,
          headers: { "content-type": "application/json" },
        })
      );
    });

    await POST(makeRequest());

    expect(callCount).toBe(2);
  }, 10_000);

  // ---------------------------------------------------------------------------
  // AC1: 400 (non-retryable) → only 1 fetch attempt
  // ---------------------------------------------------------------------------

  it("AC1: non-retryable status 400 makes only 1 fetch attempt", async () => {
    let callCount = 0;
    jest.spyOn(global, "fetch").mockImplementation(() => {
      callCount++;
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "bad request" }), {
          status: 400,
          headers: { "content-type": "application/json" },
        })
      );
    });

    await POST(makeRequest());

    expect(callCount).toBe(1);
  });

  // ---------------------------------------------------------------------------
  // AC6: proxy timeout is 60s (not 90s)
  // ---------------------------------------------------------------------------

  it("AC6: AbortController timeout is set to 60s (60000ms)", async () => {
    const setTimeoutSpy = jest.spyOn(global, "setTimeout");

    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ licitacoes: [], total_raw: 0, total_filtrado: 0 }),
        { status: 200, headers: { "content-type": "application/json" } }
      )
    );

    await POST(makeRequest());

    const msArgs = setTimeoutSpy.mock.calls.map(([, ms]) => ms);
    expect(msArgs).toContain(60_000);
    expect(msArgs).not.toContain(90_000);
  });

  // ---------------------------------------------------------------------------
  // Succeeds on second attempt
  // ---------------------------------------------------------------------------

  it("succeeds on second attempt after 502 (returns 200)", async () => {
    let callCount = 0;
    jest.spyOn(global, "fetch").mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "bad gateway" }), {
            status: 502,
            headers: { "content-type": "application/json" },
          })
        );
      }
      return Promise.resolve(
        new Response(
          JSON.stringify({ licitacoes: [], total_raw: 0, total_filtrado: 0 }),
          { status: 200, headers: { "content-type": "application/json" } }
        )
      );
    });

    const response = await POST(makeRequest());

    expect(callCount).toBe(2);
    expect(response.status).toBe(200);
  }, 10_000);

  // ---------------------------------------------------------------------------
  // 503 is retryable
  // ---------------------------------------------------------------------------

  it("AC1: 503 is retryable → 2 fetch attempts", async () => {
    let callCount = 0;
    jest.spyOn(global, "fetch").mockImplementation(() => {
      callCount++;
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "service unavailable" }), {
          status: 503,
          headers: { "content-type": "application/json" },
        })
      );
    });

    await POST(makeRequest());

    expect(callCount).toBe(2);
  }, 10_000);

  // ---------------------------------------------------------------------------
  // Missing BACKEND_URL → 503
  // ---------------------------------------------------------------------------

  it("returns 503 when BACKEND_URL not configured", async () => {
    delete process.env.BACKEND_URL;

    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response("{}", { status: 200 })
    );

    const response = await POST(makeRequest());
    expect(response.status).toBe(503);
  });
});
