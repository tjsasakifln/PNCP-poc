/**
 * UX-356 — Dashboard: Sector Slugs → Display Names
 *
 * AC1: Chart shows full display names
 * AC2: All 15 slugs mapped
 * AC3: Unknown slug falls back to raw slug
 * AC4: Long names truncated (tickFormatter — tested via unit)
 * AC5: Render with slug "vestuario" → "Vestuário e Uniformes"
 * AC6: Zero regression on other dashboard charts
 */

import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ───────────────────────────────────────────────────────────────

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

// Capture BarChart data prop to verify sector name mapping
let capturedBarChartData: any[] = [];

jest.mock("recharts", () => ({
  BarChart: ({ children, data }: any) => {
    capturedBarChartData = data || [];
    return <div data-testid="bar-chart">{children}</div>;
  },
  Bar: () => <div data-testid="bar" />,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: ({ tickFormatter }: any) => (
    <div data-testid="y-axis" data-has-formatter={!!tickFormatter}>
      {tickFormatter && (
        <span data-testid="y-axis-formatter-output">
          {tickFormatter("Engenharia Rodoviária e Infraestrutura Viária")}
        </span>
      )}
    </div>
  ),
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

// ─── Import after mocks ────────────────────────────────────────────────

import DashboardPage from "../app/dashboard/page";
import {
  SECTOR_DISPLAY_NAMES,
  getSectorDisplayName,
} from "../lib/constants/sector-names";

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
  ],
};

// Use raw slugs as returned by backend
const mockDimensions = {
  top_ufs: [
    { name: "SP", count: 15, value: 20_000_000 },
    { name: "RJ", count: 10, value: 12_000_000 },
  ],
  top_sectors: [
    { name: "engenharia", count: 8, value: 15_000_000 },
    { name: "vestuario", count: 6, value: 10_000_000 },
    { name: "saude", count: 1, value: 500_000 },
  ],
};

function mockFetchSuccess(dimensionsOverride?: any) {
  (global.fetch as jest.Mock).mockImplementation((url: string) => {
    if (url.includes("summary"))
      return Promise.resolve({ ok: true, json: async () => mockSummary });
    if (url.includes("searches-over-time"))
      return Promise.resolve({ ok: true, json: async () => mockTimeSeries });
    if (url.includes("top-dimensions"))
      return Promise.resolve({
        ok: true,
        json: async () => dimensionsOverride || mockDimensions,
      });
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

// ─── Setup ──────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  capturedBarChartData = [];
  global.fetch = jest.fn();
  mockAuthState = {
    user: { id: "user-1", email: "test@test.com" },
    session: { access_token: "mock-token" },
    loading: false,
  };
  mockFetchSuccess();
});

// ─── Tests ──────────────────────────────────────────────────────────────

describe("UX-356 — Sector Display Names in Dashboard", () => {
  describe("AC1+AC5: Chart displays full sector names", () => {
    it("should map slug 'vestuario' to 'Vestuário e Uniformes' in chart data", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });

      const vestuario = capturedBarChartData.find(
        (d) => d.name === "Vestuário e Uniformes"
      );
      expect(vestuario).toBeDefined();
      expect(vestuario.count).toBe(6);
    });

    it("should map slug 'engenharia' to 'Engenharia, Projetos e Obras'", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });

      const eng = capturedBarChartData.find(
        (d) => d.name === "Engenharia, Projetos e Obras"
      );
      expect(eng).toBeDefined();
      expect(eng.count).toBe(8);
    });

    it("should map slug 'saude' to 'Saúde'", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });

      const saude = capturedBarChartData.find((d) => d.name === "Saúde");
      expect(saude).toBeDefined();
      expect(saude.count).toBe(1);
    });
  });

  describe("AC2: All 15 slugs mapped", () => {
    it("should have mappings for all 15 sectors", () => {
      const expectedSlugs = [
        "vestuario", "alimentos", "informatica", "mobiliario",
        "papelaria", "engenharia", "software", "facilities",
        "saude", "vigilancia", "transporte", "manutencao_predial",
        "engenharia_rodoviaria", "materiais_eletricos", "materiais_hidraulicos",
      ];

      expect(Object.keys(SECTOR_DISPLAY_NAMES)).toHaveLength(15);
      for (const slug of expectedSlugs) {
        expect(SECTOR_DISPLAY_NAMES[slug]).toBeDefined();
        expect(SECTOR_DISPLAY_NAMES[slug].length).toBeGreaterThan(0);
      }
    });
  });

  describe("AC3: Unknown slug fallback", () => {
    it("should display raw slug when sector is unknown", async () => {
      mockFetchSuccess({
        top_ufs: [{ name: "SP", count: 5, value: 1_000_000 }],
        top_sectors: [{ name: "novo_setor_xyz", count: 3, value: 500_000 }],
      });

      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });

      const unknown = capturedBarChartData.find(
        (d) => d.name === "novo_setor_xyz"
      );
      expect(unknown).toBeDefined();
      expect(unknown.count).toBe(3);
    });

    it("getSectorDisplayName returns raw slug for unknown input", () => {
      expect(getSectorDisplayName("desconhecido")).toBe("desconhecido");
      expect(getSectorDisplayName("")).toBe("");
    });
  });

  describe("AC4: Long name truncation", () => {
    it("should truncate names longer than 22 chars with ellipsis via tickFormatter", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });

      // YAxis mock renders the formatter output for a long name
      const formatterOutput = screen.getByTestId("y-axis-formatter-output");
      // slice(0, 20) + "…" = "Engenharia Rodoviári…"
      expect(formatterOutput.textContent).toBe(
        "Engenharia Rodoviári…"
      );
    });
  });

  describe("AC6: Zero regression on other charts", () => {
    it("should still render line chart, pie chart, and bar chart", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("line-chart")).toBeInTheDocument();
        expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
        expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
      });
    });

    it("should still render stat cards correctly", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText("42")).toBeInTheDocument();
        expect(screen.getByText("1.523")).toBeInTheDocument();
        expect(screen.getByText("90%")).toBeInTheDocument();
      });
    });

    it("should still render UF pie chart with full state names", async () => {
      render(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
        // UF legend still shows abbreviations in the list
        expect(screen.getByText("SP")).toBeInTheDocument();
        expect(screen.getByText("RJ")).toBeInTheDocument();
      });
    });
  });
});
