/**
 * UX-337: Sidebar Navigation Tests
 * Tests AC1-AC6 (Desktop Sidebar)
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar } from "../components/Sidebar";

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
const mockSignOut = jest.fn();
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { email: "test@example.com" },
    session: { access_token: "test-token" },
    loading: false,
    signOut: mockSignOut,
    isAdmin: false,
  }),
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, val: string) => { store[key] = val; }),
    removeItem: jest.fn((key: string) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("Sidebar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    mockPathname.mockReturnValue("/buscar");
  });

  // AC1: Sidebar visible
  it("renders sidebar with data-testid", () => {
    render(<Sidebar />);
    expect(screen.getByTestId("sidebar")).toBeInTheDocument();
  });

  // AC2: Shows 6 items (SHIP-002: Alertas and Suporte/Mensagens removed — feature-gated)
  // Remaining: Buscar, Dashboard, Pipeline, Histórico, Minha Conta, Ajuda
  it("shows all navigation items", () => {
    render(<Sidebar />);
    expect(screen.getByText("Buscar")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Histórico")).toBeInTheDocument();
    expect(screen.getByText("Minha Conta")).toBeInTheDocument();
    expect(screen.getByText("Ajuda")).toBeInTheDocument();
    // SHIP-002: removed
    expect(screen.queryByText("Alertas")).not.toBeInTheDocument();
    expect(screen.queryByText("Suporte")).not.toBeInTheDocument();
  });

  // AC2: Plus Sair button
  it("shows Sair button", () => {
    render(<Sidebar />);
    expect(screen.getByText("Sair")).toBeInTheDocument();
  });

  // AC3: Active item is highlighted
  it("highlights the active item with aria-current=page", () => {
    mockPathname.mockReturnValue("/buscar");
    render(<Sidebar />);
    const buscarLink = screen.getByText("Buscar").closest("a");
    expect(buscarLink).toHaveAttribute("aria-current", "page");
  });

  it("does not highlight non-active items", () => {
    mockPathname.mockReturnValue("/buscar");
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).not.toHaveAttribute("aria-current");
  });

  it("highlights dashboard when on /dashboard", () => {
    mockPathname.mockReturnValue("/dashboard");
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveAttribute("aria-current", "page");
  });

  // SAB-004 AC2: Alertas removed (SHIP-002 feature-gated) — verify it's absent
  it("does not show Alertas link (SHIP-002 feature-gated)", () => {
    mockPathname.mockReturnValue("/alertas");
    render(<Sidebar />);
    expect(screen.queryByText("Alertas")).not.toBeInTheDocument();
  });

  // AC4: Collapse toggle
  it("can be collapsed via toggle button", () => {
    render(<Sidebar />);
    const sidebar = screen.getByTestId("sidebar");
    const toggle = screen.getByTestId("sidebar-toggle");

    // Default: expanded (200px)
    expect(sidebar.className).toContain("w-[200px]");

    // Click to collapse
    fireEvent.click(toggle);
    expect(sidebar.className).toContain("w-[56px]");

    // Labels should be hidden
    expect(screen.queryByText("Buscar")).not.toBeInTheDocument();
  });

  it("shows labels when expanded", () => {
    render(<Sidebar />);
    expect(screen.getByText("Buscar")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  // AC5: Collapsed state persists in localStorage
  it("persists collapsed state in localStorage", () => {
    render(<Sidebar />);
    const toggle = screen.getByTestId("sidebar-toggle");
    fireEvent.click(toggle);

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "smartlic-sidebar-collapsed",
      "true"
    );
  });

  it("loads collapsed state from localStorage", () => {
    localStorageMock.getItem.mockReturnValue("true");
    render(<Sidebar />);
    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar.className).toContain("w-[56px]");
  });

  // AC6: Hidden on < 1024px (lg breakpoint)
  it("has hidden lg:flex classes (visible only on desktop)", () => {
    render(<Sidebar />);
    const sidebar = screen.getByTestId("sidebar");
    expect(sidebar.className).toContain("hidden");
    expect(sidebar.className).toContain("lg:flex");
  });

  // Sign out
  it("calls signOut when Sair is clicked", () => {
    render(<Sidebar />);
    fireEvent.click(screen.getByText("Sair"));
    expect(mockSignOut).toHaveBeenCalled();
  });

  // Logo
  it("shows SmartLic logo that links to /buscar", () => {
    render(<Sidebar />);
    const logo = screen.getByText("SmartLic");
    const logoLink = logo.closest("a");
    expect(logoLink).toHaveAttribute("href", "/buscar");
  });

  // Navigation aria-label
  it("has accessible navigation label", () => {
    render(<Sidebar />);
    expect(screen.getByLabelText("Navegação principal")).toBeInTheDocument();
  });

  // ── SAB-013 AC1-AC3: Hover transitions + active left border ──

  // AC1: transition: background-color 150ms ease
  it("SAB-013 AC1: nav items have transition-[background-color] duration-150", () => {
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink?.className).toContain("transition-[background-color]");
    expect(dashboardLink?.className).toContain("duration-150");
    expect(dashboardLink?.className).toContain("ease-in-out");
  });

  // AC2: More visible hover: bg-gray-100 (light) / bg-gray-800 (dark)
  it("SAB-013 AC2: inactive items have hover:bg-gray-100 dark:hover:bg-gray-800", () => {
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink?.className).toContain("hover:bg-gray-100");
    expect(dashboardLink?.className).toContain("dark:hover:bg-gray-800");
  });

  // AC3: Active item with 4px left border accent (blue)
  it("SAB-013 AC3: active item has border-l-4 border-[var(--brand-blue)]", () => {
    mockPathname.mockReturnValue("/buscar");
    render(<Sidebar />);
    const buscarLink = screen.getByText("Buscar").closest("a");
    expect(buscarLink?.className).toContain("border-l-4");
    expect(buscarLink?.className).toContain("border-[var(--brand-blue)]");
  });

  it("SAB-013 AC3: inactive items have border-transparent (no visual jump)", () => {
    mockPathname.mockReturnValue("/buscar");
    render(<Sidebar />);
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink?.className).toContain("border-l-4");
    expect(dashboardLink?.className).toContain("border-transparent");
  });
});
