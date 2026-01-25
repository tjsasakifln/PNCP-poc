/**
 * @jest-environment node
 */
import { POST } from "@/app/api/buscar/route";
import { NextRequest } from "next/server";

// Mock fetch globally
global.fetch = jest.fn();

describe("POST /api/buscar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it("should validate missing UFs", async () => {
    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
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

    // Verify backend was called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/buscar"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" }
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

  it("should handle network errors", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Network error")
    );

    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.message).toBe("Erro interno do servidor");
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

  it("should schedule cache clearing after 10 minutes", async () => {
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
      body: JSON.stringify({
        ufs: ["SC"],
        data_inicial: "2026-01-01",
        data_final: "2026-01-07"
      })
    });

    await POST(request);

    // Verify setTimeout was called with 10 minutes (600000ms)
    expect(setTimeoutSpy).toHaveBeenCalledWith(
      expect.any(Function),
      10 * 60 * 1000
    );

    setTimeoutSpy.mockRestore();
  });

  it("should use NEXT_PUBLIC_BACKEND_URL from environment", async () => {
    const originalEnv = process.env.NEXT_PUBLIC_BACKEND_URL;
    process.env.NEXT_PUBLIC_BACKEND_URL = "http://custom:9000";

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
    process.env.NEXT_PUBLIC_BACKEND_URL = originalEnv;
  });

  it("should handle invalid UFs type", async () => {
    const request = new NextRequest("http://localhost:3000/api/buscar", {
      method: "POST",
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
