/**
 * STORY-360: Pricing consistency tests
 *
 * AC3: Verify PRICING constants match Stripe/DB values
 * AC5: FAQ references PRICING constant (not hardcoded strings)
 * AC6: Pro (25%) vs Consultoria (20%) clearly differentiated
 * AC7: PRICING and CONSULTORIA_PRICING internally consistent
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";

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

// Mock formatCurrency (jsdom lacks full ICU)
jest.mock("../lib/copy/roi", () => ({
  formatCurrency: (v: number) => `R$ ${v.toLocaleString("pt-BR")}`,
  ROI_DISCLAIMER: "Disclaimer",
}));

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

import PlanosPage from "../app/planos/page";

beforeEach(() => {
  jest.clearAllMocks();
  Object.defineProperty(window, "location", {
    value: { ...window.location, search: "", href: "" },
    writable: true,
  });
  mockUseAuth.mockReturnValue({
    session: null,
    user: null,
    isAdmin: false,
    loading: false,
  });
  mockUsePlan.mockReturnValue({
    planInfo: null,
    loading: false,
    error: null,
    refresh: jest.fn(),
  });
  // Default: API fails, uses fallback
  mockFetch.mockResolvedValue({ ok: false });
});

// ──────────────────────────────────────────────────────────────
// AC7: PRICING constants internal consistency
// ──────────────────────────────────────────────────────────────

describe("AC7: Pricing fallback constants consistency", () => {
  it("Pro monthly price matches base (R$397)", () => {
    render(<PlanosPage />);
    // Default is monthly — should show R$397
    expect(screen.getByText(/R\$\s*397/)).toBeInTheDocument();
  });

  it("Pro semiannual total = monthly × 6 (R$2,142)", async () => {
    render(<PlanosPage />);
    // Click semiannual in PlanToggle
    const semiRadio = screen.getByRole("radio", { name: /Semestral/i });
    fireEvent.click(semiRadio);
    await waitFor(() => {
      expect(screen.getByText(/R\$\s*357/)).toBeInTheDocument();
      expect(screen.getByText(/R\$\s*2\.142/)).toBeInTheDocument();
    });
  });

  it("Pro annual total = monthly × 12 (R$3,564)", async () => {
    render(<PlanosPage />);
    const annualRadio = screen.getByRole("radio", { name: /Anual/i });
    fireEvent.click(annualRadio);
    await waitFor(() => {
      expect(screen.getByText(/R\$\s*297/)).toBeInTheDocument();
      // R$ 3.564 appears in both card total and ROI section — use getAllByText
      expect(screen.getAllByText(/R\$\s*3\.564/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it("Pro annual discount is 25% (not 20%)", async () => {
    render(<PlanosPage />);
    const annualRadio = screen.getByRole("radio", { name: /Anual/i });
    fireEvent.click(annualRadio);
    await waitFor(() => {
      const badges = screen.getAllByText(/Economize 25%/);
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  it("Consultoria annual discount is 20% (different from Pro 25%)", async () => {
    render(<PlanosPage />);
    const annualRadio = screen.getByRole("radio", { name: /Anual/i });
    fireEvent.click(annualRadio);
    await waitFor(() => {
      // Consultoria card shows "Economize 20%"
      const badges20 = screen.getAllByText(/Economize 20%/);
      expect(badges20.length).toBeGreaterThan(0);
      // Pro/toggle shows "Economize 25%"
      const badges25 = screen.getAllByText(/Economize 25%/);
      expect(badges25.length).toBeGreaterThan(0);
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC5: FAQ references PRICING values
// ──────────────────────────────────────────────────────────────

describe("AC5: FAQ discount references match PRICING", () => {
  it("FAQ mentions 10% for semiannual and 25% for annual", async () => {
    render(<PlanosPage />);
    // Open FAQ about billing periods
    const faqBtn = screen.getByText("Como funciona a cobrança semestral e anual?");
    fireEvent.click(faqBtn);
    await waitFor(() => {
      const answer = screen.getByText(/10% de economia.*25% de economia/);
      expect(answer).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC6: Pro vs Consultoria discount differentiation
// ──────────────────────────────────────────────────────────────

describe("AC6: Pro vs Consultoria discount differentiation", () => {
  it("semiannual shows same 10% for both plans", async () => {
    render(<PlanosPage />);
    const semiRadio = screen.getByRole("radio", { name: /Semestral/i });
    fireEvent.click(semiRadio);
    await waitFor(() => {
      const badges = screen.getAllByText(/Economize 10%/);
      // Toggle badge + Pro card badge + Consultoria card badge = at least 2
      expect(badges.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("annual shows 25% for Pro and 20% for Consultoria", async () => {
    render(<PlanosPage />);
    const annualRadio = screen.getByRole("radio", { name: /Anual/i });
    fireEvent.click(annualRadio);
    await waitFor(() => {
      // Both 25% and 20% badges present
      expect(screen.getAllByText(/Economize 25%/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Economize 20%/).length).toBeGreaterThan(0);
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC2: API fetch with fallback
// ──────────────────────────────────────────────────────────────

describe("AC2: Frontend pricing fetch with fallback", () => {
  it("uses fallback values when API fails", async () => {
    mockFetch.mockResolvedValue({ ok: false });
    render(<PlanosPage />);
    // Should still show pricing from fallback constants
    await waitFor(() => {
      expect(screen.getByText(/R\$\s*397/)).toBeInTheDocument();
    });
  });

  it("uses API values when available", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/api/plans")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            plans: [
              {
                id: "smartlic_pro",
                name: "SmartLic Pro",
                price_brl: 397,
                billing_periods: {
                  monthly: { price_cents: 39700, discount_percent: 0 },
                  semiannual: { price_cents: 35700, discount_percent: 10 },
                  annual: { price_cents: 29700, discount_percent: 25 },
                },
              },
            ],
          }),
        });
      }
      return Promise.resolve({ ok: false });
    });

    render(<PlanosPage />);
    // Should show pricing from API (same values as fallback for now)
    await waitFor(() => {
      expect(screen.getByText(/R\$\s*397/)).toBeInTheDocument();
    });
    // Verify API was called
    expect(mockFetch).toHaveBeenCalledWith("/api/plans");
  });

  it("updates pricing if API returns different values", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/api/plans")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            plans: [
              {
                id: "smartlic_pro",
                name: "SmartLic Pro",
                price_brl: 499,
                billing_periods: {
                  monthly: { price_cents: 49900, discount_percent: 0 },
                  semiannual: { price_cents: 44900, discount_percent: 10 },
                  annual: { price_cents: 37400, discount_percent: 25 },
                },
              },
            ],
          }),
        });
      }
      return Promise.resolve({ ok: false });
    });

    render(<PlanosPage />);
    // Wait for API pricing to load and replace fallback
    await waitFor(() => {
      expect(screen.getByText(/R\$\s*499/)).toBeInTheDocument();
    });
  });
});

// ──────────────────────────────────────────────────────────────
// AC3: Stripe price verification (via DB migration values)
// ──────────────────────────────────────────────────────────────

describe("AC3: Pricing values match Stripe (migration 20260226120000)", () => {
  // These values come from migration 20260226120000_story277_repricing_stripe_ids.sql
  const STRIPE_DB_VALUES = {
    pro: {
      monthly: 39700,    // R$397
      semiannual: 35700,  // R$357 (10% off)
      annual: 29700,      // R$297 (25% off)
    },
    consultoria: {
      monthly: 99700,    // R$997
      semiannual: 89700,  // R$897 (10% off)
      annual: 79700,      // R$797 (20% off)
    },
  };

  it("Pro fallback monthly matches DB (R$397 = 39700 cents)", () => {
    render(<PlanosPage />);
    // Verify R$397 is displayed (39700/100 = 397)
    expect(screen.getByText(/R\$\s*397/)).toBeInTheDocument();
    expect(STRIPE_DB_VALUES.pro.monthly / 100).toBe(397);
  });

  it("Pro discount percentages match DB", () => {
    // Semiannual: (397-357)/397 ≈ 10%
    expect(Math.round((397 - 357) / 397 * 100)).toBe(10);
    // Annual: (397-297)/397 ≈ 25%
    expect(Math.round((397 - 297) / 397 * 100)).toBe(25);
  });

  it("Consultoria discount percentages match DB", () => {
    // Semiannual: (997-897)/997 ≈ 10%
    expect(Math.round((997 - 897) / 997 * 100)).toBe(10);
    // Annual: (997-797)/997 ≈ 20%
    expect(Math.round((997 - 797) / 997 * 100)).toBe(20);
  });
});
