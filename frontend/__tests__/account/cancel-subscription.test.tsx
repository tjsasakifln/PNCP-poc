/**
 * Tests for subscription cancellation flow (GTM-FIX-006 AC16).
 */
import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

import { CancelSubscriptionModal } from "../../components/account/CancelSubscriptionModal";
import { toast } from "sonner";

describe("CancelSubscriptionModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onCancelled: jest.fn(),
    accessToken: "test-token-123",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders when isOpen is true", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    expect(screen.getByText("Tem certeza que deseja cancelar?")).toBeInTheDocument();
  });

  it("does not render when isOpen is false", () => {
    render(<CancelSubscriptionModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText("Tem certeza que deseja cancelar?")).not.toBeInTheDocument();
  });

  it("shows retention benefits list", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    expect(screen.getByText("1000 análises mensais")).toBeInTheDocument();
    expect(screen.getByText(/Histórico de 5 anos/)).toBeInTheDocument();
    expect(screen.getByText(/Exportação Excel/)).toBeInTheDocument();
    expect(screen.getByText(/Filtros avançados/)).toBeInTheDocument();
  });

  it("shows support contact link", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    expect(screen.getByText("Falar com Suporte")).toBeInTheDocument();
  });

  it("calls onClose when 'Manter acesso' is clicked", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    fireEvent.click(screen.getByText("Manter acesso"));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it("calls API and onCancelled on successful cancellation", async () => {
    const mockEndsAt = "2026-03-15T00:00:00Z";
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, ends_at: mockEndsAt, message: "Cancelado" }),
    });

    render(<CancelSubscriptionModal {...defaultProps} />);

    await act(async () => {
      fireEvent.click(screen.getByText("Confirmar cancelamento"));
    });

    await waitFor(() => {
      expect(defaultProps.onCancelled).toHaveBeenCalledWith(mockEndsAt);
    });

    expect(toast.success).toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledWith("/api/subscriptions/cancel", {
      method: "POST",
      headers: {
        Authorization: "Bearer test-token-123",
      },
    });
  });

  it("shows error message on API failure", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Nenhuma assinatura ativa encontrada" }),
    });

    render(<CancelSubscriptionModal {...defaultProps} />);

    await act(async () => {
      fireEvent.click(screen.getByText("Confirmar cancelamento"));
    });

    await waitFor(() => {
      expect(screen.getByText("Nenhuma assinatura ativa encontrada")).toBeInTheDocument();
    });

    expect(defaultProps.onCancelled).not.toHaveBeenCalled();
  });

  it("disables buttons while cancelling", async () => {
    let resolvePromise: (value: unknown) => void;
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    global.fetch = jest.fn().mockReturnValueOnce(pendingPromise);

    render(<CancelSubscriptionModal {...defaultProps} />);

    await act(async () => {
      fireEvent.click(screen.getByText("Confirmar cancelamento"));
    });

    expect(screen.getByText("Cancelando...")).toBeInTheDocument();
    expect(screen.getByText("Cancelando...")).toBeDisabled();

    // Resolve to cleanup
    await act(async () => {
      resolvePromise!({
        ok: true,
        json: async () => ({ success: true, ends_at: "2026-03-15", message: "ok" }),
      });
    });
  });
});
