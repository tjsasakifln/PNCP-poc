/**
 * STORY-315 AC18+AC19: Alert notification bell with badge + dropdown.
 *
 * Tests for AlertNotificationBell component:
 * - AC18: Badge shows unread count
 * - AC19: Dropdown shows recent alerts
 * - Edge cases: no session, loading, empty alerts
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
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

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: (...args: unknown[]) => mockUseAuth(...args),
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
// Tests
// ---------------------------------------------------------------------------

describe("AlertNotificationBell", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({ session: mockSession });
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders bell icon button", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [] }),
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    expect(screen.getByTestId("notification-bell")).toBeInTheDocument();
  });

  it("AC18: shows badge when there are active alerts", async () => {
    const alertsData = {
      alerts: [
        { id: "a1", name: "Alert 1", active: true },
        { id: "a2", name: "Alert 2", active: true },
        { id: "a3", name: "Alert 3", active: false },
      ],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => alertsData,
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    await waitFor(() => {
      expect(screen.getByTestId("notification-badge")).toBeInTheDocument();
      expect(screen.getByTestId("notification-badge")).toHaveTextContent("2");
    });
  });

  it("AC18: badge shows 9+ when more than 9 active", async () => {
    const alerts = Array.from({ length: 15 }, (_, i) => ({
      id: `a${i}`,
      name: `Alert ${i}`,
      active: true,
    }));

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts }),
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    await waitFor(() => {
      expect(screen.getByTestId("notification-badge")).toHaveTextContent("9+");
    });
  });

  it("does not show badge when no active alerts", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        alerts: [{ id: "a1", name: "Alert 1", active: false }],
      }),
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    await waitFor(() => {
      expect(screen.queryByTestId("notification-badge")).not.toBeInTheDocument();
    });
  });

  it("AC19: clicking bell opens dropdown with alerts", async () => {
    const alertsData = {
      alerts: [
        { id: "a1", name: "Hardware SP", active: true },
        { id: "a2", name: "Software RJ", active: true },
      ],
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => alertsData,
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    // Wait for fetch to complete
    await waitFor(() => {
      expect(screen.getByTestId("notification-badge")).toBeInTheDocument();
    });

    // Click bell
    fireEvent.click(screen.getByTestId("notification-bell"));

    // Dropdown should be visible with alerts
    expect(screen.getByText("Alertas")).toBeInTheDocument();
    expect(screen.getByText("Hardware SP")).toBeInTheDocument();
    expect(screen.getByText("Software RJ")).toBeInTheDocument();
  });

  it("AC19: dropdown shows empty state when no alerts", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [] }),
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    // Click bell
    fireEvent.click(screen.getByTestId("notification-bell"));

    expect(screen.getByText("Nenhum alerta configurado")).toBeInTheDocument();
  });

  it("AC19: dropdown has manage link to /alertas", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [] }),
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    fireEvent.click(screen.getByTestId("notification-bell"));

    expect(screen.getByText("Gerenciar todos os alertas")).toBeInTheDocument();
    expect(screen.getByText("Gerenciar todos os alertas").closest("a")).toHaveAttribute(
      "href",
      "/alertas",
    );
  });

  it("returns null when no session", async () => {
    mockUseAuth.mockReturnValue({ session: null });

    const { container } = render(<AlertNotificationBell />);
    expect(container.firstChild).toBeNull();
  });

  it("handles fetch error gracefully", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    // Should still render the bell
    expect(screen.getByTestId("notification-bell")).toBeInTheDocument();
    // But no badge
    expect(screen.queryByTestId("notification-badge")).not.toBeInTheDocument();
  });

  it("handles array response format", async () => {
    // Backend might return array directly instead of {alerts: [...]}
    const alerts = [
      { id: "a1", name: "Direct Alert", active: true },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => alerts,
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    await waitFor(() => {
      expect(screen.getByTestId("notification-badge")).toHaveTextContent("1");
    });
  });

  it("closes dropdown on second click", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [] }),
    });

    await act(async () => {
      render(<AlertNotificationBell />);
    });

    // Open
    fireEvent.click(screen.getByTestId("notification-bell"));
    expect(screen.getByText("Alertas")).toBeInTheDocument();

    // Close
    fireEvent.click(screen.getByTestId("notification-bell"));
    expect(screen.queryByText("Alertas")).not.toBeInTheDocument();
  });

  it("closes dropdown on outside click", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ alerts: [] }),
    });

    await act(async () => {
      render(
        <div>
          <AlertNotificationBell />
          <button data-testid="outside">Outside</button>
        </div>,
      );
    });

    // Open
    fireEvent.click(screen.getByTestId("notification-bell"));
    expect(screen.getByText("Alertas")).toBeInTheDocument();

    // Click outside
    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(screen.queryByText("Alertas")).not.toBeInTheDocument();
  });
});
