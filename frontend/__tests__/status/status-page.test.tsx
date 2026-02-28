/**
 * STORY-316 AC22: Tests for status page components.
 * Tests: render, auto-refresh, incident list, uptime chart, footer badge.
 */

import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock BackendStatusIndicator before import
jest.mock("../../components/BackendStatusIndicator", () => ({
  useBackendStatusContext: () => ({ status: "online", isPolling: false, checkHealth: jest.fn() }),
  useBackendStatus: () => ({ status: "online", isPolling: false, checkHealth: jest.fn() }),
  BackendStatusProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  __esModule: true,
  default: () => null,
}));

// Mock framer-motion
jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
    section: ({ children, ...props }: any) => <section {...props}>{children}</section>,
    footer: ({ children, ...props }: any) => <footer {...props}>{children}</footer>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock animations (relative path — @/ alias not reliable in jest.mock)
jest.mock("../../lib/animations", () => ({
  fadeInUp: {},
  useScrollAnimation: () => ({ ref: { current: null }, isVisible: true }),
  staggerContainer: {},
  scaleIn: {},
}));

// Mock copy (relative path)
jest.mock("../../lib/copy/valueProps", () => ({
  footer: {
    dataSource: "Test data source",
    disclaimer: "Test disclaimer",
    trustBadge: "Test trust badge",
  },
}));

import StatusPage from "@/app/status/page";
import UptimeChart from "@/app/status/components/UptimeChart";
import IncidentList from "@/app/status/components/IncidentList";
import Footer from "@/app/components/Footer";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("StatusPage", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockFetch.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders loading state initially", () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: "healthy", sources: {}, components: {} }),
    });

    render(<StatusPage />);
    // Loading spinner should be present (the animate-spin class)
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("renders status page with healthy status", async () => {
    const statusData = {
      status: "healthy",
      sources: {
        pncp: { status: "healthy", latency_ms: 450, last_check: "2026-02-28T10:00:00Z" },
        portal: { status: "healthy", latency_ms: 320, last_check: "2026-02-28T10:00:00Z" },
        comprasgov: { status: "healthy", latency_ms: 200, last_check: "2026-02-28T10:00:00Z" },
      },
      components: { redis: "healthy", supabase: "healthy", arq_worker: "healthy" },
      uptime_pct_24h: 99.5,
      uptime_pct_7d: 98.0,
      uptime_pct_30d: 97.5,
      last_incident: null,
    };

    mockFetch.mockImplementation((url: string) => {
      if (url.includes("path=incidents")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ incidents: [] }) });
      }
      if (url.includes("path=uptime-history")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ history: [] }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(statusData) });
    });

    render(<StatusPage />);

    // Wait for the overall status banner (only rendered after loading completes)
    await waitFor(() => {
      expect(screen.getByText("Todos os sistemas operacionais")).toBeInTheDocument();
    });

    expect(screen.getByText("PNCP (Portal Nacional)")).toBeInTheDocument();
    expect(screen.getByText("99.5%")).toBeInTheDocument();
  });

  it("renders degraded status correctly", async () => {
    const statusData = {
      status: "degraded",
      sources: {
        pncp: { status: "healthy", latency_ms: 100 },
        portal: { status: "unhealthy", latency_ms: null, error: "timeout" },
      },
      components: { redis: "healthy", supabase: "healthy" },
      uptime_pct_24h: 75.0,
      uptime_pct_7d: 80.0,
      uptime_pct_30d: 85.0,
      last_incident: "2026-02-28T10:00:00Z",
    };

    mockFetch.mockImplementation(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(statusData) })
    );

    render(<StatusPage />);

    await waitFor(() => {
      expect(screen.getByText("Alguns sistemas com performance reduzida")).toBeInTheDocument();
    });
  });

  it("auto-refreshes every 60 seconds (AC14)", async () => {
    const statusData = {
      status: "healthy",
      sources: {},
      components: {},
      uptime_pct_24h: 100,
      uptime_pct_7d: 100,
      uptime_pct_30d: 100,
      last_incident: null,
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(statusData),
    });

    render(<StatusPage />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const initialCalls = mockFetch.mock.calls.length;

    // Advance time by 60 seconds
    act(() => {
      jest.advanceTimersByTime(60_000);
    });

    await waitFor(() => {
      expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCalls);
    });
  });
});

describe("UptimeChart", () => {
  it("renders empty state when no data", () => {
    render(<UptimeChart history={[]} />);
    expect(screen.getByText(/dados de uptime/i)).toBeInTheDocument();
  });

  it("renders bars for each day", () => {
    const history = [
      { date: "2026-02-27", uptime_pct: 100, checks: 288, healthy: 288, degraded: 0, unhealthy: 0 },
      { date: "2026-02-28", uptime_pct: 50, checks: 288, healthy: 144, degraded: 144, unhealthy: 0 },
    ];

    const { container } = render(<UptimeChart history={history} />);
    // Should have 2 bars
    const bars = container.querySelectorAll('[role="presentation"]');
    expect(bars.length).toBe(2);
  });

  it("uses correct colors for uptime levels", () => {
    const history = [
      { date: "2026-02-26", uptime_pct: 100, checks: 1, healthy: 1, degraded: 0, unhealthy: 0 },
      { date: "2026-02-27", uptime_pct: 90, checks: 1, healthy: 0, degraded: 1, unhealthy: 0 },
      { date: "2026-02-28", uptime_pct: 50, checks: 1, healthy: 0, degraded: 0, unhealthy: 1 },
    ];

    const { container } = render(<UptimeChart history={history} />);
    const bars = container.querySelectorAll('[role="presentation"]');

    expect(bars[0].className).toContain("bg-green-500");
    expect(bars[1].className).toContain("bg-yellow-500");
    expect(bars[2].className).toContain("bg-red-500");
  });
});

describe("IncidentList", () => {
  it("renders empty state when no incidents", () => {
    render(<IncidentList incidents={[]} />);
    expect(screen.getByText(/nenhum incidente/i)).toBeInTheDocument();
  });

  it("renders ongoing incident with pulse animation", () => {
    const incidents = [
      {
        id: "1",
        started_at: "2026-02-28T10:00:00Z",
        resolved_at: null,
        status: "ongoing" as const,
        affected_sources: ["pncp"],
        description: "PNCP timeout detectado",
      },
    ];

    render(<IncidentList incidents={incidents} />);
    // "Em andamento" appears twice: status label + duration display
    const emAndamento = screen.getAllByText("Em andamento");
    expect(emAndamento.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("PNCP timeout detectado")).toBeInTheDocument();
    expect(screen.getByText("pncp")).toBeInTheDocument();
  });

  it("renders resolved incident with duration", () => {
    const incidents = [
      {
        id: "2",
        started_at: "2026-02-28T10:00:00Z",
        resolved_at: "2026-02-28T11:30:00Z",
        status: "resolved" as const,
        affected_sources: ["portal", "comprasgov"],
        description: "Multi-source degradation",
      },
    ];

    render(<IncidentList incidents={incidents} />);
    expect(screen.getByText("Resolvido")).toBeInTheDocument();
    expect(screen.getByText("1h 30min")).toBeInTheDocument();
    expect(screen.getByText("portal")).toBeInTheDocument();
    expect(screen.getByText("comprasgov")).toBeInTheDocument();
  });
});

describe("Footer Status Badge (AC16-AC17)", () => {
  it("renders status badge with Operacional text", () => {
    render(<Footer />);
    expect(screen.getByText(/Status: Operacional/)).toBeInTheDocument();
  });

  it("renders link to /status page", () => {
    render(<Footer />);
    const link = screen.getByLabelText(/Status: Operacional/);
    expect(link).toHaveAttribute("href", "/status");
  });
});
