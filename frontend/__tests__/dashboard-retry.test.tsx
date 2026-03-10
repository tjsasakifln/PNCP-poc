/**
 * CRIT-018: Dashboard Retry Storm Tests
 *
 * AC11: After 5 fetch failures, component stops making requests
 * AC12: Unmount cancels all pending timers
 * AC13: Manual retry works after auto-retry exhaustion
 * AC14: Backoff intervals are respected (2s, 4s, 8s, 16s, 30s)
 * AC16: Navigate dashboard → pipeline → dashboard doesn't duplicate retry loops
 */

import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks (plain functions — immune to resetMocks: true) ───────────────

const mockTrackEvent = jest.fn();

let mockAuthState = {
  user: { id: "user-1", email: "test@test.com" } as any,
  session: { access_token: "mock-token" } as any,
  loading: false,
};

let mockBackendStatus: "online" | "offline" | "recovering" = "online";

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockAuthState,
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
  }),
}));

jest.mock("../app/components/BackendStatusIndicator", () => ({
  useBackendStatusContext: () => ({
    status: mockBackendStatus,
    isPolling: false,
    checkHealth: jest.fn(),
  }),
  BackendStatusProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useBackendStatus: () => ({
    status: mockBackendStatus,
    isPolling: false,
    checkHealth: jest.fn(),
  }),
  __esModule: true,
  default: () => null,
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

// Mock usePlan to prevent SWR /api/me fetch calls interfering with retry count assertions
jest.mock("../hooks/usePlan", () => ({
  usePlan: () => ({
    planInfo: { plan_id: "smartlic_pro", plan_name: "SmartLic Pro", capabilities: {} },
    loading: false,
    error: null,
    isFromCache: false,
    cachedAt: null,
    refresh: jest.fn(),
  }),
}));

jest.mock("recharts", () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

// ─── Lazy imports (after mocks) ──────────────────────────────────────────

import DashboardPage from "../app/dashboard/page";
import {
  useFetchWithBackoff,
  BACKOFF_DEFAULTS,
  type FetchWithBackoffOptions,
} from "../hooks/useFetchWithBackoff";

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
  jest.useRealTimers();
  global.fetch = jest.fn();
  mockAuthState = {
    user: { id: "user-1", email: "test@test.com" },
    session: { access_token: "mock-token" },
    loading: false,
  };
  mockBackendStatus = "online";
  mockFetchSuccess();
});

// ─── Tests ──────────────────────────────────────────────────────────────

describe("CRIT-018: Dashboard Retry Storm", () => {

  // ─────────────────────────────────────────────────────────────────────
  // AC11: After 3 failures (CRIT-031), component stops making requests
  // ─────────────────────────────────────────────────────────────────────
  describe("AC11: Stops after 3 failures", () => {
    it("should show final error state after 3 failed attempts", async () => {
      jest.useFakeTimers();
      (global.fetch as jest.Mock).mockRejectedValue(new Error("Server down"));

      render(<DashboardPage />);

      // Advance through 3 retries (CRIT-031: reduced from 5 to 3)
      for (let i = 0; i < 4; i++) {
        await act(async () => {
          jest.advanceTimersByTime(i === 0 ? 100 : 10_000);
          await Promise.resolve();
          await Promise.resolve();
        });
      }

      await waitFor(() => {
        expect(screen.getByTestId("dashboard-empty-state")).toBeInTheDocument();
        expect(screen.getByText("Dados temporariamente indisponíveis")).toBeInTheDocument();
        expect(screen.getByText(/Tente novamente em alguns minutos/)).toBeInTheDocument();
      });

      // Count total fetch calls
      const fetchCalls = (global.fetch as jest.Mock).mock.calls.length;

      // Advance more time — no new requests should happen
      await act(async () => {
        jest.advanceTimersByTime(60_000);
        await Promise.resolve();
      });

      expect((global.fetch as jest.Mock).mock.calls.length).toBe(fetchCalls);

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC12: Unmount cancels all pending timers
  // ─────────────────────────────────────────────────────────────────────
  describe("AC12: Unmount cleanup", () => {
    it("should cancel pending retries when component unmounts", async () => {
      jest.useFakeTimers();
      (global.fetch as jest.Mock).mockRejectedValue(new Error("Server down"));

      const { unmount } = render(<DashboardPage />);

      // Wait for first failure
      await act(async () => {
        jest.advanceTimersByTime(100);
        await Promise.resolve();
        await Promise.resolve();
      });

      const callsBefore = (global.fetch as jest.Mock).mock.calls.length;

      // Unmount while retry is scheduled
      unmount();

      // Advance past all potential backoff timers
      await act(async () => {
        jest.advanceTimersByTime(120_000);
        await Promise.resolve();
      });

      // No new fetch calls should have been made after unmount
      expect((global.fetch as jest.Mock).mock.calls.length).toBe(callsBefore);

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC13: Manual retry works after auto-retry exhaustion
  // ─────────────────────────────────────────────────────────────────────
  describe("AC13: Manual retry after exhaustion", () => {
    it("should allow manual retry after 3 automatic failures", async () => {
      jest.useFakeTimers();
      (global.fetch as jest.Mock).mockRejectedValue(new Error("Server down"));

      render(<DashboardPage />);

      // Exhaust all retries (CRIT-031: 3 retries)
      for (let i = 0; i < 4; i++) {
        await act(async () => {
          jest.advanceTimersByTime(i === 0 ? 100 : 30_000);
          await Promise.resolve();
          await Promise.resolve();
        });
      }

      await waitFor(() => {
        expect(screen.getByTestId("dashboard-empty-state")).toBeInTheDocument();
      });

      // Now mock success
      mockFetchSuccess();

      // Click manual retry
      fireEvent.click(screen.getByTestId("dashboard-retry-button"));

      await act(async () => {
        jest.advanceTimersByTime(100);
        await Promise.resolve();
        await Promise.resolve();
      });

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC14: Backoff intervals are respected (2s, 4s, 8s, 16s, 30s)
  // ─────────────────────────────────────────────────────────────────────
  describe("AC14: Backoff intervals", () => {
    it("should respect exponential backoff delays (2s, 4s, 8s, 16s)", async () => {
      jest.useFakeTimers();

      const fetchFn = jest.fn().mockRejectedValue(new Error("fail"));

      const { result } = renderHook(() =>
        useFetchWithBackoff(fetchFn, {
          enabled: true,
          maxRetries: 5,
          initialDelayMs: 2000,
          maxDelayMs: 30000,
          backoffMultiplier: 2,
          timeoutMs: 60000, // high timeout so it doesn't interfere
        })
      );

      // Initial fetch (attempt 0)
      await act(async () => {
        jest.advanceTimersByTime(0);
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(1);

      // After 1.9s — retry should NOT have happened yet
      await act(async () => {
        jest.advanceTimersByTime(1900);
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(1);

      // After 2s — first retry (attempt 1)
      await act(async () => {
        jest.advanceTimersByTime(200);
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(2);

      // After 3.9s — NOT yet (need 4s)
      await act(async () => {
        jest.advanceTimersByTime(3900);
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(2);

      // After 4s — second retry (attempt 2)
      await act(async () => {
        jest.advanceTimersByTime(200);
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(3);

      // After 7.9s — NOT yet (need 8s)
      await act(async () => {
        jest.advanceTimersByTime(7900);
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(3);

      // After 8s — third retry (attempt 3)
      await act(async () => {
        jest.advanceTimersByTime(200);
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(4);

      // After 16s — fourth retry (attempt 4)
      await act(async () => {
        jest.advanceTimersByTime(16100);
        await Promise.resolve();
        await Promise.resolve();
      });
      expect(fetchFn).toHaveBeenCalledTimes(5);

      // No more — exhausted
      expect(result.current.hasExhaustedRetries).toBe(true);

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC5/AC6: Backend status integration
  // ─────────────────────────────────────────────────────────────────────
  describe("AC5/AC6: Backend status integration", () => {
    it("should NOT make requests when backend is offline", async () => {
      mockBackendStatus = "offline";

      render(<DashboardPage />);

      // Wait a bit
      await act(async () => {
        await new Promise((r) => setTimeout(r, 100));
      });

      // No analytics fetch calls (only health calls don't count)
      const analyticsCalls = (global.fetch as jest.Mock).mock.calls.filter(
        ([url]: [string]) => url.includes("/api/analytics")
      );
      expect(analyticsCalls.length).toBe(0);
    });

    it("should fetch when backend recovers (online)", async () => {
      mockBackendStatus = "online";

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
      });
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC16: No duplicate retry loops on remount
  // ─────────────────────────────────────────────────────────────────────
  describe("AC16: No duplicates on remount", () => {
    it("should not duplicate loops after unmount + remount", async () => {
      jest.useFakeTimers();
      (global.fetch as jest.Mock).mockRejectedValue(new Error("fail"));

      // Mount
      const { unmount } = render(<DashboardPage />);

      await act(async () => {
        jest.advanceTimersByTime(100);
        await Promise.resolve();
        await Promise.resolve();
      });

      // Unmount (simulates navigating away)
      unmount();

      await act(async () => {
        jest.advanceTimersByTime(5000);
        await Promise.resolve();
      });

      const callsAfterUnmount = (global.fetch as jest.Mock).mock.calls.length;

      // Advance more time — should stay same
      await act(async () => {
        jest.advanceTimersByTime(30_000);
        await Promise.resolve();
      });

      expect((global.fetch as jest.Mock).mock.calls.length).toBe(callsAfterUnmount);

      // Remount (simulates navigating back)
      mockFetchSuccess();
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC8: Error state visual
  // ─────────────────────────────────────────────────────────────────────
  describe("AC8: Error state visual", () => {
    it("should show cloud icon, correct messages, and Tentar novamente button", async () => {
      jest.useFakeTimers();
      (global.fetch as jest.Mock).mockRejectedValue(new Error("fail"));

      render(<DashboardPage />);

      // Exhaust all retries (CRIT-031: 3 retries)
      for (let i = 0; i < 4; i++) {
        await act(async () => {
          jest.advanceTimersByTime(i === 0 ? 100 : 30_000);
          await Promise.resolve();
          await Promise.resolve();
        });
      }

      await waitFor(() => {
        const errorState = screen.getByTestId("dashboard-empty-state");
        expect(errorState).toBeInTheDocument();

        // Cloud icon (SVG with path)
        const svg = errorState.querySelector("svg");
        expect(svg).toBeTruthy();

        // Correct messages (CRIT-031 AC2)
        expect(screen.getByText("Dados temporariamente indisponíveis")).toBeInTheDocument();
        expect(screen.getByText(/Tente novamente em alguns minutos/)).toBeInTheDocument();

        // "Tentar novamente" button (CRIT-031 AC3)
        expect(screen.getByText("Tentar novamente")).toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // AC9/AC10: Skeletons don't persist indefinitely
  // ─────────────────────────────────────────────────────────────────────
  describe("AC9/AC10: Skeleton timeout", () => {
    it("should show skeletons initially, then transition to error state after timeout", async () => {
      jest.useFakeTimers();

      // Fetch that takes forever (until abort)
      (global.fetch as jest.Mock).mockImplementation(
        (_url: string, options?: { signal?: AbortSignal }) => {
          return new Promise((_resolve, reject) => {
            if (options?.signal) {
              options.signal.addEventListener("abort", () => {
                reject(new DOMException("The operation was aborted.", "AbortError"));
              });
            }
          });
        }
      );

      render(<DashboardPage />);

      // Should show skeletons initially
      expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);

      // After timeout (10s), fetch aborts → allSettled resolves with all errors → empty state
      await act(async () => {
        jest.advanceTimersByTime(11_000);
        await Promise.resolve();
        await Promise.resolve();
        await Promise.resolve();
        await Promise.resolve();
      });

      await waitFor(() => {
        // With allSettled, all sections fail after timeout → dashboard-empty-state
        expect(screen.getByTestId("dashboard-empty-state")).toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  // ─────────────────────────────────────────────────────────────────────
  // Existing dashboard functionality still works
  // ─────────────────────────────────────────────────────────────────────
  describe("Backward compatibility", () => {
    it("should render dashboard data correctly on success", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
        expect(screen.getByText("1.523")).toBeInTheDocument();
        expect(screen.getByText("84h")).toBeInTheDocument();
        expect(screen.getByText("90%")).toBeInTheDocument();
      });
    });

    it("should show empty state when no searches", async () => {
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
        expect(screen.getByText("Seu Painel de Inteligência")).toBeInTheDocument();
      });
    });
  });
});

// ─── useFetchWithBackoff hook unit tests ────────────────────────────────

describe("useFetchWithBackoff hook", () => {
  it("should return data on successful fetch", async () => {
    const fetchFn = jest.fn().mockResolvedValue({ value: 42 });

    const { result } = renderHook(() =>
      useFetchWithBackoff(fetchFn, { enabled: true, timeoutMs: 5000 })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual({ value: 42 });
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  it("should not fetch when enabled is false", async () => {
    const fetchFn = jest.fn().mockResolvedValue({ value: 42 });

    const { result } = renderHook(() =>
      useFetchWithBackoff(fetchFn, { enabled: false })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });

    expect(fetchFn).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it("should cap backoff at maxDelayMs", async () => {
    jest.useFakeTimers();

    const fetchFn = jest.fn().mockRejectedValue(new Error("fail"));

    renderHook(() =>
      useFetchWithBackoff(fetchFn, {
        enabled: true,
        maxRetries: 10,
        initialDelayMs: 10000,
        maxDelayMs: 30000,
        backoffMultiplier: 2,
        timeoutMs: 60000,
      })
    );

    // Attempt 0
    await act(async () => {
      jest.advanceTimersByTime(0);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(1);

    // Delay: min(10000*2^0, 30000) = 10000ms
    await act(async () => {
      jest.advanceTimersByTime(10100);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(2);

    // Delay: min(10000*2^1, 30000) = 20000ms
    await act(async () => {
      jest.advanceTimersByTime(20100);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(3);

    // Delay: min(10000*2^2, 30000) = 30000ms (capped)
    await act(async () => {
      jest.advanceTimersByTime(30100);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(fetchFn).toHaveBeenCalledTimes(4);

    jest.useRealTimers();
  });

  it("should reset retries on manual retry", async () => {
    jest.useFakeTimers();
    const fetchFn = jest.fn().mockRejectedValue(new Error("fail"));

    const { result } = renderHook(() =>
      useFetchWithBackoff(fetchFn, {
        enabled: true,
        maxRetries: 2,
        initialDelayMs: 100,
        timeoutMs: 60000,
      })
    );

    // Exhaust retries
    for (let i = 0; i < 3; i++) {
      await act(async () => {
        jest.advanceTimersByTime(i === 0 ? 10 : 500);
        await Promise.resolve();
        await Promise.resolve();
      });
    }

    expect(result.current.hasExhaustedRetries).toBe(true);
    const callsBefore = fetchFn.mock.calls.length;

    // Manual retry
    fetchFn.mockResolvedValueOnce({ ok: true });
    act(() => {
      result.current.manualRetry();
    });

    await act(async () => {
      jest.advanceTimersByTime(10);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(fetchFn.mock.calls.length).toBeGreaterThan(callsBefore);
    expect(result.current.hasExhaustedRetries).toBe(false);

    jest.useRealTimers();
  });
});
