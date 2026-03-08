/**
 * CRIT-030: State bleed between consecutive searches.
 *
 * AC1: Clicking "Buscar" clears all previous result content immediately
 * AC2: During loading, only progress/loading component is visible
 * AC3: Empty state only renders when !loading && result && result.licitacoes.length === 0
 * AC4: "Atualizando dados..." banner disappears when search concludes
 * AC5: Search sector A → search sector B → empty state A not visible during B loading
 * AC6: Empty state with "302 editais" doesn't persist after new search
 * AC7: Zero regression
 */
import React from "react";
import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import SearchResults from "../../app/buscar/components/SearchResults";
import type { SearchResultsProps } from "../../app/buscar/components/SearchResults";
import type { BuscaResult } from "../../app/types";

// Mock all imported components that aren't under test
jest.mock("../../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: ({ currentStep }: any) => (
    <div data-testid="loading-progress">Loading step {currentStep}</div>
  ),
}));

jest.mock("../../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => <div data-testid="loading-skeleton">Skeleton</div>,
}));

jest.mock("../../app/buscar/components/SearchEmptyState", () => ({
  SearchEmptyState: ({ rawCount }: any) => (
    <div data-testid="empty-state">
      Analisamos {rawCount} editais e nenhum correspondeu
    </div>
  ),
}));

jest.mock("../../app/buscar/components/ZeroResultsSuggestions", () => ({
  ZeroResultsSuggestions: ({ sectorName }: any) => (
    <div data-testid="zero-results-suggestions">
      Nenhuma oportunidade para {sectorName}
    </div>
  ),
}));

jest.mock("../../app/buscar/components/PartialTimeoutBanner", () => ({
  PartialTimeoutBanner: () => <div data-testid="partial-timeout-banner">Partial Timeout</div>,
}));

jest.mock("../../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => <div data-testid="refresh-banner">Refresh Banner</div>,
}));

jest.mock("../../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => <div data-testid="uf-grid">UF Grid</div>,
}));

jest.mock("../../app/buscar/components/PartialResultsPrompt", () => ({
  PartialResultsPrompt: () => <div data-testid="partial-prompt">Partial</div>,
  PartialResultsBanner: () => <div data-testid="partial-banner">Partial Banner</div>,
  FailedUfsBanner: () => <div data-testid="failed-ufs">Failed UFs</div>,
}));

jest.mock("../../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => <div data-testid="sources-unavailable">Unavailable</div>,
}));

jest.mock("../../app/buscar/components/DataQualityBanner", () => ({
  DataQualityBanner: () => <div data-testid="data-quality-banner">Data Quality</div>,
}));

jest.mock("../../app/buscar/components/TruncationWarningBanner", () => ({
  TruncationWarningBanner: () => <div data-testid="truncation">Truncated</div>,
}));

jest.mock("../../app/components/QuotaCounter", () => ({
  QuotaCounter: () => <div data-testid="quota-counter">Quota</div>,
}));

jest.mock("../../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: () => <div data-testid="licitacoes-preview">Licitacoes</div>,
}));

jest.mock("../../app/components/OrdenacaoSelect", () => ({
  OrdenacaoSelect: () => <div data-testid="ordenacao-select">Sort</div>,
}));

jest.mock("../../components/GoogleSheetsExportButton", () => ({
  __esModule: true,
  default: () => <div data-testid="gsheets">GSheets</div>,
}));

jest.mock("../../app/buscar/components/LlmSourceBadge", () => ({
  LlmSourceBadge: () => <div data-testid="llm-badge">LLM Badge</div>,
}));

jest.mock("../../app/buscar/components/ErrorDetail", () => ({
  ErrorDetail: () => <div data-testid="error-detail">Error Detail</div>,
}));

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeEmptyResult(rawCount: number = 302): BuscaResult {
  return {
    licitacoes: [],
    resumo: {
      resumo_executivo: "Nenhuma oportunidade encontrada.",
      total_oportunidades: 0,
      valor_total: 0,
      destaques: [],
    },
    total_filtrado: 0,
    total_raw: rawCount,
    download_id: null,
    ultima_atualizacao: new Date().toISOString(),
    cached: false,
    response_state: "live",
  } as any;
}

function makeResultWithOpportunities(count: number = 5): BuscaResult {
  return {
    licitacoes: Array.from({ length: count }, (_, i) => ({
      orgao: `Orgao ${i}`,
      objeto: `Objeto ${i}`,
      valor_estimado: 100000 * (i + 1),
      uf: "SP",
      confidence: "high",
    })),
    resumo: {
      resumo_executivo: "Encontramos oportunidades.",
      total_oportunidades: count,
      valor_total: count * 100000,
      destaques: [],
    },
    total_filtrado: count,
    total_raw: count * 10,
    download_id: "dl-123",
    ultima_atualizacao: new Date().toISOString(),
    cached: false,
    response_state: "live",
  } as any;
}

const defaultProps: SearchResultsProps = {
  loading: false,
  loadingStep: 1,
  estimatedTime: 30,
  stateCount: 5,
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
  ufsSelecionadas: new Set(["SP", "RJ"]),
  sectorName: "Informática",
  searchMode: "setor",
  termosArray: [],
  ordenacao: "relevancia" as any,
  onOrdenacaoChange: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),
  planInfo: null,
  session: null,
  onShowUpgradeModal: jest.fn(),
  onTrackEvent: jest.fn(),
};

// ===========================================================================
// AC1: Clicking "Buscar" clears all previous result content
// ===========================================================================

describe("CRIT-030 AC1: Previous content clears on new search", () => {
  it("empty state is NOT visible when loading=true and result=null", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={null}
        rawCount={0}
      />
    );

    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("loading progress IS visible when loading=true", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={null}
      />
    );

    expect(screen.getByTestId("loading-progress")).toBeInTheDocument();
  });
});

// ===========================================================================
// AC2: During loading, only progress/loading is visible
// ===========================================================================

describe("CRIT-030 AC2: Only loading state during search", () => {
  it("no results display when loading=true even if result object exists", () => {
    // This tests the case where result hasn't been cleared yet (React batch timing)
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={makeEmptyResult(302)}
        rawCount={302}
      />
    );

    // Loading should be visible
    expect(screen.getByTestId("loading-progress")).toBeInTheDocument();
    // Empty state should NOT be visible (guarded by !loading)
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("no cache banner when loading=true even if result is cached", () => {
    const cachedResult = {
      ...makeEmptyResult(),
      cached: true,
      cached_at: new Date().toISOString(),
    };

    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={cachedResult as any}
      />
    );

    expect(screen.queryByTestId("cache-banner")).not.toBeInTheDocument();
  });

  it("no partial timeout banner when loading=true", () => {
    const partialResult = {
      ...makeResultWithOpportunities(3),
      failed_ufs: ["BA", "MG"],
    };

    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={partialResult as any}
      />
    );

    expect(screen.queryByTestId("partial-timeout-banner")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// AC3: Empty state only renders when !loading && result && total === 0
// ===========================================================================

describe("CRIT-030 AC3: Empty state guard conditions", () => {
  it("shows empty state when !loading && result && total_oportunidades === 0", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={false}
        result={makeEmptyResult(302)}
        rawCount={302}
      />
    );

    // HARDEN-025: When total_raw > 0 && total_filtrado === 0, EmptyResults is shown instead of ZeroResultsSuggestions
    expect(screen.getByTestId("empty-results")).toBeInTheDocument();
  });

  it("does NOT show empty state when loading=true", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={makeEmptyResult(302)}
        rawCount={302}
      />
    );

    expect(screen.queryByTestId("zero-results-suggestions")).not.toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("does NOT show empty state when result is null", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={false}
        result={null}
      />
    );

    expect(screen.queryByTestId("zero-results-suggestions")).not.toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// AC4: "Atualizando dados..." banner visibility
// ===========================================================================

describe("CRIT-030 AC4: Live fetch banner lifecycle", () => {
  it("live fetch banner disappears when loading starts (new search)", () => {
    const cachedResult = {
      ...makeResultWithOpportunities(3),
      cached: false,
    };

    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={cachedResult as any}
        liveFetchInProgress={true}
      />
    );

    // The "Atualizando dados..." banner has !loading guard
    expect(screen.queryByText(/Atualizando dados em tempo real/)).not.toBeInTheDocument();
  });

  it("refresh banner not shown during loading", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        refreshAvailable={{ newCount: 5, updatedCount: 2, removedCount: 0, totalLive: 10, totalCached: 7 } as any}
        onRefreshResults={jest.fn()}
      />
    );

    expect(screen.queryByTestId("refresh-banner")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// AC5: Search A → Search B → A's empty state not visible during B
// ===========================================================================

describe("CRIT-030 AC5: Cross-search state isolation", () => {
  it("sector A empty state not visible during sector B loading", () => {
    // Simulates the exact bug scenario:
    // 1. Search Vestuário completes with 0 results (302 raw analyzed)
    // 2. User switches to Engenharia and clicks Buscar
    // 3. During Engenharia loading, Vestuário empty state should NOT appear

    // State after search A completes but before search B clears result:
    // loading=true (search B started), result still exists from A
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={makeEmptyResult(302)}
        rawCount={302}
        sectorName="Vestuário"
      />
    );

    // Vestuário's empty state with "302 editais" must NOT appear
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
    expect(screen.queryByText(/302 editais/)).not.toBeInTheDocument();

    // Loading progress should be visible
    expect(screen.getByTestId("loading-progress")).toBeInTheDocument();
  });

  it("sector A results not visible during sector B loading", () => {
    render(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={makeResultWithOpportunities(5)}
        rawCount={50}
        sectorName="Vestuário"
      />
    );

    // Results header should NOT appear during loading
    expect(screen.queryByTestId("results-header")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// AC6: "302 editais" message doesn't persist after new search
// ===========================================================================

describe("CRIT-030 AC6: Stale content cleanup", () => {
  it("302 editais empty state disappears when result is null", () => {
    const { rerender } = render(
      <SearchResults
        {...defaultProps}
        loading={false}
        result={makeEmptyResult(302)}
        rawCount={302}
      />
    );

    // HARDEN-025: When total_raw > 0 && total_filtrado === 0, EmptyResults is shown
    expect(screen.getByTestId("empty-results")).toBeInTheDocument();

    // Simulate new search: result=null, loading=true
    rerender(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={null}
        rawCount={0}
      />
    );

    // Empty results gone
    expect(screen.queryByTestId("empty-results")).not.toBeInTheDocument();
    expect(screen.queryByTestId("zero-results-suggestions")).not.toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("data quality banner disappears when new search starts", () => {
    const cachedResult = {
      ...makeResultWithOpportunities(3),
      cached: true,
      cached_at: new Date().toISOString(),
    };

    const { rerender } = render(
      <SearchResults
        {...defaultProps}
        loading={false}
        result={cachedResult as any}
        rawCount={30}
      />
    );

    // DataQualityBanner (replaced CacheBanner) should be visible when there are results
    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();

    // New search starts
    rerender(
      <SearchResults
        {...defaultProps}
        loading={true}
        result={null}
        rawCount={0}
      />
    );

    // Data quality banner gone (loading guard)
    expect(screen.queryByTestId("data-quality-banner")).not.toBeInTheDocument();
    expect(screen.queryByTestId("cache-banner")).not.toBeInTheDocument();
  });
});
