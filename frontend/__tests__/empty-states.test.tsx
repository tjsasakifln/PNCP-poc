/**
 * UX-341 — Empty States Educativos
 *
 * Tests for Pipeline, Historico, Dashboard empty states + Conta plan section.
 */

import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Shared mocks ────────────────────────────────────────────────────────────

const mockTrackEvent = jest.fn();
let mockAuthState: any = {
  user: { id: "user-1", email: "test@test.com", user_metadata: { full_name: "Test User" } },
  session: { access_token: "mock-token" },
  loading: false,
  signOut: jest.fn(),
};

let mockPlanInfo: any = null;

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockAuthState,
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));

jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({ planInfo: mockPlanInfo, loading: false, error: null, refresh: jest.fn() }),
}));

jest.mock("next/link", () => {
  return function MockLink({ children, href, ...rest }: any) {
    return <a href={href} {...rest}>{children}</a>;
  };
});

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
  usePathname: () => "/test",
}));

jest.mock("../components/PageHeader", () => ({
  PageHeader: ({ title }: any) => <div data-testid="page-header">{title}</div>,
}));

jest.mock("sonner", () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

jest.mock("../lib/error-messages", () => ({
  getUserFriendlyError: (e: any) => e?.message || "Erro",
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// ─── Pipeline mocks ──────────────────────────────────────────────────────────

let mockPipelineState: any = {
  items: [],
  loading: false,
  error: null,
  fetchItems: jest.fn(),
  updateItem: jest.fn(),
  removeItem: jest.fn(),
};

jest.mock("../hooks/usePipeline", () => ({
  usePipeline: () => mockPipelineState,
}));

jest.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: any) => <div>{children}</div>,
  DragOverlay: ({ children }: any) => <div>{children}</div>,
  closestCorners: jest.fn(),
  KeyboardSensor: jest.fn(),
  PointerSensor: jest.fn(),
  useSensor: () => ({}),
  useSensors: () => [],
}));

jest.mock("@dnd-kit/sortable", () => ({
  sortableKeyboardCoordinates: jest.fn(),
}));

jest.mock("../app/pipeline/PipelineColumn", () => ({
  PipelineColumn: () => <div data-testid="pipeline-column" />,
}));

jest.mock("../app/pipeline/PipelineCard", () => ({
  PipelineCard: () => <div data-testid="pipeline-card" />,
}));

jest.mock("../components/account/CancelSubscriptionModal", () => ({
  CancelSubscriptionModal: () => null,
}));

// ─── Reset state before each test ────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockAuthState = {
    user: { id: "user-1", email: "test@test.com", user_metadata: { full_name: "Test User" } },
    session: { access_token: "mock-token" },
    loading: false,
    signOut: jest.fn(),
  };
  mockPipelineState = {
    items: [],
    loading: false,
    error: null,
    fetchItems: jest.fn(),
    updateItem: jest.fn(),
    removeItem: jest.fn(),
  };
  mockPlanInfo = null;
  global.fetch = jest.fn();
});

// ═══════════════════════════════════════════════════════════════════════════════
// EmptyState Component
// ═══════════════════════════════════════════════════════════════════════════════

describe("EmptyState component", () => {
  let EmptyState: any;

  beforeEach(async () => {
    const mod = await import("../components/EmptyState");
    EmptyState = mod.EmptyState;
  });

  it("renders title, description, and CTA", () => {
    render(
      <EmptyState
        icon={<span data-testid="test-icon">I</span>}
        title="Test Title"
        description="Test description"
        ctaLabel="Go"
        ctaHref="/go"
      />
    );

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test description")).toBeInTheDocument();
    expect(screen.getByTestId("empty-state-cta")).toHaveAttribute("href", "/go");
    expect(screen.getByText("Go")).toBeInTheDocument();
  });

  it("renders numbered steps when provided", () => {
    render(
      <EmptyState
        icon={<span>I</span>}
        title="T"
        description="D"
        steps={["Step one", "Step two", "Step three"]}
        ctaLabel="Go"
        ctaHref="/go"
      />
    );

    expect(screen.getByText("Step one")).toBeInTheDocument();
    expect(screen.getByText("Step two")).toBeInTheDocument();
    expect(screen.getByText("Step three")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("has data-testid empty-state", () => {
    render(
      <EmptyState icon={<span>I</span>} title="T" description="D" ctaLabel="Go" ctaHref="/go" />
    );
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC1-AC3: Pipeline Empty State
// ═══════════════════════════════════════════════════════════════════════════════

describe("Pipeline empty state (AC1-AC3)", () => {
  let PipelinePage: any;

  beforeEach(async () => {
    jest.isolateModules(async () => {});
    const mod = await import("../app/pipeline/page");
    PipelinePage = mod.default;
  });

  it("AC1: shows educative empty state with 3 steps when no items", () => {
    render(<PipelinePage />);

    expect(screen.getByText("Seu Pipeline de Oportunidades")).toBeInTheDocument();
    expect(screen.getByText(/Busque licitacoes em/)).toBeInTheDocument();
    expect(screen.getByText(/Clique em "Acompanhar"/)).toBeInTheDocument();
    expect(screen.getByText(/Arraste entre as colunas/)).toBeInTheDocument();
  });

  it("AC2: CTA links to /buscar", () => {
    render(<PipelinePage />);

    const cta = screen.getByTestId("empty-state-cta");
    expect(cta).toHaveAttribute("href", "/buscar");
    expect(screen.getByText("Buscar oportunidades")).toBeInTheDocument();
  });

  it("AC3: empty state disappears when items exist", async () => {
    mockPipelineState = {
      ...mockPipelineState,
      items: [{
        id: "1",
        user_id: "user-1",
        pncp_id: "pncp-1",
        objeto: "Test item",
        orgao: "X",
        uf: "SP",
        valor_estimado: 100000,
        data_encerramento: null,
        link_pncp: null,
        stage: "descoberta",
        notes: null,
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      }],
    };
    render(<PipelinePage />);

    await waitFor(() => {
      expect(screen.queryByText("Seu Pipeline de Oportunidades")).not.toBeInTheDocument();
    });
    expect(screen.getAllByTestId("pipeline-column").length).toBeGreaterThan(0);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC4-AC6: Historico Empty State
// ═══════════════════════════════════════════════════════════════════════════════

describe("Historico empty state (AC4-AC6)", () => {
  let HistoricoPage: any;

  beforeEach(async () => {
    const mod = await import("../app/historico/page");
    HistoricoPage = mod.default;

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ sessions: [], total: 0 }),
    });
  });

  it("AC4: shows educative empty state when no sessions", async () => {
    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("Historico de Buscas")).toBeInTheDocument();
    });
  });

  it("AC5: mentions revisiting doesn't cost a new analysis", async () => {
    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText(/sem gastar uma nova analise/)).toBeInTheDocument();
    });
  });

  it("AC6: CTA 'Fazer primeira busca' links to /buscar", async () => {
    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("Historico de Buscas")).toBeInTheDocument();
    });

    const cta = screen.getByTestId("empty-state-cta");
    expect(cta).toHaveAttribute("href", "/buscar");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC7-AC8: Dashboard Empty State
// ═══════════════════════════════════════════════════════════════════════════════

describe("Dashboard empty state (AC7-AC8)", () => {
  let DashboardPage: any;

  beforeEach(async () => {
    // Mock recharts to avoid SSR issues
    jest.mock("recharts", () => ({
      BarChart: () => null,
      Bar: () => null,
      LineChart: () => null,
      Line: () => null,
      XAxis: () => null,
      YAxis: () => null,
      CartesianGrid: () => null,
      Tooltip: () => null,
      ResponsiveContainer: () => null,
      PieChart: () => null,
      Pie: () => null,
      Cell: () => null,
    }));

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        total_searches: 0,
        total_downloads: 0,
        total_opportunities: 0,
        total_value_discovered: 0,
        estimated_hours_saved: 0,
        avg_results_per_search: 0,
        success_rate: 0,
        member_since: "2026-01-01",
      }),
    });

    const mod = await import("../app/dashboard/page");
    DashboardPage = mod.default;
  });

  it("AC7: shows empty state with preview of what user will see", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Seu Painel de Inteligencia")).toBeInTheDocument();
    });

    expect(screen.getByText(/Resumo de oportunidades encontradas/)).toBeInTheDocument();
    expect(screen.getByText(/Tendencias do seu setor/)).toBeInTheDocument();
    expect(screen.getByText(/Valor total de oportunidades analisadas/)).toBeInTheDocument();
  });

  it("AC8: CTA 'Fazer primeira busca' links to /buscar", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Seu Painel de Inteligencia")).toBeInTheDocument();
    });

    const cta = screen.getByTestId("empty-state-cta");
    expect(cta).toHaveAttribute("href", "/buscar");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AC9-AC13: Conta Plan Section
// ═══════════════════════════════════════════════════════════════════════════════

describe("Conta plan section (AC9-AC13)", () => {
  let ContaPage: any;

  beforeEach(async () => {
    const mod = await import("../app/conta/page");
    ContaPage = mod.default;
  });

  it("AC9: shows trial status badge", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "free_trial",
      plan_name: "Trial",
      capabilities: { max_requests_per_month: 3 },
      quota_used: 1,
      quota_remaining: 2,
      quota_reset_date: null,
      trial_expires_at: new Date(Date.now() + 5 * 86400000).toISOString(),
      subscription_status: "trialing",
    };

    render(<ContaPage />);

    expect(screen.getByTestId("plan-section")).toBeInTheDocument();
    expect(screen.getByText("Periodo de avaliacao")).toBeInTheDocument();
  });

  it("AC9: shows active status badge for subscribers", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: { max_requests_per_month: 1000 },
      quota_used: 10,
      quota_remaining: 990,
      quota_reset_date: "2026-03-01",
      trial_expires_at: null,
      subscription_status: "active",
    };

    render(<ContaPage />);

    expect(screen.getByText("Ativo")).toBeInTheDocument();
  });

  it("AC10: shows trial days remaining and usage", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "free_trial",
      plan_name: "Trial",
      capabilities: { max_requests_per_month: 3 },
      quota_used: 1,
      quota_remaining: 2,
      quota_reset_date: null,
      trial_expires_at: new Date(Date.now() + 5 * 86400000).toISOString(),
      subscription_status: "trialing",
    };

    render(<ContaPage />);

    expect(screen.getByText("Dias restantes")).toBeInTheDocument();
    expect(screen.getByText("Analises usadas")).toBeInTheDocument();
    expect(screen.getByText("1 de 3")).toBeInTheDocument();
  });

  it("AC11: shows subscription details for active subscribers", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: { max_requests_per_month: 1000 },
      quota_used: 42,
      quota_remaining: 958,
      quota_reset_date: "2026-03-01",
      trial_expires_at: null,
      subscription_status: "active",
    };

    render(<ContaPage />);

    expect(screen.getByText("SmartLic Pro")).toBeInTheDocument();
    expect(screen.getByText("Analises este mes")).toBeInTheDocument();
    expect(screen.getByText("Proxima renovacao")).toBeInTheDocument();
  });

  it("AC12: trial user sees 'Assinar SmartLic Pro' as primary CTA", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "free_trial",
      plan_name: "Trial",
      capabilities: { max_requests_per_month: 3 },
      quota_used: 0,
      quota_remaining: 3,
      quota_reset_date: null,
      trial_expires_at: new Date(Date.now() + 5 * 86400000).toISOString(),
      subscription_status: "trialing",
    };

    render(<ContaPage />);

    expect(screen.getByText("Assinar SmartLic Pro")).toBeInTheDocument();
    const cta = screen.getByTestId("plan-cta-primary");
    expect(cta).toHaveAttribute("href", "/planos");
  });

  it("AC12: active subscriber sees 'Gerenciar acesso' as primary CTA", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: { max_requests_per_month: 1000 },
      quota_used: 10,
      quota_remaining: 990,
      quota_reset_date: "2026-03-01",
      trial_expires_at: null,
      subscription_status: "active",
    };

    render(<ContaPage />);

    expect(screen.getByText("Gerenciar acesso")).toBeInTheDocument();
  });

  it("AC13: cancel button is secondary/discreet text link", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: { max_requests_per_month: 1000 },
      quota_used: 10,
      quota_remaining: 990,
      quota_reset_date: "2026-03-01",
      trial_expires_at: null,
      subscription_status: "active",
    };

    render(<ContaPage />);

    const cancelBtn = screen.getByTestId("cancel-link");
    expect(cancelBtn).toBeInTheDocument();
    expect(cancelBtn.tagName).toBe("BUTTON");
    // Verify it's styled as discreet text (text-xs, not a big red button)
    expect(cancelBtn.className).toContain("text-xs");
    expect(cancelBtn.className).toContain("text-[var(--ink-muted)]");
  });

  it("AC9: shows expired status when subscription is not active", () => {
    mockPlanInfo = {
      user_id: "user-1",
      email: "test@test.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: { max_requests_per_month: 1000 },
      quota_used: 0,
      quota_remaining: 0,
      quota_reset_date: null,
      trial_expires_at: null,
      subscription_status: "canceled",
    };

    render(<ContaPage />);

    expect(screen.getByText("Expirado")).toBeInTheDocument();
    expect(screen.getByText("Reativar SmartLic Pro")).toBeInTheDocument();
  });
});
