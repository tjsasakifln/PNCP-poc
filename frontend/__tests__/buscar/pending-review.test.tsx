/**
 * STORY-354: Pending Review Banner — Frontend Tests
 *
 * Tests the pending review banner in SearchResults component:
 * - Blue info banner when pendingReviewCount > 0 (AI temporarily unavailable)
 * - Green success banner when reclassification completes (pendingReviewUpdate)
 * - Singular/plural text for 1 vs multiple bids
 * - data-testid="pending-review-banner" presence
 * - No banner when pendingReviewCount is 0 and no update
 * - Reclassification with rejected count shows "descartadas" text
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

// Mock heavy sub-components to avoid deep dependency chains
jest.mock("../../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: () => null,
}));

jest.mock("../../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => null,
}));

jest.mock("../../app/components/EmptyState", () => ({
  EmptyState: () => null,
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
    total_raw: 10,
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
    rawCount: 10,
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

describe("STORY-354: Pending Review Banner", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders pending review banner when pendingReviewCount > 0", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 3,
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    expect(banner).toBeInTheDocument();
    // Blue info styling
    expect(banner.className).toContain("bg-blue-50");
    expect(banner.className).toContain("border-blue-200");
    // Correct message text
    expect(banner).toHaveTextContent(
      "3 oportunidades aguardam reclassificação (IA temporariamente indisponível)"
    );
  });

  it("does not render banner when pendingReviewCount is 0 and no update", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 0,
      pendingReviewUpdate: null,
    });
    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("pending-review-banner")).not.toBeInTheDocument();
  });

  it("renders reclassification complete banner when pendingReviewUpdate has reclassifiedCount > 0", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 0,
      pendingReviewUpdate: {
        reclassifiedCount: 5,
        acceptedCount: 3,
        rejectedCount: 2,
      },
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    expect(banner).toBeInTheDocument();
    // Green success styling
    expect(banner.className).toContain("bg-emerald-50");
    expect(banner.className).toContain("border-emerald-200");
    // Correct message text
    expect(banner).toHaveTextContent("Reclassificação concluída: 3 oportunidades confirmadas");
    expect(banner).toHaveTextContent("2 descartadas");
  });

  it("shows correct singular text for 1 bid pending review", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 1,
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    expect(banner).toHaveTextContent(
      "1 oportunidade aguarda reclassificação (IA temporariamente indisponível)"
    );
    // Confirm singular form (NOT "oportunidades aguardam")
    expect(banner).not.toHaveTextContent("oportunidades aguardam");
  });

  it("shows correct plural text for multiple bids pending review", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 5,
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    expect(banner).toHaveTextContent(
      "5 oportunidades aguardam reclassificação (IA temporariamente indisponível)"
    );
    // Confirm plural form (NOT "oportunidade aguarda")
    expect(banner).not.toHaveTextContent("oportunidade aguarda");
  });

  it("banner has correct data-testid attribute", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 2,
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    expect(banner).toBeInTheDocument();
    expect(banner.getAttribute("data-testid")).toBe("pending-review-banner");
  });

  it("reclassification banner without rejected shows only confirmadas", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 0,
      pendingReviewUpdate: {
        reclassifiedCount: 4,
        acceptedCount: 4,
        rejectedCount: 0,
      },
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    expect(banner).toHaveTextContent("Reclassificação concluída: 4 oportunidades confirmadas");
    // No "descartadas" text when rejectedCount is 0
    expect(banner).not.toHaveTextContent("descartadas");
  });

  it("reclassification update takes priority over pendingReviewCount", () => {
    // When both pendingReviewCount > 0 AND pendingReviewUpdate has reclassifiedCount > 0,
    // the green success banner (reclassification complete) should be shown
    const props = makeDefaultProps({
      pendingReviewCount: 3,
      pendingReviewUpdate: {
        reclassifiedCount: 3,
        acceptedCount: 2,
        rejectedCount: 1,
      },
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    // Should show the green success banner, not the blue info one
    expect(banner.className).toContain("bg-emerald-50");
    expect(banner).toHaveTextContent("Reclassificação concluída");
    expect(banner).not.toHaveTextContent("aguardam reclassificação");
  });

  it("does not render banner when pendingReviewUpdate has reclassifiedCount of 0", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 0,
      pendingReviewUpdate: {
        reclassifiedCount: 0,
        acceptedCount: 0,
        rejectedCount: 0,
      },
    });
    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("pending-review-banner")).not.toBeInTheDocument();
  });

  it("does not render banner during loading even with pendingReviewCount > 0", () => {
    const props = makeDefaultProps({
      loading: true,
      pendingReviewCount: 5,
    });
    render(<SearchResults {...props} />);

    // The banner is inside the results block which is guarded by !loading
    expect(screen.queryByTestId("pending-review-banner")).not.toBeInTheDocument();
  });

  it("blue banner has blue icon color", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 2,
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    const svg = banner.querySelector("svg");
    expect(svg).toBeTruthy();
    // SVG elements use getAttribute("class") in jsdom, not .className
    expect(svg!.getAttribute("class")).toContain("text-blue-500");
  });

  it("green banner has emerald icon color", () => {
    const props = makeDefaultProps({
      pendingReviewCount: 0,
      pendingReviewUpdate: {
        reclassifiedCount: 2,
        acceptedCount: 2,
        rejectedCount: 0,
      },
    });
    render(<SearchResults {...props} />);

    const banner = screen.getByTestId("pending-review-banner");
    const svg = banner.querySelector("svg");
    expect(svg).toBeTruthy();
    // SVG elements use getAttribute("class") in jsdom, not .className
    expect(svg!.getAttribute("class")).toContain("text-emerald-500");
  });
});
