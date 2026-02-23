/**
 * @jest-environment node
 */
import { POST } from "@/app/api/buscar/route";
import { NextRequest } from "next/server";

// Mock fetch globally
global.fetch = jest.fn();

// Mock authentication token
const mockAuthToken = "Bearer mock-jwt-token-12345";

// Set BACKEND_URL for all tests
process.env.BACKEND_URL = "http://test-backend:8000";

/** Helper: create a mock fetch response with text() support */
function mockErrorResponse(status: number, detail?: string) {
  const body = detail !== undefined ? { detail } : {};
  const bodyStr = JSON.stringify(body);
  return {
    ok: false,
    status,
    text: async () => bodyStr,
    headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
  };
}

describe("POST /api/buscar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    try { jest.runOnlyPendingTimers(); } catch { /* already using real timers */ }
    jest.useRealTimers();
  });

  it("should validate missing UFs", async () => {
    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.message).toBe("Selecione pelo menos um estado");
  });

  it("should validate empty UFs array", async () => {
    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: [],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.message).toBe("Selecione pelo menos um estado");
  });

  it("should validate missing dates", async () => {
    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"]
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.message).toBe("Período obrigatório");
  });

  it("should proxy valid request to backend", async () => {
    const mockBackendResponse = {
      resumo: {
        resumo_executivo: "Test summary",
        total_oportunidades: 5,
        valor_total: 100000,
        destaques: ["Test"],
        distribuicao_uf: { SC: 5 },
        alerta_urgencia: null
      },
      excel_base64: Buffer.from("test").toString("base64")
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockBackendResponse),
      json: async () => mockBackendResponse
    });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.resumo).toEqual(mockBackendResponse.resumo);
    expect(data.download_id).toBeDefined();
    expect(typeof data.download_id).toBe("string");

    // Verify backend was called with auth header
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/buscar"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          "Authorization": mockAuthToken
        })
      })
    );
  });

  it("should handle backend errors", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(500, "Backend error")
    );

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.message).toBe("Backend error");
  });

  it("should handle network errors after all retries", async () => {
    jest.useRealTimers(); // Use real timers for retry delays
    // GTM-INFRA-002: Network errors are retried MAX_RETRIES=3 times before failing
    (global.fetch as jest.Mock)
      .mockRejectedValueOnce(new Error("Network error"))
      .mockRejectedValueOnce(new Error("Network error"))
      .mockRejectedValueOnce(new Error("Network error"));

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(503);
    // Should have tried 3 times (MAX_RETRIES=3)
    expect(global.fetch).toHaveBeenCalledTimes(3);
  }, 15000);

  it("GTM-INFRA-002 AC6/T3: should retry on 502 (expanded retryable statuses)", async () => {
    jest.useRealTimers();
    // GTM-INFRA-002 AC6: 502 IS now retryable (Railway deploy errors)
    // Use structured error body so sanitizer passes it through
    const errorBody = JSON.stringify({ detail: "PNCP temporarily down", error_code: "PNCP_UNAVAILABLE" });
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: false, status: 502,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      })
      .mockResolvedValueOnce({
        ok: false, status: 502,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      })
      .mockResolvedValueOnce({
        ok: false, status: 502,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(502);
    // Should retry 3 times (MAX_RETRIES=3)
    expect(global.fetch).toHaveBeenCalledTimes(3);
  }, 15000);

  it("should retry on 503 and fail after max retries", async () => {
    jest.useRealTimers();
    // GTM-INFRA-002: All 3 attempts return 503 (MAX_RETRIES=3)
    // Use structured error with error_code so sanitizer passes it through
    const errorBody = JSON.stringify({ detail: "Rate limited", error_code: "RATE_LIMITED" });
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: false, status: 503,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      })
      .mockResolvedValueOnce({
        ok: false, status: 503,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      })
      .mockResolvedValueOnce({
        ok: false, status: 503,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(503);
    expect(data.message).toBe("Rate limited");
    expect(global.fetch).toHaveBeenCalledTimes(3);
  }, 15000);

  // GTM-INFRA-002 T3: Proxy retries 524 (Cloudflare/Railway timeout)
  it("GTM-INFRA-002 T3: should retry on 524 (Railway timeout)", async () => {
    jest.useRealTimers();
    // 524 is now in RETRYABLE_STATUSES — must be retried like 502/503/504
    const errorBody = JSON.stringify({ detail: "Connection timed out", error_code: "TIMEOUT" });
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: false, status: 524,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      })
      .mockResolvedValueOnce({
        ok: false, status: 524,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      })
      .mockResolvedValueOnce({
        ok: false, status: 524,
        text: async () => errorBody,
        headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
      });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    // 524 is retried MAX_RETRIES=3 times (proves it's in RETRYABLE_STATUSES)
    expect(global.fetch).toHaveBeenCalledTimes(3);
    expect(response.status).toBe(524);
    expect(data.message).toBe("Connection timed out");
  }, 15000);

  it("should not retry on non-retryable errors (400, 401, 500)", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(400, "Bad request")
    );

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.message).toBe("Bad request");
    // Should only call fetch once (no retries for non-retryable errors)
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("should cache Excel buffer with download ID", async () => {
    const testBuffer = Buffer.from("test excel data");
    const mockBackendResponse = {
      resumo: {
        resumo_executivo: "Test",
        total_oportunidades: 1,
        valor_total: 50000,
        destaques: [],
        distribuicao_uf: { SC: 1 },
        alerta_urgencia: null
      },
      excel_base64: testBuffer.toString("base64")
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockBackendResponse),
      json: async () => mockBackendResponse
    });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    // Verify download ID is UUID format
    expect(data.download_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    );
  });

  it("should schedule cache clearing after 60 minutes", async () => {
    const mockBackendResponse = {
      resumo: {
        resumo_executivo: "Test",
        total_oportunidades: 1,
        valor_total: 50000,
        destaques: [],
        distribuicao_uf: { SC: 1 },
        alerta_urgencia: null
      },
      excel_base64: Buffer.from("test").toString("base64")
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockBackendResponse),
      json: async () => mockBackendResponse
    });

    const setTimeoutSpy = jest.spyOn(global, "setTimeout");

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    await POST(request);

    // GTM-FIX-029 AC19: Verify setTimeout was called with 8 minutes (480000ms)
    expect(setTimeoutSpy).toHaveBeenCalledWith(
      expect.any(Function),
      8 * 60 * 1000
    );

    setTimeoutSpy.mockRestore();
  });

  it("should use BACKEND_URL from environment", async () => {
    const originalEnv = process.env.BACKEND_URL;
    process.env.BACKEND_URL = "http://custom:9000";

    const mockBackendResponse = {
      resumo: {
        resumo_executivo: "Test",
        total_oportunidades: 1,
        valor_total: 50000,
        destaques: [],
        distribuicao_uf: { SC: 1 },
        alerta_urgencia: null
      },
      excel_base64: Buffer.from("test").toString("base64")
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => JSON.stringify(mockBackendResponse),
      json: async () => mockBackendResponse
    });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    await POST(request);

    expect(global.fetch).toHaveBeenCalledWith(
      "http://custom:9000/v1/buscar",
      expect.any(Object)
    );

    // Restore
    process.env.BACKEND_URL = originalEnv;
  });

  it("should handle invalid UFs type", async () => {
    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: {
        "Authorization": mockAuthToken
      },
      body: JSON.stringify({
        ufs: "SC", // Should be array
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.message).toBe("Selecione pelo menos um estado");
  });

  // CRIT-002 AC10: Contextual error message for HTTP 500
  it("should return contextual message for HTTP 500 (not generic 'Erro no backend')", async () => {
    // Empty detail triggers contextual message
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(500, "")
    );

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.message).toBe("Ocorreu um erro interno. Tente novamente em alguns segundos.");
    expect(data.message).not.toContain("Erro no backend");
  });

  // CRIT-002 AC11: Contextual error message for HTTP 502
  // GTM-INFRA-002 AC6: 502 is now retryable. With empty JSON body,
  // sanitizeProxyError detects it as non-structured and returns sanitized response.
  it("should return sanitized message for HTTP 502 with non-structured body", async () => {
    // Non-structured 502 is intercepted by sanitizer on first attempt
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false, status: 502,
      text: async () => JSON.stringify({}),
      headers: { get: (h: string) => h?.toLowerCase() === "content-type" ? "application/json" : null },
    });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(502);
    // Sanitizer intercepts non-structured 502 and returns friendly message
    expect(data.message).toBe("Nossos servidores estão sendo atualizados. Tente novamente em alguns instantes.");
    // Sanitizer returns immediately (no retries for sanitized responses)
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  // CRIT-002 AC12: All error responses include request_id
  it("should include request_id in all error responses", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(500, "Test error")
    );

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(data.request_id).toBeDefined();
    expect(typeof data.request_id).toBe("string");
    // Should be UUID format
    expect(data.request_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    // Should also be in response headers
    expect(response.headers.get("X-Request-ID")).toBe(data.request_id);
  });

  it("should include request_id in success responses", async () => {
    const mockBackendResponse = {
      resumo: {
        resumo_executivo: "Test",
        total_oportunidades: 1,
        valor_total: 50000,
        destaques: [],
        distribuicao_uf: { SC: 1 },
        alerta_urgencia: null
      },
      excel_base64: Buffer.from("test").toString("base64")
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockBackendResponse,
      text: async () => JSON.stringify(mockBackendResponse)
    });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);

    // Should have X-Request-ID header in success response
    expect(response.headers.get("X-Request-ID")).toBeDefined();
    expect(response.headers.get("X-Request-ID")).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
  });

  it("should use backend detail message when available (not contextual)", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce(
      mockErrorResponse(500, "Specific backend error message")
    );

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    // Should use backend's specific message, not generic contextual
    expect(data.message).toBe("Specific backend error message");
  });
});
