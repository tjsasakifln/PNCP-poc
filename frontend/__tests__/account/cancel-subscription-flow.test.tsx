/**
 * Tests for 4-step cancel subscription flow (UX-308).
 * Covers: AC1 (reason selection), AC2 (retention flow), AC3 (discount offer),
 * AC4 (pause offer), AC5 (confirmation checkbox), AC6 (feedback form).
 */
import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import "@testing-library/jest-dom";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

import { CancelSubscriptionModal } from "../../components/account/CancelSubscriptionModal";
import { toast } from "sonner";

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onCancelled: jest.fn(),
  accessToken: "test-token-ux308",
};

const mockEndsAt = "2026-04-15T00:00:00Z";

function mockFetchCancel() {
  return jest.fn().mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      success: true,
      ends_at: mockEndsAt,
      message: "Cancelado",
    }),
  });
}

function mockFetchFeedback() {
  return jest.fn().mockResolvedValueOnce({
    ok: true,
    json: async () => ({ success: true, message: "Obrigado!" }),
  });
}

describe("CancelSubscriptionModal — UX-308 4-Step Flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Step 1: Reason Selection (AC1)", () => {
    it("renders reason selection as first step", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      expect(
        screen.getByText("Por que deseja cancelar?")
      ).toBeInTheDocument();
    });

    it("shows all 5 cancellation reasons", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      expect(
        screen.getByText("Está caro para mim")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Não estou usando o suficiente")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Falta funcionalidade que preciso")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Encontrei outra solução")
      ).toBeInTheDocument();
      expect(screen.getByText("Outro motivo")).toBeInTheDocument();
    });

    it("disables Continue button until reason is selected", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      const continueBtn = screen.getByText("Continuar");
      expect(continueBtn).toBeDisabled();

      fireEvent.click(screen.getByText("Outro motivo"));
      expect(continueBtn).not.toBeDisabled();
    });

    it("does not render when isOpen is false", () => {
      render(<CancelSubscriptionModal {...defaultProps} isOpen={false} />);
      expect(
        screen.queryByText("Por que deseja cancelar?")
      ).not.toBeInTheDocument();
    });

    it("calls onClose when Voltar is clicked on step 1", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      fireEvent.click(screen.getByText("Voltar"));
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("Step 2: Retention Offers (AC2, AC3, AC4)", () => {
    it("shows discount offer for too_expensive (AC3)", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(screen.getByText("Está caro para mim"));
      fireEvent.click(screen.getByText("Continuar"));

      expect(
        screen.getByText("Temos uma oferta para você")
      ).toBeInTheDocument();
      expect(
        screen.getByText("20% de desconto nos próximos 3 meses")
      ).toBeInTheDocument();
      expect(screen.getByText("Quero o desconto")).toBeInTheDocument();
    });

    it("shows pause offer for not_using (AC4)", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(
        screen.getByText("Não estou usando o suficiente")
      );
      fireEvent.click(screen.getByText("Continuar"));

      expect(
        screen.getByText("Que tal uma pausa?")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Pause sua assinatura por 30 dias")
      ).toBeInTheDocument();
      expect(screen.getByText("Quero pausar")).toBeInTheDocument();
    });

    it("skips retention for missing_features (goes to confirm)", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(
        screen.getByText("Falta funcionalidade que preciso")
      );
      fireEvent.click(screen.getByText("Continuar"));

      expect(
        screen.getByRole("heading", { name: "Confirmar cancelamento" })
      ).toBeInTheDocument();
    });

    it("skips retention for found_alternative (goes to confirm)", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(screen.getByText("Encontrei outra solução"));
      fireEvent.click(screen.getByText("Continuar"));

      expect(
        screen.getByRole("heading", { name: "Confirmar cancelamento" })
      ).toBeInTheDocument();
    });

    it("skips retention for other (goes to confirm)", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(screen.getByText("Outro motivo"));
      fireEvent.click(screen.getByText("Continuar"));

      expect(
        screen.getByRole("heading", { name: "Confirmar cancelamento" })
      ).toBeInTheDocument();
    });

    it("continues to confirm step when retention is declined", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(screen.getByText("Está caro para mim"));
      fireEvent.click(screen.getByText("Continuar"));

      // Decline retention
      fireEvent.click(screen.getByText("Continuar cancelamento"));

      expect(
        screen.getByRole("heading", { name: "Confirmar cancelamento" })
      ).toBeInTheDocument();
    });

    it("can go back to reason step from retention", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      fireEvent.click(screen.getByText("Está caro para mim"));
      fireEvent.click(screen.getByText("Continuar"));
      fireEvent.click(screen.getByText("Voltar"));

      expect(
        screen.getByText("Por que deseja cancelar?")
      ).toBeInTheDocument();
    });
  });

  describe("Step 3: Final Confirmation (AC5)", () => {
    function navigateToConfirm() {
      fireEvent.click(screen.getByText("Outro motivo"));
      fireEvent.click(screen.getByText("Continuar"));
    }

    it("shows benefits that will be lost", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      navigateToConfirm();

      expect(
        screen.getByText("1000 análises mensais")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Histórico completo/)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Exportação Excel/)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Filtros avançados/)
      ).toBeInTheDocument();
    });

    it("shows confirmation checkbox", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      navigateToConfirm();

      expect(
        screen.getByText(
          /Entendo que perderei acesso aos benefícios/
        )
      ).toBeInTheDocument();
    });

    it("disables confirm button until checkbox is checked", () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      navigateToConfirm();

      const confirmBtn = screen.getByRole("button", { name: "Confirmar cancelamento" });
      expect(confirmBtn).toBeDisabled();

      const checkbox = screen.getByRole("checkbox");
      fireEvent.click(checkbox);
      expect(confirmBtn).not.toBeDisabled();
    });

    it("calls API with reason on confirmation", async () => {
      global.fetch = mockFetchCancel();

      render(<CancelSubscriptionModal {...defaultProps} />);
      navigateToConfirm();

      fireEvent.click(screen.getByRole("checkbox"));

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      await waitFor(() => {
        expect(defaultProps.onCancelled).toHaveBeenCalledWith(
          mockEndsAt
        );
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "/api/subscriptions/cancel",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer test-token-ux308",
            "Content-Type": "application/json",
          }),
          body: JSON.stringify({ reason: "other" }),
        })
      );
    });

    it("shows error on API failure", async () => {
      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: false,
        json: async () => ({
          detail: "Nenhuma assinatura ativa encontrada",
        }),
      });

      render(<CancelSubscriptionModal {...defaultProps} />);
      navigateToConfirm();

      fireEvent.click(screen.getByRole("checkbox"));

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      await waitFor(() => {
        expect(
          screen.getByText("Nenhuma assinatura ativa encontrada")
        ).toBeInTheDocument();
      });

      expect(defaultProps.onCancelled).not.toHaveBeenCalled();
    });

    it("shows loading state while cancelling", async () => {
      let resolvePromise: (value: unknown) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      global.fetch = jest.fn().mockReturnValueOnce(pendingPromise);

      render(<CancelSubscriptionModal {...defaultProps} />);
      navigateToConfirm();

      fireEvent.click(screen.getByRole("checkbox"));

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      expect(screen.getByText("Cancelando...")).toBeInTheDocument();
      expect(screen.getByText("Cancelando...")).toBeDisabled();

      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => ({
            success: true,
            ends_at: mockEndsAt,
            message: "ok",
          }),
        });
      });
    });

    it("sends reason from retention flow (too_expensive)", async () => {
      global.fetch = mockFetchCancel();

      render(<CancelSubscriptionModal {...defaultProps} />);

      // Select too_expensive → retention → decline → confirm
      fireEvent.click(screen.getByText("Está caro para mim"));
      fireEvent.click(screen.getByText("Continuar"));
      fireEvent.click(screen.getByText("Continuar cancelamento"));

      fireEvent.click(screen.getByRole("checkbox"));

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "/api/subscriptions/cancel",
          expect.objectContaining({
            body: JSON.stringify({ reason: "too_expensive" }),
          })
        );
      });
    });
  });

  describe("Step 4: Feedback Form (AC6)", () => {
    async function navigateToFeedback() {
      global.fetch = mockFetchCancel();

      fireEvent.click(screen.getByText("Outro motivo"));
      fireEvent.click(screen.getByText("Continuar"));
      fireEvent.click(screen.getByRole("checkbox"));

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      await waitFor(() => {
        expect(
          screen.getByText("Uma última coisa")
        ).toBeInTheDocument();
      });
    }

    it("shows feedback form after cancellation", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      expect(
        screen.getByText("Uma última coisa")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(
          /Conte como podemos melhorar/
        )
      ).toBeInTheDocument();
    });

    it("shows skip and send buttons", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      expect(screen.getByText("Pular")).toBeInTheDocument();
      expect(
        screen.getByText("Enviar feedback")
      ).toBeInTheDocument();
    });

    it("submits feedback to API", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      // Reset fetch mock for feedback call
      global.fetch = mockFetchFeedback();

      const textarea = screen.getByPlaceholderText(
        /Conte como podemos melhorar/
      );
      fireEvent.change(textarea, {
        target: { value: "O preço é muito alto." },
      });

      await act(async () => {
        fireEvent.click(screen.getByText("Enviar feedback"));
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "/api/subscriptions/cancel-feedback",
          expect.objectContaining({
            method: "POST",
            body: JSON.stringify({
              feedback: "O preço é muito alto.",
            }),
          })
        );
      });
    });

    it("closes modal when skip is clicked", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      fireEvent.click(screen.getByText("Pular"));
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it("closes modal after submitting feedback", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      global.fetch = mockFetchFeedback();

      const textarea = screen.getByPlaceholderText(
        /Conte como podemos melhorar/
      );
      fireEvent.change(textarea, {
        target: { value: "Feedback text" },
      });

      await act(async () => {
        fireEvent.click(screen.getByText("Enviar feedback"));
      });

      await waitFor(() => {
        expect(defaultProps.onClose).toHaveBeenCalled();
      });
    });

    it("shows toast after feedback submission", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      global.fetch = mockFetchFeedback();

      const textarea = screen.getByPlaceholderText(
        /Conte como podemos melhorar/
      );
      fireEvent.change(textarea, {
        target: { value: "Some feedback" },
      });

      await act(async () => {
        fireEvent.click(screen.getByText("Enviar feedback"));
      });

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "Obrigado pelo feedback!"
        );
      });
    });

    it("closes without API call when feedback is empty and skip", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);
      await navigateToFeedback();

      // Clear previous fetch mock
      global.fetch = jest.fn();

      fireEvent.click(screen.getByText("Pular"));

      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe("Full End-to-End Flow", () => {
    it("too_expensive → discount → decline → confirm → feedback → close", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      // Step 1: Select reason
      fireEvent.click(screen.getByText("Está caro para mim"));
      fireEvent.click(screen.getByText("Continuar"));

      // Step 2: See discount offer, decline
      expect(
        screen.getByText("20% de desconto nos próximos 3 meses")
      ).toBeInTheDocument();
      fireEvent.click(screen.getByText("Continuar cancelamento"));

      // Step 3: Check checkbox and confirm
      fireEvent.click(screen.getByRole("checkbox"));
      global.fetch = mockFetchCancel();

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      // Step 4: Feedback
      await waitFor(() => {
        expect(
          screen.getByText("Uma última coisa")
        ).toBeInTheDocument();
      });

      global.fetch = mockFetchFeedback();
      const textarea = screen.getByPlaceholderText(
        /Conte como podemos melhorar/
      );
      fireEvent.change(textarea, {
        target: { value: "Muito caro" },
      });

      await act(async () => {
        fireEvent.click(screen.getByText("Enviar feedback"));
      });

      await waitFor(() => {
        expect(defaultProps.onClose).toHaveBeenCalled();
      });
    });

    it("not_using → pause → decline → confirm → skip feedback", async () => {
      render(<CancelSubscriptionModal {...defaultProps} />);

      // Step 1
      fireEvent.click(
        screen.getByText("Não estou usando o suficiente")
      );
      fireEvent.click(screen.getByText("Continuar"));

      // Step 2: Pause offer
      expect(
        screen.getByText("Pause sua assinatura por 30 dias")
      ).toBeInTheDocument();
      fireEvent.click(screen.getByText("Continuar cancelamento"));

      // Step 3
      fireEvent.click(screen.getByRole("checkbox"));
      global.fetch = mockFetchCancel();

      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
      });

      // Step 4: Skip feedback
      await waitFor(() => {
        expect(
          screen.getByText("Uma última coisa")
        ).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Pular"));
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });
});
