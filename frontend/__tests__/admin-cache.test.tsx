/**
 * Tests for Admin Cache Dashboard (GTM-RESILIENCE-B05 AC9).
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => "/admin/cache",
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return <a href={href} {...rest}>{children}</a>;
  };
});

// Mock sonner
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock AuthProvider
const mockUseAuth = jest.fn();
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Import after mocks
import AdminCachePage from "../app/admin/cache/page";

const MOCK_METRICS = {
  hit_rate_24h: 0.73,
  miss_rate_24h: 0.27,
  stale_served_24h: 15,
  fresh_served_24h: 42,
  total_entries: 87,
  priority_distribution: { hot: 12, warm: 35, cold: 40 },
  age_distribution: { "0-1h": 15, "1-6h": 30, "6-12h": 25, "12-24h": 17 },
  degraded_keys: 3,
  avg_fetch_duration_ms: 4500,
  top_keys: [
    { params_hash: "abc123def456789012345678", access_count: 47, priority: "hot", age_hours: 1.2 },
    { params_hash: "def456789012345678abcdef", access_count: 12, priority: "warm", age_hours: 5.3 },
  ],
};

describe("AdminCachePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("shows loading state initially", () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: true,
      isAdmin: true,
    });

    render(<AdminCachePage />);
    expect(screen.getByText("Carregando...")).toBeInTheDocument();
  });

  test("shows login required without session", () => {
    mockUseAuth.mockReturnValue({
      session: null,
      loading: false,
      isAdmin: false,
    });

    render(<AdminCachePage />);
    expect(screen.getByText("Login necessário")).toBeInTheDocument();
  });

  test("shows access restricted for non-admin", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: false,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Acesso Restrito")).toBeInTheDocument();
    });
  });

  test("renders dashboard with metrics cards", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("73.0%")).toBeInTheDocument(); // hit rate
    });

    expect(screen.getByText("87")).toBeInTheDocument(); // total entries
    expect(screen.getByText("3")).toBeInTheDocument(); // degraded keys
    expect(screen.getByText("4500ms")).toBeInTheDocument(); // avg fetch
  });

  test("renders age distribution histogram", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Age Distribution")).toBeInTheDocument();
    });

    expect(screen.getByText("0-1h")).toBeInTheDocument();
    expect(screen.getByText("1-6h")).toBeInTheDocument();
    expect(screen.getByText("6-12h")).toBeInTheDocument();
    expect(screen.getByText("12-24h")).toBeInTheDocument();
    // Verify 30 appears in the 1-6h bucket
    expect(screen.getByText("30")).toBeInTheDocument();
  });

  test("renders top keys table with entries", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Top Cache Keys (2)")).toBeInTheDocument();
    });

    expect(screen.getByText("abc123def456...")).toBeInTheDocument();
    expect(screen.getByText("47")).toBeInTheDocument();
  });

  test("shows priority badges with correct labels", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      const hotBadges = screen.getAllByText("hot");
      expect(hotBadges.length).toBeGreaterThan(0);
    });
  });

  test("invalidate button calls DELETE endpoint", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    let fetchCallCount = 0;
    (global.fetch as jest.Mock).mockImplementation(async (url: string, opts: RequestInit = {}) => {
      fetchCallCount++;
      if (opts.method === "DELETE") {
        return {
          ok: true,
          json: async () => ({ deleted_levels: ["supabase", "redis", "local"] }),
        };
      }
      return { ok: true, json: async () => MOCK_METRICS };
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getAllByText("Invalidar").length).toBeGreaterThan(0);
    });

    // Click the first "Invalidar" button in table
    const invalidateButtons = screen.getAllByText("Invalidar");
    // The table buttons (not the "Invalidar Tudo" button)
    const tableButton = invalidateButtons.find(
      (btn) => btn.closest("td") !== null
    );
    if (tableButton) {
      fireEvent.click(tableButton);
    }

    await waitFor(() => {
      const deleteCalls = (global.fetch as jest.Mock).mock.calls.filter(
        (c: [string, RequestInit]) => c[1]?.method === "DELETE"
      );
      expect(deleteCalls.length).toBeGreaterThan(0);
    });
  });

  test("invalidate all shows confirmation dialog", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Invalidar Tudo")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Invalidar Tudo"));

    await waitFor(() => {
      expect(screen.getByText("Invalidar Todo o Cache")).toBeInTheDocument();
      expect(screen.getByText("Confirmar Invalidação Total")).toBeInTheDocument();
    });
  });

  test("cancel button closes confirmation dialog", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Invalidar Tudo")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Invalidar Tudo"));
    fireEvent.click(screen.getByText("Cancelar"));

    await waitFor(() => {
      expect(screen.queryByText("Invalidar Todo o Cache")).not.toBeInTheDocument();
    });
  });

  test("confirm invalidate all sends DELETE with X-Confirm header", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockImplementation(async (url: string, opts: RequestInit = {}) => {
      if (opts.method === "DELETE") {
        return {
          ok: true,
          json: async () => ({ deleted_counts: { supabase: 10, redis: 5, local: 3 } }),
        };
      }
      return { ok: true, json: async () => MOCK_METRICS };
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Invalidar Tudo")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Invalidar Tudo"));
    fireEvent.click(screen.getByText("Confirmar Invalidação Total"));

    await waitFor(() => {
      const deleteCalls = (global.fetch as jest.Mock).mock.calls.filter(
        (c: [string, RequestInit]) => c[1]?.method === "DELETE" && c[0]?.includes("/api/admin/cache")
      );
      expect(deleteCalls.length).toBeGreaterThan(0);
      // Verify X-Confirm header
      const headers = deleteCalls[0][1].headers as Record<string, string>;
      expect(headers["X-Confirm"]).toBe("delete-all");
    });
  });

  test("inspect button opens detail modal", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    const mockEntry = {
      params_hash: "abc123def456789012345678",
      user_id: "u1",
      search_params: { setor_id: "vestuario", ufs: ["SP"] },
      results_count: 15,
      sources: ["pncp"],
      fetched_at: "2026-02-19T10:00:00+00:00",
      created_at: "2026-02-19T10:00:00+00:00",
      priority: "hot",
      access_count: 47,
      last_accessed_at: "2026-02-19T14:00:00+00:00",
      fail_streak: 0,
      degraded_until: null,
      coverage: null,
      fetch_duration_ms: 3200,
      age_hours: 4.0,
      cache_status: "fresh",
    };

    (global.fetch as jest.Mock).mockImplementation(async (url: string) => {
      if (typeof url === "string" && url.includes("/cache/abc123")) {
        return { ok: true, json: async () => mockEntry };
      }
      return { ok: true, json: async () => MOCK_METRICS };
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getAllByText("Inspecionar").length).toBeGreaterThan(0);
    });

    const inspectButtons = screen.getAllByText("Inspecionar");
    fireEvent.click(inspectButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/Cache Entry: abc123def456/)).toBeInTheDocument();
    });
  });

  test("shows error state on fetch failure", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText(/Erro 500/)).toBeInTheDocument();
    });
  });

  test("link back to admin users page exists", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      const link = screen.getByText("Usuários");
      expect(link).toBeInTheDocument();
      expect(link.closest("a")).toHaveAttribute("href", "/admin");
    });
  });

  test("empty cache shows empty state", async () => {
    mockUseAuth.mockReturnValue({
      session: { access_token: "test-token" },
      loading: false,
      isAdmin: true,
    });

    const emptyMetrics = {
      ...MOCK_METRICS,
      total_entries: 0,
      top_keys: [],
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => emptyMetrics,
    });

    render(<AdminCachePage />);

    await waitFor(() => {
      expect(screen.getByText("Nenhuma entrada no cache")).toBeInTheDocument();
    });
  });
});
