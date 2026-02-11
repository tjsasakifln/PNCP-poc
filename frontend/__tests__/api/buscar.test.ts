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
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Backend error" })
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

    expect(response.status).toBe(500);
    expect(data.message).toBe("Backend error");
  });

  it("should handle network errors after all retries", async () => {
    jest.useRealTimers(); // Use real timers for retry delays
    // Network errors are retried MAX_RETRIES=2 times before failing
    (global.fetch as jest.Mock)
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
    expect(data.message).toContain("Backend indisponível");
    // Should have tried 2 times (MAX_RETRIES=2)
    expect(global.fetch).toHaveBeenCalledTimes(2);
  }, 15000);

  it("should not retry on 502 (only 503 is retryable)", async () => {
    // 502 is NOT retryable — backend already retried PNCP internally
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: false,
        status: 502,
        json: async () => ({ detail: "PNCP unavailable" })
      });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(502);
    expect(data.message).toBe("PNCP unavailable");
    // Should only call fetch once (no retries for 502)
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("should retry on 503 and fail after max retries", async () => {
    jest.useRealTimers(); // Use real timers for retry delays
    // All 2 attempts return 503 (MAX_RETRIES=2)
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ detail: "Service unavailable" }) })
      .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ detail: "Service unavailable" }) });

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      headers: { "Authorization": mockAuthToken },
      body: JSON.stringify({ ufs: ["SC"], data_inicial: "2026-01-01", data_final: "2026-01-07" })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(503);
    expect(data.message).toBe("Service unavailable");
    expect(global.fetch).toHaveBeenCalledTimes(2);
  }, 15000);

  it("should not retry on non-retryable errors (400, 401, 500)", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Bad request" })
    });

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

    // Verify setTimeout was called with 60 minutes (3600000ms)
    expect(setTimeoutSpy).toHaveBeenCalledWith(
      expect.any(Function),
      60 * 60 * 1000
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
      "http://custom:9000/buscar",
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
});
