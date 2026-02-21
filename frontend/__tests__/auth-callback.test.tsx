/**
 * UX-336 — Auth Callback PKCE Error Flash Tests
 *
 * Validates that the OAuth callback page:
 * 1. Never flashes an error screen when login can be recovered
 * 2. Falls through to getUser() when code exchange fails
 * 3. Falls through to onAuthStateChange when getUser() fails
 * 4. Shows humanized error only when ALL fallbacks fail
 * 5. Works normally when code exchange succeeds on first try
 */
import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";

// --- Supabase mock ---
const mockExchangeCodeForSession = jest.fn();
const mockGetUser = jest.fn();
const mockSetSession = jest.fn();
const mockGetSession = jest.fn();

let authStateCallback: ((event: string, session: any) => void) | null = null;
const mockUnsubscribe = jest.fn();
const mockOnAuthStateChange = jest.fn().mockImplementation((cb: any) => {
  authStateCallback = cb;
  return { data: { subscription: { unsubscribe: mockUnsubscribe } } };
});

jest.mock("../lib/supabase", () => ({
  supabase: {
    auth: {
      exchangeCodeForSession: (...args: any[]) => mockExchangeCodeForSession(...args),
      getUser: (...args: any[]) => mockGetUser(...args),
      setSession: (...args: any[]) => mockSetSession(...args),
      getSession: (...args: any[]) => mockGetSession(...args),
      onAuthStateChange: (...args: any[]) => mockOnAuthStateChange(...args),
    },
  },
}));

// --- Analytics mock ---
const mockIdentifyUser = jest.fn();
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    identifyUser: mockIdentifyUser,
    trackEvent: jest.fn(),
  }),
}));

// --- Import component after mocks ---
import AuthCallbackPage from "../app/auth/callback/page";

// --- Helpers ---
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

const fakeUser = {
  id: "user-123",
  email: "test@example.com",
};

describe("AuthCallbackPage — UX-336", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    authStateCallback = null;
    mockLocation("?code=auth-code-123");
    // Re-set onAuthStateChange implementation (clearAllMocks wipes mockImplementation)
    mockOnAuthStateChange.mockImplementation((cb: any) => {
      authStateCallback = cb;
      return { data: { subscription: { unsubscribe: mockUnsubscribe } } };
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    window.location = originalLocation;
  });

  test("AC6-1: code exchange fails with PKCE error -> getUser fallback succeeds -> no error flash", async () => {
    // Phase 1: exchangeCodeForSession fails with PKCE error
    mockExchangeCodeForSession.mockResolvedValue({
      data: { session: null },
      error: { message: "PKCE code verifier not found in storage" },
    });

    // Phase 2: getUser() succeeds (cookies are valid)
    mockGetUser.mockResolvedValue({
      data: { user: fakeUser },
      error: null,
    });

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Flush pending promises
    await act(async () => {
      await Promise.resolve();
    });

    // Should never show "Falha na autenticação"
    expect(screen.queryByText("Falha na autenticação")).not.toBeInTheDocument();

    // getUser was called as fallback
    expect(mockGetUser).toHaveBeenCalled();

    // Redirect to /buscar
    expect(window.location.href).toBe("/buscar");
  });

  test("AC6-2: code exchange fails + getUser fails + onAuthStateChange succeeds", async () => {
    // Phase 1: exchangeCodeForSession fails
    mockExchangeCodeForSession.mockResolvedValue({
      data: { session: null },
      error: { message: "PKCE code verifier not found" },
    });

    // Phase 2: getUser() returns no user (not authenticated yet)
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: null,
    });

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Flush promises for async handleCallback to complete
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    // Should still show loading (not error) while waiting for onAuthStateChange
    expect(screen.getByText("Processando autenticação...")).toBeInTheDocument();
    expect(screen.queryByText("Falha na autenticação")).not.toBeInTheDocument();

    // onAuthStateChange was registered
    expect(mockOnAuthStateChange).toHaveBeenCalled();

    // Simulate auth state change firing
    await act(async () => {
      if (authStateCallback) {
        authStateCallback("SIGNED_IN", fakeSession);
      }
    });

    // Should redirect to /buscar
    expect(window.location.href).toBe("/buscar");
    expect(mockUnsubscribe).toHaveBeenCalled();
  });

  test("AC6-3: ALL fallbacks fail -> error with humanized message (no technical terms)", async () => {
    // Phase 1: exchangeCodeForSession fails
    mockExchangeCodeForSession.mockResolvedValue({
      data: { session: null },
      error: { message: "PKCE code verifier not found in storage" },
    });

    // Phase 2: getUser() returns no user
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: null,
    });

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Flush promises
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    // Still loading (waiting for onAuthStateChange timeout)
    expect(screen.getByText("Processando autenticação...")).toBeInTheDocument();

    // Advance past the 10s onAuthStateChange timeout
    await act(async () => {
      jest.advanceTimersByTime(11000);
    });

    // NOW should show error
    expect(screen.getByText("Falha na autenticação")).toBeInTheDocument();

    // Error message should be humanized — NO technical terms
    expect(screen.getByText(/Não foi possível completar o login/)).toBeInTheDocument();
    expect(screen.queryByText(/PKCE/)).not.toBeInTheDocument();
    expect(screen.queryByText(/code.verifier/i)).not.toBeInTheDocument();
  });

  test("AC6-4: code exchange succeeds on first try -> normal flow (no regression)", async () => {
    // Phase 1: exchangeCodeForSession succeeds immediately
    mockExchangeCodeForSession.mockResolvedValue({
      data: { session: fakeSession },
      error: null,
    });
    mockSetSession.mockResolvedValue({ data: {}, error: null });

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Flush promises
    await act(async () => {
      await Promise.resolve();
    });

    // Should NOT call getUser (no fallback needed)
    expect(mockGetUser).not.toHaveBeenCalled();

    // Should redirect to /buscar
    expect(window.location.href).toBe("/buscar");

    // Should identify user
    expect(mockIdentifyUser).toHaveBeenCalledWith("user-123", expect.objectContaining({
      signup_method: "google",
    }));
  });

  test("AC6-5: 15s timeout -> humanized error message", async () => {
    // Phase 1: exchangeCodeForSession hangs forever
    mockExchangeCodeForSession.mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    await act(async () => {
      render(<AuthCallbackPage />);
    });

    // Should show loading
    expect(screen.getByText("Processando autenticação...")).toBeInTheDocument();

    // Advance past the 15s general timeout
    await act(async () => {
      jest.advanceTimersByTime(16000);
    });

    // Should show error with friendly message
    expect(screen.getByText("Falha na autenticação")).toBeInTheDocument();
    expect(screen.getByText(/Não foi possível completar o login/)).toBeInTheDocument();
  });
});
