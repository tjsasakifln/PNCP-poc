/**
 * STORY-301: API proxy route tests for /api/alerts
 *
 * Tests the Next.js API route handlers that proxy requests to the backend.
 * Since Next.js route handlers use NextRequest/NextResponse which require
 * the Web API Request class unavailable in jsdom, we mock next/server.
 */

// ---------------------------------------------------------------------------
// Mock next/server before anything imports it
// ---------------------------------------------------------------------------

const mockJsonResponse = jest.fn();

jest.mock("next/server", () => {
  class MockNextResponse {
    status: number;
    body: unknown;

    constructor(body: unknown, init?: { status?: number }) {
      this.body = body;
      this.status = init?.status || 200;
    }

    async json() {
      return this.body;
    }

    static json(body: unknown, init?: { status?: number }) {
      const resp = new MockNextResponse(body, init);
      mockJsonResponse(body, init);
      return resp;
    }
  }

  return {
    NextRequest: jest.fn(),
    NextResponse: MockNextResponse,
  };
});

// Mock proxy-error-handler
jest.mock("../lib/proxy-error-handler", () => ({
  sanitizeProxyError: jest.fn(() => null),
  sanitizeNetworkError: jest.fn(() => {
    const { NextResponse } = require("next/server");
    return NextResponse.json(
      { message: "Servico temporariamente indisponivel" },
      { status: 503 },
    );
  }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createMockRequest(options: {
  method?: string;
  authorization?: string;
  body?: Record<string, unknown>;
  correlationId?: string;
}): any {
  const headers = new Map<string, string>();
  if (options.authorization) {
    headers.set("authorization", options.authorization);
  }
  if (options.correlationId) {
    headers.set("X-Correlation-ID", options.correlationId);
  }

  return {
    method: options.method || "GET",
    headers: {
      get: (key: string) => headers.get(key) ?? null,
    },
    json: async () => options.body || {},
  };
}

// ---------------------------------------------------------------------------
// Tests — /api/alerts (GET + POST)
// ---------------------------------------------------------------------------

describe("/api/alerts route handlers", () => {
  const originalEnv = process.env;
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv, BACKEND_URL: "http://localhost:8000" };
    originalFetch = global.fetch;
    global.fetch = jest.fn();
    mockJsonResponse.mockClear();
  });

  afterEach(() => {
    process.env = originalEnv;
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  describe("GET /api/alerts", () => {
    it("proxies GET request to backend and returns alerts", async () => {
      const mockAlerts = [
        { id: "1", name: "Alert 1", active: true },
        { id: "2", name: "Alert 2", active: false },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockAlerts,
        text: async () => JSON.stringify(mockAlerts),
        headers: { get: () => "application/json" },
      });

      const { GET } = await import("../app/api/alerts/route");
      const request = createMockRequest({
        authorization: "Bearer test-token-123",
      });

      const response = await GET(request);
      const data = await response.json();

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/alerts",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test-token-123",
          }),
        }),
      );
      expect(data).toEqual(mockAlerts);
    });

    it("returns 401 when no authorization header", async () => {
      const { GET } = await import("../app/api/alerts/route");
      const request = createMockRequest({});

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.message).toBe("Autenticacao necessaria.");
    });

    it("returns 503 when BACKEND_URL is not configured", async () => {
      delete process.env.BACKEND_URL;

      const { GET } = await import("../app/api/alerts/route");
      const request = createMockRequest({
        authorization: "Bearer test-token",
      });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data.message).toBe("Servico temporariamente indisponivel");
    });
  });

  describe("POST /api/alerts", () => {
    it("proxies POST request to backend and returns 201", async () => {
      const newAlert = { id: "new-1", name: "New Alert" };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => newAlert,
        text: async () => JSON.stringify(newAlert),
        headers: { get: () => "application/json" },
      });

      const { POST } = await import("../app/api/alerts/route");
      const request = createMockRequest({
        method: "POST",
        authorization: "Bearer test-token-123",
        body: { name: "New Alert", filters: { setor: "informatica" } },
      });

      const response = await POST(request);
      const data = await response.json();

      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/v1/alerts",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer test-token-123",
            "Content-Type": "application/json",
          }),
        }),
      );
      expect(response.status).toBe(201);
      expect(data).toEqual(newAlert);
    });

    it("returns 401 for POST without auth header", async () => {
      const { POST } = await import("../app/api/alerts/route");
      const request = createMockRequest({
        method: "POST",
        body: { name: "Test" },
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.message).toBe("Autenticacao necessaria.");
    });

    it("returns 503 for POST when BACKEND_URL is missing", async () => {
      delete process.env.BACKEND_URL;

      const { POST } = await import("../app/api/alerts/route");
      const request = createMockRequest({
        method: "POST",
        authorization: "Bearer test-token",
        body: { name: "Test" },
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(503);
      expect(data.message).toBe("Servico temporariamente indisponivel");
    });
  });
});
