/**
 * GTM-FIX-007 AC13: PaymentFailedBanner component tests
 * Tests the payment failure banner shown when subscription_status = 'past_due'
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PaymentFailedBanner } from "../../components/billing/PaymentFailedBanner";

// Mock usePlan hook
const mockUsePlan = jest.fn();
jest.mock("../../hooks/usePlan", () => ({
  usePlan: () => mockUsePlan(),
}));

// Mock useAuth hook
const mockUseAuth = jest.fn();
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

const PAST_DUE_PLAN = {
  planInfo: {
    user_id: "123",
    email: "test@example.com",
    plan_id: "smartlic_pro",
    plan_name: "SmartLic Pro",
    subscription_status: "past_due",
    capabilities: {
      max_history_days: 1825,
      allow_excel: true,
      max_requests_per_month: 1000,
      max_requests_per_min: 10,
      max_summary_tokens: 1000,
      priority: "NORMAL",
    },
    quota_used: 50,
    quota_remaining: 950,
    quota_reset_date: "2026-03-01",
    trial_expires_at: null,
  },
  loading: false,
  error: null,
};

const AUTH_SESSION = {
  session: { access_token: "test-token" },
  user: { id: "123" },
};

describe("PaymentFailedBanner", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
    window.open = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // AC7: Renders when subscription_status is past_due
  it("renders banner when subscription_status is past_due", () => {
    mockUsePlan.mockReturnValue(PAST_DUE_PLAN);
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    render(<PaymentFailedBanner />);
    expect(screen.getByTestId("payment-failed-banner")).toBeInTheDocument();
  });

  // Does not render when status is active
  it("does not render when subscription_status is active", () => {
    mockUsePlan.mockReturnValue({
      ...PAST_DUE_PLAN,
      planInfo: { ...PAST_DUE_PLAN.planInfo, subscription_status: "active" },
    });
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    const { container } = render(<PaymentFailedBanner />);
    expect(container.firstChild).toBeNull();
  });

  // Does not render when status is trial
  it("does not render when subscription_status is trial", () => {
    mockUsePlan.mockReturnValue({
      ...PAST_DUE_PLAN,
      planInfo: { ...PAST_DUE_PLAN.planInfo, subscription_status: "trial" },
    });
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    const { container } = render(<PaymentFailedBanner />);
    expect(container.firstChild).toBeNull();
  });

  // Does not render when planInfo is null
  it("does not render when planInfo is null", () => {
    mockUsePlan.mockReturnValue({ planInfo: null, loading: false, error: null });
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    const { container } = render(<PaymentFailedBanner />);
    expect(container.firstChild).toBeNull();
  });

  // AC9: Correct banner text
  it("banner has correct text", () => {
    mockUsePlan.mockReturnValue(PAST_DUE_PLAN);
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    render(<PaymentFailedBanner />);
    expect(
      screen.getByText("Falha no pagamento da assinatura. Atualize seu cartão para continuar.")
    ).toBeInTheDocument();
  });

  // AC10: Update card button exists
  it("update card button exists", () => {
    mockUsePlan.mockReturnValue(PAST_DUE_PLAN);
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    render(<PaymentFailedBanner />);
    const button = screen.getByRole("button", { name: /atualizar cartão/i });
    expect(button).toBeInTheDocument();
  });

  // Calls billing portal API on button click
  it("calls billing portal API on button click", async () => {
    mockUsePlan.mockReturnValue(PAST_DUE_PLAN);
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ url: "https://billing.stripe.com/portal" }),
    });

    const user = userEvent.setup();
    render(<PaymentFailedBanner />);

    const button = screen.getByRole("button", { name: /atualizar cartão/i });
    await user.click(button);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/api/billing-portal", {
        method: "POST",
        headers: {
          Authorization: "Bearer test-token",
          "Content-Type": "application/json",
        },
      });
    });

    expect(window.open).toHaveBeenCalledWith("https://billing.stripe.com/portal", "_blank");
  });

  // Shows loading state while opening portal
  it("shows loading state while opening portal", async () => {
    mockUsePlan.mockReturnValue(PAST_DUE_PLAN);
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    (global.fetch as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({ url: "https://billing.stripe.com/portal" }),
              }),
            100
          )
        )
    );

    const user = userEvent.setup();
    render(<PaymentFailedBanner />);

    const button = screen.getByRole("button", { name: /atualizar cartão/i });
    await user.click(button);

    expect(screen.getByText("Abrindo...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Atualizar Cartão")).toBeInTheDocument();
    });
  });

  // role=alert for accessibility
  it("banner has role=alert for accessibility", () => {
    mockUsePlan.mockReturnValue(PAST_DUE_PLAN);
    mockUseAuth.mockReturnValue(AUTH_SESSION);

    render(<PaymentFailedBanner />);
    const banner = screen.getByRole("alert");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveAttribute("aria-live", "assertive");
  });
});
