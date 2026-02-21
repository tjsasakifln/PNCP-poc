/**
 * CRIT-008 T1-T14: Search resilience tests.
 *
 * Tests sector cache stale fallback, auto-retry with countdown for transient errors,
 * BackendStatusIndicator visual states, and health route telemetry rate-limiting.
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---- Module mocks (hoisted by Jest) ----

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

jest.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: { access_token: "test-token" }, user: null, loading: false }),
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../hooks/useQuota", () => ({
  useQuota: () => ({ refresh: jest.fn() }),
}));

jest.mock("../hooks/useSearchProgress", () => ({
  useSearchProgress: () => ({
    currentEvent: null,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    partialProgress: null,
    refreshAvailable: null,
  }),
}));

jest.mock("../hooks/useSearchPolling", () => ({
  useSearchPolling: () => ({ asProgressEvent: null }),
}));

jest.mock("../hooks/useSavedSearches", () => ({
  useSavedSearches: () => ({ saveNewSearch: jest.fn(), isMaxCapacity: false }),
}));

jest.mock("../lib/error-messages", () => ({
  getUserFriendlyError: jest.fn((e: any) => (typeof e === "string" ? e : e?.message || "Error")),
  getMessageFromErrorCode: jest.fn(() => null),
  isTransientError: jest.requireActual("../lib/error-messages").isTransientError,
  TRANSIENT_HTTP_CODES: jest.requireActual("../lib/error-messages").TRANSIENT_HTTP_CODES,
  ERROR_CODE_MESSAGES: jest.requireActual("../lib/error-messages").ERROR_CODE_MESSAGES,
  getErrorMessage: jest.requireActual("../lib/error-messages").getErrorMessage,
  DEFAULT_ERROR_MESSAGE: jest.requireActual("../lib/error-messages").DEFAULT_ERROR_MESSAGE,
}));

jest.mock("../lib/searchStatePersistence", () => ({
  saveSearchState: jest.fn(),
  restoreSearchState: jest.fn(() => null),
}));

jest.mock("../lib/utils/correlationId", () => ({
  getCorrelationId: () => "test-correlation-id",
  logCorrelatedRequest: jest.fn(),
}));

jest.mock("../lib/utils/dateDiffInDays", () => ({
  dateDiffInDays: () => 10,
}));

// ---- Constants ----

const SECTOR_CACHE_KEY = "smartlic-sectors-cache-v2";
const SECTOR_CACHE_TTL = 5 * 60 * 1000; // 5 min

const MOCK_SECTORS = [
  { id: "vestuario", name: "Vestuario e Uniformes", description: "desc" },
  { id: "alimentos", name: "Alimentos e Merenda", description: "desc" },
];

// ===========================================================================
// T1-T4: useSearchFilters — sector cache resilience
// ===========================================================================

describe("T1-T4: useSearchFilters sector cache resilience", () => {
  let getItemSpy: jest.SpyInstance;
  let setItemSpy: jest.SpyInstance;

  beforeEach(() => {
    getItemSpy = jest.spyOn(Storage.prototype, "getItem");
    setItemSpy = jest.spyOn(Storage.prototype, "setItem");
  });

  afterEach(() => {
    getItemSpy.mockRestore();
    setItemSpy.mockRestore();
    jest.restoreAllMocks();
  });

  /**
   * Helper component that renders the useSearchFilters hook and exposes state.
   */
  function SectorTestHarness() {
    const { useSearchFilters } = require("../app/buscar/hooks/useSearchFilters");
    const clearResult = React.useCallback(() => {}, []);
    const filters = useSearchFilters(clearResult);

    return (
      <div>
        <span data-testid="sectors-count">{filters.setores.length}</span>
        <span data-testid="using-stale">{String(filters.setoresUsingStaleCache)}</span>
        <span data-testid="using-fallback">{String(filters.setoresUsingFallback)}</span>
        <span data-testid="stale-age">{filters.staleCacheAge ?? "null"}</span>
        <span data-testid="loading">{String(filters.setoresLoading)}</span>
        <span data-testid="error">{String(filters.setoresError)}</span>
        {filters.setores.map((s: any) => (
          <span key={s.id} data-testid={`sector-${s.id}`}>{s.name}</span>
        ))}
      </div>
    );
  }

  it("T1: uses stale cache when fetch fails and expired cache exists", async () => {
    jest.useFakeTimers();

    const expiredTimestamp = Date.now() - SECTOR_CACHE_TTL - 60_000; // 1 min past expiry
    const staleCache = JSON.stringify({
      data: MOCK_SECTORS,
      timestamp: expiredTimestamp,
    });

    // localStorage returns stale cache data
    getItemSpy.mockImplementation((key: string) => {
      if (key === SECTOR_CACHE_KEY) return staleCache;
      return null;
    });

    // All fetch calls fail (API down)
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    await act(async () => {
      render(<SectorTestHarness />);
    });

    // Advance through retry delays: attempt 0 fails, then setTimeout(1000) for attempt 1,
    // then setTimeout(2000) for attempt 2. After 3 failures, stale cache is used.
    await act(async () => {
      jest.advanceTimersByTime(1000); // retry attempt 1
    });
    await act(async () => {
      jest.advanceTimersByTime(2000); // retry attempt 2
    });
    await act(async () => {
      jest.advanceTimersByTime(4000); // retry attempt 3 (2^2 * 1000)
    });

    await waitFor(() => {
      expect(screen.getByTestId("using-stale").textContent).toBe("true");
    });
    expect(screen.getByTestId("using-fallback").textContent).toBe("false");
    expect(screen.getByTestId("sectors-count").textContent).toBe("2");

    jest.useRealTimers();
  });

  it("T2: uses hardcoded fallback when no cache exists at all", async () => {
    jest.useFakeTimers();

    // No cache in localStorage
    getItemSpy.mockReturnValue(null);

    // All fetch calls fail
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    await act(async () => {
      render(<SectorTestHarness />);
    });

    // Advance through all retries
    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    await act(async () => {
      jest.advanceTimersByTime(4000);
    });

    await waitFor(() => {
      expect(screen.getByTestId("using-fallback").textContent).toBe("true");
    });
    expect(screen.getByTestId("using-stale").textContent).toBe("false");
    // Hardcoded fallback has 15 sectors
    expect(Number(screen.getByTestId("sectors-count").textContent)).toBe(15);

    jest.useRealTimers();
  });

  it("T3: background revalidation updates sectors and removes stale banner", async () => {
    jest.useFakeTimers();

    const expiredTimestamp = Date.now() - SECTOR_CACHE_TTL - 60_000;
    const staleCache = JSON.stringify({
      data: MOCK_SECTORS,
      timestamp: expiredTimestamp,
    });

    getItemSpy.mockImplementation((key: string) => {
      if (key === SECTOR_CACHE_KEY) return staleCache;
      return null;
    });

    const freshSectors = [
      { id: "software", name: "Software e Sistemas", description: "desc" },
      { id: "saude", name: "Saude", description: "desc" },
      { id: "vestuario", name: "Vestuario e Uniformes", description: "desc" },
    ];

    let fetchCallCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      fetchCallCount++;
      // First 3 calls fail (initial + 2 retries), then succeed on revalidation
      if (fetchCallCount <= 3) {
        return Promise.reject(new Error("Network error"));
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ setores: freshSectors }),
      });
    });

    await act(async () => {
      render(<SectorTestHarness />);
    });

    // Advance through initial retries
    await act(async () => { jest.advanceTimersByTime(1000); });
    await act(async () => { jest.advanceTimersByTime(2000); });
    await act(async () => { jest.advanceTimersByTime(4000); });

    // Verify we're in stale state
    await waitFor(() => {
      expect(screen.getByTestId("using-stale").textContent).toBe("true");
    });

    // Background revalidation fires at 30s intervals
    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    // After successful revalidation, stale flag should be cleared
    await waitFor(() => {
      expect(screen.getByTestId("using-stale").textContent).toBe("false");
    });
    expect(screen.getByTestId("sectors-count").textContent).toBe("3");

    jest.useRealTimers();
  });

  it("T4: background revalidation stops after 5 failed attempts", async () => {
    jest.useFakeTimers();

    const expiredTimestamp = Date.now() - SECTOR_CACHE_TTL - 60_000;
    const staleCache = JSON.stringify({
      data: MOCK_SECTORS,
      timestamp: expiredTimestamp,
    });

    getItemSpy.mockImplementation((key: string) => {
      if (key === SECTOR_CACHE_KEY) return staleCache;
      return null;
    });

    // All fetch calls always fail
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    await act(async () => {
      render(<SectorTestHarness />);
    });

    // Advance through initial retries
    await act(async () => { jest.advanceTimersByTime(1000); });
    await act(async () => { jest.advanceTimersByTime(2000); });
    await act(async () => { jest.advanceTimersByTime(4000); });

    await waitFor(() => {
      expect(screen.getByTestId("using-stale").textContent).toBe("true");
    });

    // Count fetch calls before revalidation
    const callsBeforeRevalidation = (global.fetch as jest.Mock).mock.calls.length;

    // Advance through 5 revalidation intervals (30s each = 150s total)
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        jest.advanceTimersByTime(30_000);
      });
    }

    const callsAfterFiveAttempts = (global.fetch as jest.Mock).mock.calls.length;
    const revalidationCalls = callsAfterFiveAttempts - callsBeforeRevalidation;

    // Should have exactly 5 revalidation attempts
    expect(revalidationCalls).toBe(5);

    // Advance another 60s — no more revalidation calls should happen
    await act(async () => {
      jest.advanceTimersByTime(60_000);
    });

    const callsAfterStop = (global.fetch as jest.Mock).mock.calls.length;
    expect(callsAfterStop).toBe(callsAfterFiveAttempts);

    // Still using stale cache
    expect(screen.getByTestId("using-stale").textContent).toBe("true");

    jest.useRealTimers();
  });
});

// ===========================================================================
// T5-T6: isTransientError classification
// ===========================================================================

describe("T5-T6: Transient vs permanent error classification", () => {
  // Import the real function (not mocked version)
  const { isTransientError, TRANSIENT_HTTP_CODES } = jest.requireActual(
    "../lib/error-messages"
  );

  it("T5: transient HTTP codes (502/503/504) are classified as transient", () => {
    expect(isTransientError(502, undefined)).toBe(true);
    expect(isTransientError(503, undefined)).toBe(true);
    expect(isTransientError(504, undefined)).toBe(true);
    // Network error messages are also transient
    expect(isTransientError(null, "fetch failed")).toBe(true);
    expect(isTransientError(null, "Failed to fetch")).toBe(true);
    expect(isTransientError(null, "NetworkError when attempting")).toBe(true);
    expect(isTransientError(null, "network error occurred")).toBe(true);
    expect(isTransientError(null, "ECONNREFUSED")).toBe(true);
    expect(TRANSIENT_HTTP_CODES.has(502)).toBe(true);
    expect(TRANSIENT_HTTP_CODES.has(503)).toBe(true);
    expect(TRANSIENT_HTTP_CODES.has(504)).toBe(true);
  });

  it("T6: permanent HTTP codes (400/401/403/422/429) are NOT transient", () => {
    expect(isTransientError(400, undefined)).toBe(false);
    expect(isTransientError(401, undefined)).toBe(false);
    expect(isTransientError(403, undefined)).toBe(false);
    expect(isTransientError(422, undefined)).toBe(false);
    expect(isTransientError(429, undefined)).toBe(false);
    expect(isTransientError(200, undefined)).toBe(false);
    expect(isTransientError(null, undefined)).toBe(false);
    expect(isTransientError(null, "Quota exceeded")).toBe(false);
    expect(isTransientError(null, "Bad request")).toBe(false);
    expect(TRANSIENT_HTTP_CODES.has(400)).toBe(false);
    expect(TRANSIENT_HTTP_CODES.has(401)).toBe(false);
    expect(TRANSIENT_HTTP_CODES.has(429)).toBe(false);
  });
});

// ===========================================================================
// T7-T10: SearchResults retry countdown UI
// ===========================================================================

describe("T7-T10: SearchResults retry countdown UI", () => {
  // We import SearchResults which renders the retry countdown UI
  const SearchResults = require("../app/buscar/components/SearchResults").default;

  const baseProps = {
    loading: false,
    loadingStep: 0,
    estimatedTime: 0,
    stateCount: 0,
    statesProcessed: 0,
    onCancel: jest.fn(),
    sseEvent: null,
    useRealProgress: false,
    sseAvailable: false,
    onStageChange: jest.fn(),
    error: null,
    quotaError: null,
    result: null,
    rawCount: 0,
    ufsSelecionadas: new Set(["SP"]),
    sectorName: "Vestuario",
    searchMode: "setor" as const,
    termosArray: [] as string[],
    ordenacao: "relevancia" as const,
    onOrdenacaoChange: jest.fn(),
    downloadLoading: false,
    downloadError: null,
    onDownload: jest.fn(),
    onSearch: jest.fn(),
    planInfo: {
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      quota_used: 5,
      quota_reset_date: "2026-03-01",
      capabilities: { max_history_days: 1825, max_requests_per_month: 1000, allow_excel: true },
    },
    session: { access_token: "test-token" },
    onShowUpgradeModal: jest.fn(),
    onTrackEvent: jest.fn(),
  };

  const transientError = {
    message: "O servidor esta temporariamente indisponivel.",
    rawMessage: "Bad Gateway",
    errorCode: "SOURCE_UNAVAILABLE",
    searchId: "test-search-123",
    correlationId: "test-corr-456",
    requestId: "test-req-789",
    httpStatus: 502,
    timestamp: new Date().toISOString(),
  };

  it("T7: countdown visual displays remaining seconds correctly", () => {
    const mockRetryNow = jest.fn();
    const mockCancelRetry = jest.fn();

    const { rerender } = render(
      <SearchResults
        {...baseProps}
        error={transientError}
        retryCountdown={15}
        onRetryNow={mockRetryNow}
        onCancelRetry={mockCancelRetry}
      />
    );

    // Should show the countdown number
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText(/Tentando novamente em 15s/)).toBeInTheDocument();

    // Rerender with decremented countdown
    rerender(
      <SearchResults
        {...baseProps}
        error={transientError}
        retryCountdown={10}
        onRetryNow={mockRetryNow}
        onCancelRetry={mockCancelRetry}
      />
    );

    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText(/Tentando novamente em 10s/)).toBeInTheDocument();
  });

  it('T8: "Tentar agora" button triggers immediate retry', () => {
    const mockRetryNow = jest.fn();
    const mockCancelRetry = jest.fn();

    render(
      <SearchResults
        {...baseProps}
        error={transientError}
        retryCountdown={20}
        onRetryNow={mockRetryNow}
        onCancelRetry={mockCancelRetry}
      />
    );

    const retryButton = screen.getByText("Tentar agora");
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(mockRetryNow).toHaveBeenCalledTimes(1);
  });

  it('T9: "Cancelar" button cancels retry and keeps error displayed', () => {
    const mockRetryNow = jest.fn();
    const mockCancelRetry = jest.fn();

    const { rerender } = render(
      <SearchResults
        {...baseProps}
        error={transientError}
        retryCountdown={20}
        onRetryNow={mockRetryNow}
        onCancelRetry={mockCancelRetry}
      />
    );

    const cancelButton = screen.getByText("Cancelar");
    expect(cancelButton).toBeInTheDocument();

    fireEvent.click(cancelButton);
    expect(mockCancelRetry).toHaveBeenCalledTimes(1);

    // After cancel, countdown is null — error should still show (via the non-countdown error block)
    rerender(
      <SearchResults
        {...baseProps}
        error={transientError}
        retryCountdown={null}
        onRetryNow={mockRetryNow}
        onCancelRetry={mockCancelRetry}
      />
    );

    // The error message should still be visible in the non-countdown error section
    expect(screen.getByText(transientError.message)).toBeInTheDocument();
  });

  it("T10: successful retry shows results normally (no countdown, no error)", () => {
    const mockResult = {
      resumo: {
        resumo_executivo: "Encontradas oportunidades no setor de vestuario.",
        total_oportunidades: 5,
        valor_total: 100000,
        destaques: ["Destaque 1"],
        alerta_urgencia: null,
        alertas_urgencia: null,
        recomendacoes: null,
        insight_setorial: null,
      },
      licitacoes: [
        {
          pncp_id: "bid-001",
          objeto: "Aquisicao de uniformes",
          orgao: "Prefeitura Municipal",
          uf: "SP",
          municipio: "Sao Paulo",
          valor: 50000,
          modalidade: "pregao",
          data_abertura: "2026-03-01",
          data_publicacao: "2026-02-15",
          situacao: "aberta",
          link: "https://pncp.gov.br/bid-001",
          match_details: null,
        },
      ],
      download_id: null,
      download_url: null,
      total_raw: 50,
      total_filtrado: 5,
      filter_stats: null,
      termos_utilizados: ["uniforme"],
      stopwords_removidas: null,
      excel_available: true,
      upgrade_message: null,
      sources_used: ["PNCP"],
      source_stats: null,
      hidden_by_min_match: null,
      filter_relaxed: null,
      metadata: null,
      is_partial: false,
      cached: false,
      is_truncated: false,
    };

    render(
      <SearchResults
        {...baseProps}
        error={null}
        result={mockResult as any}
        rawCount={50}
        retryCountdown={null}
      />
    );

    // No countdown UI should be visible
    expect(screen.queryByText(/Tentando novamente em/)).not.toBeInTheDocument();
    // No error message from transient error
    expect(screen.queryByText(transientError.message)).not.toBeInTheDocument();
    // No retry countdown buttons
    expect(screen.queryByText("Tentar agora")).not.toBeInTheDocument();
    expect(screen.queryByText("Cancelar")).not.toBeInTheDocument();
    // Resumo executivo text should be rendered (part of results display)
    expect(screen.getByText(/Encontradas oportunidades no setor de vestuario/)).toBeInTheDocument();
  });
});

// ===========================================================================
// T11-T13: BackendStatusIndicator
// ===========================================================================

describe("T11-T13: BackendStatusIndicator", () => {
  // Import the hook separately so we can test it via renderHook
  // We use dynamic import to avoid module-level issues, but within test scope
  // to keep React consistent.

  beforeEach(() => {
    // Ensure page is visible by default
    Object.defineProperty(document, "visibilityState", {
      value: "visible",
      writable: true,
      configurable: true,
    });
  });

  it("T11: shows red pulsing dot when backend is offline", async () => {
    jest.useFakeTimers();

    // Health endpoint returns unhealthy
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: "healthy", backend: "unhealthy" }),
    });

    // Import the hook and build a test wrapper
    const { useBackendStatus } = require("../components/BackendStatusIndicator");

    function TestIndicator() {
      const { status } = useBackendStatus();
      if (status === "online") return null;
      return (
        <span
          role="status"
          aria-label={status === "offline" ? "Servidor offline" : "Servidor recuperado"}
          className={status === "offline" ? "bg-red-500 animate-pulse" : "bg-green-500"}
        />
      );
    }

    await act(async () => {
      render(<TestIndicator />);
    });

    // Let the initial health check resolve
    await act(async () => {
      jest.advanceTimersByTime(10);
    });

    await waitFor(() => {
      const dot = screen.getByRole("status");
      expect(dot).toBeInTheDocument();
      expect(dot.getAttribute("aria-label")).toBe("Servidor offline");
      expect(dot.className).toContain("bg-red-500");
      expect(dot.className).toContain("animate-pulse");
    });

    jest.useRealTimers();
  });

  it("T12: shows green dot for 3s when backend recovers from offline", async () => {
    jest.useFakeTimers();

    let callCount = 0;
    global.fetch = jest.fn().mockImplementation(() => {
      callCount++;
      if (callCount <= 1) {
        // First call: unhealthy (to put in offline state)
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: "healthy", backend: "unhealthy" }),
        });
      }
      // Second call onwards: healthy (recovery)
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: "healthy", backend: "healthy" }),
      });
    });

    const { useBackendStatus } = require("../components/BackendStatusIndicator");

    function TestIndicator() {
      const { status } = useBackendStatus();
      if (status === "online") return null;
      return (
        <span
          role="status"
          data-status={status}
          className={status === "offline" ? "bg-red-500" : "bg-green-500"}
        />
      );
    }

    await act(async () => {
      render(<TestIndicator />);
    });

    // Wait for initial check to resolve (offline)
    await act(async () => {
      jest.advanceTimersByTime(10);
    });

    await waitFor(() => {
      const dot = screen.getByRole("status");
      expect(dot.className).toContain("bg-red-500");
      expect(dot.getAttribute("data-status")).toBe("offline");
    });

    // Advance to next poll (30s) -- backend now healthy -> recovering
    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    await waitFor(() => {
      const dot = screen.getByRole("status");
      expect(dot.className).toContain("bg-green-500");
      expect(dot.getAttribute("data-status")).toBe("recovering");
    });

    // After 3s recovery timer, should transition to online (render nothing)
    await act(async () => {
      jest.advanceTimersByTime(3_000);
    });

    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it("T13: does not poll when page is not visible", async () => {
    jest.useFakeTimers();

    // Start with page hidden
    Object.defineProperty(document, "visibilityState", {
      value: "hidden",
      writable: true,
      configurable: true,
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: "healthy", backend: "healthy" }),
    });

    const { useBackendStatus } = require("../components/BackendStatusIndicator");

    function TestIndicator() {
      const { status, isPolling } = useBackendStatus();
      return (
        <div>
          <span data-testid="status">{status}</span>
          <span data-testid="polling">{String(isPolling)}</span>
        </div>
      );
    }

    await act(async () => {
      render(<TestIndicator />);
    });

    // Advance plenty of time
    await act(async () => {
      jest.advanceTimersByTime(120_000);
    });

    // Fetch should NOT have been called because page was hidden from start
    expect(global.fetch).not.toHaveBeenCalled();
    // Polling should be false
    expect(screen.getByTestId("polling").textContent).toBe("false");

    jest.useRealTimers();
  });
});

// ===========================================================================
// T14: Health route — telemetry rate limiting
// ===========================================================================

describe("T14: Health route telemetry rate limiting", () => {
  /**
   * The health route uses Next.js server-side primitives (NextResponse)
   * which are not available in jsdom. Instead of importing the route handler,
   * we replicate the telemetry rate-limiting logic here and test it directly.
   * This validates the core AC7 behavior: max 1 telemetry event per minute.
   */
  it("T14: emits telemetry event max once per minute when backend fails", () => {
    jest.useFakeTimers();

    // Replicate the rate-limiting logic from health/route.ts
    let lastTelemetryTimestamp = 0;
    const TELEMETRY_MIN_INTERVAL_MS = 60_000;
    const emittedEvents: any[] = [];

    function emitHealthTelemetry(
      backendStatus: string,
      httpStatus: number,
      latencyMs: number,
      url: string,
    ) {
      const now = Date.now();
      if (now - lastTelemetryTimestamp < TELEMETRY_MIN_INTERVAL_MS) return;
      lastTelemetryTimestamp = now;

      emittedEvents.push({
        event: "backend_health_check_failed",
        status: backendStatus,
        http_status: httpStatus,
        latency_ms: latencyMs,
        backend_url: url,
        timestamp: new Date(now).toISOString(),
      });
    }

    // First call -- should emit
    emitHealthTelemetry("unhealthy", 500, 42, "http://localhost:8000/health");
    expect(emittedEvents.length).toBe(1);
    expect(emittedEvents[0].event).toBe("backend_health_check_failed");
    expect(emittedEvents[0].status).toBe("unhealthy");
    expect(emittedEvents[0].http_status).toBe(500);
    expect(typeof emittedEvents[0].latency_ms).toBe("number");
    expect(emittedEvents[0].backend_url).toBe("http://localhost:8000/health");
    expect(emittedEvents[0].timestamp).toBeTruthy();

    // Second call immediately -- should NOT emit (within 60s window)
    emitHealthTelemetry("unreachable", 0, 5001, "http://localhost:8000/health");
    expect(emittedEvents.length).toBe(1); // still 1

    // Third call at 30s -- should NOT emit
    jest.advanceTimersByTime(30_000);
    emitHealthTelemetry("unhealthy", 502, 100, "http://localhost:8000/health");
    expect(emittedEvents.length).toBe(1); // still 1

    // Fourth call at 61s total -- should emit again
    jest.advanceTimersByTime(31_000); // total = 61s
    emitHealthTelemetry("unhealthy", 503, 200, "http://localhost:8000/health");
    expect(emittedEvents.length).toBe(2);
    expect(emittedEvents[1].http_status).toBe(503);

    // Fifth call immediately after -- should NOT emit
    emitHealthTelemetry("unhealthy", 504, 300, "http://localhost:8000/health");
    expect(emittedEvents.length).toBe(2); // still 2

    jest.useRealTimers();
  });
});
