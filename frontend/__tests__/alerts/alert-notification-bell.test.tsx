/**
 * STORY-315 AC18+AC19: Alert notification bell with badge + dropdown.
 *
 * Tests for AlertNotificationBell component:
 * - AC18: Badge shows unread count
 * - AC19: Dropdown shows recent alerts
 * - Edge cases: no session, loading, empty alerts
 *
 * Refactored: Now mocks useAlerts() hook instead of global.fetch (ISSUE-004).
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AlertNotificationBell } from "../../app/components/AlertNotificationBell";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockSession = {
  access_token: "test-token-123",
  user: { id: "user-1", email: "test@test.com" },
};

const mockUseAuth = jest.fn();
const mockUseAlerts = jest.fn();

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: (...args: unknown[]) => mockUseAuth(...args),
}));

jest.mock("../../hooks/useAlerts", () => ({
  useAlerts: (...args: unknown[]) => mockUseAlerts(...args),
}));

jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockAlertsReturn(alerts: Array<{ id: string; name: string; active: boolean }>) {
  mockUseAlerts.mockReturnValue({
    alerts,
    error: null,
    isLoading: false,
    mutate: jest.fn(),
    refresh: jest.fn(),
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AlertNotificationBell", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({ session: mockSession });
    mockAlertsReturn([]);
  });

  it("renders bell icon button", () => {
    render(<AlertNotificationBell />);
    expect(screen.getByTestId("notification-bell")).toBeInTheDocument();
  });

  it("AC18: shows badge when there are active alerts", () => {
    mockAlertsReturn([
      { id: "a1", name: "Alert 1", active: true },
      { id: "a2", name: "Alert 2", active: true },
      { id: "a3", name: "Alert 3", active: false },
    ]);

    render(<AlertNotificationBell />);

    expect(screen.getByTestId("notification-badge")).toBeInTheDocument();
    expect(screen.getByTestId("notification-badge")).toHaveTextContent("2");
  });

  it("AC18: badge shows 9+ when more than 9 active", () => {
    const alerts = Array.from({ length: 15 }, (_, i) => ({
      id: `a${i}`,
      name: `Alert ${i}`,
      active: true,
    }));

    mockAlertsReturn(alerts);
    render(<AlertNotificationBell />);

    expect(screen.getByTestId("notification-badge")).toHaveTextContent("9+");
  });

  it("does not show badge when no active alerts", () => {
    mockAlertsReturn([{ id: "a1", name: "Alert 1", active: false }]);

    render(<AlertNotificationBell />);

    expect(screen.queryByTestId("notification-badge")).not.toBeInTheDocument();
  });

  it("AC19: clicking bell opens dropdown with alerts", () => {
    mockAlertsReturn([
      { id: "a1", name: "Hardware SP", active: true },
      { id: "a2", name: "Software RJ", active: true },
    ]);

    render(<AlertNotificationBell />);
    fireEvent.click(screen.getByTestId("notification-bell"));

    expect(screen.getByText("Alertas")).toBeInTheDocument();
    expect(screen.getByText("Hardware SP")).toBeInTheDocument();
    expect(screen.getByText("Software RJ")).toBeInTheDocument();
  });

  it("AC19: dropdown shows empty state when no alerts", () => {
    render(<AlertNotificationBell />);
    fireEvent.click(screen.getByTestId("notification-bell"));

    expect(screen.getByText("Nenhum alerta configurado")).toBeInTheDocument();
  });

  it("AC19: dropdown has manage link to /alertas", () => {
    render(<AlertNotificationBell />);
    fireEvent.click(screen.getByTestId("notification-bell"));

    expect(screen.getByText("Gerenciar todos os alertas")).toBeInTheDocument();
    expect(screen.getByText("Gerenciar todos os alertas").closest("a")).toHaveAttribute(
      "href",
      "/alertas",
    );
  });

  it("returns null when no session", () => {
    mockUseAuth.mockReturnValue({ session: null });
    const { container } = render(<AlertNotificationBell />);
    expect(container.firstChild).toBeNull();
  });

  it("shows bell with no badge when useAlerts returns empty", () => {
    mockAlertsReturn([]);
    render(<AlertNotificationBell />);

    expect(screen.getByTestId("notification-bell")).toBeInTheDocument();
    expect(screen.queryByTestId("notification-badge")).not.toBeInTheDocument();
  });

  it("closes dropdown on second click", () => {
    render(<AlertNotificationBell />);

    // Open
    fireEvent.click(screen.getByTestId("notification-bell"));
    expect(screen.getByText("Alertas")).toBeInTheDocument();

    // Close
    fireEvent.click(screen.getByTestId("notification-bell"));
    expect(screen.queryByText("Alertas")).not.toBeInTheDocument();
  });

  it("closes dropdown on outside click", () => {
    render(
      <div>
        <AlertNotificationBell />
        <button data-testid="outside">Outside</button>
      </div>,
    );

    // Open
    fireEvent.click(screen.getByTestId("notification-bell"));
    expect(screen.getByText("Alertas")).toBeInTheDocument();

    // Click outside
    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(screen.queryByText("Alertas")).not.toBeInTheDocument();
  });
});
