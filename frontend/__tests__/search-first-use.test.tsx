/**
 * @jest-environment jsdom
 *
 * UX-346: First-Use Experience Tests
 *
 * - AC8: First access has "Personalizar busca" collapsed
 * - AC9: After search, "Personalizar busca" respects last state (localStorage)
 * - AC10: Compact summary shows correct count of UFs/modalidades/status/period
 * - AC11: Verified via running all existing tests (no breakage)
 */

import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import HomePage from "../app/buscar/page";

// --------------- Mocks ---------------

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({ session: { access_token: "test" }, loading: false }),
}));

jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({ planInfo: null }),
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../hooks/useOnboarding", () => ({
  useOnboarding: () => ({ shouldShowOnboarding: false, restartTour: jest.fn() }),
}));

jest.mock("../hooks/useNavigationGuard", () => ({
  useNavigationGuard: jest.fn(),
}));

jest.mock("../hooks/useKeyboardShortcuts", () => ({
  useKeyboardShortcuts: jest.fn(),
  getShortcutDisplay: () => "",
}));

jest.mock("../components/BackendStatusIndicator", () => {
  const MockIndicator = () => null;
  MockIndicator.displayName = "BackendStatusIndicator";
  return {
    __esModule: true,
    default: MockIndicator,
    useBackendStatusContext: () => ({ status: "online", lastChecked: Date.now() }),
  };
});

jest.mock("next/navigation", () => ({
  useSearchParams: () => ({ get: () => null }),
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/buscar",
}));

jest.mock("react-simple-pull-to-refresh", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock("sonner", () => ({ toast: { info: jest.fn(), success: jest.fn() } }));

jest.mock("../components/MobileDrawer", () => ({
  MobileDrawer: () => null,
}));

// --------------- Filter mock ---------------

const ALL_UFS = new Set([
  "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
  "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
]);

const mockFilters = {
  setores: [{ id: "vestuario", name: "Vestuário e Uniformes", description: "Fardamento" }],
  setoresLoading: false,
  setoresError: false,
  setoresUsingFallback: false,
  setoresUsingStaleCache: false,
  staleCacheAge: null,
  setoresRetryCount: 0,
  setorId: "vestuario",
  setSetorId: jest.fn(),
  fetchSetores: jest.fn(),
  searchMode: "setor" as const,
  setSearchMode: jest.fn(),
  modoBusca: "abertas" as const,
  dateLabel: "Mostrando licitações abertas para proposta",
  termosArray: [] as string[],
  termoInput: "",
  setTermoInput: jest.fn(),
  termValidation: null,
  addTerms: jest.fn(),
  removeTerm: jest.fn(),
  ufsSelecionadas: new Set(ALL_UFS),
  toggleUf: jest.fn(),
  toggleRegion: jest.fn(),
  selecionarTodos: jest.fn(),
  limparSelecao: jest.fn(),
  dataInicial: "2026-02-12",
  setDataInicial: jest.fn(),
  dataFinal: "2026-02-22",
  setDataFinal: jest.fn(),
  validationErrors: {},
  canSearch: true,
  searchLabel: "Vestuário e Uniformes",
  sectorName: "Vestuário e Uniformes",
  locationFiltersOpen: false,
  setLocationFiltersOpen: jest.fn(),
  advancedFiltersOpen: false,
  setAdvancedFiltersOpen: jest.fn(),
  esferas: [] as string[],
  setEsferas: jest.fn(),
  municipios: [] as string[],
  setMunicipios: jest.fn(),
  status: "recebendo_proposta" as const,
  setStatus: jest.fn(),
  modalidades: [] as number[],
  setModalidades: jest.fn(),
  valorMin: null,
  setValorMin: jest.fn(),
  valorMax: null,
  setValorMax: jest.fn(),
  setValorValid: jest.fn(),
  ordenacao: "data_desc" as const,
  setOrdenacao: jest.fn(),
};

jest.mock("../app/buscar/hooks/useSearchFilters", () => ({
  useSearchFilters: () => mockFilters,
  DEFAULT_SEARCH_DAYS: 10,
}));

// --------------- Search mock ---------------

const mockSearch = {
  loading: false,
  result: null as any,
  error: null,
  quotaError: null,
  searchId: null,
  buscar: jest.fn(),
  setResult: jest.fn(),
  setError: jest.fn(),
  searchButtonRef: { current: null },
  handleSaveSearch: jest.fn(),
  isMaxCapacity: false,
  showSaveDialog: false,
  setShowSaveDialog: jest.fn(),
  saveSearchName: "",
  setSaveSearchName: jest.fn(),
  confirmSaveSearch: jest.fn(),
  saveError: null,
  handleLoadSearch: jest.fn(),
  handleRefresh: jest.fn().mockResolvedValue(undefined),
  handleDownload: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  estimateSearchTime: () => 15,
  statesProcessed: 0,
  cancelSearch: jest.fn(),
  sseEvent: null,
  useRealProgress: false,
  sseAvailable: false,
  sseDisconnected: false,
  isDegraded: false,
  degradedDetail: null,
  loadingStep: 0,
  ufStatuses: new Map(),
  ufTotalFound: new Map(),
  ufAllComplete: false,
  buscarForceFresh: jest.fn(),
  liveFetchInProgress: false,
  refreshAvailable: false,
  handleRefreshResults: jest.fn(),
  retryCountdown: null,
  retryNow: jest.fn(),
  cancelRetry: jest.fn(),
  restoreSearchStateOnMount: jest.fn(),
  rawCount: null,
};

jest.mock("../app/buscar/hooks/useSearch", () => ({
  useSearch: () => mockSearch,
}));

// ============================================================================

describe("UX-346: First-Use Experience", () => {
  beforeEach(() => {
    localStorage.clear();
    mockSearch.result = null;
    mockSearch.loading = false;
    mockFilters.ufsSelecionadas = new Set(ALL_UFS);
    mockFilters.modalidades = [];
    mockFilters.status = "recebendo_proposta";
    jest.clearAllMocks();
  });

  // ---------- AC8: Collapsed on first access ----------

  describe("AC8: First access — collapsed", () => {
    it("Personalizar busca is collapsed on first access", () => {
      render(<HomePage />);

      // Compact summary should be visible (data-testid)
      expect(screen.getByTestId("compact-summary")).toBeInTheDocument();

      // "Selecionar todos" only renders when accordion is open
      expect(screen.queryByText("Selecionar todos")).not.toBeInTheDocument();
    });

    it("shows first-use tip for new users", () => {
      render(<HomePage />);

      const tip = screen.getByTestId("first-use-tip");
      expect(tip).toBeInTheDocument();
      expect(tip).toHaveTextContent(/dica/i);
      expect(tip).toHaveTextContent(/selecione seu setor/i);
    });

    it("first-use tip can be dismissed", () => {
      render(<HomePage />);

      fireEvent.click(screen.getByTestId("dismiss-first-use-tip"));

      expect(screen.queryByTestId("first-use-tip")).not.toBeInTheDocument();
      expect(localStorage.getItem("smartlic-first-tip-dismissed")).toBe("true");
    });

    it("first-use tip not shown when already dismissed", () => {
      localStorage.setItem("smartlic-first-tip-dismissed", "true");

      render(<HomePage />);

      expect(screen.queryByTestId("first-use-tip")).not.toBeInTheDocument();
    });
  });

  // ---------- AC9: Returning user — respects localStorage ----------

  describe("AC9: Returning user state persistence", () => {
    it("respects localStorage open state for returning user", () => {
      localStorage.setItem("smartlic-has-searched", "true");
      localStorage.setItem("smartlic-customize-open", "open");

      render(<HomePage />);

      // "Selecionar todos" only renders when accordion is open
      expect(screen.getByText("Selecionar todos")).toBeInTheDocument();

      // Compact summary should NOT be visible (accordion is open)
      expect(screen.queryByTestId("compact-summary")).not.toBeInTheDocument();
    });

    it("respects localStorage closed state for returning user", () => {
      localStorage.setItem("smartlic-has-searched", "true");
      localStorage.setItem("smartlic-customize-open", "closed");

      render(<HomePage />);

      // Compact summary visible (collapsed)
      expect(screen.getByTestId("compact-summary")).toBeInTheDocument();

      // UF section NOT rendered
      expect(screen.queryByText("Selecionar todos")).not.toBeInTheDocument();
    });

    it("first-time user ignores customize-open localStorage", () => {
      // User somehow has customize-open but hasn't searched
      localStorage.setItem("smartlic-customize-open", "open");

      render(<HomePage />);

      // Should still be collapsed for first-time user
      expect(screen.getByTestId("compact-summary")).toBeInTheDocument();
      expect(screen.queryByText("Selecionar todos")).not.toBeInTheDocument();
    });
  });

  // ---------- AC10: Compact summary content ----------

  describe("AC10: Compact summary content", () => {
    it("shows Todo o Brasil for all 27 UFs", () => {
      render(<HomePage />);

      const summary = screen.getByTestId("compact-summary");
      expect(summary).toHaveTextContent(/todo o brasil/i);
      expect(summary).toHaveTextContent(/abertas/i);
      expect(summary).toHaveTextContent(/oportunidades recentes/i);
    });

    it("shows UF count for subset of UFs", () => {
      mockFilters.ufsSelecionadas = new Set(["SP", "RJ", "MG", "PR", "SC"]);

      render(<HomePage />);

      const summary = screen.getByTestId("compact-summary");
      expect(summary).toHaveTextContent("5 estados");
    });

    it("shows modalidade count when modalidades selected", () => {
      mockFilters.modalidades = [1, 2, 3];

      render(<HomePage />);

      const summary = screen.getByTestId("compact-summary");
      expect(summary).toHaveTextContent("3 modalidades");
    });

    it("clicking compact summary expands accordion", () => {
      render(<HomePage />);

      // Accordion is collapsed
      expect(screen.queryByText("Selecionar todos")).not.toBeInTheDocument();

      // Click summary to expand
      fireEvent.click(screen.getByTestId("compact-summary"));

      // UF section should now be visible
      expect(screen.getByText("Selecionar todos")).toBeInTheDocument();
    });
  });

  // ---------- AC7: Footer visibility ----------

  describe("AC7: Footer visibility", () => {
    // GTM-POLISH-001 AC8: Footer is always visible (not hidden before results)
    it("footer is always visible even without search results", () => {
      render(<HomePage />);

      const footer = screen.getByRole("contentinfo");
      expect(footer.className).not.toContain("hidden");
    });

    it("footer is visible after search results", () => {
      mockSearch.result = {
        resumo: {
          resumo_executivo: "Test",
          total_oportunidades: 5,
          valor_total: 100000,
          destaques: [],
        },
        total_filtrado: 5,
        licitacoes: [],
      };

      render(<HomePage />);

      const footer = screen.getByRole("contentinfo");
      expect(footer.className).not.toContain("hidden");
    });
  });

  // ---------- Search sets has-searched flag ----------

  describe("Search interaction", () => {
    it("search sets smartlic-has-searched in localStorage", async () => {
      render(<HomePage />);

      // Find the main search button (contains the search label)
      const searchButton = screen.getByRole("button", {
        name: /buscar vestuário e uniformes/i,
      });

      await act(async () => {
        fireEvent.click(searchButton);
      });

      expect(localStorage.getItem("smartlic-has-searched")).toBe("true");
    });

    it("search dismisses first-use tip", async () => {
      render(<HomePage />);

      // Tip is visible
      expect(screen.getByTestId("first-use-tip")).toBeInTheDocument();

      const searchButton = screen.getByRole("button", {
        name: /buscar vestuário e uniformes/i,
      });

      await act(async () => {
        fireEvent.click(searchButton);
      });

      // Tip should be gone
      expect(screen.queryByTestId("first-use-tip")).not.toBeInTheDocument();
    });
  });
});
