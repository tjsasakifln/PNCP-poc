/**
 * GTM-FIX-009: Email Confirmation Recovery Tests
 *
 * AC15: test_resend_button_countdown
 * AC16: test_auto_redirect_on_confirmation
 */

import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import SignupPage from "@/app/signup/page";

// Mock useRouter
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
}));

// Mock useAuth
const mockSignUpWithEmail = jest.fn();
const mockSignInWithGoogle = jest.fn();
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({
    signUpWithEmail: mockSignUpWithEmail,
    signInWithGoogle: mockSignInWithGoogle,
  }),
}));

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

// Import after mock to get the mocked version
import { toast as mockToast } from "sonner";

// Mock Next.js Link
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock analytics
jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
  getStoredUTMParams: () => ({}),
}));

// Mock error messages
jest.mock("../../lib/error-messages", () => ({
  getUserFriendlyError: (err: unknown) =>
    err instanceof Error ? err.message : String(err),
}));

// Helper to fill form, scroll consent, and submit
async function signupAndGetToConfirmation(
  email = "test@example.com"
) {
  render(<SignupPage />);

  // Fill required fields
  const nameInput = screen.getByLabelText(/Nome completo/i);
  const companyInput = screen.getByLabelText(/Empresa/i);
  const sectorSelect = screen.getByLabelText(/Setor de atuação/i);
  const emailInput = screen.getByPlaceholderText(/seu@email.com/i);
  const passwordInput = screen.getByPlaceholderText(
    /Min\. 8 caracteres, 1 maiúscula, 1 número/i
  );
  const confirmPasswordInput = screen.getByPlaceholderText(
    /Digite a senha novamente/i
  );
  const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);

  await act(async () => {
    fireEvent.change(nameInput, { target: { value: "Test User" } });
    fireEvent.change(companyInput, { target: { value: "Test Co" } });
    fireEvent.change(sectorSelect, { target: { value: "informatica" } });
    fireEvent.change(emailInput, { target: { value: email } });
    fireEvent.change(passwordInput, { target: { value: "Password123" } });
    fireEvent.change(confirmPasswordInput, {
      target: { value: "Password123" },
    });
    fireEvent.change(phoneInput, { target: { value: "11999999999" } });
  });

  // Scroll to bottom
  const scrollBox = screen.getByTestId("consent-scroll-box");
  await act(async () => {
    Object.defineProperty(scrollBox, "scrollHeight", {
      value: 500,
      configurable: true,
    });
    Object.defineProperty(scrollBox, "clientHeight", {
      value: 144,
      configurable: true,
    });
    Object.defineProperty(scrollBox, "scrollTop", {
      value: 360,
      configurable: true,
    });
    fireEvent.scroll(scrollBox);
  });

  // Check consent
  const consentCheckbox = screen.getByRole("checkbox");
  await act(async () => {
    fireEvent.click(consentCheckbox);
  });

  // Submit
  const submitButton = screen.getByRole("button", {
    name: /Criar conta$/i,
  });
  await act(async () => {
    fireEvent.click(submitButton);
  });

  // Wait for success screen
  await waitFor(() => {
    expect(screen.getByText(/Confirme seu email/i)).toBeInTheDocument();
  });
}

describe("GTM-FIX-009: Email Confirmation Screen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockSignUpWithEmail.mockResolvedValue(undefined);
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("AC15: Resend button countdown", () => {
    it("should show resend button disabled with countdown after signup", async () => {
      await signupAndGetToConfirmation();

      const resendButton = screen.getByTestId("resend-button");
      expect(resendButton).toBeDisabled();
      expect(resendButton).toHaveTextContent(/Reenviar em \d+s/);
    });

    it("should count down from 60s", async () => {
      await signupAndGetToConfirmation();

      const resendButton = screen.getByTestId("resend-button");
      expect(resendButton).toHaveTextContent("Reenviar em 60s");

      // Advance 10 seconds
      await act(async () => {
        jest.advanceTimersByTime(10000);
      });

      expect(resendButton).toHaveTextContent("Reenviar em 50s");
    });

    it("should enable resend button after countdown reaches 0", async () => {
      await signupAndGetToConfirmation();

      const resendButton = screen.getByTestId("resend-button");
      expect(resendButton).toBeDisabled();

      // Advance 60 seconds
      await act(async () => {
        jest.advanceTimersByTime(60000);
      });

      expect(resendButton).not.toBeDisabled();
      expect(resendButton).toHaveTextContent("Reenviar email");
    });

    it("should call resend API and reset countdown on click", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          message: "Email reenviado!",
        }),
      });

      await signupAndGetToConfirmation();

      // Advance past countdown
      await act(async () => {
        jest.advanceTimersByTime(60000);
      });

      const resendButton = screen.getByTestId("resend-button");
      expect(resendButton).not.toBeDisabled();

      // Click resend
      await act(async () => {
        fireEvent.click(resendButton);
      });

      // Should have called the resend endpoint
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/auth/resend-confirmation",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ email: "test@example.com" }),
        })
      );

      // Toast should show success
      expect(mockToast.success).toHaveBeenCalledWith(
        "Email reenviado! Verifique sua caixa de entrada."
      );

      // Button should be disabled again with new countdown
      expect(resendButton).toBeDisabled();
    });

    it("should show error toast when resend fails", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "Aguarde 60s antes de reenviar." }),
      });

      await signupAndGetToConfirmation();

      await act(async () => {
        jest.advanceTimersByTime(60000);
      });

      const resendButton = screen.getByTestId("resend-button");
      await act(async () => {
        fireEvent.click(resendButton);
      });

      expect(mockToast.error).toHaveBeenCalledWith(
        "Aguarde 60s antes de reenviar."
      );
    });
  });

  describe("AC16: Auto-redirect on confirmation", () => {
    it("should poll for confirmation status every 5s", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ confirmed: false }),
      });

      await signupAndGetToConfirmation();

      // First poll at 5s
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // fetch is called for polling (status check)
      const statusCalls = (global.fetch as jest.Mock).mock.calls.filter(
        (call: string[]) => call[0].includes("/api/auth/status")
      );
      expect(statusCalls.length).toBeGreaterThanOrEqual(1);
    });

    it("should show confirmed message and redirect when email is confirmed", async () => {
      // First poll returns not confirmed, second returns confirmed
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ confirmed: false }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ confirmed: true, user_id: "user-123" }),
        });

      await signupAndGetToConfirmation();

      // First poll — not confirmed
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // Second poll — confirmed
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(screen.getByText(/Email confirmado!/i)).toBeInTheDocument();
      });

      expect(mockToast.success).toHaveBeenCalledWith(
        "Email confirmado! Redirecionando..."
      );

      // Redirect after 1.5s
      await act(async () => {
        jest.advanceTimersByTime(1500);
      });

      expect(mockPush).toHaveBeenCalledWith("/onboarding");
    });
  });

  describe("Confirmation screen UI elements", () => {
    it("should show polling indicator", async () => {
      await signupAndGetToConfirmation();

      expect(
        screen.getByTestId("polling-indicator")
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("polling-indicator")
      ).toHaveTextContent(/Aguardando confirmação/);
    });

    it("should show spam helper section", async () => {
      await signupAndGetToConfirmation();

      expect(
        screen.getByText(/Não recebeu o email\?/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Verifique sua caixa de spam/i)
      ).toBeInTheDocument();
    });

    it("should show change email link", async () => {
      await signupAndGetToConfirmation();

      const changeEmailLink = screen.getByTestId("change-email-link");
      expect(changeEmailLink).toBeInTheDocument();
      expect(changeEmailLink).toHaveTextContent(/Alterar email/);
    });

    it("should go back to form when clicking 'Alterar email'", async () => {
      await signupAndGetToConfirmation();

      const changeEmailLink = screen.getByTestId("change-email-link");
      await act(async () => {
        fireEvent.click(changeEmailLink);
      });

      // Should be back on the signup form
      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: /Criar conta/i })
        ).toBeInTheDocument();
      });
    });

    it("should display the submitted email on confirmation screen", async () => {
      await signupAndGetToConfirmation("custom@email.com");

      expect(screen.getByText("custom@email.com")).toBeInTheDocument();
    });
  });
});
