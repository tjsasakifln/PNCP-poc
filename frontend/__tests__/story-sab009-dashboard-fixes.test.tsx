/**
 * SAB-009 — Dashboard: erro 500 em /api/organizations/me + badge "0%" sem contexto
 *
 * AC1-AC4: Organizations 500 error (resolved by STORY-331, verified here)
 * AC5-AC7: Badge "0%" tooltip on ProfileProgressBar
 * AC8-AC9: "Horas Economizadas" tooltip on StatCard
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── ProfileProgressBar Tooltip Tests (AC5-AC7) ──────────────────────────────

import ProfileProgressBar from "../components/ProfileProgressBar";

describe("ProfileProgressBar Tooltip (SAB-009 AC5-AC7)", () => {
  it("AC6: shows tooltip with 'Perfil de Licitante' for incomplete profile (button mode)", () => {
    const onClickNext = jest.fn();
    render(<ProfileProgressBar percentage={0} onClickNext={onClickNext} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute(
      "title",
      "Perfil de Licitante: 0% — Preencha para melhorar análises"
    );
  });

  it("AC6: tooltip includes dynamic percentage value", () => {
    const onClickNext = jest.fn();
    render(<ProfileProgressBar percentage={42} onClickNext={onClickNext} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute(
      "title",
      "Perfil de Licitante: 42% — Preencha para melhorar análises"
    );
  });

  it("AC6: shows 'completo' tooltip when profile is 100% (progressbar mode)", () => {
    render(<ProfileProgressBar percentage={100} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute(
      "title",
      "Perfil de Licitante: 100% completo"
    );
  });

  it("AC6: tooltip present on div (no onClickNext) mode", () => {
    render(<ProfileProgressBar percentage={25} />);

    const bar = screen.getByTestId("profile-progress-bar");
    expect(bar).toHaveAttribute("title", expect.stringContaining("Perfil de Licitante"));
  });
});

// ─── Dashboard StatCard Tooltip Tests (AC8-AC9) ──────────────────────────────

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

jest.mock("../components/BackendStatusIndicator", () => ({
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

import DashboardPage from "../app/dashboard/page";

const mockSummary = {
  total_searches: 32,
  total_downloads: 11,
  total_opportunities: 1826,
  total_value_discovered: 3_495_100_000,
  estimated_hours_saved: 64,
  avg_results_per_search: 57,
  success_rate: 34.4,
  member_since: "2026-02-02T00:00:00Z",
};

const mockTimeSeries = {
  data: [
    { label: "16 Feb", searches: 5, opportunities: 120, value: 5_000_000 },
    { label: "23 Feb", searches: 8, opportunities: 1800, value: 7_500_000 },
  ],
};

const mockDimensions = {
  top_ufs: [
    { name: "SP", count: 32, value: 3_495_100_000 },
    { name: "ES", count: 27, value: 3_224_700_000 },
  ],
  top_sectors: [
    { name: "vestuario", count: 16, value: 15_000_000 },
    { name: "engenharia", count: 8, value: 10_000_000 },
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

describe("Dashboard Horas Economizadas Tooltip (SAB-009 AC8-AC9)", () => {
  it("AC9: 'Horas economizadas' card has a tooltip explaining the methodology", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("64h")).toBeInTheDocument();
    });

    // Find the stat card containing "Horas economizadas"
    const label = screen.getByText("Horas economizadas");
    const card = label.closest("[title]");
    expect(card).not.toBeNull();
    expect(card!.getAttribute("title")).toMatch(
      /32 análises × 2h por análise manual/
    );
  });

  it("AC8: tooltip documents the calculation formula (searches × 2h)", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("64h")).toBeInTheDocument();
    });

    const label = screen.getByText("Horas economizadas");
    const card = label.closest("[title]");
    expect(card).not.toBeNull();
    expect(card!.getAttribute("title")).toContain("Estimativa");
    expect(card!.getAttribute("title")).toContain("2h por análise manual");
  });
});

describe("Dashboard Organizations Call (SAB-009 AC1-AC4)", () => {
  it("AC2/AC4: dashboard loads normally when user has no organization", async () => {
    // Default mock returns {} for organizations/me → no org → no team toggle
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("64h")).toBeInTheDocument();
    });

    // Team toggle should NOT be shown when user has no org
    expect(screen.queryByTestId("team-toggle")).not.toBeInTheDocument();
  });

  it("AC4: organizations/me network error does not affect dashboard", async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes("organizations/me"))
        return Promise.reject(new Error("Network error"));
      if (url.includes("summary"))
        return Promise.resolve({ ok: true, json: async () => mockSummary });
      if (url.includes("searches-over-time"))
        return Promise.resolve({ ok: true, json: async () => mockTimeSeries });
      if (url.includes("top-dimensions"))
        return Promise.resolve({ ok: true, json: async () => mockDimensions });
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("64h")).toBeInTheDocument();
    });
  });
});
