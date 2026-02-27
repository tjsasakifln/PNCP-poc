/**
 * Tests for subscription cancellation modal (GTM-FIX-006 AC16).
 * Updated for UX-308 4-step flow — covers basic rendering and backward compat.
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
    expect(screen.getByText("Por que deseja cancelar?")).toBeInTheDocument();
  });

  it("does not render when isOpen is false", () => {
    render(<CancelSubscriptionModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText("Por que deseja cancelar?")).not.toBeInTheDocument();
  });

  it("shows retention benefits list on confirm step", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    // Navigate to confirm step
    fireEvent.click(screen.getByText("Outro motivo"));
    fireEvent.click(screen.getByText("Continuar"));

    expect(screen.getByText("1000 análises mensais")).toBeInTheDocument();
    expect(screen.getByText(/Histórico completo/)).toBeInTheDocument();
    expect(screen.getByText(/Exportação Excel/)).toBeInTheDocument();
    expect(screen.getByText(/Filtros avançados/)).toBeInTheDocument();
  });

  it("shows cancellation reasons on first step", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    expect(screen.getByText("Está caro para mim")).toBeInTheDocument();
    expect(screen.getByText("Não estou usando o suficiente")).toBeInTheDocument();
  });

  it("calls onClose when 'Voltar' is clicked on step 1", () => {
    render(<CancelSubscriptionModal {...defaultProps} />);
    fireEvent.click(screen.getByText("Voltar"));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it("calls API and onCancelled on successful cancellation", async () => {
    const mockEndsAt = "2026-03-15T00:00:00Z";
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true, ends_at: mockEndsAt, message: "Cancelado" }),
    });

    render(<CancelSubscriptionModal {...defaultProps} />);

    // Navigate: reason → confirm → cancel
    fireEvent.click(screen.getByText("Outro motivo"));
    fireEvent.click(screen.getByText("Continuar"));
    fireEvent.click(screen.getByRole("checkbox"));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
    });

    await waitFor(() => {
      expect(defaultProps.onCancelled).toHaveBeenCalledWith(mockEndsAt);
    });

    expect(toast.success).toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledWith("/api/subscriptions/cancel", expect.objectContaining({
      method: "POST",
    }));
  });

  it("shows error message on API failure", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Nenhuma assinatura ativa encontrada" }),
    });

    render(<CancelSubscriptionModal {...defaultProps} />);

    // Navigate: reason → confirm → cancel
    fireEvent.click(screen.getByText("Outro motivo"));
    fireEvent.click(screen.getByText("Continuar"));
    fireEvent.click(screen.getByRole("checkbox"));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
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

    // Navigate: reason → confirm → cancel
    fireEvent.click(screen.getByText("Outro motivo"));
    fireEvent.click(screen.getByText("Continuar"));
    fireEvent.click(screen.getByRole("checkbox"));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
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
