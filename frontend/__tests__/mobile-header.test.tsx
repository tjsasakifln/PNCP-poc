/**
 * UX-340: Mobile Header Redesign Tests
 * Tests AC1-AC13 (Mobile header simplification + drawer)
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MobileDrawer } from "../components/MobileDrawer";
import { PageHeader } from "../components/PageHeader";

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
    user: {
      email: "carlos@empresa.com",
      user_metadata: { full_name: "Seu Carlos" },
    },
    session: { access_token: "test-token" },
    loading: false,
    signOut: mockSignOut,
    isAdmin: false,
  }),
}));

// Mock ThemeProvider
const mockSetTheme = jest.fn();
let mockTheme = "light";
jest.mock("../app/components/ThemeProvider", () => ({
  useTheme: () => ({
    theme: mockTheme,
    setTheme: mockSetTheme,
    config: { id: mockTheme, label: mockTheme === "dark" ? "Dark" : "Light", isDark: mockTheme === "dark", canvas: "#fff", ink: "#000", preview: "#fff" },
  }),
  THEMES: [
    { id: "light", label: "Light", isDark: false, canvas: "#ffffff", ink: "#1e2d3b", preview: "#ffffff" },
    { id: "dark", label: "Dark", isDark: true, canvas: "#121212", ink: "#e0e0e0", preview: "#121212" },
  ],
}));

// Mock analytics
jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    resetUser: jest.fn(),
  }),
}));

// Mock QuotaBadge (used by PageHeader)
jest.mock("../app/components/QuotaBadge", () => ({
  QuotaBadge: () => <span data-testid="quota-badge">quota</span>,
}));

// Mock ThemeToggle (used by PageHeader desktop)
jest.mock("../app/components/ThemeToggle", () => ({
  ThemeToggle: () => <button data-testid="theme-toggle">theme</button>,
}));

// Mock UserMenu (used by PageHeader desktop)
jest.mock("../app/components/UserMenu", () => ({
  UserMenu: () => <button data-testid="user-menu">user</button>,
}));

describe("MobileDrawer", () => {
  const onClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname.mockReturnValue("/buscar");
    mockTheme = "light";
    document.body.style.overflow = "";
  });

  // AC4: Hamburger opens drawer with all navigation options
  it("renders drawer panel when open=true", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    expect(screen.getByTestId("mobile-drawer-panel")).toBeInTheDocument();
  });

  it("does not render when open=false", () => {
    render(<MobileDrawer open={false} onClose={onClose} />);
    expect(screen.queryByTestId("mobile-drawer-panel")).not.toBeInTheDocument();
  });

  // AC5: Drawer shows user name + email at top
  it("shows user name and email", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    expect(screen.getByTestId("drawer-user-name")).toHaveTextContent("Seu Carlos");
    expect(screen.getByTestId("drawer-user-email")).toHaveTextContent("carlos@empresa.com");
  });

  // AC4: All navigation items present
  it("includes all primary navigation items", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    expect(screen.getByText("Buscar")).toBeInTheDocument();
    expect(screen.getByText("Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Historico")).toBeInTheDocument();
    expect(screen.getByText("Mensagens")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  // AC3: Buscas Salvas moved to drawer
  it("includes Buscas Salvas in secondary nav", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    expect(screen.getByText("Buscas Salvas")).toBeInTheDocument();
    expect(screen.getByText("Minha Conta")).toBeInTheDocument();
    expect(screen.getByText("Ajuda")).toBeInTheDocument();
  });

  // AC2: Theme toggle moved to drawer
  it("includes theme toggle in drawer", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    expect(screen.getByTestId("drawer-theme-toggle")).toBeInTheDocument();
    expect(screen.getByText("Tema Escuro")).toBeInTheDocument();
  });

  it("toggles theme from light to dark", () => {
    mockTheme = "light";
    render(<MobileDrawer open={true} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("drawer-theme-toggle"));
    expect(mockSetTheme).toHaveBeenCalledWith("dark");
  });

  it("toggles theme from dark to light", () => {
    mockTheme = "dark";
    render(<MobileDrawer open={true} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("drawer-theme-toggle"));
    expect(mockSetTheme).toHaveBeenCalledWith("light");
  });

  // Sign out
  it("has sign out button that calls signOut", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("drawer-sign-out"));
    expect(mockSignOut).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  // AC6: Drawer closes on X click
  it("closes on X button click", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("mobile-drawer-close"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // AC6: Drawer closes on backdrop click
  it("closes on backdrop click", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("mobile-drawer-backdrop"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // AC6: Drawer closes on Escape
  it("closes on Escape key", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // AC7: Drawer closes on navigation
  it("closes when pathname changes", () => {
    const { rerender } = render(<MobileDrawer open={true} onClose={onClose} />);
    // Simulate route change
    mockPathname.mockReturnValue("/pipeline");
    rerender(<MobileDrawer open={true} onClose={onClose} />);
    expect(onClose).toHaveBeenCalled();
  });

  // AC8: Touch target >= 44px
  it("close button has min 44px touch target", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    const closeBtn = screen.getByTestId("mobile-drawer-close");
    expect(closeBtn.className).toContain("min-w-[44px]");
    expect(closeBtn.className).toContain("min-h-[44px]");
  });

  it("all nav items have min 44px touch target", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    const navLinks = screen.getByRole("navigation").querySelectorAll("a, button");
    navLinks.forEach((el) => {
      expect(el.className).toContain("min-h-[44px]");
    });
  });

  // AC9: Slide from right animation, 200ms
  it("panel has slide-in-right animation with 200ms duration", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    const panel = screen.getByTestId("mobile-drawer-panel");
    expect(panel.className).toContain("animate-slide-in-right");
    expect(panel.style.animationDuration).toBe("200ms");
  });

  // Accessibility
  it("has proper aria attributes", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    const panel = screen.getByTestId("mobile-drawer-panel");
    expect(panel).toHaveAttribute("role", "dialog");
    expect(panel).toHaveAttribute("aria-modal", "true");
  });

  // Body scroll lock
  it("locks body scroll when open", () => {
    render(<MobileDrawer open={true} onClose={onClose} />);
    expect(document.body.style.overflow).toBe("hidden");
  });

  it("unlocks body scroll on unmount", () => {
    const { unmount } = render(<MobileDrawer open={true} onClose={onClose} />);
    unmount();
    expect(document.body.style.overflow).toBe("");
  });

  // Active state highlighting
  it("highlights active nav item", () => {
    mockPathname.mockReturnValue("/buscar");
    render(<MobileDrawer open={true} onClose={onClose} />);
    const buscarLink = screen.getByText("Buscar").closest("a");
    expect(buscarLink?.className).toContain("brand-blue");
  });
});

describe("PageHeader — Mobile", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname.mockReturnValue("/dashboard");
  });

  // AC1: Header mobile shows Logo + hamburger "Menu"
  it("renders hamburger button with 'Menu' label", () => {
    render(<PageHeader title="Dashboard" />);
    const btn = screen.getByTestId("mobile-menu-button");
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveTextContent("Menu");
  });

  // AC1: Logo visible on mobile
  it("renders SmartLic logo link", () => {
    render(<PageHeader title="Dashboard" />);
    expect(screen.getByText("SmartLic")).toBeInTheDocument();
  });

  // AC8: Hamburger touch target >= 44px
  it("hamburger has min 44px touch target", () => {
    render(<PageHeader title="Dashboard" />);
    const btn = screen.getByTestId("mobile-menu-button");
    expect(btn.className).toContain("min-w-[44px]");
    expect(btn.className).toContain("min-h-[44px]");
  });

  // AC2 + AC3: ThemeToggle and UserMenu hidden on mobile (via lg:hidden/lg:flex CSS)
  it("desktop controls are in a hidden-on-mobile container", () => {
    render(<PageHeader title="Dashboard" />);
    const themeToggle = screen.getByTestId("theme-toggle");
    const container = themeToggle.closest("div");
    expect(container?.className).toContain("hidden lg:flex");
  });

  // AC10: Desktop shows title + controls
  it("renders page title for desktop", () => {
    render(<PageHeader title="Dashboard" />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  // AC11: Breakpoint at 1024px (lg: classes)
  it("hamburger uses lg:hidden breakpoint", () => {
    render(<PageHeader title="Dashboard" />);
    const btn = screen.getByTestId("mobile-menu-button");
    expect(btn.className).toContain("lg:hidden");
  });

  // Opens drawer on hamburger click
  it("opens MobileDrawer on hamburger click", () => {
    render(<PageHeader title="Dashboard" />);
    expect(screen.queryByTestId("mobile-drawer-panel")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("mobile-menu-button"));
    expect(screen.getByTestId("mobile-drawer-panel")).toBeInTheDocument();
  });
});
