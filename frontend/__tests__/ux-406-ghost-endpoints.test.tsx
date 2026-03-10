/**
 * UX-406 — Remove 404 calls to dashboard (ghost endpoints)
 *
 * AC1: Org fetches gated by NEXT_PUBLIC_ORGS_ENABLED (default: false)
 * AC2: When flag disabled, no fetch to /api/organizations/* and no team toggle
 * AC3: No console error 404 on dashboard when flag disabled
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

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
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));

jest.mock("../app/components/BackendStatusIndicator", () => ({
  useBackendStatusContext: () => ({
    status: "online",
    isPolling: false,
    checkHealth: jest.fn(),
  }),
  BackendStatusProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useBackendStatus: () => ({
    status: "online",
    isPolling: false,
    checkHealth: jest.fn(),
  }),
  __esModule: true,
  default: () => null,
}));

jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
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

// ─── Lazy import (after mocks) ─────────────────────────────────────────────

import DashboardPage from "../app/dashboard/page";

// ─── Test Data ──────────────────────────────────────────────────────────────

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
  ],
};

const mockDimensions = {
  top_ufs: [{ name: "SP", count: 15, value: 20_000_000 }],
  top_sectors: [{ name: "Vestuário", count: 20, value: 15_000_000 }],
};

function mockFetchSuccess() {
  (global.fetch as jest.Mock).mockImplementation((url: string) => {
    if (url.includes("summary"))
      return Promise.resolve({ ok: true, json: async () => mockSummary });
    if (url.includes("searches-over-time"))
      return Promise.resolve({ ok: true, json: async () => mockTimeSeries });
    if (url.includes("top-dimensions"))
      return Promise.resolve({ ok: true, json: async () => mockDimensions });
    // profile-completeness and any other endpoint
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

// ─── Setup ──────────────────────────────────────────────────────────────────

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

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("UX-406: Ghost endpoint removal", () => {
  // Note: NEXT_PUBLIC_ORGS_ENABLED is undefined in test env → evaluates to false

  it("AC1/AC2: does NOT fetch /api/organizations/me when flag disabled", async () => {
    render(<DashboardPage />);

    // Wait for dashboard to fully load
    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
    });

    const calls = (global.fetch as jest.Mock).mock.calls.map(([url]: [string]) => url);
    const orgCalls = calls.filter((url: string) => url.includes("/api/organizations"));
    expect(orgCalls).toHaveLength(0);
  });

  it("AC2: team/personal toggle is NOT rendered when flag disabled", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("42")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("team-toggle")).not.toBeInTheDocument();
    expect(screen.queryByTestId("toggle-personal")).not.toBeInTheDocument();
    expect(screen.queryByTestId("toggle-team")).not.toBeInTheDocument();
  });

  it("AC3: dashboard works normally without regression when flag disabled", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      // Stat cards render
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("1.523")).toBeInTheDocument();
      expect(screen.getByText("90%")).toBeInTheDocument();

      // Charts render
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
      expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
      expect(screen.getByTestId("bar-chart")).toBeInTheDocument();

      // Quick links render
      expect(screen.getByRole("link", { name: /Nova Busca/i })).toHaveAttribute("href", "/buscar");
    });

    // Analytics tracked
    expect(mockTrackEvent).toHaveBeenCalledWith("dashboard_viewed", { period: "week" });
  });
});
