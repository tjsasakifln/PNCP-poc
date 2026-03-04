/**
 * SAB-012: Microcopy, formatação monetária e UX login/mobile
 *
 * Tests all 12 ACs across 4 fronts:
 * - AC4: formatCurrencyBR helper (unit tests)
 * - AC1-AC3: Search time display rules in Histórico
 * - AC5-AC6: PT-BR currency applied to Dashboard/Histórico
 * - AC7-AC9: Mobile bottom nav abbreviations
 * - AC10-AC12: Login page visual hierarchy
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { formatCurrencyBR } from "../lib/format-currency";

// ============================================================================
// AC4: formatCurrencyBR unit tests (no rendering needed)
// ============================================================================

describe("SAB-012 AC4: formatCurrencyBR helper", () => {
  it("formats billions as 'R$ X,X bi'", () => {
    expect(formatCurrencyBR(3_495_100_000)).toBe("R$ 3,5 bi");
    expect(formatCurrencyBR(1_000_000_000)).toBe("R$ 1,0 bi");
    expect(formatCurrencyBR(10_500_000_000)).toBe("R$ 10,5 bi");
  });

  it("formats millions as 'R$ X,X mi'", () => {
    expect(formatCurrencyBR(130_700_000)).toBe("R$ 130,7 mi");
    expect(formatCurrencyBR(1_000_000)).toBe("R$ 1,0 mi");
    expect(formatCurrencyBR(45_000_000)).toBe("R$ 45,0 mi");
    expect(formatCurrencyBR(3_500_000)).toBe("R$ 3,5 mi");
  });

  it("formats thousands in PT-BR standard (R$ X.XXX)", () => {
    expect(formatCurrencyBR(45_000)).toBe("R$ 45.000");
    expect(formatCurrencyBR(1_500)).toBe("R$ 1.500");
    expect(formatCurrencyBR(999_999)).toBe("R$ 999.999");
  });

  it("formats small values without decimals", () => {
    expect(formatCurrencyBR(500)).toBe("R$ 500");
    expect(formatCurrencyBR(0)).toBe("R$ 0");
  });

  it("uses comma as decimal separator (PT-BR)", () => {
    const result = formatCurrencyBR(2_750_000_000);
    expect(result).toContain(",");
    expect(result).toBe("R$ 2,8 bi");
  });
});

// ============================================================================
// Mocks for component rendering
// ============================================================================

// Mutable auth state — changed per describe block
let mockAuthState: any = {
  session: { access_token: "test-token", user: { id: "u1", email: "test@test.com", created_at: "2026-01-01" } },
  user: { id: "u1", email: "test@test.com" },
  loading: false,
  signOut: jest.fn(),
  signInWithEmail: jest.fn(),
  signInWithMagicLink: jest.fn(),
  signInWithGoogle: jest.fn(),
};

jest.mock("next/link", () => {
  return function MockLink({ children, ...props }: any) {
    return <a {...props}>{children}</a>;
  };
});
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/historico",
  useSearchParams: () => new URLSearchParams(),
}));
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockAuthState,
}));
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), identifyUser: jest.fn() }),
}));
jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({ planInfo: null }),
}));
jest.mock("../components/PageHeader", () => ({
  PageHeader: function Mock({ title }: any) { return <h1>{title}</h1>; },
}));
jest.mock("../components/EmptyState", () => ({
  EmptyState: function Mock() { return null; },
}));
jest.mock("../components/ErrorStateWithRetry", () => ({
  ErrorStateWithRetry: function Mock() { return null; },
}));
jest.mock("../components/AuthLoadingScreen", () => ({
  AuthLoadingScreen: function Mock() { return null; },
}));
jest.mock("../lib/error-messages", () => ({
  getUserFriendlyError: (m: string) => m,
  translateAuthError: (m: string) => m,
}));
jest.mock("../lib/constants/sector-names", () => ({
  getSectorDisplayName: (s: string) => s,
}));
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), info: jest.fn(), success: jest.fn() },
  Toaster: () => null,
}));
jest.mock("../app/components/InstitutionalSidebar", () => {
  return function MockSidebar() {
    return <div data-testid="sidebar" />;
  };
});
jest.mock("next/dynamic", () => {
  return function mockDynamic() {
    return function MockDynamicComponent() { return null; };
  };
});

import HistoricoPage from "../app/historico/page";
import { BottomNav } from "../components/BottomNav";
import LoginPage from "../app/login/page";

// ============================================================================
// Helper
// ============================================================================

function makeSession(overrides: Record<string, any> = {}) {
  return {
    id: "session-1",
    sectors: ["informatica"],
    ufs: ["SP"],
    data_inicial: "2026-01-01",
    data_final: "2026-01-10",
    custom_keywords: null,
    total_raw: 100,
    total_filtered: 10,
    valor_total: 50000,
    resumo_executivo: "Test",
    created_at: "2026-01-01T00:00:00Z",
    status: "completed",
    error_message: null,
    error_code: null,
    duration_ms: null,
    pipeline_stage: null,
    started_at: "2026-01-01T00:00:00Z",
    response_state: null,
    ...overrides,
  };
}

// ============================================================================
// AC1-AC3: Search time display (Histórico)
// ============================================================================

describe("SAB-012 AC1-AC3: Search time display in Histórico", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthState = {
      session: { access_token: "test-token", user: { id: "u1", email: "test@test.com", created_at: "2026-01-01" } },
      user: { id: "u1", email: "test@test.com" },
      loading: false,
      signOut: jest.fn(),
      signInWithEmail: jest.fn(),
      signInWithMagicLink: jest.fn(),
      signInWithGoogle: jest.fn(),
    };
  });

  it("AC1: shows 'Análise profunda' label when duration > 60s", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        sessions: [makeSession({ duration_ms: 93800 })],
        total: 1,
      }),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("Análise profunda")).toBeInTheDocument();
      expect(screen.getByTestId("deep-analysis-label")).toBeInTheDocument();
    });

    // Should NOT show the raw time
    expect(screen.queryByText("93.8s")).not.toBeInTheDocument();
  }, 10000);

  it("AC2: shows time badge when duration < 30s", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        sessions: [makeSession({ duration_ms: 5200 })],
        total: 1,
      }),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId("fast-search-badge")).toBeInTheDocument();
      expect(screen.getByText("5.2s")).toBeInTheDocument();
    });

    expect(screen.queryByText("Análise profunda")).not.toBeInTheDocument();
  }, 10000);

  it("AC3: hides time completely when duration is 30-60s", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        sessions: [makeSession({ duration_ms: 45000 })],
        total: 1,
      }),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("informatica")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("deep-analysis-label")).not.toBeInTheDocument();
    expect(screen.queryByTestId("fast-search-badge")).not.toBeInTheDocument();
    expect(screen.queryByText("45.0s")).not.toBeInTheDocument();
  }, 10000);

  it("AC3: hides time when duration_ms is null", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        sessions: [makeSession({ duration_ms: null })],
        total: 1,
      }),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("informatica")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("deep-analysis-label")).not.toBeInTheDocument();
    expect(screen.queryByTestId("fast-search-badge")).not.toBeInTheDocument();
  }, 10000);

  it("AC6: Histórico uses PT-BR currency formatting", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        sessions: [makeSession({ valor_total: 3_500_000 })],
        total: 1,
      }),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByText("R$ 3,5 mi")).toBeInTheDocument();
    });
  }, 10000);
});

// ============================================================================
// AC7-AC9: BottomNav abbreviations
// ============================================================================

describe("SAB-012 AC7-AC9: Mobile bottom nav abbreviations", () => {
  beforeEach(() => {
    mockAuthState = {
      session: { access_token: "test-token", user: { id: "u1", email: "test@test.com" } },
      loading: false,
      signOut: jest.fn(),
    };
  });

  // SHIP-002: Mensagens removed, Dash added in place of Msgs
  it("AC8: uses abbreviated labels consistently", () => {
    render(<BottomNav />);

    expect(screen.getByText("Busca")).toBeInTheDocument();
    expect(screen.getByText("Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Hist.")).toBeInTheDocument();
    expect(screen.getByText("Dash")).toBeInTheDocument();
    expect(screen.getByText("Mais")).toBeInTheDocument();
  });

  it("AC8: old long labels are not present", () => {
    render(<BottomNav />);

    expect(screen.queryByText("Buscar")).not.toBeInTheDocument();
    expect(screen.queryByText("Histórico")).not.toBeInTheDocument();
  });

  it("AC9: abbreviated items have aria-label for accessibility", () => {
    render(<BottomNav />);

    const histLink = screen.getByText("Hist.").closest("a");
    expect(histLink).toHaveAttribute("aria-label", "Histórico");

    const dashLink = screen.getByText("Dash").closest("a");
    expect(dashLink).toHaveAttribute("aria-label", "Dashboard");
  });

  it("AC9: labels have truncate class to prevent overflow", () => {
    render(<BottomNav />);

    const labels = screen.getByTestId("bottom-nav").querySelectorAll("span.truncate");
    expect(labels.length).toBeGreaterThanOrEqual(4);
  });
});

// ============================================================================
// AC10-AC12: Login page hierarchy
// ============================================================================

describe("SAB-012 AC10-AC12: Login page visual hierarchy", () => {
  beforeEach(() => {
    // Login tests need session=null to show the login form
    mockAuthState = {
      session: null,
      user: null,
      loading: false,
      signOut: jest.fn(),
      signInWithEmail: jest.fn(),
      signInWithMagicLink: jest.fn(),
      signInWithGoogle: jest.fn(),
    };
  });

  it("AC10: Google OAuth button has primary styling (shadow-md, border-2, font-semibold)", () => {
    render(<LoginPage />);

    const googleBtn = screen.getByTestId("google-oauth-button");
    expect(googleBtn).toBeInTheDocument();
    expect(googleBtn.className).toContain("shadow-md");
    expect(googleBtn.className).toContain("border-2");
    expect(googleBtn.className).toContain("font-semibold");
    expect(googleBtn.className).toContain("text-base");
  });

  it("AC10: Google OAuth button is full-width", () => {
    render(<LoginPage />);

    const googleBtn = screen.getByTestId("google-oauth-button");
    expect(googleBtn.className).toContain("w-full");
  });

  it("AC11: Divider says 'ou continue com email'", () => {
    render(<LoginPage />);

    expect(screen.getByText("ou continue com email")).toBeInTheDocument();
  });

  it("AC12: Email mode toggle has smaller secondary styling", () => {
    render(<LoginPage />);

    const emailToggle = screen.getByText("Email + Senha");
    expect(emailToggle.className).toContain("text-xs");

    const magicToggle = screen.getByText("Magic Link");
    expect(magicToggle.className).toContain("text-xs");
  });

  it("AC12: Submit button is less prominent than Google OAuth", () => {
    render(<LoginPage />);

    const googleBtn = screen.getByTestId("google-oauth-button");
    const submitBtn = screen.getByRole("button", { name: /Entrar$/i });

    // Google: text-base, font-semibold, shadow-md
    expect(googleBtn.className).toContain("text-base");
    expect(googleBtn.className).toContain("font-semibold");
    expect(googleBtn.className).toContain("shadow-md");

    // Submit: text-sm, font-medium
    expect(submitBtn.className).toContain("text-sm");
    expect(submitBtn.className).toContain("font-medium");
  });
});
