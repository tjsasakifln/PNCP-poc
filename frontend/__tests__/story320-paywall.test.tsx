/**
 * STORY-320: Trial Paywall — Frontend Tests
 *
 * Covers:
 * - AC15: TrialPaywall overlay renders on day 8+ (paywallApplied=true)
 * - AC16: No paywall on days 1-7 (full_access phase)
 * - AC17: No paywall for paid users (not_trial phase)
 * - AC12: Persistent upgrade banner in limited_access
 * - useTrialPhase hook: loading, fetch, cache, unauthenticated
 * - SearchResults: paywall overlay positioning and banner integration
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mocks — must appear before component imports
// ---------------------------------------------------------------------------

const mockTrackEvent = jest.fn();
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));

const mockSession: { access_token: string } | null = {
  access_token: "test-access-token",
};
const mockUseAuth = jest.fn();
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock("next/link", () => {
  return ({ children, href, onClick, ...props }: any) => (
    <a href={href} onClick={onClick} {...props}>
      {children}
    </a>
  );
});

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

// Mock heavy SearchResults sub-components to avoid deep dependency chains
jest.mock("../app/buscar/components/SearchStateManager", () => ({
  SearchStateManager: () => null,
}));
jest.mock("../app/buscar/components/DataQualityBanner", () => ({
  DataQualityBanner: () => null,
}));
jest.mock("../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../app/buscar/components/LlmSourceBadge", () => ({
  LlmSourceBadge: () => null,
}));
jest.mock("../app/buscar/components/ErrorDetail", () => ({
  ErrorDetail: () => null,
}));
jest.mock("../app/buscar/components/ZeroResultsSuggestions", () => ({
  ZeroResultsSuggestions: () => null,
}));
jest.mock("../app/buscar/components/FilterRelaxedBanner", () => ({
  FilterRelaxedBanner: () => null,
}));
jest.mock("../app/buscar/components/ExpiredCacheBanner", () => ({
  ExpiredCacheBanner: () => null,
}));
jest.mock("../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => null,
}));
jest.mock("../app/buscar/components/PartialResultsPrompt", () => ({
  PartialResultsPrompt: () => null,
}));
jest.mock("../app/buscar/components/SourceStatusGrid", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => null,
}));
jest.mock("../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: () => null,
}));
jest.mock("../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => null,
}));
jest.mock("../app/buscar/components/SearchEmptyState", () => ({
  SearchEmptyState: () => null,
}));
jest.mock("../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: () => <div data-testid="licitacoes-preview">Preview</div>,
}));
jest.mock("../app/components/OrdenacaoSelect", () => ({
  OrdenacaoSelect: () => null,
}));
jest.mock("../app/components/QuotaCounter", () => ({
  QuotaCounter: () => null,
}));
jest.mock("../components/GoogleSheetsExportButton", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../components/billing/TrialUpsellCTA", () => ({
  TrialUpsellCTA: () => null,
}));
jest.mock("../app/buscar/types/searchPhase", () => ({
  deriveSearchPhase: () => "idle",
}));

// Mock framer-motion to avoid animation issues in tests
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, className, ...rest }: any) => (
      <div className={className} {...rest}>
        {children}
      </div>
    ),
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// ---------------------------------------------------------------------------
// Component imports — after mocks
// ---------------------------------------------------------------------------

import { TrialPaywall } from "../components/billing/TrialPaywall";
import { useTrialPhase } from "../hooks/useTrialPhase";
import SearchResults from "../app/buscar/components/SearchResults";
import type { SearchResultsProps } from "../app/buscar/components/SearchResults";
import type { BuscaResult } from "../app/types";
import { renderHook } from "@testing-library/react";

// ---------------------------------------------------------------------------
// sessionStorage mock helper
// ---------------------------------------------------------------------------

function mockSessionStorage(overrides: Partial<Storage> = {}) {
  const store: Record<string, string> = {};
  const mock = {
    getItem: jest.fn((key: string) => store[key] ?? null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      Object.keys(store).forEach((k) => delete store[k]);
    }),
    length: 0,
    key: jest.fn(),
    ...overrides,
  };
  Object.defineProperty(window, "sessionStorage", {
    value: mock,
    writable: true,
  });
  return mock;
}

// ---------------------------------------------------------------------------
// Minimal BuscaResult factory
// ---------------------------------------------------------------------------

function makeResult(
  overrides: Partial<BuscaResult> = {}
): BuscaResult {
  return {
    resumo: {
      total_oportunidades: 10,
      valor_total: 0,
      texto: "Resumo de teste",
      resumo_executivo: "Resumo executivo de teste. Segundo ponto. Terceiro ponto.",
    } as any,
    licitacoes: [],
    download_id: null,
    total_raw: 25,
    total_filtrado: 10,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    excel_available: false,
    upgrade_message: null,
    source_stats: null,
    response_state: "live",
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Minimal SearchResultsProps factory
// ---------------------------------------------------------------------------

function makeSearchResultsProps(
  overrides: Partial<SearchResultsProps> = {}
): SearchResultsProps {
  return {
    loading: false,
    loadingStep: 0,
    estimatedTime: 0,
    stateCount: 1,
    statesProcessed: 1,
    onCancel: jest.fn(),
    sseEvent: null,
    useRealProgress: false,
    sseAvailable: false,
    onStageChange: jest.fn(),
    error: null,
    quotaError: null,
    result: makeResult(),
    rawCount: 25,
    ufsSelecionadas: new Set(["SP"]),
    sectorName: "Tecnologia",
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
    trialPhase: "limited_access",
    paywallApplied: true,
    totalBeforePaywall: 25,
    ...overrides,
  };
}

// ===========================================================================
// TrialPaywall Component Tests
// ===========================================================================

describe("TrialPaywall", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSessionStorage(); // fresh sessionStorage for each test
  });

  // -------------------------------------------------------------------------
  // AC15: Renders on day 8+
  // -------------------------------------------------------------------------

  describe("AC15: renders paywall overlay when paywallApplied is true", () => {
    it("renders overlay with correct data-testid", () => {
      render(<TrialPaywall additionalCount={15} />);
      expect(
        screen.getByTestId("trial-paywall-overlay")
      ).toBeInTheDocument();
    });

    it("shows additional count in paywall headline", () => {
      render(<TrialPaywall additionalCount={15} />);
      expect(
        screen.getByText("Desbloqueie 15 resultados adicionais")
      ).toBeInTheDocument();
    });

    it("shows correct count when additionalCount is 0", () => {
      render(<TrialPaywall additionalCount={0} />);
      expect(
        screen.getByText("Desbloqueie 0 resultados adicionais")
      ).toBeInTheDocument();
    });

    it("CTA button links to /planos", () => {
      render(<TrialPaywall additionalCount={10} />);
      const cta = screen.getByTestId("trial-paywall-cta");
      expect(cta).toHaveAttribute("href", "/planos");
    });

    it("CTA button text is correct", () => {
      render(<TrialPaywall additionalCount={10} />);
      expect(
        screen.getByText("Assinar SmartLic Pro")
      ).toBeInTheDocument();
    });

    it("dismiss button stores timestamp in sessionStorage", () => {
      const sessionMock = mockSessionStorage();
      render(<TrialPaywall additionalCount={10} />);

      const dismissBtn = screen.getByTestId("trial-paywall-dismiss");
      fireEvent.click(dismissBtn);

      expect(sessionMock.setItem).toHaveBeenCalledWith(
        "smartlic_paywall_dismiss",
        expect.any(String)
      );
    });

    it("dismissed paywall returns null (overlay not rendered)", () => {
      render(<TrialPaywall additionalCount={10} />);

      const dismissBtn = screen.getByTestId("trial-paywall-dismiss");
      fireEvent.click(dismissBtn);

      expect(
        screen.queryByTestId("trial-paywall-overlay")
      ).not.toBeInTheDocument();
    });

    it("tracks paywall_shown event on mount (when not dismissed)", () => {
      render(<TrialPaywall additionalCount={10} context="search" />);
      expect(mockTrackEvent).toHaveBeenCalledWith("trial_paywall_shown", {
        context: "search",
        additional: 10,
      });
    });

    it("tracks paywall_dismissed event on dismiss click", () => {
      render(<TrialPaywall additionalCount={10} context="search" />);
      jest.clearAllMocks();

      fireEvent.click(screen.getByTestId("trial-paywall-dismiss"));

      expect(mockTrackEvent).toHaveBeenCalledWith("trial_paywall_dismissed", {
        context: "search",
      });
    });

    it("tracks paywall_clicked event on CTA click", () => {
      render(<TrialPaywall additionalCount={10} context="search" />);
      jest.clearAllMocks();

      fireEvent.click(screen.getByTestId("trial-paywall-cta"));

      expect(mockTrackEvent).toHaveBeenCalledWith("trial_paywall_clicked", {
        context: "search",
        additional: 10,
      });
    });

    it("uses default context 'search' when no context prop provided", () => {
      render(<TrialPaywall additionalCount={5} />);
      expect(mockTrackEvent).toHaveBeenCalledWith("trial_paywall_shown", {
        context: "search",
        additional: 5,
      });
    });

    it("has role=dialog and aria-label for accessibility", () => {
      render(<TrialPaywall additionalCount={10} />);
      const overlay = screen.getByTestId("trial-paywall-overlay");
      expect(overlay).toHaveAttribute("role", "dialog");
      expect(overlay).toHaveAttribute("aria-label", "Paywall de trial");
    });

    it("does not show paywall when sessionStorage has unexpired dismiss timestamp", () => {
      // Simulate an already-dismissed state within the TTL
      const recentTimestamp = String(Date.now() - 1000); // 1 second ago
      mockSessionStorage({
        getItem: jest.fn((key: string) => {
          if (key === "smartlic_paywall_dismiss") return recentTimestamp;
          return null;
        }),
      });

      render(<TrialPaywall additionalCount={10} />);

      // Should not render overlay since already dismissed
      expect(
        screen.queryByTestId("trial-paywall-overlay")
      ).not.toBeInTheDocument();
    });

    it("shows paywall when sessionStorage has expired dismiss timestamp", () => {
      // Simulate a dismiss timestamp older than 1 hour (3_600_000 ms)
      const expiredTimestamp = String(Date.now() - 3_700_000);
      mockSessionStorage({
        getItem: jest.fn((key: string) => {
          if (key === "smartlic_paywall_dismiss") return expiredTimestamp;
          return null;
        }),
        setItem: jest.fn(),
      });

      render(<TrialPaywall additionalCount={10} />);

      expect(
        screen.getByTestId("trial-paywall-overlay")
      ).toBeInTheDocument();
    });

    it("does not track shown event when already dismissed", () => {
      const recentTimestamp = String(Date.now() - 1000);
      mockSessionStorage({
        getItem: jest.fn((key: string) => {
          if (key === "smartlic_paywall_dismiss") return recentTimestamp;
          return null;
        }),
      });

      render(<TrialPaywall additionalCount={10} />);

      // paywall_shown should NOT be called since it's dismissed
      expect(mockTrackEvent).not.toHaveBeenCalledWith(
        "trial_paywall_shown",
        expect.anything()
      );
    });
  });
});

// ===========================================================================
// SearchResults Component Tests — paywall integration
// ===========================================================================

describe("SearchResults — trial paywall integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSessionStorage();
  });

  // -------------------------------------------------------------------------
  // AC16: No paywall on days 1-7
  // -------------------------------------------------------------------------

  describe("AC16: No paywall on days 1-7 (full_access phase)", () => {
    it("no paywall overlay when trialPhase is full_access", () => {
      const props = makeSearchResultsProps({
        trialPhase: "full_access",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByTestId("trial-paywall-overlay")
      ).not.toBeInTheDocument();
    });

    it("no persistent upgrade banner when trialPhase is full_access", () => {
      const props = makeSearchResultsProps({
        trialPhase: "full_access",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByTestId("trial-paywall-banner")
      ).not.toBeInTheDocument();
    });

    it("no paywall-related text when full_access", () => {
      const props = makeSearchResultsProps({
        trialPhase: "full_access",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByText(/modo preview/i)
      ).not.toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // AC17: No paywall for paid users
  // -------------------------------------------------------------------------

  describe("AC17: No paywall for paid users (not_trial phase)", () => {
    it("no paywall overlay when trialPhase is not_trial", () => {
      const props = makeSearchResultsProps({
        trialPhase: "not_trial",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByTestId("trial-paywall-overlay")
      ).not.toBeInTheDocument();
    });

    it("no persistent banner when trialPhase is not_trial", () => {
      const props = makeSearchResultsProps({
        trialPhase: "not_trial",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByTestId("trial-paywall-banner")
      ).not.toBeInTheDocument();
    });

    it("no preview-mode text when not_trial", () => {
      const props = makeSearchResultsProps({
        trialPhase: "not_trial",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByText(/modo preview/i)
      ).not.toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // AC12: Persistent banner in limited_access
  // -------------------------------------------------------------------------

  describe("AC12: Persistent upgrade banner in limited_access phase", () => {
    it("shows persistent banner with gradient when trialPhase is limited_access", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false, // paywall component not applied but banner should still show
        totalBeforePaywall: 25,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.getByTestId("trial-paywall-banner")
      ).toBeInTheDocument();
    });

    it("banner has upgrade CTA text", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false,
        totalBeforePaywall: 25,
      });
      render(<SearchResults {...props} />);
      expect(screen.getByText(/Ver planos/i)).toBeInTheDocument();
    });

    it("banner CTA links to /planos", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false,
        totalBeforePaywall: 25,
      });
      render(<SearchResults {...props} />);
      const cta = screen.getByTestId("trial-paywall-banner-cta");
      expect(cta).toHaveAttribute("href", "/planos");
    });

    it("banner shows preview mode message", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false,
        totalBeforePaywall: 25,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.getByText(/modo preview/i)
      ).toBeInTheDocument();
    });

    it("banner has role=banner for accessibility", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false,
        totalBeforePaywall: 25,
      });
      render(<SearchResults {...props} />);
      const banner = screen.getByTestId("trial-paywall-banner");
      expect(banner).toHaveAttribute("role", "banner");
    });
  });

  // -------------------------------------------------------------------------
  // No results — paywall banner should not show
  // -------------------------------------------------------------------------

  describe("no banner when result has 0 oportunidades", () => {
    it("no banner in limited_access when total_oportunidades is 0", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false,
        totalBeforePaywall: 0,
        result: makeResult({ resumo: { total_oportunidades: 0, valor_total: 0, texto: "", resumo_executivo: "" } as any }),
      });
      render(<SearchResults {...props} />);
      // The banner only renders inside the results block (when total_oportunidades > 0)
      expect(
        screen.queryByTestId("trial-paywall-banner")
      ).not.toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------------------
  // Not loading — verify results render with paywall present
  // -------------------------------------------------------------------------

  describe("paywall overlay with paywallApplied=true", () => {
    it("renders TrialPaywall overlay when paywallApplied is true and limited_access", () => {
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: true,
        totalBeforePaywall: 25,
      });
      render(<SearchResults {...props} />);
      // TrialPaywall is rendered (not mocked) — overlay should be present
      expect(
        screen.getByTestId("trial-paywall-overlay")
      ).toBeInTheDocument();
    });

    it("no overlay when paywallApplied is false even in limited_access", () => {
      // Overlay is only rendered by the TrialPaywall component when paywallApplied=true
      const props = makeSearchResultsProps({
        trialPhase: "limited_access",
        paywallApplied: false,
        totalBeforePaywall: null,
      });
      render(<SearchResults {...props} />);
      expect(
        screen.queryByTestId("trial-paywall-overlay")
      ).not.toBeInTheDocument();
    });
  });
});

// ===========================================================================
// useTrialPhase Hook Tests
// ===========================================================================

// SWR wrapper to isolate cache between tests
import { SWRConfig } from "swr";

const swrWrapper = ({ children }: { children: React.ReactNode }) => (
  <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0, errorRetryCount: 0 }}>
    {children}
  </SWRConfig>
);

describe("useTrialPhase hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSessionStorage();
    // Default: authenticated session
    mockUseAuth.mockReturnValue({ session: mockSession });
  });

  it("returns full_access phase with loading=true initially", () => {
    // Fetch won't resolve during synchronous render
    (global as any).fetch = jest.fn().mockImplementation(
      () => new Promise(() => {}) // pending forever
    );

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    expect(result.current.phase).toBe("full_access");
    expect(result.current.loading).toBe(true);
  });

  it("fetches /api/trial-status and returns phase on success", async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trial_phase: "limited_access",
        trial_day: 10,
        days_remaining: 4,
      }),
    } as Response);
    (global as any).fetch = fetchMock;

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.phase).toBe("limited_access");
    expect(result.current.day).toBe(10);
    expect(result.current.daysRemaining).toBe(4);

    expect(fetchMock).toHaveBeenCalledWith("/api/trial-status", {
      headers: { Authorization: "Bearer test-access-token" },
    });
  });

  it("returns full_access when fetch fails (network error)", async () => {
    (global as any).fetch = jest
      .fn()
      .mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // SWR: on error with no data, hook returns full_access fallback
    expect(result.current.phase).toBe("full_access");
    expect(result.current.daysRemaining).toBe(999);
  });

  it("returns full_access when response is not ok", async () => {
    // fetchTrialStatus returns null for non-ok responses
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Unauthorized" }),
    } as Response);

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // fetchTrialStatus returns null for non-ok → hook returns full_access
    expect(result.current.phase).toBe("full_access");
  });

  it("SWR deduplication prevents redundant fetches within interval", async () => {
    // TD-008: SWR handles caching via dedupingInterval (5 min)
    // This replaces the old sessionStorage cache test
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trial_phase: "full_access",
        trial_day: 3,
        days_remaining: 11,
      }),
    } as Response);
    (global as any).fetch = fetchMock;

    // Use a shared SWR cache for this test to verify deduplication
    const sharedWrapper = ({ children }: { children: React.ReactNode }) => (
      <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 300_000, errorRetryCount: 0 }}>
        {children}
      </SWRConfig>
    );

    const { result } = renderHook(() => useTrialPhase(), { wrapper: sharedWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.phase).toBe("full_access");
    // Fetch should have been called once
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("returns full_access when not authenticated (no session)", async () => {
    mockUseAuth.mockReturnValue({ session: null });

    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);
    (global as any).fetch = fetchMock;

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.phase).toBe("full_access");
    expect(result.current.daysRemaining).toBe(999);
    // Should NOT fetch for unauthenticated users
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns full_access when session has no access_token", async () => {
    mockUseAuth.mockReturnValue({ session: {} }); // session exists but no access_token

    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);
    (global as any).fetch = fetchMock;

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.phase).toBe("full_access");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("handles missing fields in API response gracefully", async () => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}), // no trial_phase, no trial_day, etc.
    } as Response);

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.phase).toBe("full_access"); // default fallback
    expect(result.current.day).toBe(0);
    expect(result.current.daysRemaining).toBe(0);
  });

  it("returns not_trial phase for paid users", async () => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        trial_phase: "not_trial",
        trial_day: 0,
        days_remaining: 0,
      }),
    } as Response);

    const { result } = renderHook(() => useTrialPhase(), { wrapper: swrWrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.phase).toBe("not_trial");
    expect(result.current.day).toBe(0);
    expect(result.current.daysRemaining).toBe(0);
  });
});
