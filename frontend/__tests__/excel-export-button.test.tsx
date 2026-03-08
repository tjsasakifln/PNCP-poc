/**
 * UX-349 T1-T9: Excel export button visibility and state tests.
 *
 * AC8: Button appears when results exist
 * AC9: States (processing/ready/failed) render correctly
 * AC10: Zero regressions (verified by running full suite)
 */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---- Module mocks (hoisted by Jest) ----

jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  );
});

jest.mock("../hooks/useSearchSSE", () => ({
  useSearchSSE: () => ({
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
  }),
}));

// Mock child components that aren't relevant to Excel button tests
jest.mock("../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: () => null,
}));
jest.mock("../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => null,
}));
jest.mock("../app/buscar/components/SearchEmptyState", () => ({
  SearchEmptyState: () => null,
}));
jest.mock("../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => null,
}));
jest.mock("../app/buscar/components/PartialResultsPrompt", () => ({
  PartialResultsPrompt: () => null,
  PartialResultsBanner: () => null,
  FailedUfsBanner: () => null,
}));
jest.mock("../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => null,
}));
jest.mock("../app/buscar/components/TruncationWarningBanner", () => ({
  TruncationWarningBanner: () => null,
}));
jest.mock("../app/components/QuotaCounter", () => ({
  QuotaCounter: () => null,
}));
jest.mock("../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: () => null,
}));
jest.mock("../app/components/OrdenacaoSelect", () => ({
  OrdenacaoSelect: () => null,
}));
jest.mock("../app/buscar/components/LlmSourceBadge", () => ({
  LlmSourceBadge: () => null,
}));
jest.mock("../app/buscar/components/ErrorDetail", () => ({
  ErrorDetail: () => null,
}));
jest.mock("../app/buscar/components/PartialTimeoutBanner", () => ({
  PartialTimeoutBanner: () => null,
}));
jest.mock("../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../components/GoogleSheetsExportButton", () => ({
  __esModule: true,
  default: () => <button data-testid="google-sheets-button">Google Sheets</button>,
}));

// ---- Import component under test ----
import SearchResults from "../app/buscar/components/SearchResults";
import type { BuscaResult } from "../app/types";

// ---- Test helpers ----

const BASE_PLAN_INFO = {
  plan_id: "smartlic_pro",
  plan_name: "SmartLic Pro",
  quota_used: 5,
  quota_reset_date: "2026-03-01",
  capabilities: {
    max_history_days: 1825,
    max_requests_per_month: 1000,
    allow_excel: true,
  },
};

const FREE_PLAN_INFO = {
  ...BASE_PLAN_INFO,
  plan_id: "free_trial",
  plan_name: "Trial",
  capabilities: {
    max_history_days: 30,
    max_requests_per_month: 10,
    allow_excel: false,
  },
};

function makeResult(overrides: Partial<BuscaResult> = {}): BuscaResult {
  return {
    resumo: {
      resumo_executivo: "Resumo de teste",
      total_oportunidades: 5,
      valor_total: 100000,
      destaques: [],
    } as any,
    licitacoes: [{ id: "1" }] as any,
    download_id: null,
    download_url: null,
    total_raw: 10,
    total_filtrado: 5,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    excel_available: true,
    upgrade_message: null,
    source_stats: null,
    ...overrides,
  };
}

const DEFAULT_PROPS = {
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
  rawCount: 10,
  ufsSelecionadas: new Set(["SP", "RJ"]),
  sectorName: "Informática",
  searchMode: "setor" as const,
  termosArray: [] as string[],
  ordenacao: "relevancia" as any,
  onOrdenacaoChange: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),
  session: { access_token: "test-token" },
  onShowUpgradeModal: jest.fn(),
  onTrackEvent: jest.fn(),
};

// ===========================================================================
// T1: AC8 — Excel button appears when results exist
// ===========================================================================

describe("T1: Excel button visible with results (AC8)", () => {
  it("should show active download button when results exist with download_url", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ download_url: "https://example.com/file.xlsx", excel_status: "ready" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
    expect(btn).toHaveTextContent("Baixar Excel (5 licitações)");
  });

  it("should show active download button when results exist with download_id", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ download_id: "abc-123", excel_status: "ready" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });

  it("should show active button when excel_status is null (inline fallback)", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ download_url: "https://example.com/file.xlsx", excel_status: null })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });

  it("should show upgrade link when plan does not allow Excel", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult()}
        planInfo={FREE_PLAN_INFO}
      />,
    );
    expect(screen.queryByTestId("excel-download-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("excel-processing-button")).not.toBeInTheDocument();
    expect(
      screen.getByText(/Assine para exportar/),
    ).toBeInTheDocument();
  });
});

// ===========================================================================
// T2: AC2 — Processing state shows spinner
// ===========================================================================

describe("T2: Processing state (AC2)", () => {
  it("should show processing spinner when excel_status is processing and no download", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ excel_status: "processing" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-processing-button");
    expect(btn).toBeInTheDocument();
    expect(btn).toBeDisabled();
    expect(btn).toHaveTextContent("Gerando Excel...");
  });

  it("should show active button if processing but download_url already set (SSE arrived)", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({
          excel_status: "processing",
          download_url: "https://example.com/file.xlsx",
        })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    // Should show active button because download is available
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });
});

// ===========================================================================
// T3: AC3 — Ready state shows count
// ===========================================================================

describe("T3: Ready state with count (AC3)", () => {
  it("should show button with licitações count", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({
          download_url: "https://example.com/file.xlsx",
          excel_status: "ready",
        })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toHaveTextContent("Baixar Excel (5 licitações)");
  });

  it("should use singular form for single licitação", () => {
    const result = makeResult({
      download_url: "https://example.com/file.xlsx",
      excel_status: "ready",
    });
    result.resumo.total_oportunidades = 1;

    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={result}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toHaveTextContent("Baixar Excel (1 licitação)");
  });
});

// ===========================================================================
// T4: AC4 — Failed state shows retry button
// ===========================================================================

describe("T4: Failed state with retry (AC4)", () => {
  it("should show retry button when excel_status is failed", () => {
    const onSearch = jest.fn();
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        onSearch={onSearch}
        result={makeResult({ excel_status: "failed" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-retry-button");
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveTextContent("Gerar novamente");

    fireEvent.click(btn);
    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it("should NOT show retry when failed but download_url exists", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({
          excel_status: "failed",
          download_url: "https://example.com/old-file.xlsx",
        })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    // download_url exists → show active button instead
    expect(screen.queryByTestId("excel-retry-button")).not.toBeInTheDocument();
    expect(screen.getByTestId("excel-download-button")).toBeInTheDocument();
  });
});

// ===========================================================================
// T5: AC4 — Processing timeout triggers retry
// ===========================================================================

describe("T5: Processing timeout (AC4)", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it("should show retry button after 60s of processing", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ excel_status: "processing" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );

    // Initially in processing state
    expect(screen.getByTestId("excel-processing-button")).toBeInTheDocument();
    expect(screen.queryByTestId("excel-retry-button")).not.toBeInTheDocument();

    // Advance 60 seconds
    act(() => {
      jest.advanceTimersByTime(60_000);
    });

    // Should now show retry
    expect(screen.queryByTestId("excel-processing-button")).not.toBeInTheDocument();
    expect(screen.getByTestId("excel-retry-button")).toBeInTheDocument();
  });

  it("should NOT timeout if download becomes available", () => {
    const { rerender } = render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ excel_status: "processing" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );

    // Start in processing
    expect(screen.getByTestId("excel-processing-button")).toBeInTheDocument();

    // SSE delivers download_url before timeout
    act(() => {
      jest.advanceTimersByTime(20_000);
    });

    rerender(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({
          excel_status: "processing",
          download_url: "https://example.com/file.xlsx",
        })}
        planInfo={BASE_PLAN_INFO}
      />,
    );

    // Should show active button (download available overrides processing)
    expect(screen.getByTestId("excel-download-button")).toBeInTheDocument();
    expect(screen.queryByTestId("excel-processing-button")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// T6: AC5 — Inline fallback (no ARQ) shows active button
// ===========================================================================

describe("T6: Inline fallback (AC5)", () => {
  it("should show active button when excel_status is null with download_id (inline mode)", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ excel_status: null, download_id: "inline-123" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });

  it("should show active button when excel_status is undefined (backward compat)", () => {
    const result = makeResult();
    delete (result as any).excel_status;
    result.download_url = "https://example.com/file.xlsx";

    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={result}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    const btn = screen.getByTestId("excel-download-button");
    expect(btn).toBeInTheDocument();
  });
});

// ===========================================================================
// T7: Download button calls onDownload handler
// ===========================================================================

describe("T7: Download handler integration", () => {
  it("should call onDownload when active button is clicked", () => {
    const onDownload = jest.fn();
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        onDownload={onDownload}
        result={makeResult({ download_url: "https://example.com/file.xlsx" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    fireEvent.click(screen.getByTestId("excel-download-button"));
    expect(onDownload).toHaveBeenCalledTimes(1);
  });

  it("should show 'Preparando download...' when downloadLoading is true", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        downloadLoading={true}
        result={makeResult({ download_url: "https://example.com/file.xlsx" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    expect(screen.getByText("Preparando download...")).toBeInTheDocument();
  });
});

// ===========================================================================
// T8: Google Sheets button renders (AC7)
// ===========================================================================

describe("T8: Google Sheets button (AC7)", () => {
  it("should render Google Sheets button when plan allows Excel", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult({ download_url: "https://example.com/file.xlsx" })}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    expect(screen.getByTestId("google-sheets-button")).toBeInTheDocument();
  });

  it("should NOT render Google Sheets button when plan does not allow Excel", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={makeResult()}
        planInfo={FREE_PLAN_INFO}
      />,
    );
    expect(screen.queryByTestId("google-sheets-button")).not.toBeInTheDocument();
  });
});

// ===========================================================================
// T9: No button when no results
// ===========================================================================

describe("T9: No button without results", () => {
  it("should not show any download button when result is null", () => {
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={null}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    expect(screen.queryByTestId("excel-download-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("excel-processing-button")).not.toBeInTheDocument();
    expect(screen.queryByTestId("excel-retry-button")).not.toBeInTheDocument();
  });

  it("should not show download button when total_oportunidades is 0", () => {
    const result = makeResult();
    result.resumo.total_oportunidades = 0;
    render(
      <SearchResults
        {...DEFAULT_PROPS}
        result={result}
        planInfo={BASE_PLAN_INFO}
      />,
    );
    expect(screen.queryByTestId("excel-download-button")).not.toBeInTheDocument();
  });
});
