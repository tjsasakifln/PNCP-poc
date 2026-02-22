/**
 * UX-339: Planos page tests — contextual banners + pricing visibility
 * Verifies that logged-in users always see full pricing, with status banners.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock usePlan hook
const mockUsePlan = jest.fn();
jest.mock("../hooks/usePlan", () => ({
  usePlan: () => mockUsePlan(),
}));

// Mock useAuth hook
const mockUseAuth = jest.fn();
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock useAnalytics
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

// Mock LandingNavbar
jest.mock("../app/components/landing/LandingNavbar", () => {
  return function MockLandingNavbar() {
    return <div data-testid="landing-navbar">Navbar</div>;
  };
});

// Mock PlanToggle
jest.mock("../components/subscriptions/PlanToggle", () => ({
  PlanToggle: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <div data-testid="plan-toggle">
      <button onClick={() => onChange("monthly")}>Mensal</button>
      <button onClick={() => onChange("semiannual")}>Semestral</button>
      <button onClick={() => onChange("annual")}>Anual</button>
    </div>
  ),
}));

// Mock formatCurrency
jest.mock("../lib/copy/roi", () => ({
  formatCurrency: (v: number) => `R$ ${(v).toLocaleString("pt-BR")}`,
}));

// Mock error-messages
jest.mock("../lib/error-messages", () => ({
  getUserFriendlyError: () => "Erro",
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// Mock sonner
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

import PlanosPage from "../app/planos/page";

// Helper: base plan info
function makePlanInfo(overrides: Record<string, unknown> = {}) {
  return {
    user_id: "user-1",
    email: "test@test.com",
    plan_id: "free_trial",
    plan_name: "Trial",
    subscription_status: "active",
    trial_expires_at: null,
    capabilities: {
      max_history_days: 30,
      allow_excel: false,
      max_requests_per_month: 3,
      max_requests_per_min: 1,
      max_summary_tokens: 500,
      priority: "LOW",
    },
    quota_used: 0,
    quota_remaining: 3,
    quota_reset_date: "2026-03-01",
    ...overrides,
  };
}

function setupMocks(opts: {
  session?: boolean;
  isAdmin?: boolean;
  planInfo?: ReturnType<typeof makePlanInfo> | null;
  profilePlanId?: string;
  profileIsAdmin?: boolean;
}) {
  const {
    session = false,
    isAdmin = false,
    planInfo = null,
    profilePlanId,
    profileIsAdmin,
  } = opts;

  mockUseAuth.mockReturnValue({
    session: session ? { access_token: "tok-123" } : null,
    user: session ? { id: "user-1" } : null,
    isAdmin,
    loading: false,
  });

  mockUsePlan.mockReturnValue({
    planInfo,
    loading: false,
    error: null,
    refresh: jest.fn(),
  });

  // Mock fetch for profile endpoint
  const profileResponse = profilePlanId || profileIsAdmin
    ? { plan_id: profilePlanId, is_admin: profileIsAdmin }
    : null;

  mockFetch.mockImplementation((url: string) => {
    if (typeof url === "string" && url.includes("/v1/me")) {
      return Promise.resolve({
        ok: !!profileResponse,
        json: () => Promise.resolve(profileResponse || {}),
      });
    }
    // billing-portal
    if (typeof url === "string" && url.includes("/api/billing-portal")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ url: "https://billing.stripe.com/session" }),
      });
    }
    // checkout
    if (typeof url === "string" && url.includes("/v1/checkout")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ checkout_url: "https://checkout.stripe.com/session" }),
      });
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
  });
}

beforeEach(() => {
  jest.clearAllMocks();
  // Reset window.location.search
  Object.defineProperty(window, "location", {
    value: { ...window.location, search: "", href: "" },
    writable: true,
  });
});

// ──────────────────────────────────────────────────────────────
// AC1: Logged-in user (any status) always sees full pricing
// ──────────────────────────────────────────────────────────────

describe("AC1: Pricing always visible for logged-in users", () => {
  it("shows pricing card for active subscriber", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "smartlic_pro", subscription_status: "active" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByText("SmartLic Pro")).toBeInTheDocument();
      expect(screen.getByText(/1\.000 análises por mês/)).toBeInTheDocument();
    });
  });

  it("shows pricing card for admin user (no longer blocked by overlay)", async () => {
    setupMocks({
      session: true,
      isAdmin: true,
      planInfo: makePlanInfo(),
      profileIsAdmin: true,
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByText("SmartLic Pro")).toBeInTheDocument();
      expect(screen.getByText(/1\.000 análises por mês/)).toBeInTheDocument();
    });
  });

  it("shows pricing card for trial user", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "free_trial", subscription_status: "active" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByText("SmartLic Pro")).toBeInTheDocument();
    });
  });

  it("shows pricing card for trial expired user", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "free_trial", subscription_status: "expired" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByText("SmartLic Pro")).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC2: Contextual status banner
// ──────────────────────────────────────────────────────────────

describe("AC2: Contextual status banner", () => {
  it("shows subscriber banner for active subscriber", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "smartlic_pro", subscription_status: "active" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByTestId("status-banner-subscriber")).toBeInTheDocument();
      expect(screen.getByText(/Você possui acesso completo ao SmartLic/)).toBeInTheDocument();
    });
  });

  it("shows trial banner with days remaining", async () => {
    const futureDate = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString();
    setupMocks({
      session: true,
      planInfo: makePlanInfo({
        plan_id: "free_trial",
        subscription_status: "active",
        trial_expires_at: futureDate,
      }),
    });
    render(<PlanosPage />);
    // Banner renders immediately from mocked usePlan
    const banner = await screen.findByTestId("status-banner-trial");
    expect(banner).toBeInTheDocument();
    expect(banner.textContent).toMatch(/período de avaliação/);
    // Days remaining depends on trial_expires_at from planInfo
    expect(banner.textContent).toMatch(/\d+ dias restantes/);
  });

  it("shows singular 'dia restante' for 1 day", async () => {
    // Set expiry to just under 24h from now to ensure ceil gives 1
    const tomorrowDate = new Date(Date.now() + 0.5 * 24 * 60 * 60 * 1000).toISOString();
    setupMocks({
      session: true,
      planInfo: makePlanInfo({
        plan_id: "free_trial",
        subscription_status: "active",
        trial_expires_at: tomorrowDate,
      }),
    });
    render(<PlanosPage />);
    const banner = await screen.findByTestId("status-banner-trial");
    expect(banner.textContent).toMatch(/1 dia restante/);
  });

  it("shows expired banner for trial expired", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "free_trial", subscription_status: "expired" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByTestId("status-banner-expired")).toBeInTheDocument();
      expect(screen.getByText(/período de avaliação encerrou/)).toBeInTheDocument();
    });
  });

  it("shows privileged banner for admin", async () => {
    setupMocks({
      session: true,
      isAdmin: true,
      planInfo: makePlanInfo(),
      profileIsAdmin: true,
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByTestId("status-banner-privileged")).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC3: Subscriber sees "Gerenciar assinatura" → billing portal
// ──────────────────────────────────────────────────────────────

describe("AC3: Gerenciar assinatura for subscriber", () => {
  it("shows 'Gerenciar assinatura' button in banner", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "smartlic_pro", subscription_status: "active" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getAllByText("Gerenciar assinatura").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("calls billing portal on banner button click", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "smartlic_pro", subscription_status: "active" }),
    });
    render(<PlanosPage />);
    const user = userEvent.setup();

    await waitFor(() => {
      expect(screen.getByTestId("status-banner-subscriber")).toBeInTheDocument();
    });

    // Click the banner "Gerenciar assinatura" button
    const bannerBtn = screen.getByTestId("status-banner-subscriber").querySelector("button")!;
    await user.click(bannerBtn);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/billing-portal",
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC4: Trial user sees "Assinar agora" CTA
// ──────────────────────────────────────────────────────────────

describe("AC4: Trial user CTA", () => {
  it("shows 'Assinar agora' CTA for trial user", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "free_trial", subscription_status: "active" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Assinar agora" })).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC5: Trial expired user sees urgency CTA
// ──────────────────────────────────────────────────────────────

describe("AC5: Trial expired CTA", () => {
  it("shows 'Continuar com SmartLic' CTA for expired trial", async () => {
    setupMocks({
      session: true,
      planInfo: makePlanInfo({ plan_id: "free_trial", subscription_status: "expired" }),
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Continuar com SmartLic" })).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC6: Toggle mensal/semestral/anual funcional
// ──────────────────────────────────────────────────────────────

describe("AC6: Billing period toggle", () => {
  it("renders PlanToggle component", async () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    expect(screen.getByTestId("plan-toggle")).toBeInTheDocument();
  });
});

// ──────────────────────────────────────────────────────────────
// AC7: FAQ visible and functional
// ──────────────────────────────────────────────────────────────

describe("AC7: FAQ visible", () => {
  it("shows all FAQ questions", async () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    expect(screen.getByText("Posso cancelar a qualquer momento?")).toBeInTheDocument();
    expect(screen.getByText("Existe contrato de fidelidade?")).toBeInTheDocument();
    expect(screen.getByText("O que acontece se eu cancelar?")).toBeInTheDocument();
    expect(screen.getByText("Como funciona a cobrança semestral e anual?")).toBeInTheDocument();
  });

  it("toggles FAQ answer on click", async () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    const user = userEvent.setup();
    const faqBtn = screen.getByText("Posso cancelar a qualquer momento?");
    await user.click(faqBtn);
    expect(screen.getByText(/Cancele quando quiser e mantenha o acesso/)).toBeInTheDocument();
  });

  it("FAQ visible for admin user too", async () => {
    setupMocks({
      session: true,
      isAdmin: true,
      planInfo: makePlanInfo(),
      profileIsAdmin: true,
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByText("Perguntas Frequentes")).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC8: ROI section visible
// ──────────────────────────────────────────────────────────────

describe("AC8: ROI section visible", () => {
  it("shows ROI anchor message", async () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    expect(screen.getByText(/Uma única licitação ganha/)).toBeInTheDocument();
  });

  it("ROI visible for admin user too", async () => {
    setupMocks({
      session: true,
      isAdmin: true,
      planInfo: makePlanInfo(),
      profileIsAdmin: true,
    });
    render(<PlanosPage />);
    await waitFor(() => {
      expect(screen.getByText(/Uma única licitação ganha/)).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC9: Non-logged user sees normal page (no banner)
// ──────────────────────────────────────────────────────────────

describe("AC9: Non-logged user (anonymous)", () => {
  it("shows no status banner", () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    expect(screen.queryByTestId("status-banner-subscriber")).not.toBeInTheDocument();
    expect(screen.queryByTestId("status-banner-trial")).not.toBeInTheDocument();
    expect(screen.queryByTestId("status-banner-expired")).not.toBeInTheDocument();
    expect(screen.queryByTestId("status-banner-privileged")).not.toBeInTheDocument();
  });

  it("shows 'Começar Agora' CTA", () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    expect(screen.getByRole("button", { name: "Começar Agora" })).toBeInTheDocument();
  });

  it("shows pricing content normally", () => {
    setupMocks({ session: false });
    render(<PlanosPage />);
    expect(screen.getByText("SmartLic Pro")).toBeInTheDocument();
    expect(screen.getByText(/1\.000 análises por mês/)).toBeInTheDocument();
    expect(screen.getByText("Perguntas Frequentes")).toBeInTheDocument();
  });
});
