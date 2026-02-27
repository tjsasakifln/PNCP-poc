/**
 * STORY-299: Tests for SLO admin dashboard page.
 *
 * Covers:
 * - AC7: SLO compliance gauges
 * - AC8: Error budget bars
 * - AC9: Trend display / alert rules table
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

// Mock useAuth
const mockUseAuth = jest.fn();
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/admin/slo",
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

import AdminSLOPage from "../app/admin/slo/page";

// ============================================================================
// Test data
// ============================================================================

const mockSLOResponse = {
  compliance: "compliant",
  slos: {
    search_success_rate: {
      key: "search_success_rate",
      name: "Search Success Rate",
      description: "Proportion of searches completing successfully",
      target: 0.95,
      window_days: 7,
      unit: "ratio",
      sli_value: 0.97,
      is_met: true,
      error_budget_total: 0.05,
      error_budget_consumed_pct: 40.0,
      error_budget_remaining_pct: 60.0,
    },
    search_latency_p50: {
      key: "search_latency_p50",
      name: "Search Latency p50",
      description: "50th percentile search pipeline duration",
      target: 15.0,
      window_days: 7,
      unit: "seconds",
      sli_value: 8.5,
      is_met: true,
      error_budget_total: 0.0,
      error_budget_consumed_pct: 56.7,
      error_budget_remaining_pct: 43.3,
    },
    search_latency_p99: {
      key: "search_latency_p99",
      name: "Search Latency p99",
      description: "99th percentile search pipeline duration",
      target: 60.0,
      window_days: 7,
      unit: "seconds",
      sli_value: 45.0,
      is_met: true,
      error_budget_total: 0.0,
      error_budget_consumed_pct: 75.0,
      error_budget_remaining_pct: 25.0,
    },
    sse_connection_success: {
      key: "sse_connection_success",
      name: "SSE Connection Success",
      description: "Proportion of SSE connections established without error",
      target: 0.99,
      window_days: 7,
      unit: "ratio",
      sli_value: 0.995,
      is_met: true,
      error_budget_total: 0.01,
      error_budget_consumed_pct: 50.0,
      error_budget_remaining_pct: 50.0,
    },
    api_availability: {
      key: "api_availability",
      name: "API Availability (non-5xx)",
      description: "Proportion of API requests not returning 5xx errors",
      target: 0.995,
      window_days: 30,
      unit: "ratio",
      sli_value: 0.998,
      is_met: true,
      error_budget_total: 0.005,
      error_budget_consumed_pct: 40.0,
      error_budget_remaining_pct: 60.0,
    },
  },
  alerts: [
    {
      name: "SearchSuccessLow",
      severity: "critical",
      for_duration: "15m",
      summary: "Search success rate is critically low (<90%)",
      firing: false,
      value: 0.97,
    },
    {
      name: "SearchLatencyHigh",
      severity: "warning",
      for_duration: "10m",
      summary: "Search p99 latency exceeds 90s",
      firing: false,
      value: 45.0,
    },
    {
      name: "SSEDropRate",
      severity: "warning",
      for_duration: "5m",
      summary: "SSE connection drops exceed 20%",
      firing: false,
      value: 0.005,
    },
    {
      name: "ErrorBudgetBurn",
      severity: "critical",
      for_duration: "1h",
      summary: "Error budget burn rate is critically high",
      firing: false,
      value: 0.4,
    },
    {
      name: "WorkerTimeout",
      severity: "critical",
      for_duration: "0m",
      summary: "Gunicorn worker timeout detected",
      firing: false,
      value: 0,
    },
  ],
  firing_count: 0,
  recording_rules: {
    "smartlic:search_success_rate": "sum(rate(smartlic_searches_total...))",
  },
};

const mockViolationResponse = {
  ...mockSLOResponse,
  compliance: "violation",
  slos: {
    ...mockSLOResponse.slos,
    search_success_rate: {
      ...mockSLOResponse.slos.search_success_rate,
      sli_value: 0.85,
      is_met: false,
      error_budget_consumed_pct: 100.0,
      error_budget_remaining_pct: 0.0,
    },
  },
  alerts: [
    { ...mockSLOResponse.alerts[0], firing: true, value: 0.85 },
    ...mockSLOResponse.alerts.slice(1),
  ],
  firing_count: 1,
};

// ============================================================================
// Tests
// ============================================================================

describe("AdminSLOPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("shows loading state when auth is loading", () => {
    mockUseAuth.mockReturnValue({ session: null, loading: true, isAdmin: false });
    render(<AdminSLOPage />);
    expect(screen.getByText("Carregando...")).toBeInTheDocument();
  });

  it("shows login link when no session", () => {
    mockUseAuth.mockReturnValue({ session: null, loading: false, isAdmin: false });
    render(<AdminSLOPage />);
    expect(screen.getByText("Login necessario")).toBeInTheDocument();
  });

  it("shows access restricted for non-admin", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: false,
    });
    render(<AdminSLOPage />);
    await waitFor(() => {
      expect(screen.getByText("Acesso Restrito")).toBeInTheDocument();
    });
  });

  it("AC7: renders SLO compliance gauges when data loads", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("SLO Dashboard")).toBeInTheDocument();
      expect(screen.getByText("All SLOs Met")).toBeInTheDocument();
    });

    // Check SLO names are displayed
    expect(screen.getAllByText("Search Success Rate").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Search Latency p50").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SSE Connection Success").length).toBeGreaterThan(0);
  });

  it("AC7: shows MET badges when SLOs are compliant", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      const metBadges = screen.getAllByText("MET");
      expect(metBadges.length).toBe(5);
    });
  });

  it("AC7: shows VIOLATED badge when SLO is not met", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockViolationResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("SLO Violation")).toBeInTheDocument();
      expect(screen.getByText("VIOLATED")).toBeInTheDocument();
    });
  });

  it("AC8: renders error budget bars", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("Error Budget")).toBeInTheDocument();
      // Check for "remaining" percentages (multiple SLOs may share the same value)
      expect(screen.getAllByText(/remaining/).length).toBeGreaterThanOrEqual(5);
    });
  });

  it("renders alert rules table", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("Alert Rules")).toBeInTheDocument();
      expect(screen.getByText("SearchSuccessLow")).toBeInTheDocument();
      expect(screen.getByText("SearchLatencyHigh")).toBeInTheDocument();
      expect(screen.getByText("WorkerTimeout")).toBeInTheDocument();
    });
  });

  it("shows FIRING badge when alerts are active", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockViolationResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("1 firing")).toBeInTheDocument();
      expect(screen.getByText("FIRING")).toBeInTheDocument();
    });
  });

  it("shows OK badges for non-firing alerts", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      const okBadges = screen.getAllByText("OK");
      expect(okBadges.length).toBe(5);
    });
  });

  it("AC9: renders recording rules reference", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("Prometheus Recording Rules")).toBeInTheDocument();
      expect(screen.getByText("smartlic:search_success_rate")).toBeInTheDocument();
    });
  });

  it("shows error message on fetch failure", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal error" }),
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("Internal error")).toBeInTheDocument();
    });
  });

  it("renders navigation links", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getByText("Usuarios")).toBeInTheDocument();
      expect(screen.getByText("Metrics")).toBeInTheDocument();
      expect(screen.getByText("Cache")).toBeInTheDocument();
    });
  });

  it("displays severity badges for alerts", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test" },
      loading: false,
      isAdmin: true,
    });
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSLOResponse,
    });

    render(<AdminSLOPage />);

    await waitFor(() => {
      expect(screen.getAllByText("CRITICAL").length).toBeGreaterThanOrEqual(3);
      expect(screen.getAllByText("WARNING").length).toBeGreaterThanOrEqual(2);
    });
  });
});
