/**
 * SAB-004: NavigationShell Tests
 * Verifies that /alertas (and /mensagens) are protected routes
 * that render with sidebar and bottom nav.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { NavigationShell } from "../components/NavigationShell";

// Mock next/navigation
const mockPathname = jest.fn(() => "/buscar");
jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  })),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

// Mock AuthProvider
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { email: "test@example.com" },
    session: { access_token: "test-token" },
    loading: false,
    signOut: jest.fn(),
    isAdmin: false,
  }),
}));

// Mock Sidebar
jest.mock("../components/Sidebar", () => ({
  Sidebar: () => <div data-testid="sidebar">Sidebar</div>,
}));

// Mock BottomNav
jest.mock("../components/BottomNav", () => ({
  BottomNav: () => <div data-testid="bottom-nav">BottomNav</div>,
}));

// Mock MfaEnforcementBanner
jest.mock("../components/auth/MfaEnforcementBanner", () => ({
  MfaEnforcementBanner: () => null,
}));

describe("NavigationShell", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // SHIP-002: /alertas and /mensagens removed from PROTECTED_ROUTES (feature-gated)
  const protectedRoutes = [
    "/buscar",
    "/dashboard",
    "/pipeline",
    "/historico",
    "/conta",
    "/admin",
  ];

  const publicRoutes = ["/", "/login", "/signup", "/planos", "/ajuda"];

  protectedRoutes.forEach((route) => {
    it(`renders sidebar and bottom nav on ${route}`, () => {
      mockPathname.mockReturnValue(route);
      render(
        <NavigationShell>
          <div data-testid="page-content">Content</div>
        </NavigationShell>
      );
      expect(screen.getByTestId("sidebar")).toBeInTheDocument();
      expect(screen.getByTestId("bottom-nav")).toBeInTheDocument();
      expect(screen.getByTestId("page-content")).toBeInTheDocument();
    });
  });

  publicRoutes.forEach((route) => {
    it(`does NOT render sidebar on public route ${route}`, () => {
      mockPathname.mockReturnValue(route);
      render(
        <NavigationShell>
          <div data-testid="page-content">Content</div>
        </NavigationShell>
      );
      expect(screen.queryByTestId("sidebar")).not.toBeInTheDocument();
      expect(screen.queryByTestId("bottom-nav")).not.toBeInTheDocument();
      expect(screen.getByTestId("page-content")).toBeInTheDocument();
    });
  });

  // SHIP-002: /alertas removed from PROTECTED_ROUTES — no sidebar on these routes
  it("does NOT render sidebar on /alertas (SHIP-002 feature-gated)", () => {
    mockPathname.mockReturnValue("/alertas");
    render(
      <NavigationShell>
        <div>Alertas page</div>
      </NavigationShell>
    );
    expect(screen.queryByTestId("sidebar")).not.toBeInTheDocument();
  });

  // SHIP-002: /mensagens removed from PROTECTED_ROUTES — no sidebar on these routes
  it("does NOT render sidebar on /mensagens (SHIP-002 feature-gated)", () => {
    mockPathname.mockReturnValue("/mensagens");
    render(
      <NavigationShell>
        <div>Mensagens page</div>
      </NavigationShell>
    );
    expect(screen.queryByTestId("sidebar")).not.toBeInTheDocument();
  });
});
