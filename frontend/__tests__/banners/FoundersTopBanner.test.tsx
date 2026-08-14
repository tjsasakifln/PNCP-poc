/**
 * Issue #787: FoundersTopBanner component tests
 * Tests visibility/hide logic for the global founders top banner.
 */

import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FoundersTopBanner } from "../../components/banners/FoundersTopBanner";

// Mock useUser context
const mockUseUser = jest.fn();
jest.mock("../../contexts/UserContext", () => ({
  useUser: () => mockUseUser(),
}));

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Deadlines must be relative to "now": a fixed 2026-06-30 expired on 2026-08-13
// and hid the banner in every "renders when available" case.
const FUTURE_DEADLINE = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString();
const PAST_DEADLINE = "2026-06-30T23:59:59Z";

// Founding availability response helpers
const AVAILABLE = {
  available: true,
  seats_remaining: 10,
  deadline_at: FUTURE_DEADLINE,
};

const NOT_AVAILABLE = {
  available: false,
  seats_remaining: 0,
  deadline_at: FUTURE_DEADLINE,
};

const SOLD_OUT = {
  available: true,
  seats_remaining: 0,
  deadline_at: FUTURE_DEADLINE,
};

const EXPIRED = {
  available: true,
  seats_remaining: 10,
  deadline_at: PAST_DEADLINE,
};

// User context states
const TRIAL_USER = {
  planInfo: {
    plan_id: "free_trial",
    plan_name: "Free Trial",
    subscription_status: "trial",
    trial_expires_at: "2026-05-21T00:00:00Z",
    capabilities: {},
    quota_used: 0,
    quota_remaining: 10,
    quota_reset_date: "",
    dunning_phase: "healthy",
    days_since_failure: null,
    subscription_end_date: null,
    user_id: "user-123",
    email: "test@example.com",
  },
  planLoading: false,
};

const ACTIVE_PAYING_USER = {
  planInfo: {
    plan_id: "smartlic_pro",
    plan_name: "SmartLic Pro",
    subscription_status: "active",
    trial_expires_at: null, // active subscriber, not trial
    capabilities: {},
    quota_used: 50,
    quota_remaining: 950,
    quota_reset_date: "",
    dunning_phase: "healthy",
    days_since_failure: null,
    subscription_end_date: "2027-05-07T00:00:00Z",
    user_id: "user-456",
    email: "pro@example.com",
  },
  planLoading: false,
};

const LOADING_USER = {
  planInfo: null,
  planLoading: true,
};

function mockFetchAvailability(data: object) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => data,
  });
}

describe("FoundersTopBanner", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    // Default: trial user
    mockUseUser.mockReturnValue(TRIAL_USER);
  });

  it("is sunset and does not recruit seats (#2111)", () => {
    const { container } = render(<FoundersTopBanner />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe.skip("FoundersTopBanner legado (sunset)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    mockUseUser.mockReturnValue(TRIAL_USER);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe("renders when available", () => {
    it("shows the banner when available=true and user is not paying subscriber", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(AVAILABLE);

      render(<FoundersTopBanner />);

      await waitFor(() => {
        expect(screen.getByTestId("founders-top-banner")).toBeInTheDocument();
      });
      expect(
        screen.getByText(/Plano Fundadores: acesso vitalício por R\$997/)
      ).toBeInTheDocument();
    });

    it("shows the CTA link pointing to /fundadores", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(AVAILABLE);

      render(<FoundersTopBanner />);

      await waitFor(() => {
        expect(screen.getByRole("link", { name: /saiba mais/i })).toBeInTheDocument();
      });
      expect(screen.getByRole("link", { name: /saiba mais/i })).toHaveAttribute(
        "href",
        "/fundadores"
      );
    });

    it("shows dismiss button with correct aria-label", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(AVAILABLE);

      render(<FoundersTopBanner />);

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Fechar banner Fundadores" })
        ).toBeInTheDocument();
      });
    });
  });

  describe("hidden when seats_remaining=0", () => {
    it("does not render when seats_remaining is 0", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(SOLD_OUT);

      const { container } = render(<FoundersTopBanner />);

      // Wait a tick for async fetch
      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(container.firstChild).toBeNull();
    });
  });

  describe("hidden when deadline has passed", () => {
    it("does not render when deadline_at is in the past", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(EXPIRED);

      const { container } = render(<FoundersTopBanner />);

      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(container.firstChild).toBeNull();
    });
  });

  describe("hidden when available=false", () => {
    it("does not render when available is false", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(NOT_AVAILABLE);

      const { container } = render(<FoundersTopBanner />);

      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(container.firstChild).toBeNull();
    });
  });

  describe("hidden when user is active paying subscriber", () => {
    it("does not render for active subscriber with no trial_expires_at", async () => {
      mockUseUser.mockReturnValue(ACTIVE_PAYING_USER);
      // Should not even fetch availability
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => AVAILABLE });

      const { container } = render(<FoundersTopBanner />);

      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(container.firstChild).toBeNull();
    });
  });

  describe("dismiss button hides banner and sets localStorage", () => {
    it("hides the banner when dismiss button is clicked", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(AVAILABLE);

      const user = userEvent.setup();
      render(<FoundersTopBanner />);

      await waitFor(() => {
        expect(screen.getByTestId("founders-top-banner")).toBeInTheDocument();
      });

      const dismissBtn = screen.getByRole("button", {
        name: "Fechar banner Fundadores",
      });
      await user.click(dismissBtn);

      await waitFor(() => {
        expect(screen.queryByTestId("founders-top-banner")).not.toBeInTheDocument();
      });
    });

    it("sets localStorage key on dismiss", async () => {
      mockUseUser.mockReturnValue(TRIAL_USER);
      mockFetchAvailability(AVAILABLE);

      const user = userEvent.setup();
      render(<FoundersTopBanner />);

      await waitFor(() => {
        expect(screen.getByTestId("founders-top-banner")).toBeInTheDocument();
      });

      await user.click(screen.getByRole("button", { name: "Fechar banner Fundadores" }));

      const stored = localStorage.getItem("founders_banner_dismissed");
      expect(stored).not.toBeNull();
      const ts = parseInt(stored!, 10);
      expect(ts).toBeGreaterThan(Date.now() - 5000); // within last 5s
    });

    it("does not render when localStorage dismiss key is fresh (< 7 days)", async () => {
      // Pre-set a fresh dismiss timestamp
      localStorage.setItem("founders_banner_dismissed", String(Date.now() - 1000));
      mockUseUser.mockReturnValue(TRIAL_USER);

      const { container } = render(<FoundersTopBanner />);

      // Should stay hidden — no fetch should be needed
      await act(async () => {
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(container.firstChild).toBeNull();
    });
  });
});
