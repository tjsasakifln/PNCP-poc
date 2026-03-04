/**
 * UX-408 — Auth Race Condition & PKCE Verifier Tests
 *
 * T1: AuthProvider does not setState after unmount (AC1)
 * T2: Public page (landing) does not generate AuthApiError in console (AC2/AC5)
 * T3: Callback without code_verifier shows friendly message (AC3)
 * T4: Callback with code_verifier works normally (AC4 telemetry + normal flow)
 */
import React from "react";
import { render, screen, waitFor, act, cleanup } from "@testing-library/react";

// ============================================================
// PART 1: AuthProvider Tests (T1, T2)
// ============================================================

// --- AuthProvider Supabase mock ---
const mockGetUser_AP = jest.fn();
const mockGetSession_AP = jest.fn();
const mockRefreshSession_AP = jest.fn();
const mockOnAuthStateChange_AP = jest.fn();

jest.mock("../lib/supabase", () => ({
  supabase: {
    auth: {
      getUser: (...args: any[]) => mockGetUser_AP(...args),
      getSession: (...args: any[]) => mockGetSession_AP(...args),
      refreshSession: (...args: any[]) => mockRefreshSession_AP(...args),
      onAuthStateChange: (cb: any) => {
        mockOnAuthStateChange_AP(cb);
        return { data: { subscription: { unsubscribe: jest.fn() } } };
      },
      signInWithPassword: jest.fn().mockResolvedValue({ error: null }),
      signUp: jest.fn().mockResolvedValue({ error: null }),
      signInWithOtp: jest.fn().mockResolvedValue({ error: null }),
      signInWithOAuth: jest.fn().mockResolvedValue({ error: null }),
      signOut: jest.fn().mockResolvedValue({ error: null }),
      exchangeCodeForSession: jest.fn(),
      setSession: jest.fn(),
    },
  },
}));

// Mock next/navigation
const mockRouterPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockRouterPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

// Mock analytics
const mockTrackEvent = jest.fn();
const mockIdentifyUser = jest.fn();
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    identifyUser: mockIdentifyUser,
    trackEvent: mockTrackEvent,
  }),
}));

// Mock fetch for admin status
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ is_admin: false }),
}) as any;

process.env.NEXT_PUBLIC_BACKEND_URL = "http://test-backend:8000";

import { AuthProvider, useAuth } from "../app/components/AuthProvider";

function TestConsumer() {
  const { user, loading } = useAuth();
  return (
    <div>
      <span data-testid="loading">{loading ? "true" : "false"}</span>
      <span data-testid="user">{user ? user.email : "null"}</span>
    </div>
  );
}

describe("UX-408: AuthProvider race condition fixes", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockGetUser_AP.mockResolvedValue({ data: { user: null } });
    mockGetSession_AP.mockResolvedValue({ data: { session: null } });
    mockRefreshSession_AP.mockResolvedValue({ data: { session: null }, error: null });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("T1 (AC1): AuthProvider does not call setState after unmount", async () => {
    // getUser will resolve AFTER the component unmounts
    let resolveGetUser: (value: any) => void;
    mockGetUser_AP.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveGetUser = resolve;
        })
    );

    const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    const { unmount } = render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    // Component is mounted and loading
    expect(screen.getByTestId("loading")).toHaveTextContent("true");

    // Unmount BEFORE getUser resolves
    unmount();

    // Now resolve getUser — should NOT cause setState warning
    await act(async () => {
      resolveGetUser!({ data: { user: { email: "test@example.com", id: "123" } } });
      await Promise.resolve();
    });

    // No "Can't perform a React state update on an unmounted component" error
    // This is the key assertion — if isMounted guard is missing, React will warn
    const stateUpdateWarnings = consoleErrorSpy.mock.calls.filter((call) =>
      String(call[0]).includes("unmounted")
    );
    expect(stateUpdateWarnings).toHaveLength(0);

    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  test("T2 (AC2/AC5): Public page without user does not generate console.error AuthApiError", async () => {
    // Simulate AuthApiError from getUser on a public page (no session)
    const authApiError = new Error("AuthApiError: invalid claim: missing sub claim");
    (authApiError as any).name = "AuthApiError";

    mockGetUser_AP.mockRejectedValue(authApiError);
    mockGetSession_AP.mockResolvedValue({ data: { session: null } });

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    // Wait for auth to complete
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    // AC5: No console.error with AuthApiError — should use console.warn instead
    const authErrors = consoleErrorSpy.mock.calls.filter((call) =>
      String(call[0]).includes("AuthApiError") || String(call[0]).includes("Auth check failed")
    );
    expect(authErrors).toHaveLength(0);

    // AC2: console.warn should contain the friendly message
    const authWarns = consoleWarnSpy.mock.calls.filter((call) =>
      String(call[0]).includes("Sessão expirada")
    );
    expect(authWarns.length).toBeGreaterThan(0);

    // User should resolve to null (no crash)
    await waitFor(() => {
      expect(screen.getByTestId("user")).toHaveTextContent("null");
    });

    consoleErrorSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });
});

// ============================================================
// PART 2: OAuth Callback Tests (T3, T4)
// ============================================================

// We need to test the callback page in isolation.
// Since the supabase mock is already set up above, we import callback separately.
import AuthCallbackPage from "../app/auth/callback/page";

const originalLocation = window.location;

function mockLocation(search: string) {
  // @ts-ignore
  delete window.location;
  // @ts-ignore
  window.location = {
    ...originalLocation,
    href: `http://localhost:3000/auth/callback${search}`,
    search,
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
  };
}

const fakeSession = {
  user: {
    id: "user-123",
    email: "test@example.com",
    created_at: "2026-01-01T00:00:00Z",
  },
  access_token: "access-token-1234567890abcdef",
  refresh_token: "refresh-token",
  expires_at: Math.floor(Date.now() / 1000) + 3600,
};

// Get reference to the mocked supabase for direct manipulation
const { supabase: mockedSupabase } = require("../lib/supabase");

describe("UX-408: OAuth callback PKCE verifier checks", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockLocation("?code=auth-code-123");
    // Clear localStorage
    localStorage.clear();
    mockOnAuthStateChange_AP.mockImplementation((cb: any) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    window.location = originalLocation;
    localStorage.clear();
  });

  test("T3 (AC3): Callback without code_verifier shows friendly message with login button", async () => {
    // NO code_verifier in localStorage
    // (localStorage is clean after clear)

    const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Flush promises
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    // AC3: Should show specific PKCE missing message
    await waitFor(() => {
      expect(
        screen.getByText("Sessão de login expirada. Por favor, tente fazer login novamente.")
      ).toBeInTheDocument();
    });

    // Should have a "Tentar novamente" link to /login
    const loginLink = screen.getByRole("link", { name: /tentar novamente/i });
    expect(loginLink).toHaveAttribute("href", "/login");

    // AC4: trackEvent should have been called with oauth_pkce_missing
    expect(mockTrackEvent).toHaveBeenCalledWith(
      "oauth_pkce_missing",
      expect.objectContaining({ has_code: true })
    );

    // exchangeCodeForSession should NOT have been called
    expect(mockedSupabase.auth.exchangeCodeForSession).not.toHaveBeenCalled();

    consoleWarnSpy.mockRestore();
  });

  test("T4 (AC3 positive): Callback WITH code_verifier proceeds to exchange normally", async () => {
    // Set code_verifier in localStorage BEFORE render (simulates Supabase PKCE flow)
    localStorage.setItem("sb-fqqyovlzdzimiwfofdjk-auth-code-verifier", "test-verifier-abc123");

    // Configure exchangeCodeForSession to succeed
    const exchangeMock = mockedSupabase.auth.exchangeCodeForSession as jest.Mock;
    exchangeMock.mockResolvedValue({
      data: { session: fakeSession },
      error: null,
    });
    (mockedSupabase.auth.setSession as jest.Mock).mockResolvedValue({ data: {}, error: null });

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Flush multiple promise ticks for retry loop
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    // exchangeCodeForSession SHOULD have been called (code_verifier exists)
    expect(exchangeMock).toHaveBeenCalledWith("auth-code-123");

    // Should redirect to /buscar on success
    expect(window.location.href).toBe("/buscar");

    // trackEvent for oauth_pkce_missing should NOT have been called
    expect(mockTrackEvent).not.toHaveBeenCalledWith(
      "oauth_pkce_missing",
      expect.anything()
    );
  });
});
