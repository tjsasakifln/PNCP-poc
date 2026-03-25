/**
 * GTM-POLISH-001: Loading Consistency Tests
 *
 * T1: AuthLoadingScreen renders with logo + skeleton cards
 * T2: Pipeline page shows skeleton during data loading
 * T3: Footer in buscar page is always visible (never hidden without results)
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Shared mocks (declared before imports)
// ---------------------------------------------------------------------------

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}));

jest.mock("next/link", () => {
  const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

// framer-motion: pass-through to avoid animation side-effects in tests
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// error-messages — must include both isTransientError and getMessageFromErrorCode
jest.mock("../../lib/error-messages", () => ({
  getUserFriendlyError: (e: unknown) =>
    e instanceof Error ? e.message : "Erro desconhecido",
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
  ERROR_CODE_MESSAGES: {},
}));

// ---------------------------------------------------------------------------
// T1 — AuthLoadingScreen
// ---------------------------------------------------------------------------

import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";

describe("T1 — AuthLoadingScreen (GTM-POLISH-001 AC1-AC3)", () => {
  it("renders the root container with data-testid=auth-loading-screen", () => {
    render(<AuthLoadingScreen />);
    expect(screen.getByTestId("auth-loading-screen")).toBeInTheDocument();
  });

  it("renders the header skeleton (logo placeholder + avatar placeholder)", () => {
    const { container } = render(<AuthLoadingScreen />);
    // The header row has two animate-pulse elements (logo + avatar)
    const headerPulses = container.querySelectorAll(
      "[data-testid='auth-loading-screen'] > div:first-child .animate-pulse"
    );
    expect(headerPulses.length).toBeGreaterThanOrEqual(2);
  });

  it("renders a grid of 3 skeleton cards", () => {
    const { container } = render(<AuthLoadingScreen />);
    // The card grid contains 3 divs with animate-pulse inside it
    const gridPulses = container.querySelectorAll(
      ".grid.grid-cols-1 .animate-pulse"
    );
    expect(gridPulses.length).toBe(3);
  });

  it("renders 4 list skeleton rows below the card grid", () => {
    const { container } = render(<AuthLoadingScreen />);
    // The list skeleton (.space-y-3) has 4 animate-pulse items
    const listPulses = container.querySelectorAll(
      ".space-y-3 .animate-pulse"
    );
    expect(listPulses.length).toBe(4);
  });

  it("has animate-fade-in class on root for smooth transition", () => {
    render(<AuthLoadingScreen />);
    const root = screen.getByTestId("auth-loading-screen");
    expect(root).toHaveClass("animate-fade-in");
  });

  it("fills at least the full viewport height", () => {
    render(<AuthLoadingScreen />);
    const root = screen.getByTestId("auth-loading-screen");
    expect(root).toHaveClass("min-h-screen");
  });
});

// ---------------------------------------------------------------------------
// T2 — Pipeline page skeleton during loading
// ---------------------------------------------------------------------------

// Mock heavy @dnd-kit dependencies used by pipeline page
jest.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  DragOverlay: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  closestCorners: jest.fn(),
  KeyboardSensor: jest.fn(),
  PointerSensor: jest.fn(),
  useSensor: jest.fn(() => ({})),
  useSensors: jest.fn(() => []),
}));

jest.mock("@dnd-kit/sortable", () => ({
  sortableKeyboardCoordinates: jest.fn(),
  SortableContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: jest.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
  verticalListSortingStrategy: jest.fn(),
}));

jest.mock("@dnd-kit/utilities", () => ({
  CSS: { Transform: { toString: () => null } },
}));

// next/dynamic: resolve dynamic imports synchronously (prevents loading fallback
// being rendered in jsdom — PipelineKanban/_KanbanSkeleton would otherwise appear
// as the loading state even when loading=false and items exist).
jest.mock("next/dynamic", () => ({
  __esModule: true,
  default: (loader: () => Promise<{ default: React.ComponentType } | React.ComponentType>) => {
    // Return the mock that jest.mock("../../app/pipeline/PipelineKanban") provides
    // We resolve via the already-registered module mock synchronously.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const mod = require("../../app/pipeline/PipelineKanban");
    // dynamic() is called twice: once for PipelineKanban, once for ReadOnlyKanban.
    // The loader receives the module — we can't distinguish at mock time which export
    // is requested, so we return the full mock module and let Next.js pick.
    // Since page.tsx does .then(mod => mod.PipelineKanban) / .then(mod => mod.ReadOnlyKanban),
    // we return a component that wraps both named exports gracefully.
    const Stub = ({ children }: { children?: React.ReactNode }) => (
      <div data-testid="pipeline-kanban-stub">{children}</div>
    );
    Stub.displayName = "DynamicStub";
    return Stub;
  },
}));

// Mock sub-components used by PipelinePage to keep tests focused
jest.mock("../../components/PageHeader", () => ({
  PageHeader: ({ title }: { title: string }) => (
    <header data-testid="page-header">{title}</header>
  ),
}));

jest.mock("../../components/EmptyState", () => ({
  EmptyState: () => <div data-testid="empty-state" />,
}));

jest.mock("../../components/ErrorStateWithRetry", () => ({
  ErrorStateWithRetry: ({ message }: { message: string }) => (
    <div data-testid="error-state">{message}</div>
  ),
}));

// AuthLoadingScreen is NOT mocked so T1 tests the real component.
// T2 pipeline tests check for data-testid="auth-loading-screen" which the
// real component also renders — the mock override is therefore unnecessary.

// Mock PipelineColumn and PipelineCard to avoid deep dnd-kit tree
jest.mock("../../app/pipeline/PipelineColumn", () => ({
  PipelineColumn: ({ stage }: { stage: string }) => (
    <div data-testid={`column-${stage}`} />
  ),
}));

jest.mock("../../app/pipeline/PipelineCard", () => ({
  PipelineCard: () => <div data-testid="pipeline-card" />,
}));

jest.mock("../../app/pipeline/PipelineMobileTabs", () => ({
  PipelineMobileTabs: () => <div data-testid="pipeline-mobile-tabs" />,
}));

jest.mock("../../hooks/useIsMobile", () => ({
  useIsMobile: () => false,
}));

jest.mock("../../hooks/usePlan", () => ({
  usePlan: () => ({
    planInfo: { plan_id: "smartlic_pro", subscription_status: "active" },
    planType: "smartlic_pro",
    isLoading: false,
  }),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../../hooks/useTrialPhase", () => ({
  useTrialPhase: () => ({ phase: "active" }),
}));

jest.mock("../../hooks/useShepherdTour", () => ({
  useShepherdTour: () => ({
    isCompleted: () => true,
    startTour: jest.fn(),
    restartTour: jest.fn(),
  }),
}));

jest.mock("../../components/billing/TrialUpsellCTA", () => ({
  TrialUpsellCTA: () => <div data-testid="trial-upsell-cta" />,
}));

jest.mock("../../components/OnboardingTourButton", () => ({
  OnboardingTourButton: () => <div data-testid="onboarding-tour-button" />,
}));

// Controlled mock for usePipeline
const mockUsePipeline = jest.fn();
jest.mock("../../hooks/usePipeline", () => ({
  usePipeline: () => mockUsePipeline(),
}));

// Controlled mock for useAuth
const mockUseAuth = jest.fn();
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// sonner toast (used by PipelinePage on drag error)
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), success: jest.fn(), info: jest.fn() },
}));

import PipelinePage from "../../app/pipeline/page";

describe("T2 — Pipeline page skeleton during data loading (GTM-POLISH-001 AC4)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows pipeline-skeleton when authenticated and pipeline data is loading", () => {
    // Auth resolved (not loading), session present
    mockUseAuth.mockReturnValue({
      session: { access_token: "tok-abc" },
      loading: false,
    });

    // Pipeline: loading=true, no items yet
    mockUsePipeline.mockReturnValue({
      items: [],
      loading: true,
      error: null,
      fetchItems: jest.fn(),
      updateItem: jest.fn(),
      removeItem: jest.fn(),
    });

    render(<PipelinePage />);

    expect(screen.getByTestId("pipeline-skeleton")).toBeInTheDocument();
  });

  it("renders AuthLoadingScreen while auth is still resolving", () => {
    mockUseAuth.mockReturnValue({
      session: null,
      loading: true,
    });

    mockUsePipeline.mockReturnValue({
      items: [],
      loading: false,
      error: null,
      fetchItems: jest.fn(),
      updateItem: jest.fn(),
      removeItem: jest.fn(),
    });

    render(<PipelinePage />);

    // PipelinePage delegates to AuthLoadingScreen when authLoading=true
    expect(screen.getByTestId("auth-loading-screen")).toBeInTheDocument();
    // The pipeline skeleton must NOT be shown while auth is pending
    expect(screen.queryByTestId("pipeline-skeleton")).not.toBeInTheDocument();
  });

  it("does NOT show pipeline-skeleton when loading is false and items exist", () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "tok-xyz" },
      loading: false,
    });

    mockUsePipeline.mockReturnValue({
      items: [
        {
          id: "i1",
          user_id: "u1",
          pncp_id: "p1",
          objeto: "Objeto de teste",
          orgao: "Orgao",
          uf: "SP",
          valor_estimado: 10000,
          data_encerramento: null,
          link_pncp: null,
          stage: "descoberta",
          notes: null,
          created_at: "2026-01-01T00:00:00",
          updated_at: "2026-01-01T00:00:00",
        },
      ],
      loading: false,
      error: null,
      fetchItems: jest.fn(),
      updateItem: jest.fn(),
      removeItem: jest.fn(),
    });

    render(<PipelinePage />);

    expect(screen.queryByTestId("pipeline-skeleton")).not.toBeInTheDocument();
  });

  it("skeleton contains one column div per pipeline stage", () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "tok-abc" },
      loading: false,
    });

    mockUsePipeline.mockReturnValue({
      items: [],
      loading: true,
      error: null,
      fetchItems: jest.fn(),
      updateItem: jest.fn(),
      removeItem: jest.fn(),
    });

    const { container } = render(<PipelinePage />);
    const skeleton = screen.getByTestId("pipeline-skeleton");

    // STAGES_ORDER has 5 stages: descoberta, analise, proposta, negociacao, concluido
    // Each stage produces one flex-shrink-0 column div inside the skeleton
    const columns = skeleton.querySelectorAll(".flex-shrink-0");
    expect(columns.length).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// T3 — Buscar page footer always visible
// ---------------------------------------------------------------------------

// The buscar page has many heavy dependencies — we need to mock them all
// so the footer renders regardless of search state.

jest.mock("react-simple-pull-to-refresh", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

jest.mock("../../hooks/useOnboarding", () => ({
  useOnboarding: () => ({ shouldShowOnboarding: false, restartTour: jest.fn() }),
}));

jest.mock("../../hooks/useKeyboardShortcuts", () => ({
  useKeyboardShortcuts: jest.fn(),
  getShortcutDisplay: () => "Ctrl+K",
}));

jest.mock("../../hooks/usePlan", () => ({
  usePlan: () => ({
    planType: "free_trial",
    isLoading: false,
    trialDaysRemaining: 7,
    isTrialExpired: false,
  }),
}));

jest.mock("../../app/components/ThemeToggle", () => ({
  ThemeToggle: () => <button>Theme</button>,
}));

jest.mock("../../app/components/UserMenu", () => ({
  UserMenu: () => <div />,
}));

jest.mock("../../app/components/SavedSearchesDropdown", () => ({
  SavedSearchesDropdown: () => <div />,
}));

jest.mock("../../app/components/QuotaBadge", () => ({
  QuotaBadge: () => <div />,
}));

jest.mock("../../app/components/PlanBadge", () => ({
  PlanBadge: () => <div />,
}));

jest.mock("../../app/components/UpgradeModal", () => ({
  UpgradeModal: () => <div />,
}));

jest.mock("../../app/components/TrialConversionScreen", () => ({
  TrialConversionScreen: () => <div />,
}));

jest.mock("../../app/components/TrialExpiringBanner", () => ({
  TrialExpiringBanner: () => <div />,
}));

jest.mock("../../app/components/TrialCountdown", () => ({
  TrialCountdown: () => <div />,
}));

jest.mock("../../app/components/Dialog", () => ({
  Dialog: ({
    children,
    isOpen,
  }: {
    children: React.ReactNode;
    isOpen: boolean;
  }) => (isOpen ? <div role="dialog">{children}</div> : null),
}));

// Search hooks — shapes must match exactly what buscar/page.tsx uses
jest.mock("../../app/buscar/hooks/useSearchFilters", () => ({
  useSearchFilters: () => ({
    // Set-based UF selection (page uses .size)
    ufsSelecionadas: new Set<string>(),
    setUfsSelecionadas: jest.fn(),
    toggleUf: jest.fn(),
    toggleRegion: jest.fn(),
    allUfsSelected: false,
    toggleAllUfs: jest.fn(),

    searchMode: "setor" as const,
    setSearchMode: jest.fn(),
    setorId: "",
    setSetorId: jest.fn(),
    sectorName: "",
    termosArray: [],
    setTermosArray: jest.fn(),
    termoInput: "",
    setTermoInput: jest.fn(),
    addTerms: jest.fn(),
    removeTerm: jest.fn(),
    termValidation: null,

    dataInicial: "2026-02-14",
    setDataInicial: jest.fn(),
    dataFinal: "2026-02-24",
    setDataFinal: jest.fn(),

    modoBusca: "publicacao" as const,
    setModoBusca: jest.fn(),

    status: "todas" as const,
    setStatus: jest.fn(),
    modalidades: [] as number[],
    setModalidades: jest.fn(),
    valorMin: null,
    setValorMin: jest.fn(),
    valorMax: null,
    setValorMax: jest.fn(),
    esferas: [],
    setEsferas: jest.fn(),
    municipios: [],
    setMunicipios: jest.fn(),
    ordenacao: "data_desc" as const,
    setOrdenacao: jest.fn(),

    setores: [],
    isLoadingSetores: false,
    validationErrors: {},
    isFormValid: false,
    searchLabel: "",
    hasProfileContext: false,
    clearFilters: jest.fn(),
  }),
}));

jest.mock("../../app/buscar/hooks/useSearch", () => ({
  useSearch: () => ({
    loading: false,
    loadingStep: 1,
    statesProcessed: 0,
    error: null,
    quotaError: null,
    result: null,
    setResult: jest.fn(),
    setError: jest.fn(),
    rawCount: 0,
    searchId: null,
    useRealProgress: false,
    sseEvent: null,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    partialProgress: null,
    refreshAvailable: null,
    cancelSearch: jest.fn(),
    buscar: jest.fn(),
    estimateSearchTime: () => 30,
    restoreSearchStateOnMount: jest.fn(),
    savedSearches: [],
    currentSavedSearchId: null,
    saveCurrentSearch: jest.fn(),
    loadSavedSearch: jest.fn(),
    deleteSavedSearch: jest.fn(),
    showSaveDialog: false,
    setShowSaveDialog: jest.fn(),
    saveSearchName: "",
    setSaveSearchName: jest.fn(),
    saveError: null,
    confirmSaveSearch: jest.fn(),
    upgradeRequired: false,
    setUpgradeRequired: jest.fn(),
  }),
}));

jest.mock("../../hooks/useNavigationGuard", () => ({
  useNavigationGuard: jest.fn(),
}));

// Buscar sub-components
jest.mock("../../app/buscar/components/SearchForm", () => ({
  __esModule: true,
  default: () => <div data-testid="search-form" />,
}));

jest.mock("../../app/buscar/components/SearchResults", () => ({
  __esModule: true,
  default: () => <div data-testid="search-results" />,
}));

jest.mock("../../app/components/BackendStatusIndicator", () => ({
  __esModule: true,
  default: () => <div />,
  useBackendStatusContext: () => ({ status: "online", lastChecked: null }),
}));

jest.mock("../../app/buscar/components/SearchErrorBoundary", () => ({
  SearchErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("../../components/MobileDrawer", () => ({
  MobileDrawer: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("../../lib/utils/dateDiffInDays", () => ({
  dateDiffInDays: () => 0,
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("../../lib/lastSearchCache", () => ({
  checkHasLastSearch: () => false,
  getLastSearch: () => null,
}));

// The buscar page wraps HomePageContent in Suspense — useSearchParams needs
// to be mocked at the page level to avoid the Suspense boundary issue.
// We already mock next/navigation above, which covers useSearchParams.

import HomePage from "../../app/buscar/page";

describe("T3 — Buscar page footer always visible (GTM-POLISH-001 AC8)", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Auth: resolved, authenticated user
    mockUseAuth.mockReturnValue({
      session: { access_token: "tok-buscar" },
      user: { id: "user-1", email: "test@example.com" },
      loading: false,
      isAdmin: false,
    });
  });

  it("renders a footer element on the buscar page", () => {
    render(<HomePage />);
    // The footer uses role="contentinfo" (implicit for <footer>)
    const footer = document.querySelector("footer");
    expect(footer).not.toBeNull();
    expect(footer).toBeInTheDocument();
  });

  it("footer does not have the 'hidden' class (always visible)", () => {
    render(<HomePage />);
    const footer = document.querySelector("footer");
    expect(footer).not.toBeNull();
    expect(footer!.className).not.toContain("hidden");
  });

  it("footer is visible even when search result is null (no results state)", () => {
    // useSearch already returns result: null via the mock above
    render(<HomePage />);

    const footer = document.querySelector("footer");
    expect(footer).not.toBeNull();
    expect(footer).toBeVisible();
  });

  // UX-419: Compact footer replaces 4-section footer with inline links
  it("footer contains essential links (Planos, Privacidade, Termos)", () => {
    render(<HomePage />);

    expect(screen.getByText(/Planos e Preços/i)).toBeInTheDocument();
    expect(screen.getByText(/Política de Privacidade/i)).toBeInTheDocument();
    expect(screen.getByText(/Termos de Uso/i)).toBeInTheDocument();
  });

  it("footer contains copyright notice", () => {
    render(<HomePage />);
    expect(
      screen.getByText(/CONFENGE Avaliações/i)
    ).toBeInTheDocument();
  });
});
