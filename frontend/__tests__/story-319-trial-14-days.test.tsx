/**
 * STORY-319: Frontend tests for 14-day trial.
 * AC16: Components display "14 dias" instead of "30 dias".
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => "/buscar",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock useAnalytics
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    trackPage: jest.fn(),
  }),
}));

// Mock useExperiments
jest.mock("../hooks/useExperiments", () => ({
  useExperiments: () => ({
    experiments: {},
    getVariant: () => null,
    getExperimentProperties: () => ({}),
    isLoaded: true,
  }),
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe("STORY-319: TrialExpiringBanner threshold", () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { TrialExpiringBanner } = require("../app/components/TrialExpiringBanner");

  it("AC8: shows banner when 6 days remaining (day 8 of 14-day trial)", () => {
    render(<TrialExpiringBanner daysRemaining={6} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("AC8: shows banner when 1 day remaining", () => {
    render(<TrialExpiringBanner daysRemaining={1} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("AC8: hides banner when 7 days remaining (before day 8)", () => {
    const { container } = render(<TrialExpiringBanner daysRemaining={7} />);
    expect(container.innerHTML).toBe("");
  });

  it("AC8: hides banner when 14 days remaining (start of trial)", () => {
    const { container } = render(<TrialExpiringBanner daysRemaining={14} />);
    expect(container.innerHTML).toBe("");
  });

  it("AC8: shows banner when 3 days remaining", () => {
    render(<TrialExpiringBanner daysRemaining={3} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("AC8: dismisses banner on close", () => {
    render(<TrialExpiringBanner daysRemaining={3} />);
    const dismissButton = screen.getByLabelText("Dispensar");
    fireEvent.click(dismissButton);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("STORY-319: TrialCountdown badge", () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { TrialCountdown } = require("../app/components/TrialCountdown");

  it("AC7: renders countdown for 14-day trial", () => {
    render(<TrialCountdown daysRemaining={14} />);
    expect(screen.getByText(/14 dias de acesso completo/)).toBeInTheDocument();
  });

  it("AC7: renders countdown for 7 days remaining", () => {
    render(<TrialCountdown daysRemaining={7} />);
    expect(screen.getByText(/7 dias de acesso completo/)).toBeInTheDocument();
  });

  it("AC7: renders nothing when 0 days remaining", () => {
    const { container } = render(<TrialCountdown daysRemaining={0} />);
    expect(container.innerHTML).toBe("");
  });
});

describe("STORY-319: InstitutionalSidebar copy", () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const InstitutionalSidebar = require("../app/components/InstitutionalSidebar").default;

  beforeEach(() => {
    // InstitutionalSidebar fetches /api/metrics/daily-volume on signup variant
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ total: 0 }),
    });
  });

  it("AC11: signup benefits say 14 dias", () => {
    render(<InstitutionalSidebar variant="signup" />);
    expect(screen.getByText("14 dias do produto completo — sem limites")).toBeInTheDocument();
  });

  it("AC11: does NOT mention 30 dias", () => {
    render(<InstitutionalSidebar variant="signup" />);
    expect(screen.queryByText(/30 dias do produto completo/)).not.toBeInTheDocument();
  });
});

describe("STORY-319: valueProps copy", () => {
  it("AC12: guarantee says 14 dias", () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { pricing } = require("../lib/copy/valueProps");
    expect(pricing.comparison.guarantee.smartlic).toContain("14 dias");
    expect(pricing.comparison.guarantee.smartlic).not.toContain("30 dias");
  });

  it("AC12: guarantee description says 14 dias", () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { pricing } = require("../lib/copy/valueProps");
    expect(pricing.guarantee.description).toContain("14 dias");
    expect(pricing.guarantee.description).not.toContain("30 dias");
  });
});
