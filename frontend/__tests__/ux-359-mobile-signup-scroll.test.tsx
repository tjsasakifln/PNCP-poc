/**
 * UX-359 — Mobile Signup Scroll Discoverability
 *
 * Tests:
 * AC1: Sidebar uses min-h-[50vh] on mobile, not min-h-screen
 * AC2: Chevron scroll indicator renders on mobile
 * AC3: Auto-scroll via ?scroll=form URL param
 * AC4: Responsive layout optimizations (padding, flex-wrap)
 * AC5: Login page gets same corrections
 * AC6: No regressions on desktop layout
 */
import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Next.js mocks ─────────────────────────────────────────────────────────────
const mockPush = jest.fn();
const mockSearchParams = new URLSearchParams();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => "/signup",
}));

jest.mock("next/link", () => {
  const Link = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
  Link.displayName = "Link";
  return Link;
});

// ─── Auth + Analytics mocks ────────────────────────────────────────────────────
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    signUpWithEmail: jest.fn(),
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
  getStoredUTMParams: () => ({}),
}));

// ─── Sonner toast mock ─────────────────────────────────────────────────────────
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// ─── error-messages mock ───────────────────────────────────────────────────────
jest.mock("../lib/error-messages", () => ({
  translateAuthError: (msg: string) => msg,
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// ─── Imports (after mocks) ─────────────────────────────────────────────────────
import InstitutionalSidebar from "../app/components/InstitutionalSidebar";
import SignupPage from "../app/signup/page";
import LoginPage from "../app/login/page";

// ─── Helpers ───────────────────────────────────────────────────────────────────
const originalScrollIntoView = HTMLElement.prototype.scrollIntoView;

beforeEach(() => {
  jest.clearAllMocks();
  HTMLElement.prototype.scrollIntoView = jest.fn();
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ confirmed: false }),
  });
  // Reset window.location.search
  Object.defineProperty(window, "location", {
    writable: true,
    value: { ...window.location, search: "" },
  });
});

afterEach(() => {
  HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
});

// ─── AC1: Sidebar height tests ─────────────────────────────────────────────────
describe("AC1 — Sidebar with reduced mobile height", () => {
  it("uses min-h-[50vh] class instead of min-h-screen", () => {
    const { container } = render(
      <InstitutionalSidebar variant="signup" />
    );
    const sidebar = container.firstChild as HTMLElement;
    expect(sidebar.className).toContain("min-h-[50vh]");
    expect(sidebar.className).not.toContain("min-h-screen");
  });

  it("preserves md:min-h-0 for desktop layout", () => {
    const { container } = render(
      <InstitutionalSidebar variant="signup" />
    );
    const sidebar = container.firstChild as HTMLElement;
    expect(sidebar.className).toContain("md:min-h-0");
  });

  it("sidebar content (headline, benefits, stats) renders correctly", () => {
    render(<InstitutionalSidebar variant="signup" />);
    expect(screen.getByText(/melhores oportunidades/i)).toBeInTheDocument();
    expect(screen.getByText(/7 dias do produto completo/i)).toBeInTheDocument();
    expect(screen.getByText("27")).toBeInTheDocument();
  });
});

// ─── AC2: Scroll indicator tests ────────────────────────────────────────────────
describe("AC2 — Chevron scroll indicator", () => {
  it("renders chevron when scrollTargetId is provided", () => {
    render(<InstitutionalSidebar variant="signup" scrollTargetId="signup-form" />);
    expect(screen.getByTestId("scroll-chevron")).toBeInTheDocument();
  });

  it("does NOT render chevron when scrollTargetId is not provided", () => {
    render(<InstitutionalSidebar variant="signup" />);
    expect(screen.queryByTestId("scroll-chevron")).not.toBeInTheDocument();
  });

  it("chevron has md:hidden class (mobile only)", () => {
    render(<InstitutionalSidebar variant="signup" scrollTargetId="signup-form" />);
    const chevron = screen.getByTestId("scroll-chevron");
    expect(chevron.className).toContain("md:hidden");
  });

  it("chevron has bounce animation class", () => {
    render(<InstitutionalSidebar variant="signup" scrollTargetId="signup-form" />);
    const chevron = screen.getByTestId("scroll-chevron");
    expect(chevron.className).toContain("animate-bounce-gentle");
  });

  it("chevron disappears after scrolling >50px", () => {
    render(<InstitutionalSidebar variant="signup" scrollTargetId="signup-form" />);
    expect(screen.getByTestId("scroll-chevron")).toBeInTheDocument();

    // Simulate scroll >50px
    act(() => {
      Object.defineProperty(window, "scrollY", { value: 100, writable: true });
      window.dispatchEvent(new Event("scroll"));
    });

    expect(screen.queryByTestId("scroll-chevron")).not.toBeInTheDocument();
  });

  it("chevron reappears when scrolling back to top", () => {
    render(<InstitutionalSidebar variant="signup" scrollTargetId="signup-form" />);

    // Scroll down
    act(() => {
      Object.defineProperty(window, "scrollY", { value: 100, writable: true });
      window.dispatchEvent(new Event("scroll"));
    });
    expect(screen.queryByTestId("scroll-chevron")).not.toBeInTheDocument();

    // Scroll back up
    act(() => {
      Object.defineProperty(window, "scrollY", { value: 20, writable: true });
      window.dispatchEvent(new Event("scroll"));
    });
    expect(screen.getByTestId("scroll-chevron")).toBeInTheDocument();
  });

  it("chevron click calls scrollIntoView on target element", () => {
    const mockScrollIntoView = jest.fn();
    const target = document.createElement("div");
    target.id = "signup-form";
    target.scrollIntoView = mockScrollIntoView;
    document.body.appendChild(target);

    render(<InstitutionalSidebar variant="signup" scrollTargetId="signup-form" />);
    fireEvent.click(screen.getByTestId("scroll-chevron"));

    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });

    document.body.removeChild(target);
  });
});

// ─── AC3: Auto-scroll via URL param ────────────────────────────────────────────
describe("AC3 — Auto-scroll to form", () => {
  it("signup page auto-scrolls when ?scroll=form is present", async () => {
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...window.location, search: "?scroll=form" },
    });

    render(<SignupPage />);

    await waitFor(() => {
      // The formRef element should have scrollIntoView called
      expect(HTMLElement.prototype.scrollIntoView).toHaveBeenCalled();
    }, { timeout: 1000 });
  });

  it("signup form container has scroll-mt-4 class", () => {
    render(<SignupPage />);
    const formContainer = document.getElementById("signup-form");
    expect(formContainer).toBeInTheDocument();
    expect(formContainer?.className).toContain("scroll-mt-4");
  });

  it("signup form container has id='signup-form'", () => {
    render(<SignupPage />);
    expect(document.getElementById("signup-form")).toBeInTheDocument();
  });
});

// ─── AC4: Layout responsive optimization ────────────────────────────────────────
describe("AC4 — Responsive layout optimization", () => {
  it("sidebar uses p-4 py-6 on mobile (reduced padding)", () => {
    const { container } = render(
      <InstitutionalSidebar variant="signup" />
    );
    const sidebar = container.firstChild as HTMLElement;
    expect(sidebar.className).toContain("p-4");
    expect(sidebar.className).toContain("py-6");
  });

  it("sidebar uses md:p-12 for desktop (unchanged)", () => {
    const { container } = render(
      <InstitutionalSidebar variant="signup" />
    );
    const sidebar = container.firstChild as HTMLElement;
    expect(sidebar.className).toContain("md:p-12");
  });

  it("stats row uses flex-wrap for narrow screens", () => {
    const { container } = render(
      <InstitutionalSidebar variant="signup" />
    );
    // Find the stats container by looking for the flex-wrap class
    const statsContainer = container.querySelector(".flex.flex-wrap");
    expect(statsContainer).toBeInTheDocument();
  });

  it("signup form container uses py-4 on mobile, md:py-8 on desktop", () => {
    render(<SignupPage />);
    const formContainer = document.getElementById("signup-form");
    expect(formContainer?.className).toContain("py-4");
    expect(formContainer?.className).toContain("md:py-8");
  });
});

// ─── AC5: Login page corrections ────────────────────────────────────────────────
describe("AC5 — Login page with same corrections", () => {
  it("login page renders with institutional sidebar", () => {
    render(<LoginPage />);
    // Login page should render the institutional sidebar content
    expect(screen.getByText(/antes da concorrência/i)).toBeInTheDocument();
  });

  it("login form container has id='login-form'", () => {
    render(<LoginPage />);
    expect(document.getElementById("login-form")).toBeInTheDocument();
  });

  it("login form container has scroll-mt-4 class", () => {
    render(<LoginPage />);
    const formContainer = document.getElementById("login-form");
    expect(formContainer?.className).toContain("scroll-mt-4");
  });
});

// ─── AC6: Desktop layout preservation ───────────────────────────────────────────
describe("AC6 — Desktop layout preserved (no regressions)", () => {
  it("signup page uses flex-col md:flex-row layout", () => {
    const { container } = render(<SignupPage />);
    const outerDiv = container.querySelector(".flex.flex-col.md\\:flex-row");
    expect(outerDiv).toBeInTheDocument();
  });

  it("sidebar has w-full md:w-1/2 classes", () => {
    const { container } = render(<SignupPage />);
    // The sidebar should have w-full md:w-1/2
    const sidebar = container.querySelector('[class*="min-h-[50vh]"]');
    expect(sidebar?.className).toContain("w-full");
    expect(sidebar?.className).toContain("md:w-1/2");
  });

  it("sidebar has relative positioning for chevron", () => {
    const { container } = render(
      <InstitutionalSidebar variant="signup" scrollTargetId="test" />
    );
    const sidebar = container.firstChild as HTMLElement;
    expect(sidebar.className).toContain("relative");
  });

  it("login page maintains side-by-side layout on desktop", () => {
    const { container } = render(<LoginPage />);
    const outerDiv = container.querySelector(".flex.flex-col.md\\:flex-row");
    expect(outerDiv).toBeInTheDocument();
  });
});
