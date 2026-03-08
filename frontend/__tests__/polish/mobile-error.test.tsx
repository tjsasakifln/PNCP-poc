/**
 * GTM-POLISH-002: Mobile Error States
 *
 * T1: Auto-retry card renders without overflow at 375px
 *   - retry-countdown has `max-w-full overflow-hidden` classes
 *   - Buttons stack vertically via `flex-col sm:flex-row`
 * T2: ErrorDetail expandable section is scrollable (has `overflow-y-auto` class)
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks required BEFORE component imports
// ---------------------------------------------------------------------------

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// next/link mock (SearchResults uses <Link>)
jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// next/navigation mock
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// Heavy sub-components that don't matter for these tests
jest.mock("../../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => null,
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
  LicitacoesPreview: () => null,
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

jest.mock("../../app/buscar/components/ZeroResultsSuggestions", () => ({
  ZeroResultsSuggestions: () => null,
}));

// ---------------------------------------------------------------------------
// Imports (after mocks)
// ---------------------------------------------------------------------------

import SearchResults from "../../app/buscar/components/SearchResults";
import { ErrorDetail } from "../../app/buscar/components/ErrorDetail";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Minimal valid props for SearchResults — only what's needed to mount it */
function makeMinimalProps(overrides: Record<string, any> = {}) {
  return {
    loading: false,
    loadingStep: 0,
    estimatedTime: 30,
    stateCount: 27,
    statesProcessed: 0,
    onCancel: jest.fn(),
    sseEvent: null,
    useRealProgress: false,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    onStageChange: jest.fn(),
    error: null,
    quotaError: null,
    result: null,
    rawCount: 0,
    ufsSelecionadas: new Set<string>(),
    sectorName: "Vestuário",
    searchMode: "setor" as const,
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

// ---------------------------------------------------------------------------
// T1 — Auto-retry card renders without overflow at 375px
// ---------------------------------------------------------------------------

describe("GTM-POLISH-002 T1: retry-countdown card layout (375px mobile)", () => {
  const mockError = {
    message: "Temporariamente indisponível. Tente novamente em instantes.",
    rawMessage: "upstream connect error",
    errorCode: "INTERNAL_ERROR" as any,
    correlationId: "abc-123",
    requestId: null,
    httpStatus: 503,
    searchId: "search-xyz",
    timestamp: "2026-02-24T10:00:00.000Z",
  };

  it("renders retry-countdown card when error + retryCountdown > 0", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 10,
      retryMessage: "Falha temporária. Reconectando...",
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    expect(screen.getByTestId("retry-countdown")).toBeInTheDocument();
  });

  it("retry-countdown card has max-w-full class to prevent overflow", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 15,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    const card = screen.getByTestId("retry-countdown");
    expect(card).toHaveClass("max-w-full");
  });

  it("retry-countdown card has overflow-hidden class", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 15,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    const card = screen.getByTestId("retry-countdown");
    expect(card).toHaveClass("overflow-hidden");
  });

  it("buttons container uses flex-col for mobile stacking", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 10,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    const { container } = render(<SearchResults {...props} />);

    const card = screen.getByTestId("retry-countdown");
    // The div wrapping the buttons should have flex-col (mobile) and sm:flex-row (desktop)
    const buttonWrapper = card.querySelector(".flex-col");
    expect(buttonWrapper).not.toBeNull();
  });

  it("buttons have sm:flex-row for desktop layout (class present in markup)", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 10,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    const { container } = render(<SearchResults {...props} />);

    // The buttons wrapper div should contain "sm:flex-row" in its className
    const card = container.querySelector('[data-testid="retry-countdown"]');
    const buttonWrapper = card?.querySelector("div.flex-col");
    expect(buttonWrapper?.className).toContain("sm:flex-row");
  });

  it("renders both Tentar agora and Cancelar buttons", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 10,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    expect(screen.getByTestId("retry-now-button")).toBeInTheDocument();
    expect(screen.getByText("Cancelar")).toBeInTheDocument();
  });

  it("displays countdown seconds in text", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 7,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    expect(screen.getByTestId("retry-countdown-text")).toHaveTextContent("7s");
  });

  it("does NOT render retry-countdown card when retryCountdown is 0", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: 0,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("retry-countdown")).not.toBeInTheDocument();
  });

  it("does NOT render retry-countdown card when retryCountdown is null", () => {
    const props = makeMinimalProps({
      error: mockError,
      retryCountdown: null,
      onRetryNow: jest.fn(),
      onCancelRetry: jest.fn(),
    });

    render(<SearchResults {...props} />);

    expect(screen.queryByTestId("retry-countdown")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// T2 — ErrorDetail is scrollable on mobile
// ---------------------------------------------------------------------------

describe("GTM-POLISH-002 T2: ErrorDetail scrollable on mobile", () => {
  it("renders ErrorDetail component when given a searchId", () => {
    render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage="Timeout ao conectar na fonte de dados"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    expect(screen.getByTestId("error-detail")).toBeInTheDocument();
  });

  it("expandable section has overflow-y-auto class when open", () => {
    const { container } = render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage="Timeout ao conectar na fonte de dados"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    // Click to expand
    const toggleButton = screen.getByRole("button", { name: /Detalhes técnicos/i });
    fireEvent.click(toggleButton);

    // The scrollable container should be present with overflow-y-auto
    const scrollable = container.querySelector(".overflow-y-auto");
    expect(scrollable).not.toBeNull();
    expect(scrollable).toHaveClass("overflow-y-auto");
  });

  it("expandable section has overflow-x-hidden to prevent horizontal scroll", () => {
    const { container } = render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage="Timeout ao conectar"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Detalhes técnicos/i }));

    const scrollable = container.querySelector(".overflow-y-auto");
    expect(scrollable).toHaveClass("overflow-x-hidden");
  });

  it("expandable section has break-all to handle long strings without overflow", () => {
    const longMsg = "averylongerrormessagewithoutspaces".repeat(5);
    const { container } = render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage={longMsg}
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Detalhes técnicos/i }));

    const scrollable = container.querySelector(".overflow-y-auto");
    expect(scrollable).toHaveClass("break-all");
  });

  it("expandable section has max-h-48 to constrain height on mobile", () => {
    const { container } = render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage="Test error"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Detalhes técnicos/i }));

    const scrollable = container.querySelector(".overflow-y-auto");
    expect(scrollable).toHaveClass("max-h-48");
  });

  it("does not show scrollable section when collapsed", () => {
    const { container } = render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage="Test error"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    // Initially collapsed — no scrollable container
    expect(container.querySelector(".overflow-y-auto")).toBeNull();
  });

  it("shows search ID inside scrollable section when expanded", () => {
    render(
      <ErrorDetail
        searchId="search-abc-123"
        errorMessage="Test error"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Detalhes técnicos/i }));

    expect(screen.getByText(/search-abc-123/)).toBeInTheDocument();
  });

  it("shows error code badge when error code is provided via structured error", () => {
    render(
      <ErrorDetail
        error={{
          message: "Timeout",
          rawMessage: "upstream timeout",
          errorCode: "TIMEOUT",
          correlationId: null,
          requestId: null,
          httpStatus: 504,
          searchId: "search-xyz",
          timestamp: "2026-02-24T10:00:00.000Z",
        }}
      />
    );

    expect(screen.getByText("Tempo esgotado")).toBeInTheDocument();
  });

  it("returns null when no searchId and no errorMessage provided", () => {
    const { container } = render(
      <ErrorDetail />
    );

    expect(container.firstChild).toBeNull();
  });

  it("toggles open/closed on repeated clicks", () => {
    const { container } = render(
      <ErrorDetail
        searchId="search-xyz"
        errorMessage="Some error"
        timestamp="2026-02-24T10:00:00.000Z"
      />
    );

    const button = screen.getByRole("button", { name: /Detalhes técnicos/i });

    // Open
    fireEvent.click(button);
    expect(container.querySelector(".overflow-y-auto")).not.toBeNull();

    // Close
    fireEvent.click(button);
    expect(container.querySelector(".overflow-y-auto")).toBeNull();
  });
});
