/**
 * COPY-378: Success state filter context line
 *
 * Tests:
 * - AC1+AC2: Shows "Analisamos X oportunidades e selecionamos Y compatíveis com seu perfil"
 * - AC3: Graceful degradation — line not shown when filterSummary is null
 * - AC5: 3 scenarios — with stats, without stats, zero results
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks — must appear before component imports
// ---------------------------------------------------------------------------

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  })),
  usePathname: jest.fn(() => "/buscar"),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  );
});

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: null, user: null, loading: false }),
}));

jest.mock("../../hooks/useQuota", () => ({
  useQuota: () => ({
    quota: null,
    loading: false,
    error: null,
    refetch: jest.fn(),
  }),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  },
}));

jest.mock("../../lib/error-messages", () => ({
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
  ERROR_CODE_MESSAGES: {},
}));

jest.mock("../../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: () => null,
}));

jest.mock("../../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => null,
}));

jest.mock("../../app/buscar/components/SearchEmptyState", () => ({
  SearchEmptyState: () => null,
}));

jest.mock("../../app/buscar/components/ZeroResultsSuggestions", () => ({
  ZeroResultsSuggestions: () => null,
}));

jest.mock("../../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("../../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => null,
}));

jest.mock("../../app/buscar/components/PartialResultsPrompt", () => ({
  PartialResultsPrompt: () => null,
}));

jest.mock("../../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => null,
}));

jest.mock("../../app/buscar/components/DataQualityBanner", () => ({
  DataQualityBanner: () => null,
}));

jest.mock("../../app/components/QuotaCounter", () => ({
  QuotaCounter: () => null,
}));

jest.mock("../../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: () => <div data-testid="licitacoes-preview">Preview</div>,
}));

jest.mock("../../app/components/OrdenacaoSelect", () => ({
  OrdenacaoSelect: () => null,
}));

jest.mock("../../components/GoogleSheetsExportButton", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("../../app/buscar/components/LlmSourceBadge", () => ({
  LlmSourceBadge: () => null,
}));

jest.mock("../../app/buscar/components/ErrorDetail", () => ({
  ErrorDetail: () => null,
}));

jest.mock("../../app/buscar/components/FilterRelaxedBanner", () => ({
  FilterRelaxedBanner: () => null,
}));

jest.mock("../../app/buscar/components/ExpiredCacheBanner", () => ({
  ExpiredCacheBanner: () => null,
}));

jest.mock("../../app/buscar/components/SourceStatusGrid", () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock("../../app/buscar/components/SearchStateManager", () => ({
  SearchStateManager: () => null,
}));

jest.mock("../../app/buscar/types/searchPhase", () => ({
  deriveSearchPhase: () => "idle",
}));

jest.mock("../../components/billing/TrialUpsellCTA", () => ({
  TrialUpsellCTA: () => null,
}));

jest.mock("../../components/billing/TrialPaywall", () => ({
  TrialPaywall: () => null,
}));

jest.mock("../../components/ui/Pagination", () => ({
  Pagination: () => null,
  useInitPagination: () => ({
    currentPage: 1,
    pageSize: 20,
    setCurrentPage: jest.fn(),
    setPageSize: jest.fn(),
  }),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, className, ...rest }: any) => (
      <div className={className} {...rest}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// ---------------------------------------------------------------------------
// Component imports — after mocks
// ---------------------------------------------------------------------------

import SearchResults from "../../app/buscar/components/SearchResults";
import type { SearchResultsProps } from "../../app/buscar/components/SearchResults";
import type { BuscaResult } from "../../app/types";
import type { FilterSummary } from "../../hooks/useSearchSSE";

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeResult(overrides: Partial<BuscaResult> = {}): BuscaResult {
  return {
    resumo: {
      titulo: "Test",
      descricao: "",
      recomendacoes: [],
      total_oportunidades: 5,
      valor_total: 1000,
    } as any,
    licitacoes: Array.from({ length: 5 }, (_, i) => ({
      orgao: `Orgao ${i}`,
      objeto: `Objeto ${i}`,
      valor_estimado: 100000 * (i + 1),
      uf: "SP",
      pncp_id: `pncp-${i}`,
    })) as any,
    download_id: null,
    total_raw: 1200,
    total_filtrado: 5,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    excel_available: false,
    upgrade_message: null,
    source_stats: null,
    pending_review_count: 0,
    ...overrides,
  };
}

function makeDefaultProps(overrides: Partial<SearchResultsProps> = {}): SearchResultsProps {
  return {
    loading: false,
    loadingStep: 1,
    estimatedTime: 30,
    stateCount: 5,
    statesProcessed: 5,
    onCancel: jest.fn(),
    sseEvent: null,
    useRealProgress: false,
    sseAvailable: false,
    onStageChange: jest.fn(),
    error: null,
    quotaError: null,
    result: makeResult(),
    rawCount: 1200,
    ufsSelecionadas: new Set(["SP"]),
    sectorName: "Tecnologia",
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
    pendingReviewCount: 0,
    pendingReviewUpdate: null,
    ...overrides,
  };
}

// ===========================================================================
// Tests
// ===========================================================================

describe("COPY-378: Filter context line", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // AC1+AC2: With filterSummary available — shows context line
  it("AC1+AC2: shows filter context line with totalRaw from filterSummary", () => {
    const filterSummary: FilterSummary = {
      totalRaw: 1200,
      totalFiltered: 5,
      rejectedKeyword: 800,
      rejectedValue: 300,
      rejectedLlm: 95,
    };
    const props = makeDefaultProps({ filterSummary });
    render(<SearchResults {...props} />);

    const line = screen.getByTestId("filter-context-line");
    expect(line).toBeInTheDocument();
    expect(line).toHaveTextContent(
      /Analisamos 1\.200 oportunidades e selecionamos 5 compatíveis com seu perfil/
    );
  });

  // AC1: Singular form — "1 compatível"
  it("AC1: uses singular 'compatível' when 1 result", () => {
    const result = makeResult({
      resumo: {
        titulo: "Test",
        descricao: "",
        recomendacoes: [],
        total_oportunidades: 1,
        valor_total: 500,
      } as any,
      licitacoes: [{
        orgao: "Orgao 1",
        objeto: "Objeto 1",
        valor_estimado: 500,
        uf: "SP",
        pncp_id: "pncp-1",
      }] as any,
    });
    const filterSummary: FilterSummary = {
      totalRaw: 800,
      totalFiltered: 1,
      rejectedKeyword: 500,
      rejectedValue: 200,
      rejectedLlm: 99,
    };
    const props = makeDefaultProps({ result, filterSummary });
    render(<SearchResults {...props} />);

    const line = screen.getByTestId("filter-context-line");
    expect(line).toHaveTextContent(
      /selecionamos 1 compatível com seu perfil/
    );
    // Must NOT say "compatíveis"
    expect(line.textContent).not.toMatch(/compatíveis/);
  });

  // AC3: Without filterSummary — line not shown (graceful degradation)
  it("AC3: does not show filter context line when filterSummary is null", () => {
    const props = makeDefaultProps({ filterSummary: null });
    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("filter-context-line")).not.toBeInTheDocument();
  });

  it("AC3: does not show filter context line when filterSummary is undefined", () => {
    const props = makeDefaultProps({ filterSummary: undefined });
    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("filter-context-line")).not.toBeInTheDocument();
  });

  // AC4: Discreet style — text-sm, text-ink-secondary
  it("AC4: uses discreet styling (text-sm text-ink-secondary)", () => {
    const filterSummary: FilterSummary = {
      totalRaw: 500,
      totalFiltered: 10,
      rejectedKeyword: 300,
      rejectedValue: 100,
      rejectedLlm: 90,
    };
    const props = makeDefaultProps({ filterSummary });
    render(<SearchResults {...props} />);

    const line = screen.getByTestId("filter-context-line");
    expect(line.className).toContain("text-sm");
    expect(line.className).toContain("text-ink-secondary");
  });

  // AC5 scenario 3: Zero results — results section not rendered
  it("AC5: filter context line not shown when zero results (total_oportunidades=0)", () => {
    const result = makeResult({
      resumo: {
        titulo: "Test",
        descricao: "",
        recomendacoes: [],
        total_oportunidades: 0,
        valor_total: 0,
      } as any,
      licitacoes: [],
    });
    const filterSummary: FilterSummary = {
      totalRaw: 1200,
      totalFiltered: 0,
      rejectedKeyword: 1000,
      rejectedValue: 200,
      rejectedLlm: 0,
    };
    const props = makeDefaultProps({ result, filterSummary });
    render(<SearchResults {...props} />);

    // With 0 results, the results section isn't rendered at all
    expect(screen.queryByTestId("filter-context-line")).not.toBeInTheDocument();
  });

  // Edge case: filterSummary with totalRaw=0 — don't show line
  it("does not show filter context line when totalRaw is 0", () => {
    const filterSummary: FilterSummary = {
      totalRaw: 0,
      totalFiltered: 0,
      rejectedKeyword: 0,
      rejectedValue: 0,
      rejectedLlm: 0,
    };
    const props = makeDefaultProps({ filterSummary });
    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("filter-context-line")).not.toBeInTheDocument();
  });
});
