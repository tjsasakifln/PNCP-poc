/**
 * UX-337: Bottom Navigation Tests
 * Tests AC7-AC10 (Mobile Bottom Nav)
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BottomNav } from "../components/BottomNav";

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

describe("BottomNav", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPathname.mockReturnValue("/buscar");
  });

  // AC7: Bottom nav appears with 5 items
  it("renders bottom nav with 5 items (4 links + Mais)", () => {
    render(<BottomNav />);
    const nav = screen.getByTestId("bottom-nav");
    expect(nav).toBeInTheDocument();

    expect(screen.getByText("Buscar")).toBeInTheDocument();
    expect(screen.getByText("Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Historico")).toBeInTheDocument();
    expect(screen.getByText("Msg")).toBeInTheDocument();
    expect(screen.getByText("Mais")).toBeInTheDocument();
  });

  // AC7: Hidden on >= 1024px
  it("has lg:hidden class (hidden on desktop)", () => {
    render(<BottomNav />);
    const nav = screen.getByTestId("bottom-nav");
    expect(nav.className).toContain("lg:hidden");
  });

  // AC8: Each item has icon + label
  it("each item displays both icon and label text", () => {
    render(<BottomNav />);
    // All items should have visible text labels
    const items = ["Buscar", "Pipeline", "Historico", "Msg", "Mais"];
    items.forEach((label) => {
      const el = screen.getByText(label);
      expect(el).toBeInTheDocument();
      // Parent should contain an SVG icon
      const parent = el.closest("a, button");
      expect(parent?.querySelector("svg")).toBeTruthy();
    });
  });

  // AC9: Touch targets >= 44px
  it("all items have min-w-[44px] min-h-[44px] for WCAG touch targets", () => {
    render(<BottomNav />);
    const items = screen.getByTestId("bottom-nav").querySelectorAll("a, button");
    items.forEach((item) => {
      expect(item.className).toContain("min-w-[44px]");
      expect(item.className).toContain("min-h-[44px]");
    });
  });

  // AC10: "Mais" opens drawer with Conta, Ajuda, Sair
  it("opens drawer when Mais is clicked", () => {
    render(<BottomNav />);
    expect(screen.queryByTestId("bottom-nav-drawer")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("bottom-nav-more"));
    expect(screen.getByTestId("bottom-nav-drawer")).toBeInTheDocument();
  });

  it("drawer shows Minha Conta, Ajuda, Sair", () => {
    render(<BottomNav />);
    fireEvent.click(screen.getByTestId("bottom-nav-more"));

    expect(screen.getByText("Minha Conta")).toBeInTheDocument();
    expect(screen.getByText("Ajuda")).toBeInTheDocument();
    expect(screen.getByText("Sair")).toBeInTheDocument();
  });

  it("drawer shows Dashboard link", () => {
    render(<BottomNav />);
    fireEvent.click(screen.getByTestId("bottom-nav-more"));

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("drawer closes when backdrop is clicked", () => {
    render(<BottomNav />);
    fireEvent.click(screen.getByTestId("bottom-nav-more"));
    expect(screen.getByTestId("bottom-nav-drawer")).toBeInTheDocument();

    // Click the backdrop (aria-hidden div)
    const backdrop = screen.getByTestId("bottom-nav-drawer").querySelector('[aria-hidden="true"]');
    fireEvent.click(backdrop!);
    expect(screen.queryByTestId("bottom-nav-drawer")).not.toBeInTheDocument();
  });

  // Active state
  it("highlights active item with aria-current", () => {
    mockPathname.mockReturnValue("/pipeline");
    render(<BottomNav />);
    const pipelineLink = screen.getByText("Pipeline").closest("a");
    expect(pipelineLink).toHaveAttribute("aria-current", "page");
  });

  it("does not highlight inactive items", () => {
    mockPathname.mockReturnValue("/buscar");
    render(<BottomNav />);
    const pipelineLink = screen.getByText("Pipeline").closest("a");
    expect(pipelineLink).not.toHaveAttribute("aria-current");
  });

  // Mais highlights when drawer route is active
  it("highlights Mais button when /conta is active", () => {
    mockPathname.mockReturnValue("/conta");
    render(<BottomNav />);
    const mais = screen.getByTestId("bottom-nav-more");
    expect(mais.className).toContain("brand-blue");
  });

  // Sair calls signOut
  it("calls signOut when Sair is clicked in drawer", () => {
    render(<BottomNav />);
    fireEvent.click(screen.getByTestId("bottom-nav-more"));
    fireEvent.click(screen.getByText("Sair"));
    expect(mockSignOut).toHaveBeenCalled();
  });

  // Accessible label
  it("has accessible navigation label", () => {
    render(<BottomNav />);
    expect(screen.getByLabelText("Navegacao mobile")).toBeInTheDocument();
  });

  // Spacer for content
  it("renders spacer div for content offset", () => {
    const { container } = render(<BottomNav />);
    const spacers = container.querySelectorAll('[aria-hidden="true"]');
    // At least the spacer div
    expect(spacers.length).toBeGreaterThan(0);
  });
});
