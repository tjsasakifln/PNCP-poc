/**
 * TD-006 AC3 / TD-008: Isolated test suite for usePipeline hook (SWR-based).
 *
 * SWR auto-fetches on mount, so mocks must account for the initial GET calls
 * (one for items, one for alerts).
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import React from "react";
import { SWRConfig } from "swr";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockSession = { access_token: "pipeline-test-token" };

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: mockSession }),
}));

jest.mock("../../lib/error-messages", () => ({
  getUserFriendlyError: (e: unknown) =>
    e instanceof Error ? e.message : String(e),
  getMessageFromErrorCode: jest.fn(() => null),
  isTransientError: jest.fn(() => false),
  getRetryMessage: jest.fn(() => "Tentando novamente..."),
  getHumanizedError: jest.fn(() => ({
    message: "Erro",
    actionLabel: "Tentar novamente",
    tone: "blue" as const,
    suggestReduceScope: false,
  })),
  getErrorMessage: jest.fn((e: any) => (typeof e === "string" ? e : "Erro")),
  DEFAULT_ERROR_MESSAGE: "Ocorreu um erro inesperado.",
  TRANSIENT_HTTP_CODES: new Set([502, 503, 504]),
  translateAuthError: jest.fn((e: string) => e),
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import { usePipeline } from "../../hooks/usePipeline";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makePipelineItem(overrides: Record<string, unknown> = {}) {
  return {
    id: "item-1",
    user_id: "user-1",
    pncp_id: "pncp-123",
    objeto: "Teste de licitacao",
    orgao: "Orgao X",
    uf: "SP",
    valor_estimado: 50000,
    data_encerramento: "2026-04-01",
    link_pncp: "https://pncp.gov.br/123",
    stage: "descoberta",
    notes: null,
    created_at: "2026-03-01T00:00:00Z",
    updated_at: "2026-03-01T00:00:00Z",
    version: 1,
    ...overrides,
  };
}

/** Default empty response for SWR auto-fetch */
const emptyOk = () => ({
  ok: true,
  json: async () => ({ items: [], total: 0 }),
});

/** Wrap hook with isolated SWR cache */
function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(
    SWRConfig,
    { value: { provider: () => new Map(), dedupingInterval: 0, errorRetryCount: 0 } },
    children
  );
}

beforeEach(() => {
  mockFetch.mockReset();
  // Default: SWR auto-fetches items + alerts on mount
  mockFetch.mockImplementation((url: string) => {
    if (typeof url === "string" && url.includes("pipeline")) {
      return Promise.resolve(emptyOk());
    }
    return Promise.resolve(emptyOk());
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("usePipeline (isolated)", () => {
  // 1. fetchItems success
  test("fetchItems loads items and total", async () => {
    const items = [makePipelineItem(), makePipelineItem({ id: "item-2" })];
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("limit=200") && !url.includes("_path")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items, total: 2 }),
        });
      }
      return Promise.resolve(emptyOk());
    });

    const { result } = renderHook(() => usePipeline(), { wrapper });

    await waitFor(() => {
      expect(result.current.items).toHaveLength(2);
    });
    expect(result.current.total).toBe(2);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  // 2. fetchItems with stage filter
  test("fetchItems passes stage parameter", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });

    await act(async () => {
      await result.current.fetchItems("analise");
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("stage=analise"),
      expect.any(Object)
    );
  });

  // 3. fetchItems error via SWR
  test("fetchItems sets error on failure", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("limit=200") && !url.includes("_path")) {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: async () => ({ detail: "Internal server error" }),
        });
      }
      return Promise.resolve(emptyOk());
    });

    const { result } = renderHook(() => usePipeline(), { wrapper });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
    expect(result.current.items).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  // 4. addItem success
  test("addItem adds new item to state", async () => {
    const newItem = makePipelineItem({ id: "new-1" });

    const { result } = renderHook(() => usePipeline(), { wrapper });

    // Wait for initial SWR fetch to complete
    await waitFor(() => expect(result.current.loading).toBe(false));

    // Mock the POST call, then the SWR revalidation GET that follows
    mockFetch
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: async () => newItem,
        })
      )
      .mockImplementation((url: string) => {
        if (typeof url === "string" && url.includes("limit=200") && !url.includes("_path")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [newItem], total: 1 }),
          });
        }
        return Promise.resolve(emptyOk());
      });

    let returned: any;
    await act(async () => {
      returned = await result.current.addItem({
        pncp_id: "pncp-new",
        objeto: "Nova licitacao",
        orgao: "Orgao Y",
        uf: "RJ",
        valor_estimado: 100000,
        data_encerramento: "2026-05-01",
        link_pncp: null,
        stage: "descoberta",
        notes: null,
      });
    });

    expect(returned).toEqual(newItem);
    await waitFor(() => expect(result.current.items).toContainEqual(newItem));
    expect(mockFetch).toHaveBeenCalledWith("/api/pipeline", expect.objectContaining({
      method: "POST",
    }));
  });

  // 5. addItem 409 conflict (duplicate)
  test("addItem throws on 409 conflict", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 409,
        json: async () => ({ detail: "Duplicate" }),
      })
    );

    await expect(
      act(async () => {
        await result.current.addItem({
          pncp_id: "pncp-dup",
          objeto: "Duplicata",
          orgao: null,
          uf: null,
          valor_estimado: null,
          data_encerramento: null,
          link_pncp: null,
          stage: "descoberta",
          notes: null,
        });
      })
    ).rejects.toThrow("Esta licita\u00e7\u00e3o j\u00e1 est\u00e1 no seu pipeline.");
  });

  // 6. addItem 403 pipeline limit exceeded
  test("addItem throws with pipeline limit info on 403", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 403,
        json: async () => ({
          detail: {
            error_code: "PIPELINE_LIMIT_EXCEEDED",
            limit: 50,
            current: 50,
            message: "Limit reached",
          },
        }),
      })
    );

    let caughtError: any;
    try {
      await act(async () => {
        await result.current.addItem({
          pncp_id: "pncp-over",
          objeto: "Over limit",
          orgao: null,
          uf: null,
          valor_estimado: null,
          data_encerramento: null,
          link_pncp: null,
          stage: "descoberta",
          notes: null,
        });
      });
    } catch (err) {
      caughtError = err;
    }

    expect(caughtError).toBeDefined();
    expect(caughtError.isPipelineLimitExceeded).toBe(true);
    expect(caughtError.limit).toBe(50);
    expect(caughtError.current).toBe(50);
  });

  // 7. updateItem success
  test("updateItem updates item in state", async () => {
    const item1 = makePipelineItem({ id: "item-1", stage: "descoberta", version: 1 });
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("limit=200") && !url.includes("_path")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [item1], total: 1 }),
        });
      }
      return Promise.resolve(emptyOk());
    });

    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.items).toHaveLength(1));

    const updatedItem = { ...item1, stage: "analise", version: 2 };
    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: async () => updatedItem,
      })
    );

    let returned: any;
    await act(async () => {
      returned = await result.current.updateItem("item-1", { stage: "analise" as any });
    });

    expect(returned.stage).toBe("analise");
  });

  // 8. updateItem 409 version conflict
  test("updateItem throws on 409 version conflict", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 409,
        json: async () => ({ detail: "Version mismatch" }),
      })
    );

    let caughtError: any;
    try {
      await act(async () => {
        await result.current.updateItem("item-1", { stage: "analise" as any });
      });
    } catch (err) {
      caughtError = err;
    }

    expect(caughtError).toBeDefined();
    expect(caughtError.isConflict).toBe(true);
  });

  // 9. removeItem success
  test("removeItem removes item from state", async () => {
    const item1 = makePipelineItem({ id: "item-1" });
    const item2 = makePipelineItem({ id: "item-2" });
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("limit=200") && !url.includes("_path")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [item1, item2], total: 2 }),
        });
      }
      return Promise.resolve(emptyOk());
    });

    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.items).toHaveLength(2));

    // Mock the DELETE call, then the SWR revalidation GET that follows
    mockFetch
      .mockImplementationOnce(() =>
        Promise.resolve({ ok: true, json: async () => ({}) })
      )
      .mockImplementation((url: string) => {
        if (typeof url === "string" && url.includes("limit=200") && !url.includes("_path")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [item2], total: 1 }),
          });
        }
        return Promise.resolve(emptyOk());
      });

    await act(async () => {
      await result.current.removeItem("item-1");
    });

    await waitFor(() => expect(result.current.items).toHaveLength(1));
    expect(result.current.items[0].id).toBe("item-2");
  });

  // 10. removeItem error
  test("removeItem throws on failure", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockFetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Delete failed" }),
      })
    );

    await expect(
      act(async () => {
        await result.current.removeItem("item-1");
      })
    ).rejects.toThrow("Delete failed");
  });

  // 11. fetchAlerts loads via SWR
  test("fetchAlerts loads alerts", async () => {
    const alertItem = makePipelineItem({ id: "alert-1", stage: "analise" });
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("_path")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ items: [alertItem] }),
        });
      }
      return Promise.resolve(emptyOk());
    });

    const { result } = renderHook(() => usePipeline(), { wrapper });

    await waitFor(() => {
      expect(result.current.alerts).toHaveLength(1);
    });
    expect(result.current.alerts[0].id).toBe("alert-1");
  });

  // 12. fetchAlerts silent fail
  test("fetchAlerts silently fails on error", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("_path")) {
        return Promise.reject(new Error("Network error"));
      }
      return Promise.resolve(emptyOk());
    });

    const { result } = renderHook(() => usePipeline(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.alerts).toEqual([]);
  });

  // 13. Auth headers
  test("sends Authorization header with session token", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer pipeline-test-token",
        }),
      })
    );
  });

  // 14. Loading transitions to false after fetch
  test("loading becomes false after fetch completes", async () => {
    const { result } = renderHook(() => usePipeline(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.items).toEqual([]);
  });
});
