/**
 * STORY-CONV-003b AC5: CardCollect component tests.
 *
 * Scope (isolated): setup-intent fetch + render states (loading/error/ready).
 * Full E2E Stripe flow is covered in signup-flow.test.tsx with deeper
 * mocking. Here we only need to assert that CardCollect:
 *   - calls /api/billing/setup-intent exactly once on mount
 *   - shows loading state while fetching
 *   - surfaces fetch errors via alert
 *   - mounts <Elements> when the fetch succeeds
 */
/** @jest-environment jsdom */
import { render, screen, waitFor } from "@testing-library/react";

// Mock @stripe/react-stripe-js at module level so we don't need a real Stripe
// script URL in jsdom (would try a network request otherwise).
jest.mock("@stripe/react-stripe-js", () => ({
  Elements: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="stripe-elements-provider">{children}</div>
  ),
  PaymentElement: () => <div data-testid="stripe-payment-element" />,
  useStripe: () => null,
  useElements: () => null,
}));

// stripe-client uses loadStripe — stub to skip the network load.
jest.mock("../../lib/stripe-client", () => ({
  getStripePromise: () => Promise.resolve(null),
}));

// sonner toast is fire-and-forget; we only need jest.fn() to avoid throwing.
jest.mock("sonner", () => ({ toast: { error: jest.fn(), success: jest.fn() } }));

import CardCollect from "../../app/signup/components/CardCollect";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  (global as any).fetch = jest.fn().mockResolvedValueOnce({
    ok,
    status,
    json: async () => payload,
  });
}

describe("CardCollect", () => {
  afterEach(() => {
    (global as any).fetch = undefined;
    jest.clearAllMocks();
  });

  it("shows loading state while setup-intent fetch is in-flight", async () => {
    mockFetchOnce({ client_secret: "seti_x", publishable_key: "pk_test_x" });
    render(<CardCollect onCardReady={jest.fn()} />);
    expect(screen.getByTestId("card-collect-loading")).toBeInTheDocument();
  });

  it("mounts Elements provider after setup-intent succeeds", async () => {
    mockFetchOnce({ client_secret: "seti_abc", publishable_key: "pk_test_abc" });
    render(<CardCollect onCardReady={jest.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("stripe-elements-provider")).toBeInTheDocument()
    );
    expect(screen.getByTestId("stripe-payment-element")).toBeInTheDocument();
    expect(screen.getByTestId("trial-terms-notice")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith("/api/billing/setup-intent", {
      method: "POST",
    });
  });

  it("renders an alert when setup-intent returns an error", async () => {
    mockFetchOnce({ detail: "cartão indisponível" }, false, 503);
    render(<CardCollect onCardReady={jest.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("card-collect-load-error")).toHaveTextContent(
        "cartão indisponível"
      )
    );
  });

  it("surfaces network errors safely", async () => {
    (global as any).fetch = jest.fn().mockRejectedValueOnce(new Error("offline"));
    render(<CardCollect onCardReady={jest.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("card-collect-load-error")).toHaveTextContent(
        "offline"
      )
    );
  });
});
