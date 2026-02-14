/**
 * Tests for STORY-233: Login page displays correct messages per reason code
 * AC3: login_required vs session_expired message display
 */

import React from "react";
import { render, waitFor } from "@testing-library/react";

// Track what useSearchParams returns
let mockSearchParamsValue = new URLSearchParams();

// ---- Mocks (use require-style references to survive Jest hoisting) ----

// Sonner toast - reference via require after mock
jest.mock("sonner", () => ({
  toast: {
    error: jest.fn(),
    info: jest.fn(),
    success: jest.fn(),
  },
  Toaster: () => null,
}));

// Get reference AFTER mock setup
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { toast: mockToast } = require("sonner");

jest.mock("../app/components/InstitutionalSidebar", () => {
  return function MockSidebar() {
    return <div data-testid="sidebar" />;
  };
});

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => "/login",
  useSearchParams: () => mockSearchParamsValue,
}));

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    signInWithEmail: jest.fn(),
    signInWithMagicLink: jest.fn(),
    signInWithGoogle: jest.fn(),
    session: null,
    loading: false,
  }),
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    identifyUser: jest.fn(),
  }),
}));

// Mock window.history.replaceState
const replaceStateSpy = jest.fn();
Object.defineProperty(window, "history", {
  writable: true,
  configurable: true,
  value: { replaceState: replaceStateSpy, pushState: jest.fn(), state: {} },
});

// Import AFTER all mocks
import LoginPage from "../app/login/page";

describe("Login page reason messages (STORY-233 AC3)", () => {
  beforeEach(() => {
    mockToast.error.mockClear();
    mockToast.info.mockClear();
    mockToast.success.mockClear();
    replaceStateSpy.mockClear();
    mockSearchParamsValue = new URLSearchParams();
  });

  it("shows info toast for login_required reason", async () => {
    mockSearchParamsValue = new URLSearchParams("reason=login_required");

    render(<LoginPage />);

    await waitFor(() => {
      expect(mockToast.info).toHaveBeenCalledWith(
        "Faça login para acessar esta página."
      );
    });

    // Should NOT show error toast for informational reasons
    expect(mockToast.error).not.toHaveBeenCalled();
  });

  it("shows error toast for session_expired reason", async () => {
    mockSearchParamsValue = new URLSearchParams("reason=session_expired");

    render(<LoginPage />);

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith(
        "Sua sessão expirou. Faça login novamente."
      );
    });

    // Should NOT show info toast for error reasons
    expect(mockToast.info).not.toHaveBeenCalled();
  });

  it("handles error param correctly (AC4 - no regression)", async () => {
    mockSearchParamsValue = new URLSearchParams("error=auth_failed");

    render(<LoginPage />);

    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith(
        "Falha na autenticação. Tente novamente."
      );
    });
  });

  it("clears reason param from URL after displaying", async () => {
    mockSearchParamsValue = new URLSearchParams("reason=login_required");

    render(<LoginPage />);

    await waitFor(() => {
      expect(replaceStateSpy).toHaveBeenCalled();
    });
  });

  it("does nothing when no reason or error param present", () => {
    mockSearchParamsValue = new URLSearchParams();

    render(<LoginPage />);

    expect(mockToast.error).not.toHaveBeenCalled();
    expect(mockToast.info).not.toHaveBeenCalled();
  });
});

describe("Login page ERROR_MESSAGES map (STORY-233)", () => {
  it("login page source contains login_required message", () => {
    const fs = require("fs");
    const path = require("path");
    const loginSrc = fs.readFileSync(
      path.join(__dirname, "..", "app", "login", "page.tsx"),
      "utf-8"
    );

    // AC3: Must have login_required message
    expect(loginSrc).toContain("login_required");
    expect(loginSrc).toContain("Faça login para acessar esta página.");

    // AC3: Must have session_expired message
    expect(loginSrc).toContain("session_expired");
    expect(loginSrc).toContain("Sua sessão expirou. Faça login novamente.");

    // Must use INFO_REASONS to distinguish toast types
    expect(loginSrc).toContain("INFO_REASONS");
  });
});
