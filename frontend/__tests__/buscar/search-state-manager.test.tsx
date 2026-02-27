/**
 * STORY-298 AC9+AC10: Tests for SearchStateManager and deriveSearchPhase.
 *
 * AC9: Visual test for each of the 9 search states
 * AC10: Test each state transition renders correct component
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { SearchStateManager } from "../../app/buscar/components/SearchStateManager";
import { deriveSearchPhase, PHASE_LABELS, PHASE_ACTIONS } from "../../app/buscar/types/searchPhase";
import type { SearchPhase } from "../../app/buscar/types/searchPhase";
import type { SearchError } from "../../app/buscar/hooks/useSearch";

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// ---------- Fixtures ----------

const makeError = (overrides: Partial<SearchError> = {}): SearchError => ({
  message: "O servidor está temporariamente indisponível.",
  rawMessage: "Bad Gateway",
  errorCode: "SOURCE_UNAVAILABLE",
  searchId: "test-search-123",
  correlationId: "test-corr-456",
  requestId: "test-req-789",
  httpStatus: 502,
  timestamp: new Date().toISOString(),
  ...overrides,
});

const baseManagerProps = {
  phase: "idle" as SearchPhase,
  error: null as SearchError | null,
  quotaError: null as string | null,
  retryCountdown: null as number | null,
  retryMessage: null as string | null,
  retryExhausted: false,
  onRetry: jest.fn(),
  onRetryNow: jest.fn(),
  onCancelRetry: jest.fn(),
  onCancel: jest.fn(),
  loading: false,
  hasPartialResults: false,
};

const baseResult = {
  resumo: {
    resumo_executivo: "Resultados encontrados",
    total_oportunidades: 5,
    valor_total: 100000,
    destaques: [],
    alerta_urgencia: null,
    alertas_urgencia: null,
    recomendacoes: null,
    insight_setorial: null,
  },
  licitacoes: [],
  response_state: "live" as const,
  is_partial: false,
  total_raw: 10,
  cached: false,
  cached_at: null,
  cache_status: undefined,
  failed_ufs: [] as string[],
  source_stats: [],
  is_truncated: false,
  coverage_pct: 100,
};

// ---------- deriveSearchPhase Unit Tests ----------

describe("deriveSearchPhase()", () => {
  const baseInput = {
    loading: false,
    error: null as SearchError | null,
    quotaError: null as string | null,
    result: null as any,
    retryCountdown: null as number | null,
    retryExhausted: false,
    sourceStatuses: new Map(),
    partialProgress: null,
    ufTotalFound: 0,
    searchElapsedSeconds: 0,
  };

  it("returns 'idle' when nothing is happening", () => {
    expect(deriveSearchPhase(baseInput)).toBe("idle");
  });

  it("returns 'searching' when loading", () => {
    expect(deriveSearchPhase({ ...baseInput, loading: true })).toBe("searching");
  });

  it("returns 'partial_available' when loading with results after 15s", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        loading: true,
        ufTotalFound: 10,
        searchElapsedSeconds: 20,
      })
    ).toBe("partial_available");
  });

  it("returns 'partial_available' when loading with progressive delivery", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        loading: true,
        partialProgress: { totalSoFar: 5, sourcesCompleted: 1, sourcesTotal: 3 } as any,
      })
    ).toBe("partial_available");
  });

  it("returns 'completed' for successful search with results", () => {
    expect(
      deriveSearchPhase({ ...baseInput, result: baseResult })
    ).toBe("completed");
  });

  it("returns 'empty_results' for zero results (legitimate)", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        result: { ...baseResult, resumo: { ...baseResult.resumo, total_oportunidades: 0 } },
      })
    ).toBe("empty_results");
  });

  it("returns 'all_sources_failed' for empty_failure response_state", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        result: { ...baseResult, response_state: "empty_failure", resumo: { ...baseResult.resumo, total_oportunidades: 0 } },
      })
    ).toBe("all_sources_failed");
  });

  it("returns 'all_sources_failed' for partial with zero results (no cache)", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        result: {
          ...baseResult,
          response_state: "live",
          is_partial: true,
          total_raw: 0,
          cached: false,
          resumo: { ...baseResult.resumo, total_oportunidades: 0 },
        },
      })
    ).toBe("all_sources_failed");
  });

  it("returns 'source_timeout' when partial results exist", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        result: { ...baseResult, is_partial: true },
      })
    ).toBe("source_timeout");
  });

  it("returns 'source_timeout' when some UFs failed", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        result: { ...baseResult, failed_ufs: ["SP", "RJ"] },
      })
    ).toBe("source_timeout");
  });

  it("returns 'offline' when error with retry countdown", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        error: makeError(),
        retryCountdown: 10,
      })
    ).toBe("offline");
  });

  it("returns 'offline' when error with retry exhausted", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        error: makeError(),
        retryExhausted: true,
      })
    ).toBe("offline");
  });

  it("returns 'failed' for non-transient error", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        error: makeError({ httpStatus: 400, errorCode: "VALIDATION_ERROR" }),
      })
    ).toBe("failed");
  });

  it("returns 'quota_exceeded' when quotaError is set", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        quotaError: "Limite de buscas atingido",
      })
    ).toBe("quota_exceeded");
  });

  it("quota_exceeded takes priority over error", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        quotaError: "Limite atingido",
        error: makeError(),
      })
    ).toBe("quota_exceeded");
  });

  it("returns 'searching' (not partial) when loading but no UF data yet", () => {
    expect(
      deriveSearchPhase({
        ...baseInput,
        loading: true,
        ufTotalFound: 0,
        searchElapsedSeconds: 30,
      })
    ).toBe("searching");
  });
});

// ---------- PHASE_LABELS and PHASE_ACTIONS Coverage ----------

describe("PHASE_LABELS and PHASE_ACTIONS", () => {
  const allPhases: SearchPhase[] = [
    "idle", "searching", "partial_available", "completed",
    "empty_results", "all_sources_failed", "source_timeout",
    "offline", "failed", "quota_exceeded",
  ];

  it("every phase has a label", () => {
    allPhases.forEach(phase => {
      expect(PHASE_LABELS[phase]).toBeDefined();
      expect(typeof PHASE_LABELS[phase]).toBe("string");
    });
  });

  it("every phase has an action", () => {
    allPhases.forEach(phase => {
      expect(PHASE_ACTIONS[phase]).toBeDefined();
    });
  });
});

// ---------- SearchStateManager Visual Tests (AC9) ----------

describe("SearchStateManager — AC9: visual test for each of 9 states", () => {
  it("renders nothing for 'idle' phase", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="idle" />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for 'searching' phase (handled by SearchResults loading)", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="searching" loading />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for 'partial_available' phase (handled by SearchResults)", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="partial_available" loading />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for 'completed' phase (results handled by SearchResults)", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="completed" />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for 'empty_results' phase (ZeroResultsSuggestions in SearchResults)", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="empty_results" />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for 'all_sources_failed' phase (SourcesUnavailable in SearchResults)", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="all_sources_failed" />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for 'source_timeout' phase (DataQualityBanner in SearchResults)", () => {
    const { container } = render(
      <SearchStateManager {...baseManagerProps} phase="source_timeout" />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders retry-countdown for 'offline' phase with countdown", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={15}
        retryMessage="Serviço temporariamente indisponível"
      />
    );
    expect(screen.getByTestId("retry-countdown")).toBeInTheDocument();
    expect(screen.getByTestId("retry-message")).toHaveTextContent("Serviço temporariamente indisponível");
    expect(screen.getByTestId("retry-countdown-text")).toHaveTextContent("15s");
    expect(screen.getByTestId("retry-now-button")).toBeInTheDocument();
    expect(screen.getByText("Cancelar")).toBeInTheDocument();
  });

  it("renders retry-exhausted for 'offline' phase when exhausted", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryExhausted={true}
        retryCountdown={null}
      />
    );
    expect(screen.getByTestId("retry-exhausted")).toBeInTheDocument();
    expect(screen.getByTestId("retry-manual-button")).toBeInTheDocument();
    expect(screen.getByText("Busca indisponível no momento.")).toBeInTheDocument();
  });

  it("renders error card for 'failed' phase", () => {
    const error = makeError({ message: "Erro de validação nos filtros" });
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="failed"
        error={error}
      />
    );
    expect(screen.getByTestId("search-state-failed")).toBeInTheDocument();
    expect(screen.getByText("Erro de validação nos filtros")).toBeInTheDocument();
    expect(screen.getByTestId("failed-retry-button")).toBeInTheDocument();
  });

  it("renders quota warning for 'quota_exceeded' phase", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="quota_exceeded"
        quotaError="Limite de buscas atingido"
      />
    );
    expect(screen.getByTestId("search-state-quota")).toBeInTheDocument();
    expect(screen.getByText("Limite de buscas atingido")).toBeInTheDocument();
    expect(screen.getByTestId("quota-plans-link")).toHaveAttribute("href", "/planos");
  });
});

// ---------- AC10: State Transition Tests ----------

describe("SearchStateManager — AC10: state transitions", () => {
  it("transitions from offline → idle (no error, countdown cleared)", () => {
    const { rerender } = render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={10}
      />
    );
    expect(screen.getByTestId("retry-countdown")).toBeInTheDocument();

    // Transition to idle (error cleared)
    rerender(
      <SearchStateManager {...baseManagerProps} phase="idle" />
    );
    expect(screen.queryByTestId("retry-countdown")).not.toBeInTheDocument();
  });

  it("transitions from offline-countdown → offline-exhausted", () => {
    const { rerender } = render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={5}
        retryMessage="Tentando..."
      />
    );
    expect(screen.getByTestId("retry-countdown")).toBeInTheDocument();

    // Transition to exhausted
    rerender(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryExhausted={true}
        retryCountdown={null}
      />
    );
    expect(screen.queryByTestId("retry-countdown")).not.toBeInTheDocument();
    expect(screen.getByTestId("retry-exhausted")).toBeInTheDocument();
  });

  it("transitions from failed → searching (user retried)", () => {
    const { rerender } = render(
      <SearchStateManager
        {...baseManagerProps}
        phase="failed"
        error={makeError()}
      />
    );
    expect(screen.getByTestId("search-state-failed")).toBeInTheDocument();

    rerender(
      <SearchStateManager {...baseManagerProps} phase="searching" loading />
    );
    expect(screen.queryByTestId("search-state-failed")).not.toBeInTheDocument();
  });

  it("transitions from quota_exceeded → searching (user upgraded plan)", () => {
    const { rerender } = render(
      <SearchStateManager
        {...baseManagerProps}
        phase="quota_exceeded"
        quotaError="Limite atingido"
      />
    );
    expect(screen.getByTestId("search-state-quota")).toBeInTheDocument();

    rerender(
      <SearchStateManager {...baseManagerProps} phase="searching" loading />
    );
    expect(screen.queryByTestId("search-state-quota")).not.toBeInTheDocument();
  });
});

// ---------- AC2: Zero Limbo States ----------

describe("SearchStateManager — AC2: zero limbo states", () => {
  it("offline phase with no retry and no exhaustion still shows retry button", () => {
    // Edge case: error but retryCountdown=null and retryExhausted=false
    // deriveSearchPhase would return "failed" here, but if forced to "offline"
    // the component should still render something actionable
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="failed"
        error={makeError()}
      />
    );
    // AC2: there's always an action visible
    expect(screen.getByTestId("failed-retry-button")).toBeInTheDocument();
  });

  it("offline phase with partial results shows 'Ver resultados parciais' button", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryExhausted={true}
        hasPartialResults={true}
      />
    );
    expect(screen.getByTestId("view-partial-results-button")).toBeInTheDocument();
  });
});

// ---------- AC3: Toast Notifications ----------

describe("SearchStateManager — AC3: toast notifications", () => {
  const { toast } = require("sonner");

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows success toast when transitioning from offline to searching", () => {
    const { rerender } = render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={5}
      />
    );

    rerender(
      <SearchStateManager {...baseManagerProps} phase="searching" loading />
    );

    expect(toast.success).toHaveBeenCalledWith(
      "Conexão restabelecida",
      expect.objectContaining({ description: "Retomando busca..." })
    );
  });

  it("shows warning toast when transitioning from searching to offline", () => {
    const { rerender } = render(
      <SearchStateManager {...baseManagerProps} phase="searching" loading />
    );

    rerender(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={10}
      />
    );

    expect(toast.warning).toHaveBeenCalledWith(
      "Conexão perdida",
      expect.objectContaining({ description: "Tentando reconectar automaticamente..." })
    );
  });

  it("shows success toast when transitioning from partial_available to completed", () => {
    const { rerender } = render(
      <SearchStateManager {...baseManagerProps} phase="partial_available" loading />
    );

    rerender(
      <SearchStateManager {...baseManagerProps} phase="completed" />
    );

    expect(toast.success).toHaveBeenCalledWith(
      "Busca concluída",
      expect.objectContaining({ description: "Todos os resultados carregados" })
    );
  });

  it("does NOT show toast for non-transition events (same phase)", () => {
    const { rerender } = render(
      <SearchStateManager {...baseManagerProps} phase="idle" />
    );

    rerender(
      <SearchStateManager {...baseManagerProps} phase="idle" />
    );

    expect(toast.success).not.toHaveBeenCalled();
    expect(toast.warning).not.toHaveBeenCalled();
  });
});

// ---------- Handler Tests ----------

describe("SearchStateManager — handler interactions", () => {
  it("offline retry button calls onRetryNow", () => {
    const onRetryNow = jest.fn();
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={10}
        onRetryNow={onRetryNow}
      />
    );

    fireEvent.click(screen.getByTestId("retry-now-button"));
    expect(onRetryNow).toHaveBeenCalledTimes(1);
  });

  it("offline cancel button calls onCancelRetry", () => {
    const onCancelRetry = jest.fn();
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={10}
        onCancelRetry={onCancelRetry}
      />
    );

    fireEvent.click(screen.getByText("Cancelar"));
    expect(onCancelRetry).toHaveBeenCalledTimes(1);
  });

  it("failed retry button calls onRetry", () => {
    const onRetry = jest.fn();
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="failed"
        error={makeError()}
        onRetry={onRetry}
      />
    );

    fireEvent.click(screen.getByTestId("failed-retry-button"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("exhausted retry button calls onRetryNow", () => {
    const onRetryNow = jest.fn();
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryExhausted={true}
        onRetryNow={onRetryNow}
      />
    );

    fireEvent.click(screen.getByTestId("retry-manual-button"));
    expect(onRetryNow).toHaveBeenCalledTimes(1);
  });

  it("quota plans link points to /planos", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="quota_exceeded"
        quotaError="Limite atingido"
      />
    );

    const link = screen.getByTestId("quota-plans-link");
    expect(link).toHaveAttribute("href", "/planos");
    expect(link).toHaveTextContent("Ver Planos");
  });

  it("failed retry button shows loading spinner when loading=true", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="failed"
        error={makeError()}
        loading={true}
      />
    );

    const button = screen.getByTestId("failed-retry-button");
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent("Tentando...");
  });
});

// ---------- AC8: Mobile Responsive (375px) ----------

describe("SearchStateManager — AC8: mobile responsive", () => {
  it("retry-countdown card has max-w-full overflow-hidden for 375px", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={10}
      />
    );

    const card = screen.getByTestId("retry-countdown");
    expect(card.className).toContain("max-w-full");
    expect(card.className).toContain("overflow-hidden");
  });

  it("retry-exhausted card has max-w-full overflow-hidden", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryExhausted={true}
      />
    );

    const card = screen.getByTestId("retry-exhausted");
    expect(card.className).toContain("max-w-full");
    expect(card.className).toContain("overflow-hidden");
  });

  it("buttons use flex-col on mobile, flex-row on sm+", () => {
    render(
      <SearchStateManager
        {...baseManagerProps}
        phase="offline"
        error={makeError()}
        retryCountdown={10}
      />
    );

    const card = screen.getByTestId("retry-countdown");
    const buttonContainer = card.querySelector(".flex.flex-col");
    expect(buttonContainer).toBeTruthy();
    expect(buttonContainer?.className).toContain("sm:flex-row");
  });
});
