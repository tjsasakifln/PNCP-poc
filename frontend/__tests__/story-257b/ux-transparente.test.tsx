/**
 * STORY-257B: Frontend UX Transparente e Resiliente
 * Tests T1-T8 for all new components and integrations
 */

// ---------------------------------------------------------------------------
// Top-level mocks for useSearch dependencies
// ---------------------------------------------------------------------------
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: { access_token: "test-token" }, loading: false }),
}));
jest.mock("../../hooks/useQuota", () => ({
  useQuota: () => ({ refresh: jest.fn() }),
}));
jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));
jest.mock("../../hooks/useSavedSearches", () => ({
  useSavedSearches: () => ({ saveNewSearch: jest.fn(), isMaxCapacity: false }),
}));
// STORY-367: useSearchProgress deleted — mock with mutable _override for T2 control
// NOTE: resetMocks:true in jest.config resets jest.fn() between tests, so we use a plain
// function with a mutable override object instead.
jest.mock("../../hooks/useSearchSSE", () => {
  const _default = {
    currentEvent: null,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    partialProgress: null,
    refreshAvailable: null,
    ufStatuses: new Map(),
    ufTotalFound: 0,
    ufAllComplete: false,
    batchProgress: null,
    isConnected: false,
  };
  return {
    useSearchSSE: () => (globalThis as any).__useSearchSSE_override ?? { ..._default },
  };
});
jest.mock("../../hooks/useSearchPolling", () => ({
  useSearchPolling: () => ({
    asProgressEvent: null,
  }),
}));
jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));
jest.mock("../../lib/error-messages", () => ({
  ...jest.requireActual("../../lib/error-messages"),
}));
jest.mock("../../lib/searchStatePersistence", () => ({
  saveSearchState: jest.fn(),
  restoreSearchState: jest.fn(() => null),
}));
jest.mock("../../lib/utils/dateDiffInDays", () => ({
  dateDiffInDays: () => 7,
}));
jest.mock("../../lib/utils/correlationId", () => ({
  getCorrelationId: () => "test-correlation-id",
  logCorrelatedRequest: jest.fn(),
}));

import { render, screen, fireEvent } from "@testing-library/react";
import { renderHook, act as hookAct } from "@testing-library/react";
import React from "react";

// ---------------------------------------------------------------------------
// T1: UfProgressGrid renders correctly with 1, 5, 27 UFs
// ---------------------------------------------------------------------------
import { UfProgressGrid } from "@/app/buscar/components/UfProgressGrid";
import type { UfStatus } from "@/app/buscar/hooks/useUfProgress";

describe("T1: UfProgressGrid rendering", () => {
  const makeStatuses = (ufs: string[], status: UfStatus["status"] = "pending"): Map<string, UfStatus> => {
    const map = new Map<string, UfStatus>();
    ufs.forEach(uf => map.set(uf, { status }));
    return map;
  };

  it("renders 1 UF correctly", () => {
    const statuses = makeStatuses(["SP"]);
    const { container } = render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);
    expect(screen.getByText("SP")).toBeInTheDocument();
    expect(container.querySelectorAll("[aria-label]")).toHaveLength(1);
  });

  it("renders 5 UFs sorted alphabetically", () => {
    const statuses = makeStatuses(["SP", "RJ", "MG", "BA", "RS"]);
    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);
    const labels = screen.getAllByText(/^(BA|MG|RJ|RS|SP)$/);
    expect(labels).toHaveLength(5);
    const texts = labels.map(el => el.textContent);
    expect(texts).toEqual(["BA", "MG", "RJ", "RS", "SP"]);
  });

  it("renders all 27 UFs", () => {
    const ALL_UFS = [
      "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
      "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
      "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    ];
    const statuses = makeStatuses(ALL_UFS);
    render(<UfProgressGrid ufStatuses={statuses} totalFound={0} />);
    ALL_UFS.forEach(uf => {
      expect(screen.getByText(uf)).toBeInTheDocument();
    });
  });

  it("displays correct status labels", () => {
    const statuses = new Map<string, UfStatus>([
      ["SP", { status: "success", count: 10 }],
      ["RJ", { status: "failed" }],
      ["MG", { status: "fetching" }],
    ]);
    render(<UfProgressGrid ufStatuses={statuses} totalFound={10} />);
    expect(screen.getByText("10 oportunidades")).toBeInTheDocument();
    expect(screen.getByText("Indisponível")).toBeInTheDocument();
    expect(screen.getByText("Consultando...")).toBeInTheDocument();
  });

  it("displays progressive counter with singular/plural", () => {
    const statuses = new Map<string, UfStatus>([
      ["SP", { status: "success", count: 1 }],
    ]);
    render(<UfProgressGrid ufStatuses={statuses} totalFound={1} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("oportunidade")).toBeInTheDocument();
  });

  it("displays recovered status with badge", () => {
    const statuses = new Map<string, UfStatus>([
      ["SP", { status: "recovered", count: 5 }],
    ]);
    render(<UfProgressGrid ufStatuses={statuses} totalFound={5} />);
    expect(screen.getByText(/Recuperado/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// T2: useUfProgress thin wrapper maps useSearchSSE return values (STORY-367)
// Dynamic SSE behavior tested in useUfProgress-reconnection.test.tsx
// ---------------------------------------------------------------------------
import { useUfProgress } from "@/app/buscar/hooks/useUfProgress";

describe("T2: useUfProgress thin wrapper mapping", () => {
  const defaultSSE = {
    currentEvent: null,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    partialProgress: null,
    refreshAvailable: null,
    ufStatuses: new Map(),
    ufTotalFound: 0,
    ufAllComplete: false,
    batchProgress: null,
    isConnected: false,
  };

  afterEach(() => {
    delete (globalThis as any).__useSearchSSE_override;
  });

  it("maps ufStatuses from useSearchSSE", () => {
    const pendingMap = new Map([
      ["SP", { status: "pending" as const }],
      ["RJ", { status: "pending" as const }],
      ["MG", { status: "pending" as const }],
    ]);
    (globalThis as any).__useSearchSSE_override = { ...defaultSSE, ufStatuses: pendingMap };

    const { result } = renderHook(() =>
      useUfProgress({ searchId: "test-1", enabled: true, selectedUfs: ["SP", "RJ", "MG"] })
    );
    expect(result.current.ufStatuses.size).toBe(3);
    expect(result.current.ufStatuses.get("SP")?.status).toBe("pending");
  });

  it("maps totalFound from useSearchSSE ufTotalFound", () => {
    const updatedMap = new Map([
      ["SP", { status: "success" as const, count: 15 }],
      ["RJ", { status: "pending" as const }],
    ]);
    (globalThis as any).__useSearchSSE_override = {
      ...defaultSSE,
      ufStatuses: updatedMap,
      ufTotalFound: 15,
    };

    const { result } = renderHook(() =>
      useUfProgress({ searchId: "test-2", enabled: true, selectedUfs: ["SP", "RJ"] })
    );
    expect(result.current.ufStatuses.get("SP")?.status).toBe("success");
    expect(result.current.ufStatuses.get("SP")?.count).toBe(15);
    expect(result.current.totalFound).toBe(15);
  });

  it("maps allComplete from useSearchSSE ufAllComplete", () => {
    (globalThis as any).__useSearchSSE_override = {
      ...defaultSSE,
      ufStatuses: new Map([
        ["SP", { status: "success" as const, count: 10 }],
        ["RJ", { status: "failed" as const }],
      ]),
      ufTotalFound: 10,
      ufAllComplete: true,
    };

    const { result } = renderHook(() =>
      useUfProgress({ searchId: "test-3", enabled: true, selectedUfs: ["SP", "RJ"] })
    );
    expect(result.current.allComplete).toBe(true);
  });

  it("maps sseDisconnected from useSearchSSE", () => {
    (globalThis as any).__useSearchSSE_override = {
      ...defaultSSE,
      sseDisconnected: true,
    };

    const { result } = renderHook(() =>
      useUfProgress({ searchId: "test-4", enabled: true, selectedUfs: ["SP"] })
    );
    expect(result.current.sseDisconnected).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// T3: Partial results prompt appears after 15s with partial data
// ---------------------------------------------------------------------------
import { PartialResultsPrompt } from "@/app/buscar/components/PartialResultsPrompt";

describe("T3: PartialResultsPrompt", () => {
  it("renders prompt with correct counts", () => {
    render(
      <PartialResultsPrompt
        totalFound={25} succeededCount={5} pendingCount={3} elapsedSeconds={20}
        onViewPartial={jest.fn()} onWaitComplete={jest.fn()} dismissed={false}
      />
    );
    expect(screen.getByText("Resultados parciais disponíveis")).toBeInTheDocument();
    expect(screen.getByText(/25/)).toBeInTheDocument();
    expect(screen.getByText(/5 estados/)).toBeInTheDocument();
    expect(screen.getByText("Ver resultados parciais")).toBeInTheDocument();
    expect(screen.getByText("Aguardar busca completa")).toBeInTheDocument();
  });

  it("returns null when dismissed", () => {
    const { container } = render(
      <PartialResultsPrompt
        totalFound={25} succeededCount={5} pendingCount={3} elapsedSeconds={20}
        onViewPartial={jest.fn()} onWaitComplete={jest.fn()} dismissed={true}
      />
    );
    expect(container.innerHTML).toBe("");
  });

  it("calls onViewPartial when button clicked", () => {
    const onViewPartial = jest.fn();
    render(
      <PartialResultsPrompt
        totalFound={25} succeededCount={5} pendingCount={3} elapsedSeconds={20}
        onViewPartial={onViewPartial} onWaitComplete={jest.fn()} dismissed={false}
      />
    );
    fireEvent.click(screen.getByText("Ver resultados parciais"));
    expect(onViewPartial).toHaveBeenCalledTimes(1);
  });

  it("calls onWaitComplete when dismiss button clicked", () => {
    const onWaitComplete = jest.fn();
    render(
      <PartialResultsPrompt
        totalFound={25} succeededCount={5} pendingCount={3} elapsedSeconds={20}
        onViewPartial={jest.fn()} onWaitComplete={onWaitComplete} dismissed={false}
      />
    );
    fireEvent.click(screen.getByText("Aguardar busca completa"));
    expect(onWaitComplete).toHaveBeenCalledTimes(1);
  });

  it("uses singular forms correctly", () => {
    render(
      <PartialResultsPrompt
        totalFound={1} succeededCount={1} pendingCount={1} elapsedSeconds={16}
        onViewPartial={jest.fn()} onWaitComplete={jest.fn()} dismissed={false}
      />
    );
    expect(screen.getByText(/1 oportunidade/)).toBeInTheDocument();
    // Both succeededCount=1 and pendingCount=1 produce "1 estado"
    const estadoElements = screen.getAllByText(/1 estado\b/);
    expect(estadoElements.length).toBeGreaterThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// T4: CacheBanner tests removed — component deprecated and deleted (STORY-284 AC6)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// T5: "Tentar atualizar" sends force_fresh: true
// ---------------------------------------------------------------------------
import { useSearch } from "@/app/buscar/hooks/useSearch";

describe("T5: force_fresh parameter", () => {
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    global.fetch = originalFetch;
  });

  it("includes force_fresh in request body when buscarForceFresh is called", async () => {
    let capturedBody: any = null;
    global.fetch = jest.fn().mockImplementation(async (url: string, options: any) => {
      if (url === "/api/buscar" && options?.method === "POST") {
        capturedBody = JSON.parse(options.body);
        return {
          ok: true,
          json: async () => ({
            resumo: { resumo_executivo: "test", total_oportunidades: 0, valor_total: 0, destaques: [] },
            licitacoes: [], download_id: null, total_raw: 0, total_filtrado: 0,
            filter_stats: null, termos_utilizados: null, stopwords_removidas: null,
            excel_available: false, upgrade_message: null, source_stats: null,
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    const filters = makeMockFilters();
    const { result } = renderHook(() => useSearch(filters));

    await hookAct(async () => {
      await result.current.buscarForceFresh();
    });

    expect(capturedBody).toBeTruthy();
    expect(capturedBody.force_fresh).toBe(true);
  });

  it("does NOT include force_fresh in normal search", async () => {
    let capturedBody: any = null;
    global.fetch = jest.fn().mockImplementation(async (url: string, options: any) => {
      if (url === "/api/buscar" && options?.method === "POST") {
        capturedBody = JSON.parse(options.body);
        return {
          ok: true,
          json: async () => ({
            resumo: { resumo_executivo: "test", total_oportunidades: 0, valor_total: 0, destaques: [] },
            licitacoes: [], download_id: null, total_raw: 0, total_filtrado: 0,
            filter_stats: null, termos_utilizados: null, stopwords_removidas: null,
            excel_available: false, upgrade_message: null, source_stats: null,
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    const filters = makeMockFilters();
    const { result } = renderHook(() => useSearch(filters));

    await hookAct(async () => {
      await result.current.buscar();
    });

    expect(capturedBody).toBeTruthy();
    expect(capturedBody.force_fresh).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// T6: Fallback screen does not display technical source names
// ---------------------------------------------------------------------------
import { SourcesUnavailable } from "@/app/buscar/components/SourcesUnavailable";

describe("T6: SourcesUnavailable no technical names", () => {
  it("does not display PNCP, ComprasGov, or technical names", () => {
    const { container } = render(
      <SourcesUnavailable onRetry={jest.fn()} onLoadLastSearch={jest.fn()} hasLastSearch={false} retrying={false} />
    );
    const text = container.textContent || "";
    expect(text).not.toMatch(/PNCP/i);
    expect(text).not.toMatch(/ComprasGov/i);
    expect(text).not.toMatch(/circuit.?breaker/i);
    expect(text).not.toMatch(/HTTP/i);
    expect(text).not.toMatch(/\b5\d{2}\b/);
  });

  it("displays user-friendly message", () => {
    render(
      <SourcesUnavailable onRetry={jest.fn()} onLoadLastSearch={jest.fn()} hasLastSearch={false} retrying={false} />
    );
    expect(screen.getByText(/Fontes temporariamente indisponíveis/)).toBeInTheDocument();
    expect(screen.getByText(/temporariamente/)).toBeInTheDocument();
  });

  it("shows cooldown timer on retry button", () => {
    render(
      <SourcesUnavailable onRetry={jest.fn()} onLoadLastSearch={jest.fn()} hasLastSearch={true} retrying={false} />
    );
    expect(screen.getByText(/Tentar novamente \(0:30\)/)).toBeInTheDocument();
  });

  // GTM-UX-004 AC6: Button hidden (not disabled) when no last search
  it("hides 'Ver última busca salva' when no last search", () => {
    render(
      <SourcesUnavailable onRetry={jest.fn()} onLoadLastSearch={jest.fn()} hasLastSearch={false} retrying={false} />
    );
    expect(screen.queryByText("Ver última busca salva")).not.toBeInTheDocument();
  });

  it("enables 'Ver última busca salva' when last search exists", () => {
    render(
      <SourcesUnavailable onRetry={jest.fn()} onLoadLastSearch={jest.fn()} hasLastSearch={true} retrying={false} />
    );
    const btn = screen.getByText("Ver última busca salva");
    expect(btn.closest("button")).not.toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// T7: Retry on 500 and 502 (mock fetch, use fake timers for delays)
// ---------------------------------------------------------------------------
describe("T7: Client retry on 500/502", () => {
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    jest.useFakeTimers();
  });
  afterEach(async () => {
    // Flush any pending timers/microtasks before restoring
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    global.fetch = originalFetch;
  });

  it("retries on 500 and succeeds on 3rd attempt", async () => {
    let fetchCallCount = 0;
    global.fetch = jest.fn().mockImplementation(async (url: string, options: any) => {
      if (url === "/api/buscar" && options?.method === "POST") {
        fetchCallCount++;
        if (fetchCallCount <= 2) {
          return { ok: false, status: 500, json: async () => ({ message: "Server Error" }) };
        }
        return {
          ok: true,
          json: async () => ({
            resumo: { resumo_executivo: "test", total_oportunidades: 5, valor_total: 100000, destaques: [] },
            licitacoes: [], download_id: "test-id", total_raw: 10, total_filtrado: 5,
            filter_stats: null, termos_utilizados: null, stopwords_removidas: null,
            excel_available: true, upgrade_message: null, source_stats: null,
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    const filters = makeMockFilters();
    const { result } = renderHook(() => useSearch(filters));

    let searchPromise: Promise<void>;
    hookAct(() => {
      searchPromise = result.current.buscar();
    });

    // Use advanceTimersByTimeAsync for proper microtask flushing between retries
    await hookAct(async () => { await jest.advanceTimersByTimeAsync(3500); });
    await hookAct(async () => { await jest.advanceTimersByTimeAsync(8500); });
    await hookAct(async () => { await searchPromise!; });

    expect(fetchCallCount).toBe(3);
    expect(result.current.result).toBeTruthy();
    expect(result.current.error).toBeNull();
  });

  it("retries on 502 and fails after max retries", async () => {
    let fetchCallCount = 0;
    global.fetch = jest.fn().mockImplementation(async (url: string, options: any) => {
      if (url === "/api/buscar" && options?.method === "POST") {
        fetchCallCount++;
        return { ok: false, status: 502, json: async () => ({ message: "Bad Gateway" }) };
      }
      return { ok: true, json: async () => ({}) };
    });

    const filters = makeMockFilters();
    const { result } = renderHook(() => useSearch(filters));

    let searchPromise: Promise<void>;
    hookAct(() => {
      searchPromise = result.current.buscar();
    });

    // Use advanceTimersByTimeAsync for proper microtask flushing
    await hookAct(async () => { await jest.advanceTimersByTimeAsync(3500); });
    await hookAct(async () => { await jest.advanceTimersByTimeAsync(8500); });
    await hookAct(async () => { await searchPromise!; });

    expect(fetchCallCount).toBe(3);
    expect(result.current.error).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// T8: Messages with correct accents (snapshot test in pt-BR)
// NOTE: DegradationBanner and CacheBanner tests removed — components deprecated and deleted (STORY-284 AC6)
// ---------------------------------------------------------------------------
import { FailedUfsBanner, PartialResultsBanner } from "@/app/buscar/components/PartialResultsPrompt";

describe("T8: pt-BR accents and i18n", () => {
  it("FailedUfsBanner uses correct Portuguese", () => {
    const { container } = render(
      <FailedUfsBanner successCount={5} failedUfs={["SP", "RJ"]} onRetryFailed={jest.fn()} loading={false} />
    );
    const text = container.textContent || "";
    expect(text).toContain("estados");
    expect(text).toContain("temporariamente indisponíveis");
    expect(text).not.toContain("indisponiveis");
  });

  it("PartialResultsBanner uses correct Portuguese", () => {
    const { container } = render(
      <PartialResultsBanner visibleCount={5} totalCount={10} searching={true} />
    );
    const text = container.textContent || "";
    expect(text).toContain("Mostrando");
    expect(text).toContain("5 de 10 estados");
    expect(text).toContain("Busca em andamento");
  });

  it("SourcesUnavailable uses correct Portuguese with accents", () => {
    const { container } = render(
      <SourcesUnavailable onRetry={jest.fn()} onLoadLastSearch={jest.fn()} hasLastSearch={false} retrying={false} />
    );
    const text = container.textContent || "";
    expect(text).toContain("indisponíveis");
    expect(text).toContain("acessíveis");
    expect(text).not.toContain("indisponiveis");
  });

});

// ---------------------------------------------------------------------------
// Helper: mock filters for useSearch tests
// ---------------------------------------------------------------------------
function makeMockFilters() {
  return {
    ufsSelecionadas: new Set(["SP"]),
    dataInicial: "2026-01-01",
    dataFinal: "2026-01-31",
    searchMode: "setor" as const,
    modoBusca: "abertas" as const,
    setorId: "vestuario",
    termosArray: [] as string[],
    status: "aberta" as const,
    modalidades: [] as number[],
    valorMin: null,
    valorMax: null,
    esferas: [] as any[],
    municipios: [] as any[],
    ordenacao: "data" as const,
    sectorName: "Vestuário",
    canSearch: true,
    setOrdenacao: jest.fn(),
    setUfsSelecionadas: jest.fn(),
    setDataInicial: jest.fn(),
    setDataFinal: jest.fn(),
    setSearchMode: jest.fn(),
    setSetorId: jest.fn(),
    setTermosArray: jest.fn(),
    setStatus: jest.fn(),
    setModalidades: jest.fn(),
    setValorMin: jest.fn(),
    setValorMax: jest.fn(),
    setEsferas: jest.fn(),
    setMunicipios: jest.fn(),
  };
}
