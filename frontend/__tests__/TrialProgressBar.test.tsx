/**
 * STORY-448: TrialProgressBar component tests
 * AC1: Not rendered on excluded paths (/login, etc.)
 * AC3: Color classes by urgency (green/yellow/red)
 * AC5: Not rendered for paid users or expired trials
 */

import { render, screen } from "@testing-library/react";
import { TrialProgressBar } from "../components/TrialProgressBar";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockTrackEvent = jest.fn();

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    session: { access_token: "mock-token" },
  }),
}));

jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    onClick,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    onClick?: () => void;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} onClick={onClick} {...props}>
        {children}
      </a>
    );
  };
});

// SWR mock — must always return an object (never undefined)
jest.mock("swr", () => {
  function useSWR() {
    return {
      data: { total_searches: 5, total_opportunities: 12 },
      error: undefined,
    };
  }
  return { __esModule: true, default: useSWR, mutate: jest.fn() };
});

// pathname mock (overridden per test)
const mockUsePathname = jest.fn(() => "/buscar");
jest.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
}));

// usePlan mock — factory so tests can override planInfo
const mockPlanInfo = {
  plan_id: "free_trial",
  subscription_status: "trialing",
  // trial_expires_at: 7 days from now → day ≈ 8 (14 - 7 + 1)
  trial_expires_at: new Date(
    Date.now() + 7 * 24 * 60 * 60 * 1000
  ).toISOString(),
};

jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({ planInfo: mockPlanInfo }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Override planInfo for a single test by replacing the module mock inline.
 * We re-import so jest.mock hoisting still applies — instead, we manipulate
 * the shared `mockPlanInfo` object directly.
 */
function setPlanInfo(overrides: Partial<typeof mockPlanInfo>) {
  Object.assign(mockPlanInfo, overrides);
}

function resetPlanInfo() {
  mockPlanInfo.plan_id = "free_trial";
  mockPlanInfo.subscription_status = "trialing";
  mockPlanInfo.trial_expires_at = new Date(
    Date.now() + 7 * 24 * 60 * 60 * 1000
  ).toISOString();
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("TrialProgressBar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePathname.mockReturnValue("/buscar");
    resetPlanInfo();
  });

  // AC5: Not rendered for paid users
  it("does not render for paid user (plan_id !== free_trial)", () => {
    setPlanInfo({ plan_id: "smartlic_pro" });
    render(<TrialProgressBar />);
    expect(
      screen.queryByTestId("trial-progress-bar")
    ).not.toBeInTheDocument();
  });

  // AC5: Not rendered for expired trial
  it("does not render for expired trial", () => {
    setPlanInfo({ subscription_status: "expired" });
    render(<TrialProgressBar />);
    expect(
      screen.queryByTestId("trial-progress-bar")
    ).not.toBeInTheDocument();
  });

  // AC1: Not rendered on /login
  it("does not render on /login route", () => {
    mockUsePathname.mockReturnValue("/login");
    render(<TrialProgressBar />);
    expect(
      screen.queryByTestId("trial-progress-bar")
    ).not.toBeInTheDocument();
  });

  // AC1: Not rendered on /auth/* routes
  it("does not render on /auth/callback route", () => {
    mockUsePathname.mockReturnValue("/auth/callback");
    render(<TrialProgressBar />);
    expect(
      screen.queryByTestId("trial-progress-bar")
    ).not.toBeInTheDocument();
  });

  // AC1: Not rendered on root path
  it("does not render on / (root)", () => {
    mockUsePathname.mockReturnValue("/");
    render(<TrialProgressBar />);
    expect(
      screen.queryByTestId("trial-progress-bar")
    ).not.toBeInTheDocument();
  });

  // AC3: Green color for day 1-7
  it("renders with green classes for trial day 5 (9 days remaining)", () => {
    // 9 days left → day = 14 - 9 + 1 = 6
    setPlanInfo({
      trial_expires_at: new Date(
        Date.now() + 9 * 24 * 60 * 60 * 1000
      ).toISOString(),
    });
    render(<TrialProgressBar />);
    const bar = screen.getByTestId("trial-progress-bar");
    expect(bar).toBeInTheDocument();
    expect(bar.className).toContain("bg-green-50");
    expect(bar.className).toContain("text-green-800");
  });

  // AC3: Yellow color for day 8-11
  it("renders with yellow classes for trial day 10 (5 days remaining)", () => {
    // 5 days left → day = 14 - 5 + 1 = 10
    setPlanInfo({
      trial_expires_at: new Date(
        Date.now() + 5 * 24 * 60 * 60 * 1000
      ).toISOString(),
    });
    render(<TrialProgressBar />);
    const bar = screen.getByTestId("trial-progress-bar");
    expect(bar).toBeInTheDocument();
    expect(bar.className).toContain("bg-yellow-50");
    expect(bar.className).toContain("text-yellow-800");
  });

  // AC3: Red color for day 12-14
  it("renders with red classes for trial day 13 (2 days remaining)", () => {
    // 2 days left → day = 14 - 2 + 1 = 13
    setPlanInfo({
      trial_expires_at: new Date(
        Date.now() + 2 * 24 * 60 * 60 * 1000
      ).toISOString(),
    });
    render(<TrialProgressBar />);
    const bar = screen.getByTestId("trial-progress-bar");
    expect(bar).toBeInTheDocument();
    expect(bar.className).toContain("bg-red-50");
    expect(bar.className).toContain("text-red-800");
  });

  // AC2: Shows analytics data in message
  it("renders with correct analytics text from summary data", () => {
    // 7 days left → day = 8
    render(<TrialProgressBar />);
    expect(
      screen.getByText(/Dia \d+ de 14 — Você já fez 5 buscas e encontrou 12 editais\./)
    ).toBeInTheDocument();
  });

  // AC4: CTA link points to /planos
  it("CTA link points to /planos", () => {
    render(<TrialProgressBar />);
    const cta = screen.getByTestId("trial-progress-bar-cta");
    expect(cta).toHaveAttribute("href", "/planos");
    expect(cta).toHaveTextContent("Ver Planos →");
  });

  // Renders on authenticated page (/buscar)
  it("renders on authenticated page /buscar", () => {
    render(<TrialProgressBar />);
    expect(screen.getByTestId("trial-progress-bar")).toBeInTheDocument();
  });
});
