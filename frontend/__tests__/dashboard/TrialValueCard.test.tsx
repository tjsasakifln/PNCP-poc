/**
 * STORY-443: TrialValueCard component tests
 * AC1: Only renders for free_trial + not expired
 * AC3: CTA links to /planos
 * AC4: Progress bar present
 * AC5: Does not render for pagantes or expired
 * AC6: Skeleton during loading
 */

import { render, screen } from "@testing-library/react";
import { TrialValueCard } from "../../app/dashboard/components/TrialValueCard";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockUseAuth = jest.fn();
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

const mockUsePlan = jest.fn();
jest.mock("../../hooks/usePlan", () => ({
  usePlan: () => mockUsePlan(),
}));

const mockUseSWR = jest.fn();
jest.mock("swr", () => ({
  __esModule: true,
  default: (...args: unknown[]) => mockUseSWR(...args),
}));

jest.mock("next/link", () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const FUTURE_EXPIRES = new Date(Date.now() + 7 * 86_400_000).toISOString(); // 7 days from now
const PAST_EXPIRES = new Date(Date.now() - 1 * 86_400_000).toISOString(); // expired yesterday

const SESSION = { access_token: "test-token" };

const TRIAL_PLAN_INFO = {
  plan_id: "free_trial",
  trial_expires_at: FUTURE_EXPIRES,
  subscription_status: "trialing",
};

const PAID_PLAN_INFO = {
  plan_id: "smartlic_pro",
  trial_expires_at: null,
  subscription_status: "active",
};

const MOCK_DATA = {
  total_value: 1_500_000,
  total_opportunities: 42,
  searches_used: 7,
  trial_expires_at: FUTURE_EXPIRES,
};

function setupMocks({
  planInfo = TRIAL_PLAN_INFO,
  swrData = MOCK_DATA,
  swrLoading = false,
}: {
  planInfo?: typeof TRIAL_PLAN_INFO | typeof PAID_PLAN_INFO | null;
  swrData?: typeof MOCK_DATA | null;
  swrLoading?: boolean;
} = {}) {
  mockUseAuth.mockReturnValue({ session: SESSION });
  mockUsePlan.mockReturnValue({ planInfo });
  mockUseSWR.mockReturnValue({ data: swrData, isLoading: swrLoading });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("TrialValueCard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("does not render for paid users (AC5)", () => {
    setupMocks({ planInfo: PAID_PLAN_INFO });
    const { container } = render(<TrialValueCard />);
    expect(container.firstChild).toBeNull();
  });

  it("does not render for expired trial (AC5)", () => {
    setupMocks({
      planInfo: { ...TRIAL_PLAN_INFO, trial_expires_at: PAST_EXPIRES },
    });
    const { container } = render(<TrialValueCard />);
    expect(container.firstChild).toBeNull();
  });

  it("shows skeleton while loading (AC6)", () => {
    setupMocks({ swrData: null, swrLoading: true });
    render(<TrialValueCard />);
    expect(screen.getByTestId("trial-value-card-skeleton")).toBeInTheDocument();
  });

  it("renders card with data for active trial user (AC1 + AC4)", () => {
    setupMocks();
    render(<TrialValueCard />);

    expect(screen.getByTestId("trial-value-card")).toBeInTheDocument();

    // AC4: Progress bar present
    expect(screen.getByTestId("trial-progress-bar")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();

    // Metrics displayed
    expect(screen.getByTestId("trial-total-value")).toBeInTheDocument();
    expect(screen.getByTestId("trial-total-opportunities")).toHaveTextContent("42");
    expect(screen.getByTestId("trial-searches-used")).toHaveTextContent("7");

    // Header text
    expect(screen.getByText("Você está no trial gratuito")).toBeInTheDocument();
  });

  it("CTA button links to /planos (AC3)", () => {
    setupMocks();
    render(<TrialValueCard />);

    const cta = screen.getByTestId("trial-cta-link");
    expect(cta).toBeInTheDocument();
    expect(cta).toHaveAttribute("href", "/planos");
    expect(cta).toHaveTextContent("Continue analisando com SmartLic Pro");
  });

  it("formats large values compactly", () => {
    setupMocks({ swrData: { ...MOCK_DATA, total_value: 1_500_000 } });
    render(<TrialValueCard />);
    expect(screen.getByTestId("trial-total-value")).toHaveTextContent("R$ 1.5M");
  });
});
