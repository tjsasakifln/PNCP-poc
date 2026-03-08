/**
 * CRIT-053 AC8: Source honesty — DataQualityBanner + SearchResults degraded sources.
 *
 * Tests:
 * 1. DataQualityBanner renders when sourcesDegraded includes PNCP
 * 2. DataQualityBanner does NOT render when sourcesDegraded is empty
 * 3. SearchResults shows degraded zero results message
 * 4. SearchResults shows normal ZeroResultsSuggestions when no degradation
 * 5. DataQualityBanner severity escalates to warning with degraded sources
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DataQualityBanner } from "../app/buscar/components/DataQualityBanner";
import type { DataQualityBannerProps } from "../app/buscar/components/DataQualityBanner";
import SearchResults from "../app/buscar/components/SearchResults";
import type { SearchResultsProps } from "../app/buscar/components/SearchResults";
import type { BuscaResult } from "../app/types";

// ---------------------------------------------------------------------------
// Mocks — heavy sub-components that SearchResults imports
// ---------------------------------------------------------------------------

jest.mock("../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => <div data-testid="refresh-banner">Refresh Banner</div>,
}));

jest.mock("../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => <div data-testid="uf-grid">UF Grid</div>,
}));

jest.mock("../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => (
    <div data-testid="sources-unavailable">Unavailable</div>
  ),
}));

jest.mock("../app/buscar/components/FilterRelaxedBanner", () => ({
  FilterRelaxedBanner: () => (
    <div data-testid="filter-relaxed-banner">Relaxed</div>
  ),
}));

jest.mock("../app/buscar/components/ExpiredCacheBanner", () => ({
  ExpiredCacheBanner: () => (
    <div data-testid="expired-cache-banner">Expired</div>
  ),
}));

jest.mock("../app/buscar/components/SearchStateManager", () => ({
  SearchStateManager: () => null,
}));

jest.mock("../app/buscar/components/ZeroResultsSuggestions", () => ({
  ZeroResultsSuggestions: ({ sectorName }: any) => (
    <div data-testid="zero-results-suggestions">
      Nenhuma oportunidade para {sectorName}
    </div>
  ),
}));

jest.mock("../app/components/QuotaCounter", () => ({
  QuotaCounter: () => <div data-testid="quota-counter">Quota</div>,
}));

jest.mock("../app/buscar/components/SearchEmptyState", () => ({
  SearchEmptyState: ({ rawCount }: any) => (
    <div data-testid="empty-state">
      Analisamos {rawCount} editais
    </div>
  ),
}));

jest.mock("../components/billing/TrialUpsellCTA", () => ({
  TrialUpsellCTA: () => null,
}));

// TD-007 sub-components
jest.mock("../app/buscar/components/search-results/ResultsHeader", () => ({
  ResultsHeader: () => <div data-testid="results-header">Header</div>,
}));

jest.mock("../app/buscar/components/search-results/ResultsToolbar", () => ({
  ResultsToolbar: () => <div data-testid="results-toolbar">Toolbar</div>,
}));

jest.mock("../app/buscar/components/search-results/ResultsFilters", () => ({
  ResultsFilters: () => <div data-testid="results-filters">Filters</div>,
}));

jest.mock("../app/buscar/components/search-results/ResultCard", () => ({
  ResultCard: () => <div data-testid="result-card">Card</div>,
}));

jest.mock("../app/buscar/components/search-results/ResultsList", () => ({
  ResultsList: () => <div data-testid="results-list">List</div>,
}));

jest.mock("../app/buscar/components/search-results/ResultsLoadingSection", () => ({
  ResultsLoadingSection: () => null,
}));

jest.mock("../app/buscar/components/search-results/ResultsFooter", () => ({
  ResultsFooter: () => <div data-testid="results-footer">Footer</div>,
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
  usePathname: () => "/buscar",
  useSearchParams: () => new URLSearchParams(),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Minimal DataQualityBanner props with nothing to report. */
function makeCleanBannerProps(
  overrides?: Partial<DataQualityBannerProps>
): DataQualityBannerProps {
  return {
    totalUfs: 5,
    succeededUfs: 5,
    failedUfs: [],
    isCached: false,
    cachedAt: null,
    cacheStatus: undefined,
    isTruncated: false,
    sourcesTotal: 3,
    sourcesAvailable: 3,
    sourceNames: ["PNCP", "PCP", "ComprasGov"],
    responseState: "live",
    coveragePct: 100,
    sourcesDegraded: [],
    onRefresh: jest.fn(),
    onRetry: jest.fn(),
    loading: false,
    ...overrides,
  };
}

/** BuscaResult with zero opportunities. */
function makeZeroResult(overrides?: Partial<BuscaResult>): BuscaResult {
  return {
    licitacoes: [],
    resumo: {
      resumo_executivo: "Nenhuma oportunidade encontrada.",
      total_oportunidades: 0,
      valor_total: 0,
      destaques: [],
    },
    total_filtrado: 0,
    total_raw: 0,
    download_id: null,
    download_url: null,
    ultima_atualizacao: new Date().toISOString(),
    cached: false,
    response_state: "live",
    source_stats: [
      { source_code: "PNCP", record_count: 0, duration_ms: 500, error: null, status: "success" },
    ],
    excel_available: false,
    upgrade_message: null,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    hidden_by_min_match: null,
    filter_relaxed: null,
    metadata: null,
    is_partial: false,
    ...overrides,
  } as BuscaResult;
}

/** Minimal SearchResultsProps for rendering SearchResults. */
function makeSearchResultsProps(
  overrides?: Partial<SearchResultsProps>
): SearchResultsProps {
  return {
    loading: false,
    loadingStep: 0,
    estimatedTime: 0,
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
    sectorName: "Engenharia",
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
    ...overrides,
  };
}

// ===========================================================================
// Test 1: DataQualityBanner renders when sourcesDegraded includes PNCP
// ===========================================================================

describe("CRIT-053 AC8: DataQualityBanner with degraded sources", () => {
  it("renders warning when sourcesDegraded includes PNCP", () => {
    const onRetry = jest.fn();

    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PNCP"],
          onRetry,
        })}
      />
    );

    // Banner should be rendered
    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toBeInTheDocument();

    // Should have amber/warning styling
    expect(banner.className).toContain("bg-amber");

    // Should contain PNCP degradation message
    expect(
      screen.getByText(/fonte principal \(PNCP\) esta com lentidao/i)
    ).toBeInTheDocument();

    // "Tentar novamente" button should be rendered (failedUfs is empty
    // but sourcesDegraded triggers warning, and isError is false so
    // the action button depends on whether isStale is set. Since
    // sourcesDegraded alone doesn't make isError or isStale true,
    // let's check with failedUfs to trigger the retry button)
  });

  it("renders 'Tentar novamente' button when PNCP is degraded and there are failed UFs", () => {
    const onRetry = jest.fn();

    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PNCP"],
          failedUfs: ["BA"],
          succeededUfs: 4,
          onRetry,
        })}
      />
    );

    const retryButton = screen.getByText("Tentar novamente");
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders non-PNCP degraded sources message", () => {
    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PCP", "ComprasGov"],
        })}
      />
    );

    expect(
      screen.getByText(/Fontes degradadas: PCP, ComprasGov/)
    ).toBeInTheDocument();
  });
});

// ===========================================================================
// Test 2: DataQualityBanner does NOT render when sourcesDegraded is empty
// ===========================================================================

describe("CRIT-053 AC8: DataQualityBanner hidden when no issues", () => {
  it("returns null when sourcesDegraded is empty and all values normal", () => {
    const { container } = render(
      <DataQualityBanner {...makeCleanBannerProps({ sourcesDegraded: [] })} />
    );

    // Banner should NOT render — hasAnythingToReport returns false
    expect(screen.queryByTestId("data-quality-banner")).not.toBeInTheDocument();
    // Container should be empty (component returns null)
    expect(container.innerHTML).toBe("");
  });

  it("returns null when sourcesDegraded is undefined and all values normal", () => {
    const { container } = render(
      <DataQualityBanner
        {...makeCleanBannerProps({ sourcesDegraded: undefined })}
      />
    );

    expect(screen.queryByTestId("data-quality-banner")).not.toBeInTheDocument();
    expect(container.innerHTML).toBe("");
  });
});

// ===========================================================================
// Test 3: SearchResults shows degraded zero results message
// ===========================================================================

describe("CRIT-053 AC8: SearchResults degraded zero results", () => {
  it("renders degraded-zero-results when sources_degraded has entries and total is 0", () => {
    const onSearch = jest.fn();
    const result = makeZeroResult({
      sources_degraded: ["PNCP"],
      response_state: "degraded",
    });

    render(
      <SearchResults
        {...makeSearchResultsProps({
          result,
          onSearch,
        })}
      />
    );

    // The degraded zero results section should be rendered
    const degradedSection = screen.getByTestId("degraded-zero-results");
    expect(degradedSection).toBeInTheDocument();

    // Should contain the PNCP unavailability message
    expect(
      screen.getByText(
        /PNCP.*esta temporariamente indisponivel/i
      )
    ).toBeInTheDocument();

    // Should have a "Tentar Novamente" button
    const retryButton = screen.getByTestId("degraded-retry-button");
    expect(retryButton).toBeInTheDocument();
    expect(retryButton.textContent).toBe("Tentar Novamente");

    // Clicking the retry button triggers onSearch
    fireEvent.click(retryButton);
    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it("renders DataQualityBanner inside degraded zero results section", () => {
    const result = makeZeroResult({
      sources_degraded: ["PNCP"],
      response_state: "degraded",
    });

    render(
      <SearchResults
        {...makeSearchResultsProps({ result })}
      />
    );

    // DataQualityBanner should be present (rendered via renderDataQualityBanner)
    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });

  it("does NOT render degraded-zero-results when response_state is empty_failure", () => {
    const result = makeZeroResult({
      sources_degraded: ["PNCP"],
      response_state: "empty_failure",
    });

    render(
      <SearchResults
        {...makeSearchResultsProps({ result })}
      />
    );

    // empty_failure path renders SourcesUnavailable instead
    expect(screen.queryByTestId("degraded-zero-results")).not.toBeInTheDocument();
    expect(screen.getByTestId("sources-unavailable")).toBeInTheDocument();
  });

  it("prefers onRetryForceFresh over onSearch for retry button", () => {
    const onSearch = jest.fn();
    const onRetryForceFresh = jest.fn();
    const result = makeZeroResult({
      sources_degraded: ["PNCP"],
      response_state: "degraded",
    });

    render(
      <SearchResults
        {...makeSearchResultsProps({
          result,
          onSearch,
          onRetryForceFresh,
        })}
      />
    );

    const retryButton = screen.getByTestId("degraded-retry-button");
    fireEvent.click(retryButton);

    // Should call onRetryForceFresh (not onSearch) when available
    expect(onRetryForceFresh).toHaveBeenCalledTimes(1);
    expect(onSearch).not.toHaveBeenCalled();
  });
});

// ===========================================================================
// Test 4: SearchResults shows normal ZeroResultsSuggestions when no degradation
// ===========================================================================

describe("CRIT-053 AC8: SearchResults normal zero results (no degradation)", () => {
  it("renders ZeroResultsSuggestions when sources_degraded is undefined", () => {
    const result = makeZeroResult({
      sources_degraded: undefined,
      is_partial: false,
      response_state: "live",
    });

    render(
      <SearchResults
        {...makeSearchResultsProps({
          result,
          sectorName: "Engenharia",
        })}
      />
    );

    // Should show ZeroResultsSuggestions (the normal empty state)
    expect(screen.getByTestId("zero-results-suggestions")).toBeInTheDocument();
    expect(
      screen.getByText(/Nenhuma oportunidade para Engenharia/)
    ).toBeInTheDocument();

    // Should NOT show degraded zero results
    expect(screen.queryByTestId("degraded-zero-results")).not.toBeInTheDocument();
  });

  it("renders ZeroResultsSuggestions when sources_degraded is empty array", () => {
    const result = makeZeroResult({
      sources_degraded: [],
      is_partial: false,
      response_state: "live",
    });

    render(
      <SearchResults
        {...makeSearchResultsProps({
          result,
          sectorName: "Vestuario",
        })}
      />
    );

    expect(screen.getByTestId("zero-results-suggestions")).toBeInTheDocument();
    expect(screen.queryByTestId("degraded-zero-results")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// Test 5: DataQualityBanner severity escalates to warning with degraded sources
// ===========================================================================

describe("CRIT-053 AC8: DataQualityBanner severity escalation", () => {
  it("derives 'warning' severity when sourcesDegraded has entries", () => {
    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PNCP"],
        })}
      />
    );

    const banner = screen.getByTestId("data-quality-banner");

    // Warning severity uses amber colors
    expect(banner.className).toContain("bg-amber");
    expect(banner.className).toContain("border-amber");
  });

  it("derives 'info' severity when sourcesDegraded is empty (with other reportable condition)", () => {
    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: [],
          // isCached makes hasAnythingToReport return true, but severity stays info
          isCached: true,
          cachedAt: new Date().toISOString(),
          cacheStatus: "fresh",
        })}
      />
    );

    const banner = screen.getByTestId("data-quality-banner");

    // Info severity uses blue colors (not amber)
    expect(banner.className).toContain("bg-blue");
    expect(banner.className).not.toContain("bg-amber");
  });

  it("derives 'error' severity when succeededUfs is 0 (overrides degraded sources)", () => {
    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PNCP"],
          succeededUfs: 0,
        })}
      />
    );

    const banner = screen.getByTestId("data-quality-banner");

    // Error severity uses red colors (takes priority over warning)
    expect(banner.className).toContain("bg-red");
  });

  it("derives 'warning' severity when sourcesDegraded has non-PNCP sources", () => {
    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PCP"],
        })}
      />
    );

    const banner = screen.getByTestId("data-quality-banner");

    // Warning severity
    expect(banner.className).toContain("bg-amber");
    expect(
      screen.getByText(/Fontes degradadas: PCP/)
    ).toBeInTheDocument();
  });

  it("includes degraded sources in pipe-separated message segments", () => {
    render(
      <DataQualityBanner
        {...makeCleanBannerProps({
          sourcesDegraded: ["PNCP"],
          failedUfs: ["BA"],
          succeededUfs: 4,
        })}
      />
    );

    // Message should include both segments: timeout count + PNCP degradation
    expect(screen.getByText(/1 timeout/)).toBeInTheDocument();
    expect(
      screen.getByText(/fonte principal \(PNCP\) esta com lentidao/)
    ).toBeInTheDocument();
  });
});
