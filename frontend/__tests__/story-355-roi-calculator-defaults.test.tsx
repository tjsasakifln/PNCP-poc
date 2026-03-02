/**
 * STORY-355: ROI calculator — defaults honestos e disclaimers
 *
 * Tests:
 * - AC1: Disclaimer visible in all calculator scenarios
 * - AC2: timeSavedPerSearch = 3.0 (not 8.5)
 * - AC3: "Investimento se paga na primeira licitação ganha" copy preserved
 * - AC4: potentialReturn is dynamic (not hardcoded "500x")
 * - AC5: Conservative scenario exists alongside default
 * - AC6: Copy is NOT banned
 * - AC7: Disclaimer in all scenarios
 */

import { render, screen, fireEvent } from "@testing-library/react";
import {
  calculateROI,
  calculateConservativeROI,
  calculatePotentialReturn,
  DEFAULT_VALUES,
  ROI_DISCLAIMER,
  getROIMessage,
  getPresetScenarioROI,
} from "@/lib/copy/roi";
import { pricing, BANNED_PHRASES } from "@/lib/copy/valueProps";
import PricingPage from "@/app/pricing/page";
import PlanosPage from "@/app/planos/page";

// Mock Footer for pricing page
jest.mock("../app/components/Footer", () => {
  return function MockFooter() {
    return <div data-testid="footer">Footer</div>;
  };
});

// Mock PlanToggle for planos page
jest.mock("../components/subscriptions/PlanToggle", () => ({
  PlanToggle: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <div role="radiogroup" aria-label="Escolha seu período de acesso">
      <input type="radio" name="billing" value="monthly" aria-label="Mensal" aria-checked={value === "monthly"} onClick={() => onChange("monthly")} readOnly />
      <input type="radio" name="billing" value="semiannual" aria-label="Semestral Economize 10%" aria-checked={value === "semiannual"} onClick={() => onChange("semiannual")} readOnly />
      <input type="radio" name="billing" value="annual" aria-label="Anual Economize 20%" aria-checked={value === "annual"} onClick={() => onChange("annual")} readOnly />
    </div>
  ),
}));

// Mock AuthProvider
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    session: null,
    user: null,
    isAdmin: false,
    loading: false,
  }),
}));

// Mock usePlan
jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({
    planInfo: null,
    loading: false,
    error: null,
    refresh: jest.fn(),
  }),
}));

// Mock useAnalytics
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    identifyUser: jest.fn(),
    resetUser: jest.fn(),
    trackPageView: jest.fn(),
  }),
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock sonner
jest.mock("sonner", () => ({
  toast: { error: jest.fn(), success: jest.fn() },
}));

// Mock LandingNavbar
jest.mock("../app/components/landing/LandingNavbar", () => {
  return function MockNavbar() {
    return <div data-testid="landing-navbar">Navbar</div>;
  };
});

// Mock TestimonialSection
jest.mock("../components/TestimonialSection", () => {
  const MockTestimonialSection = () => <div data-testid="testimonials">Testimonials</div>;
  MockTestimonialSection.TESTIMONIALS = [];
  return MockTestimonialSection;
});

// Mock fetch
global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 401 });

// Mock window.location
const originalLocation = window.location;

beforeEach(() => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 401 });
  // @ts-expect-error - mocking window.location
  delete window.location;
  window.location = { ...originalLocation, href: "", search: "" };
});

afterAll(() => {
  window.location = originalLocation;
});

// ============================================================================
// UNIT TESTS — roi.ts logic
// ============================================================================

describe("STORY-355: ROI Calculator Defaults", () => {
  describe("AC2: timeSavedPerSearch adjusted to 3.0", () => {
    it("should have timeSavedPerSearch = 3.0", () => {
      expect(DEFAULT_VALUES.timeSavedPerSearch).toBe(3.0);
    });

    it("should NOT be 8.5 (old inflated value)", () => {
      expect(DEFAULT_VALUES.timeSavedPerSearch).not.toBe(8.5);
    });

    it("should have conservativeMultiplier = 0.5", () => {
      expect(DEFAULT_VALUES.conservativeMultiplier).toBe(0.5);
    });

    it("should produce ROI < 50x with defaults (was 170x)", () => {
      const result = calculateROI({
        hoursPerWeek: DEFAULT_VALUES.hoursPerWeek,
        costPerHour: DEFAULT_VALUES.costPerHour,
        planPrice: 397,
      });
      expect(result.roi).toBeLessThan(50);
    });

    it("should still produce positive ROI with defaults", () => {
      const result = calculateROI({
        hoursPerWeek: DEFAULT_VALUES.hoursPerWeek,
        costPerHour: DEFAULT_VALUES.costPerHour,
        planPrice: 397,
      });
      expect(result.monthlySavings).toBeGreaterThan(0);
      expect(result.roi).toBeGreaterThan(0);
    });
  });

  describe("AC1: ROI_DISCLAIMER exists", () => {
    it("should export ROI_DISCLAIMER constant", () => {
      expect(ROI_DISCLAIMER).toBeDefined();
      expect(typeof ROI_DISCLAIMER).toBe("string");
    });

    it("should contain key disclaimer text", () => {
      expect(ROI_DISCLAIMER).toContain("Valores estimados");
      expect(ROI_DISCLAIMER).toContain("não garante vitória em licitações");
    });

    it("should mention SmartLic role accurately", () => {
      expect(ROI_DISCLAIMER).toContain("auxilia na descoberta e priorização");
    });
  });

  describe("AC3: Copy 'se paga na primeira licitação ganha' preserved", () => {
    it("should have tagline in ROI message for high ROI", () => {
      const msg = getROIMessage({
        hoursPerWeek: 20,
        costPerHour: 200,
        planPrice: 397,
      });
      expect(msg.tagline).toBe(
        "Investimento se paga na primeira licitação ganha"
      );
    });
  });

  describe("AC4: potentialReturn is dynamic", () => {
    it("should calculate potentialReturn dynamically", () => {
      const result = calculatePotentialReturn(200_000, 397);
      const expected = Math.round(200_000 / (397 * 12));
      expect(result).toBe(`${expected}x`);
    });

    it("should NOT be hardcoded '500x'", () => {
      const result = calculatePotentialReturn(200_000, 397);
      expect(result).not.toBe("500x");
    });

    it("should scale with contract value", () => {
      const small = calculatePotentialReturn(100_000, 397);
      const large = calculatePotentialReturn(500_000, 397);
      const smallNum = parseInt(small);
      const largeNum = parseInt(large);
      expect(largeNum).toBeGreaterThan(smallNum);
    });

    it("should scale with plan price", () => {
      const cheap = calculatePotentialReturn(200_000, 297);
      const expensive = calculatePotentialReturn(200_000, 997);
      const cheapNum = parseInt(cheap);
      const expensiveNum = parseInt(expensive);
      expect(cheapNum).toBeGreaterThan(expensiveNum);
    });

    it("valueProps.pricing.roi.exampleCalculation.potentialReturn should be dynamic", () => {
      const pr = pricing.roi.calculator.exampleCalculation.potentialReturn;
      expect(pr).not.toBe("500x");
      expect(pr).toMatch(/^\d+x$/);
    });
  });

  describe("AC5: Conservative scenario calculator", () => {
    it("should export calculateConservativeROI function", () => {
      expect(typeof calculateConservativeROI).toBe("function");
    });

    it("should produce lower ROI than default", () => {
      const inputs = { hoursPerWeek: 10, costPerHour: 100, planPrice: 397 };
      const standard = calculateROI(inputs);
      const conservative = calculateConservativeROI(inputs);
      expect(conservative.roi).toBeLessThan(standard.roi);
    });

    it("should produce lower savings than default", () => {
      const inputs = { hoursPerWeek: 10, costPerHour: 100, planPrice: 397 };
      const standard = calculateROI(inputs);
      const conservative = calculateConservativeROI(inputs);
      expect(conservative.monthlySavings).toBeLessThan(standard.monthlySavings);
    });

    it("should use 50% of hoursPerWeek", () => {
      const inputs = { hoursPerWeek: 10, costPerHour: 100, planPrice: 397 };
      const conservative = calculateConservativeROI(inputs);
      const halfHoursResult = calculateROI({ ...inputs, hoursPerWeek: 5 });
      expect(conservative.manualSearchCostPerMonth).toBe(halfHoursResult.manualSearchCostPerMonth);
    });
  });

  describe("AC6: Copy is NOT banned", () => {
    it("'se paga na primeira licitação' should NOT be in BANNED_PHRASES", () => {
      const isBanned = BANNED_PHRASES.some((phrase) =>
        "Investimento se paga na primeira licitação ganha"
          .toLowerCase()
          .includes(phrase.toLowerCase())
      );
      expect(isBanned).toBe(false);
    });
  });

  describe("AC7: Disclaimer in all preset scenarios", () => {
    it.each(["freelancer", "pme", "enterprise"] as const)(
      "scenario '%s' should produce valid ROI with disclaimer available",
      (scenario) => {
        const result = getPresetScenarioROI(scenario, 397);
        expect(result.roi).toBeGreaterThan(0);
        expect(ROI_DISCLAIMER).toBeDefined();
      }
    );
  });
});

// ============================================================================
// COMPONENT TESTS — pricing/page.tsx
// ============================================================================

describe("STORY-355: Pricing Page ROI Calculator", () => {
  it("AC1: should render ROI disclaimer on pricing page", () => {
    render(<PricingPage />);
    const disclaimer = screen.getByTestId("roi-disclaimer");
    expect(disclaimer).toBeInTheDocument();
    expect(disclaimer.textContent).toContain("Valores estimados");
    expect(disclaimer.textContent).toContain("não garante vitória em licitações");
  });

  it("AC5: should render scenario toggle with default and conservative options", () => {
    render(<PricingPage />);
    const toggle = screen.getByTestId("scenario-toggle");
    expect(toggle).toBeInTheDocument();
    expect(screen.getByText("Cenário Padrão")).toBeInTheDocument();
    expect(screen.getByText("Cenário Conservador")).toBeInTheDocument();
  });

  it("AC5: should switch to conservative scenario on click", () => {
    render(<PricingPage />);
    const conservativeBtn = screen.getByTestId("conservative-toggle");

    const defaultRoi = screen.getByTestId("roi-value").textContent;
    fireEvent.click(conservativeBtn);
    const conservativeRoi = screen.getByTestId("roi-value").textContent;
    expect(conservativeRoi).not.toBe(defaultRoi);
  });

  it("AC5: conservative scenario should show lower manual cost", () => {
    render(<PricingPage />);
    const defaultCost = screen.getByTestId("manual-cost").textContent;

    fireEvent.click(screen.getByTestId("conservative-toggle"));
    const conservativeCost = screen.getByTestId("manual-cost").textContent;
    expect(conservativeCost).not.toBe(defaultCost);
  });

  it("AC1+AC7: disclaimer remains visible after switching scenarios", () => {
    render(<PricingPage />);
    expect(screen.getByTestId("roi-disclaimer")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("conservative-toggle"));
    expect(screen.getByTestId("roi-disclaimer")).toBeInTheDocument();
  });
});

// ============================================================================
// COMPONENT TESTS — planos/page.tsx
// ============================================================================

describe("STORY-355: Planos Page ROI Disclaimer", () => {
  it("AC1: should render ROI disclaimer on planos page", () => {
    render(<PlanosPage />);
    const disclaimer = screen.getByTestId("roi-disclaimer");
    expect(disclaimer).toBeInTheDocument();
    expect(disclaimer.textContent).toContain("Valores estimados");
    expect(disclaimer.textContent).toContain("não garante vitória em licitações");
  });
});
