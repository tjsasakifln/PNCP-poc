/**
 * STORY-323: Revenue Share Tracking — Frontend Tests
 *
 * AC16: Signup detects ?partner=slug and shows badge
 * AC17: Planos detects partner cookie and shows discount banner
 * AC18: Admin partners page renders table
 */

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// ── Mocks ───────────────────────────────────────────────────────────────────

// Mock useAuth
const mockSession = { access_token: "test-token" };
const mockUser = { id: "user-1", email: "test@test.com" };

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({
    session: mockSession,
    user: mockUser,
    loading: false,
    isAdmin: true,
    signUpWithEmail: jest.fn(),
    signInWithGoogle: jest.fn(),
  }),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), identifyUser: jest.fn() }),
  getStoredUTMParams: () => ({}),
}));

jest.mock("../../hooks/usePlan", () => ({
  usePlan: () => ({
    planInfo: { plan_id: "free_trial", subscription_status: "active" },
    loading: false,
  }),
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  },
}));

jest.mock("../../lib/error-messages", () => ({
  translateAuthError: (msg: string) => msg,
  getUserFriendlyError: (err: unknown) => (err instanceof Error ? err.message : "erro"),
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

jest.mock("../../lib/plans", () => ({
  PLAN_CONFIGS: { smartlic_pro: { displayNamePt: "SmartLic Pro", price: "R$ 397" } },
}));

jest.mock("../../components/subscriptions/PlanToggle", () => ({
  PlanToggle: ({ onChange }: { onChange: (v: string) => void }) => (
    <button onClick={() => onChange("monthly")}>Toggle</button>
  ),
}));

jest.mock("../../lib/copy/roi", () => ({
  formatCurrency: (v: number) => `R$ ${v}`,
}));

jest.mock("../../components/TestimonialSection", () => {
  const component = () => <div>Testimonials</div>;
  component.TESTIMONIALS = [];
  return { __esModule: true, default: component, TESTIMONIALS: [] };
});

jest.mock("../../app/components/landing/LandingNavbar", () => ({
  __esModule: true,
  default: () => <div>Navbar</div>,
}));

jest.mock("../../app/components/InstitutionalSidebar", () => ({
  __esModule: true,
  default: () => <div>Sidebar</div>,
}));

// ── Tests ───────────────────────────────────────────────────────────────────

describe("STORY-323: Partner Revenue Share", () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset cookies
    document.cookie = "smartlic_partner=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
    // Reset URL
    Object.defineProperty(window, "location", {
      value: { ...window.location, search: "", href: "" },
      writable: true,
    });
  });

  describe("AC16: Signup page partner detection", () => {
    it("shows partner badge when ?partner=slug is present", async () => {
      Object.defineProperty(window, "location", {
        value: { ...window.location, search: "?partner=triunfo-legis" },
        writable: true,
      });

      // Dynamic import to pick up URL mock
      const SignupPage = (await import("../../app/signup/page")).default;
      render(<SignupPage />);

      await waitFor(() => {
        const badge = screen.queryByTestId("partner-badge");
        expect(badge).toBeInTheDocument();
      });
    });

    it("persists partner slug to localStorage", async () => {
      Object.defineProperty(window, "location", {
        value: { ...window.location, search: "?partner=concreta" },
        writable: true,
      });

      const SignupPage = (await import("../../app/signup/page")).default;
      render(<SignupPage />);

      await waitFor(() => {
        expect(localStorage.getItem("smartlic_partner")).toBe("concreta");
      });
    });

    it("does not show badge when no partner param", async () => {
      Object.defineProperty(window, "location", {
        value: { ...window.location, search: "" },
        writable: true,
      });
      localStorage.removeItem("smartlic_partner");

      const SignupPage = (await import("../../app/signup/page")).default;
      render(<SignupPage />);

      const badge = screen.queryByTestId("partner-badge");
      expect(badge).not.toBeInTheDocument();
    });
  });

  describe("AC17: Planos page partner discount", () => {
    it("shows discount banner when partner is in localStorage", async () => {
      localStorage.setItem("smartlic_partner", "triunfo-legis");

      const PlanosPage = (await import("../../app/planos/page")).default;
      render(<PlanosPage />);

      await waitFor(() => {
        const banner = screen.queryByTestId("partner-discount-banner");
        expect(banner).toBeInTheDocument();
      });
    });

    it("does not show discount banner without partner", async () => {
      localStorage.removeItem("smartlic_partner");

      const PlanosPage = (await import("../../app/planos/page")).default;
      render(<PlanosPage />);

      const banner = screen.queryByTestId("partner-discount-banner");
      expect(banner).not.toBeInTheDocument();
    });
  });

  describe("AC18: Admin partners dashboard", () => {
    it("renders partners table with data", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            partners: [
              {
                id: "p-1",
                name: "Triunfo Legis",
                slug: "triunfo-legis",
                contact_email: "triunfo@test.com",
                status: "active",
                revenue_share_pct: 25,
                referrals_total: 5,
                referrals_active: 3,
                monthly_share: 297.75,
                created_at: "2026-01-01",
              },
            ],
          }),
      }) as jest.Mock;

      const PartnersPage = (await import("../../app/admin/partners/page")).default;
      render(<PartnersPage />);

      await waitFor(() => {
        expect(screen.getByText("Triunfo Legis")).toBeInTheDocument();
      });
    });

    it("shows empty state when no partners", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ partners: [] }),
      }) as jest.Mock;

      const PartnersPage = (await import("../../app/admin/partners/page")).default;
      render(<PartnersPage />);

      await waitFor(() => {
        expect(screen.getByText("Nenhum parceiro cadastrado")).toBeInTheDocument();
      });
    });

    it("export CSV button is present", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ partners: [] }),
      }) as jest.Mock;

      const PartnersPage = (await import("../../app/admin/partners/page")).default;
      render(<PartnersPage />);

      await waitFor(() => {
        expect(screen.getByText("Exportar CSV")).toBeInTheDocument();
      });
    });

    it("create partner form toggles", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ partners: [] }),
      }) as jest.Mock;

      const PartnersPage = (await import("../../app/admin/partners/page")).default;
      render(<PartnersPage />);

      await waitFor(() => {
        expect(screen.getByText("Novo Parceiro")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Novo Parceiro"));

      await waitFor(() => {
        expect(screen.getByText("Cancelar")).toBeInTheDocument();
        expect(screen.getByText("Nome da Consultoria")).toBeInTheDocument();
      });
    });
  });
});
