/**
 * DashboardPage Tests — UX-338
 *
 * Covers: loading timeout (AC5), empty state (AC2), error retry (AC4),
 * data rendering (AC1/AC3), no silent errors (AC6)
 */

import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks (plain functions — immune to resetMocks: true) ───────────────

const mockTrackEvent = jest.fn();

let mockAuthState = {
  user: { id: "user-1", email: "test@test.com" } as any,
  session: { access_token: "mock-token" } as any,
  loading: false,
};

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockAuthState,
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return <a href={href}>{children}</a>;
  };
});

jest.mock("../components/PageHeader", () => ({
  PageHeader: ({ title, extraControls }: any) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      {extraControls}
    </div>
  ),
}));

jest.mock("recharts", () => ({
  BarChart: ({ children }: any) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  LineChart: ({ children }: any) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: any) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

// ─── Lazy import (after mocks) ──────────────────────────────────────────

import DashboardPage from "../app/dashboard/page";

// ─── Test Data ──────────────────────────────────────────────────────────

const mockSummary = {
  total_searches: 42,
  total_downloads: 38,
  total_opportunities: 1523,
  total_value_discovered: 45_000_000,
  estimated_hours_saved: 84,
  avg_results_per_search: 36,
  success_rate: 90,
  member_since: "2025-01-15T00:00:00Z",
};

const mockTimeSeries = {
  data: [
    { label: "01/02", searches: 5, opportunities: 120, value: 5_000_000 },
    { label: "02/02", searches: 8, opportunities: 180, value: 7_500_000 },
  ],
};

const mockDimensions = {
  top_ufs: [
    { name: "SP", count: 15, value: 20_000_000 },
    { name: "RJ", count: 10, value: 12_000_000 },
  ],
  top_sectors: [
    { name: "Vestuário", count: 20, value: 15_000_000 },
    { name: "Facilities", count: 12, value: 10_000_000 },
  ],
};

function mockFetchSuccess() {
  (global.fetch as jest.Mock).mockImplementation((url: string) => {
    if (url.includes("summary"))
      return Promise.resolve({ ok: true, json: async () => mockSummary });
    if (url.includes("searches-over-time"))
      return Promise.resolve({ ok: true, json: async () => mockTimeSeries });
    if (url.includes("top-dimensions"))
      return Promise.resolve({ ok: true, json: async () => mockDimensions });
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

// ─── Setup ──────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn();
  mockAuthState = {
    user: { id: "user-1", email: "test@test.com" },
    session: { access_token: "mock-token" },
    loading: false,
  };
  mockFetchSuccess();
});

// ─── Tests ──────────────────────────────────────────────────────────────

describe("DashboardPage — UX-338", () => {
  describe("AC1: Dashboard loads content", () => {
    it("should render stat cards after data loads", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
        expect(screen.getByText("1.523")).toBeInTheDocument();
        expect(screen.getByText("84h")).toBeInTheDocument();
        expect(screen.getByText("90%")).toBeInTheDocument();
      });
    });

    it("should always use proxy URL, never direct backend", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
      });

      const calls = (global.fetch as jest.Mock).mock.calls;
      for (const [url] of calls) {
        expect(url).toMatch(/^\/api\/analytics\?/);
        expect(url).not.toContain("v1/analytics");
      }
    });
  });

  describe("AC2: Empty state educativo", () => {
    it('should show "Seu painel de inteligência" when no searches', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes("summary"))
          return Promise.resolve({
            ok: true,
            json: async () => ({ ...mockSummary, total_searches: 0 }),
          });
        if (url.includes("searches-over-time"))
          return Promise.resolve({ ok: true, json: async () => ({ data: [] }) });
        if (url.includes("top-dimensions"))
          return Promise.resolve({ ok: true, json: async () => ({ top_ufs: [], top_sectors: [] }) });
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<DashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Seu painel de inteligência")
        ).toBeInTheDocument();
        expect(
          screen.getByText(
            /resumos das suas buscas, tendências e oportunidades/i
          )
        ).toBeInTheDocument();
      });
    });

    it('should have CTA "Fazer primeira busca" linking to /buscar', async () => {
      (global.fetch as jest.Mock).mockImplementation((url: string) => {
        if (url.includes("summary"))
          return Promise.resolve({
            ok: true,
            json: async () => ({ ...mockSummary, total_searches: 0 }),
          });
        if (url.includes("searches-over-time"))
          return Promise.resolve({ ok: true, json: async () => ({ data: [] }) });
        if (url.includes("top-dimensions"))
          return Promise.resolve({ ok: true, json: async () => ({ top_ufs: [], top_sectors: [] }) });
      });

      render(<DashboardPage />);

      await waitFor(() => {
        const link = screen.getByRole("link", {
          name: /Fazer primeira busca/i,
        });
        expect(link).toHaveAttribute("href", "/buscar");
      });
    });
  });

  describe("AC3: Real metrics when data exists", () => {
    it("should display currency formatted total value", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/R\$ 45.*M/)).toBeInTheDocument();
      });
    });

    it("should render charts", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("line-chart")).toBeInTheDocument();
        expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });
    });

    it("should track dashboard_viewed event", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith("dashboard_viewed", {
          period: "week",
        });
      });
    });
  });

  describe("AC4: Error state with retry", () => {
    it("should show error message on fetch failure", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Network error")
      );

      render(<DashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Não foi possível carregar o painel")
        ).toBeInTheDocument();
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("should retry data fetch on button click (not page reload)", async () => {
      // All 3 fetches fail
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Network error")
      );

      render(<DashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByText("Não foi possível carregar o painel")
        ).toBeInTheDocument();
      });

      // Now set fetch to succeed for retry
      mockFetchSuccess();
      const retryButton = screen.getByRole("button", {
        name: /Tentar novamente/i,
      });
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
      });
    });
  });

  describe("AC5: Loading timeout after 10s", () => {
    it("should show skeletons while loading", () => {
      // fetch never resolves
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      render(<DashboardPage />);

      const pulses = document.querySelectorAll(".animate-pulse");
      expect(pulses.length).toBeGreaterThan(0);
    });

    it("should show timeout error after 10s of loading", async () => {
      jest.useFakeTimers();

      // Make fetch respect AbortController signal
      (global.fetch as jest.Mock).mockImplementation(
        (_url: string, options?: { signal?: AbortSignal }) => {
          return new Promise((_resolve, reject) => {
            if (options?.signal) {
              options.signal.addEventListener("abort", () => {
                reject(
                  new DOMException("The operation was aborted.", "AbortError")
                );
              });
            }
          });
        }
      );

      render(<DashboardPage />);

      // Verify loading skeletons appear
      expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);

      // Advance past the 10s timeout
      act(() => {
        jest.advanceTimersByTime(11_000);
      });

      await waitFor(() => {
        expect(
          screen.getByText(/demorou demais para carregar/i)
        ).toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  describe("AC6: No silent console errors", () => {
    it("should log error to console on fetch failure", async () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();
      (global.fetch as jest.Mock).mockRejectedValue(
        new Error("Test error")
      );

      render(<DashboardPage />);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          "[Dashboard] Fetch error:",
          "Test error"
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe("Auth guard", () => {
    it("should show login prompt when not authenticated", () => {
      mockAuthState = { user: null, session: null, loading: false } as any;

      render(<DashboardPage />);

      expect(
        screen.getByText(/Faça login para acessar o dashboard/i)
      ).toBeInTheDocument();
    });

    it("should show loading when auth is loading", () => {
      mockAuthState = { user: null, session: null, loading: true } as any;

      render(<DashboardPage />);

      expect(screen.getByText(/Carregando/i)).toBeInTheDocument();
    });
  });

  describe("Quick links", () => {
    it("should display quick access links", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByRole("link", { name: /Nova Busca/i })
        ).toHaveAttribute("href", "/buscar");
        expect(
          screen.getByRole("link", { name: /Histórico/i })
        ).toHaveAttribute("href", "/historico");
        expect(
          screen.getByRole("link", { name: /Minha Conta/i })
        ).toHaveAttribute("href", "/conta");
      });
    });
  });
});
