/**
 * GTM-UX-002: Erros Silenciosos → Estados de Erro Explicitos
 *
 * T1: Historico mostra error state quando API falha
 * T2: Dashboard mostra error state (nao zeros) quando API falha
 * T3: Backend analytics retorna 503 quando Supabase indisponivel (backend test)
 * T4: Retry button funciona e recarrega dados
 * T5: Empty state diferente de error state visualmente
 * T6: Zero resultados mostra sugestoes acionaveis
 * T7: Botao "Ver resultados" de estados proximos ajusta filtros
 */

import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Shared Mocks ─────────────────────────────────────────────────────

const mockTrackEvent = jest.fn();

let mockAuthState: any = {
  user: { id: "user-1", email: "test@test.com" },
  session: { access_token: "mock-token" },
  loading: false,
  isAdmin: false,
};

let mockBackendStatus: "online" | "offline" | "recovering" = "online";

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockAuthState,
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));

jest.mock("../app/components/BackendStatusIndicator", () => ({
  useBackendStatusContext: () => ({
    status: mockBackendStatus,
    isPolling: false,
    checkHealth: jest.fn(),
  }),
  BackendStatusProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useBackendStatus: () => ({
    status: mockBackendStatus,
    isPolling: false,
    checkHealth: jest.fn(),
  }),
  __esModule: true,
  default: () => null,
}));

jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("../components/PageHeader", () => ({
  PageHeader: ({ title }: any) => <div data-testid="page-header"><h1>{title}</h1></div>,
}));

// TD-008: historico page now uses useSessions SWR hook instead of global.fetch
let mockUseSessionsReturn: any = {
  sessions: [],
  total: 0,
  loading: false,
  error: null,
  errorTimestamp: null,
  refresh: jest.fn(),
  silentRefresh: jest.fn(),
};
jest.mock("../hooks/useSessions", () => ({
  useSessions: () => mockUseSessionsReturn,
}));

// FE-007: mensagens page now uses useConversations SWR hook instead of global.fetch
let mockUseConversationsReturn: any = {
  conversations: [],
  isLoading: false,
  error: null,
  mutate: jest.fn(),
  refresh: jest.fn(),
};
jest.mock("../hooks/useConversations", () => ({
  useConversations: () => mockUseConversationsReturn,
}));

jest.mock("recharts", () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div />,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  PieChart: ({ children }: any) => <div>{children}</div>,
  Pie: () => <div />,
  Cell: () => <div />,
}));

// ─── Setup ─────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  jest.useRealTimers();
  global.fetch = jest.fn();
  mockAuthState = {
    user: { id: "user-1", email: "test@test.com" },
    session: { access_token: "mock-token" },
    loading: false,
    isAdmin: false,
  };
  mockBackendStatus = "online";
  mockUseSessionsReturn = {
    sessions: [],
    total: 0,
    loading: false,
    error: null,
    errorTimestamp: null,
    refresh: jest.fn(),
    silentRefresh: jest.fn(),
  };
  mockUseConversationsReturn = {
    conversations: [],
    isLoading: false,
    error: null,
    mutate: jest.fn(),
    refresh: jest.fn(),
  };
});

// ─── T1: Historico mostra error state quando API falha ──────────────

describe("T1: Historico shows error state when API fails", () => {
  it("should show ErrorStateWithRetry when /api/sessions fails", async () => {
    mockUseSessionsReturn = {
      sessions: [],
      total: 0,
      loading: false,
      error: "Não foi possível carregar seu histórico.",
      errorTimestamp: new Date().toISOString(),
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    const HistoricoPage = require("../app/historico/page").default;
    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId("error-state")).toBeInTheDocument();
      expect(screen.getByTestId("error-retry-button")).toBeInTheDocument();
    });
  });

  it("should show ErrorStateWithRetry when /api/sessions returns non-ok", async () => {
    mockUseSessionsReturn = {
      sessions: [],
      total: 0,
      loading: false,
      error: "Não foi possível carregar seu histórico.",
      errorTimestamp: new Date().toISOString(),
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    const HistoricoPage = require("../app/historico/page").default;
    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId("error-state")).toBeInTheDocument();
    });
  });
});

// ─── T2: Dashboard mostra error state (nao zeros) quando API falha ──

describe("T2: Dashboard shows error state (not zeros) when API fails", () => {
  it("should show per-card error states when individual endpoints fail", async () => {
    jest.useFakeTimers();

    // Summary fails, others succeed
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes("summary"))
        return Promise.resolve({ ok: false, status: 503 });
      if (url.includes("searches-over-time"))
        return Promise.resolve({ ok: true, json: async () => ({ data: [] }) });
      if (url.includes("top-dimensions"))
        return Promise.resolve({ ok: true, json: async () => ({ top_ufs: [], top_sectors: [] }) });
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    const DashboardPage = require("../app/dashboard/page").default;
    render(<DashboardPage />);

    // Wait for retries to exhaust
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        jest.advanceTimersByTime(i === 0 ? 100 : 30_000);
        await Promise.resolve();
        await Promise.resolve();
      });
    }

    // Should NOT show zeros — should show error state
    await waitFor(() => {
      // Error state should be present (either per-card or full-page)
      const errorStates = screen.queryAllByTestId("error-state");
      const dashboardErrorState = screen.queryByTestId("dashboard-empty-state");
      expect(errorStates.length + (dashboardErrorState ? 1 : 0)).toBeGreaterThan(0);
    });

    jest.useRealTimers();
  });
});

// ─── T4: Retry button funciona e recarrega dados ──────────────────

describe("T4: Retry button works and reloads data", () => {
  it("should call refresh when retry button is clicked in Historico", async () => {
    const mockRefresh = jest.fn();
    mockUseSessionsReturn = {
      sessions: [],
      total: 0,
      loading: false,
      error: "Não foi possível carregar seu histórico.",
      errorTimestamp: new Date().toISOString(),
      refresh: mockRefresh,
      silentRefresh: jest.fn(),
    };

    const HistoricoPage = require("../app/historico/page").default;
    render(<HistoricoPage />);

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByTestId("error-state")).toBeInTheDocument();
    });

    // Click retry
    fireEvent.click(screen.getByTestId("error-retry-button"));

    // Should trigger refresh via useSessions
    expect(mockRefresh).toHaveBeenCalled();
  });
});

// ─── T5: Empty state diferente de error state visualmente ──────────

describe("T5: Empty state different from error state visually", () => {
  it("should show EmptyState (not error) when Historico has no sessions", async () => {
    mockUseSessionsReturn = {
      sessions: [],
      total: 0,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    const HistoricoPage = require("../app/historico/page").default;
    render(<HistoricoPage />);

    // Wait for the EmptyState to appear via data-testid (avoids Unicode encoding issues)
    await waitFor(() => {
      expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    }, { timeout: 5000 });

    // Should NOT show error state when there are simply no results
    expect(screen.queryByTestId("error-state")).not.toBeInTheDocument();
  });

  it("should show ErrorState (not empty) when Historico API fails", async () => {
    mockUseSessionsReturn = {
      sessions: [],
      total: 0,
      loading: false,
      error: "Não foi possível carregar seu histórico.",
      errorTimestamp: new Date().toISOString(),
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    };

    const HistoricoPage = require("../app/historico/page").default;
    render(<HistoricoPage />);

    await waitFor(() => {
      // Should show error state with retry button
      expect(screen.getByTestId("error-state")).toBeInTheDocument();
      expect(screen.getByTestId("error-retry-button")).toBeInTheDocument();
    });

    // Should NOT show the friendly empty state
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();
  });

  it("should show empty state (not error) in Mensagens when no conversations exist", async () => {
    // FE-007: mensagens page uses useConversations hook (not global.fetch)
    mockUseConversationsReturn = {
      conversations: [],
      isLoading: false,
      error: null,
      mutate: jest.fn(),
      refresh: jest.fn(),
    };

    const MensagensPage = require("../app/mensagens/page").default;
    render(<MensagensPage />);

    await waitFor(() => {
      // GTM-POLISH-001 AC9: Updated empty state text
      expect(screen.getByText(/Nenhuma conversa ainda/)).toBeInTheDocument();
      expect(screen.queryByTestId("error-state")).not.toBeInTheDocument();
    });
  });

  it("should show error state (not empty) in Mensagens when API fails", async () => {
    // FE-007: mensagens page uses useConversations hook (not global.fetch)
    mockUseConversationsReturn = {
      conversations: [],
      isLoading: false,
      error: "Não foi possível carregar suas conversas",
      mutate: jest.fn(),
      refresh: jest.fn(),
    };

    const MensagensPage = require("../app/mensagens/page").default;
    render(<MensagensPage />);

    await waitFor(() => {
      expect(screen.getByTestId("error-state")).toBeInTheDocument();
      expect(screen.queryByText(/Nenhuma mensagem ainda/)).not.toBeInTheDocument();
    });
  });
});

// ─── T6: Zero resultados mostra sugestoes acionaveis ───────────────

describe("T6: Zero results shows actionable suggestions", () => {
  it("should render ZeroResultsSuggestions with clickable buttons", () => {
    const { ZeroResultsSuggestions } = require("../app/buscar/components/ZeroResultsSuggestions");

    const mockAdjustPeriod = jest.fn();
    const mockAddNeighbors = jest.fn();
    const mockChangeSector = jest.fn();

    render(
      <ZeroResultsSuggestions
        sectorName="Informatica"
        ufCount={3}
        dayRange={30}
        onAdjustPeriod={mockAdjustPeriod}
        onAddNeighborStates={mockAddNeighbors}
        onChangeSector={mockChangeSector}
      />
    );

    // AC10: Specific message
    expect(screen.getByText(/Nenhuma oportunidade encontrada/)).toBeInTheDocument();
    expect(screen.getByText(/Informatica/)).toBeInTheDocument();
    expect(screen.getByText(/3 estados/)).toBeInTheDocument();
    expect(screen.getByText(/30 dias/)).toBeInTheDocument();

    // AC12: Clickable buttons
    const periodBtn = screen.getByTestId("suggestion-adjust-period");
    const neighborsBtn = screen.getByTestId("suggestion-add-neighbors");
    const sectorBtn = screen.getByTestId("suggestion-change-sector");

    expect(periodBtn).toBeInTheDocument();
    expect(neighborsBtn).toBeInTheDocument();
    expect(sectorBtn).toBeInTheDocument();

    // Click and verify callbacks
    fireEvent.click(periodBtn);
    expect(mockAdjustPeriod).toHaveBeenCalledTimes(1);

    fireEvent.click(neighborsBtn);
    expect(mockAddNeighbors).toHaveBeenCalledTimes(1);

    fireEvent.click(sectorBtn);
    expect(mockChangeSector).toHaveBeenCalledTimes(1);
  });
});

// ─── T7: Botao "Ver resultados" de estados proximos ────────────────

describe("T7: Nearby results button adjusts filters and re-executes", () => {
  it("should show nearby results banner and handle click", () => {
    const { ZeroResultsSuggestions } = require("../app/buscar/components/ZeroResultsSuggestions");

    const mockViewNearby = jest.fn();

    render(
      <ZeroResultsSuggestions
        sectorName="Informatica"
        ufCount={2}
        dayRange={30}
        nearbyResultsCount={15}
        onViewNearbyResults={mockViewNearby}
      />
    );

    // AC11: Nearby results banner
    expect(screen.getByText(/15/)).toBeInTheDocument();
    expect(screen.getByText(/estados proximos/)).toBeInTheDocument();

    // AC11: Click "Ver resultados"
    const viewBtn = screen.getByTestId("view-nearby-results");
    expect(viewBtn).toBeInTheDocument();

    fireEvent.click(viewBtn);
    expect(mockViewNearby).toHaveBeenCalledTimes(1);
  });

  it("should NOT show nearby results when count is 0", () => {
    const { ZeroResultsSuggestions } = require("../app/buscar/components/ZeroResultsSuggestions");

    render(
      <ZeroResultsSuggestions
        sectorName="Informatica"
        ufCount={2}
        dayRange={30}
        nearbyResultsCount={0}
        onViewNearbyResults={jest.fn()}
      />
    );

    expect(screen.queryByTestId("view-nearby-results")).not.toBeInTheDocument();
  });
});

// ─── ErrorStateWithRetry Component Tests ────────────────────────────

describe("ErrorStateWithRetry component", () => {
  it("should render message, icon, and retry button", () => {
    const { ErrorStateWithRetry } = require("../components/ErrorStateWithRetry");

    render(
      <ErrorStateWithRetry
        message="Erro de teste"
        onRetry={jest.fn()}
      />
    );

    expect(screen.getByTestId("error-state")).toBeInTheDocument();
    expect(screen.getByText("Erro de teste")).toBeInTheDocument();
    expect(screen.getByTestId("error-retry-button")).toBeInTheDocument();
  });

  it("should show timestamp when provided", () => {
    const { ErrorStateWithRetry } = require("../components/ErrorStateWithRetry");

    render(
      <ErrorStateWithRetry
        message="Erro"
        timestamp="2026-02-23T14:30:00Z"
        onRetry={jest.fn()}
      />
    );

    expect(screen.getByText(/Erro registrado em/)).toBeInTheDocument();
  });

  it("should show loading state during retry", async () => {
    const { ErrorStateWithRetry } = require("../components/ErrorStateWithRetry");

    let resolveRetry: () => void;
    const retryPromise = new Promise<void>((resolve) => { resolveRetry = resolve; });
    const onRetry = jest.fn(() => retryPromise);

    render(
      <ErrorStateWithRetry
        message="Erro"
        onRetry={onRetry}
      />
    );

    fireEvent.click(screen.getByTestId("error-retry-button"));

    await waitFor(() => {
      expect(screen.getByText(/Tentando/)).toBeInTheDocument();
    });

    // Resolve the retry
    await act(async () => {
      resolveRetry!();
    });
  });

  it("should render in compact mode", () => {
    const { ErrorStateWithRetry } = require("../components/ErrorStateWithRetry");

    render(
      <ErrorStateWithRetry
        message="Erro compacto"
        onRetry={jest.fn()}
        compact
      />
    );

    expect(screen.getByTestId("error-state")).toBeInTheDocument();
    expect(screen.getByText("Erro compacto")).toBeInTheDocument();
  });
});
