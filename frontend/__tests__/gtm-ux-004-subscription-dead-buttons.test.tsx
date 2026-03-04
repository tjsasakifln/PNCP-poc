/**
 * GTM-UX-004: Subscription Status Proxy + Dead Buttons
 *
 * T1: Tested in proxy-error-handler.test.ts (node env required)
 * T2: Cache localStorage used as fallback
 * T3: Button "Ver ultima busca" works when there's saved search
 * T4: Button hidden when no saved search
 * T5: Polling post-checkout works
 */
import React from "react";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── T2: Cache localStorage used as fallback ────────────────────────────────

const mockSession = { access_token: "test-token" };
const mockUser = { id: "user-123", email: "test@example.com" };

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    session: mockSession,
    user: mockUser,
    loading: false,
    signOut: jest.fn(),
  }),
}));

import { usePlan } from "../hooks/usePlan";

describe("T2: Cache localStorage used as fallback", () => {
  let mockFetch: jest.Mock;

  beforeEach(() => {
    jest.useFakeTimers();
    mockFetch = jest.fn();
    global.fetch = mockFetch;
    localStorage.clear();
    jest.spyOn(console, "warn").mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it("falls back to cached plan when backend is offline", async () => {
    const cachedPlan = {
      user_id: "user-123",
      email: "test@example.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: {
        max_history_days: 1825,
        allow_excel: true,
        max_requests_per_month: 1000,
        max_requests_per_min: 10,
        max_summary_tokens: 500,
        priority: "NORMAL",
      },
      quota_used: 5,
      quota_remaining: 995,
      quota_reset_date: "2026-03-01",
      trial_expires_at: null,
      subscription_status: "active",
    };

    localStorage.setItem(
      "smartlic_cached_plan",
      JSON.stringify({ data: cachedPlan, timestamp: Date.now() })
    );

    mockFetch.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => usePlan());

    // Exhaust retries
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        jest.advanceTimersByTime(i === 0 ? 100 : 10_000);
        await Promise.resolve();
        await Promise.resolve();
      });
    }

    await waitFor(() => {
      expect(result.current.planInfo?.plan_id).toBe("smartlic_pro");
      expect(result.current.isFromCache).toBe(true);
      expect(result.current.cachedAt).toBeGreaterThan(0);
    });
  });

  it("returns null planInfo and error when no cache and backend offline", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => usePlan());

    for (let i = 0; i < 5; i++) {
      await act(async () => {
        jest.advanceTimersByTime(i === 0 ? 100 : 10_000);
        await Promise.resolve();
        await Promise.resolve();
      });
    }

    await waitFor(() => {
      expect(result.current.planInfo).toBeNull();
      expect(result.current.error).toBeTruthy();
      expect(result.current.isFromCache).toBe(false);
    });
  });

  it("isFromCache is false when fresh data loaded successfully", async () => {
    const freshPlan = {
      user_id: "user-123",
      email: "test@example.com",
      plan_id: "smartlic_pro",
      plan_name: "SmartLic Pro",
      capabilities: {
        max_history_days: 1825,
        allow_excel: true,
        max_requests_per_month: 1000,
        max_requests_per_min: 10,
        max_summary_tokens: 500,
        priority: "NORMAL",
      },
      quota_used: 5,
      quota_remaining: 995,
      quota_reset_date: "2026-03-01",
      trial_expires_at: null,
      subscription_status: "active",
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => freshPlan,
    });

    const { result } = renderHook(() => usePlan());

    await act(async () => {
      jest.advanceTimersByTime(100);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(result.current.planInfo?.plan_id).toBe("smartlic_pro");
      expect(result.current.isFromCache).toBe(false);
      expect(result.current.cachedAt).toBeNull();
    });
  });
});

// ─── T3 & T4: SourcesUnavailable button behavior ──────────────────────────

import { SourcesUnavailable } from "@/app/buscar/components/SourcesUnavailable";

describe("T3: Button 'Ver ultima busca' works when there's saved search", () => {
  it("shows and enables button when hasLastSearch=true", () => {
    const onLoadLastSearch = jest.fn();
    render(
      <SourcesUnavailable
        onRetry={jest.fn()}
        onLoadLastSearch={onLoadLastSearch}
        hasLastSearch={true}
        retrying={false}
      />
    );

    const btn = screen.getByRole("button", { name: /última análise salva/i });
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();

    fireEvent.click(btn);
    expect(onLoadLastSearch).toHaveBeenCalledTimes(1);
  });
});

describe("T4: Button hidden when no saved search", () => {
  it("does not render 'Ver ultima busca' button when hasLastSearch=false", () => {
    render(
      <SourcesUnavailable
        onRetry={jest.fn()}
        onLoadLastSearch={jest.fn()}
        hasLastSearch={false}
        retrying={false}
      />
    );

    expect(
      screen.queryByRole("button", { name: /última análise salva/i })
    ).not.toBeInTheDocument();
  });
});

// ─── T5: Polling post-checkout ─────────────────────────────────────────────

// Mock next/navigation and useAnalytics
jest.mock("next/navigation", () => ({
  useSearchParams: () => ({
    get: (key: string) => (key === "plan" ? "smartlic_pro" : null),
  }),
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
  }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  Rocket: () => <span>Rocket</span>,
  Zap: () => <span>Zap</span>,
  Trophy: () => <span>Trophy</span>,
  CheckCircle: () => <span>CheckCircle</span>,
  Loader2: () => <span>Loader2</span>,
  AlertCircle: () => <span>AlertCircle</span>,
  PartyPopper: () => <span>PartyPopper</span>,
}));

describe("T5: Polling post-checkout works", () => {
  let mockFetchT5: jest.Mock;

  beforeEach(() => {
    jest.useFakeTimers();
    mockFetchT5 = jest.fn();
    global.fetch = mockFetchT5;
    jest.spyOn(console, "warn").mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it("polls every 5s and shows confirmation when active", async () => {
    // First poll: still pending
    mockFetchT5.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "pending" }),
    });
    // Second poll: active
    mockFetchT5.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: "active" }),
    });

    // Dynamic import to avoid conflicts with other mocks
    const { default: ObrigadoPage } = await import(
      "../app/planos/obrigado/page"
    );

    await act(async () => {
      render(<ObrigadoPage />);
    });

    // Shows "Ativando" initially
    expect(screen.getByText(/Ativando sua conta/i)).toBeInTheDocument();

    // Advance past first poll interval (5s)
    await act(async () => {
      jest.advanceTimersByTime(5000);
      await Promise.resolve();
      await Promise.resolve();
    });

    // Advance past second poll interval (5s)
    await act(async () => {
      jest.advanceTimersByTime(5000);
      await Promise.resolve();
      await Promise.resolve();
    });

    // After activation, shows confirmation
    await waitFor(() => {
      expect(screen.getByText(/Assinatura confirmada/i)).toBeInTheDocument();
    });
  });
});

// ─── lastSearchCache utility tests ──────────────────────────────────────────

import {
  saveLastSearch,
  getLastSearch,
  checkHasLastSearch,
} from "../lib/lastSearchCache";

describe("lastSearchCache utility", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("saves and retrieves last search", () => {
    const mockResult = { licitacoes: [{ id: "1" }], total_raw: 1 };
    saveLastSearch(mockResult);

    const cached = getLastSearch();
    expect(cached).not.toBeNull();
    expect(cached!.result).toEqual(mockResult);
    expect(cached!.timestamp).toBeGreaterThan(0);
  });

  it("returns null when no search saved", () => {
    expect(getLastSearch()).toBeNull();
    expect(checkHasLastSearch()).toBe(false);
  });

  it("checkHasLastSearch returns true after save", () => {
    saveLastSearch({ licitacoes: [] });
    expect(checkHasLastSearch()).toBe(true);
  });

  it("expires after 24 hours", () => {
    const mockResult = { licitacoes: [{ id: "1" }] };
    saveLastSearch(mockResult);

    // Manually set old timestamp
    const stored = JSON.parse(localStorage.getItem("smartlic_last_search")!);
    stored.timestamp = Date.now() - 25 * 60 * 60 * 1000; // 25h ago
    localStorage.setItem("smartlic_last_search", JSON.stringify(stored));

    expect(getLastSearch()).toBeNull();
    expect(checkHasLastSearch()).toBe(false);
  });
});
