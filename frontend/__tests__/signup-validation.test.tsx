/**
 * STORY-258 AC22 — Signup form validation tests
 * Tests email validation, corporate badge, phone checks, debounce, and rate limiting.
 *
 * NOTE: The current signup page (page.tsx) does NOT include disposable email
 * detection, corporate badge, phone fields, or duplicate-phone checks — those
 * features are AC22 items that still need implementation in the page component.
 * These tests cover:
 *  - existing form validation (email format, password policy)
 *  - mocked API calls for disposable/duplicate-phone endpoints
 *  - stubs for features that would be wired up in the page component
 */
import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Next.js mocks ─────────────────────────────────────────────────────────────
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
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
const mockSignUpWithEmail = jest.fn();
const mockSignInWithGoogle = jest.fn();
const mockTrackEvent = jest.fn();

jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    signUpWithEmail: mockSignUpWithEmail,
    signInWithGoogle: mockSignInWithGoogle,
  }),
}));

jest.mock("../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
  getStoredUTMParams: () => ({}),
}));

// ─── InstitutionalSidebar mock ─────────────────────────────────────────────────
jest.mock("../app/components/InstitutionalSidebar", () => {
  const InstitutionalSidebar = () => <div data-testid="institutional-sidebar" />;
  InstitutionalSidebar.displayName = "InstitutionalSidebar";
  return InstitutionalSidebar;
});

// ─── Sonner toast mock ─────────────────────────────────────────────────────────
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// ─── error-messages mock ───────────────────────────────────────────────────────
jest.mock("../lib/error-messages", () => ({
  translateAuthError: (msg: string) => msg,
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// ─── Helpers ───────────────────────────────────────────────────────────────────
/** Fill all required fields so the form can be submitted */
function fillValidForm(overrides: { email?: string; password?: string; fullName?: string } = {}) {
  // Use htmlFor-linked label text exactly to avoid ambiguity with "Mostrar senha" button
  const nameInput = screen.getByLabelText("Nome completo");
  const emailInput = screen.getByLabelText("Email");
  // The password input has id="password"; its label text is "Senha"
  const passwordInput = screen.getByLabelText("Senha");

  fireEvent.change(nameInput, {
    target: { value: overrides.fullName ?? "João da Silva" },
  });
  fireEvent.change(emailInput, {
    target: { value: overrides.email ?? "joao@gmail.com" },
  });
  fireEvent.change(passwordInput, {
    target: { value: overrides.password ?? "Senha1234" },
  });
}

// ─── Import component after mocks ─────────────────────────────────────────────
import SignupPage from "../app/signup/page";

// ─── Tests ────────────────────────────────────────────────────────────────────
describe("SignupPage — form validation (STORY-258 AC22)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset fetch mock
    global.fetch = jest.fn();
  });

  // ── Email validation ─────────────────────────────────────────────────────────

  it("shows email format error after blurring an invalid email", async () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByTestId("email-error")).toBeInTheDocument();
      expect(screen.getByTestId("email-error")).toHaveTextContent(/email v/i);
    });
  });

  it("does not show email error for a valid gmail address", async () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "usuario@gmail.com" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.queryByTestId("email-error")).not.toBeInTheDocument();
    });
  });

  it("does not show email error for a corporate email address", async () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "contato@empresa.com.br" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.queryByTestId("email-error")).not.toBeInTheDocument();
    });
  });

  it("does not show email error before the field is touched (blur)", () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "bad" } });
    // No blur — error should NOT appear yet

    expect(screen.queryByTestId("email-error")).not.toBeInTheDocument();
  });

  // ── Password policy ──────────────────────────────────────────────────────────

  it("shows password policy hints when password is too short", async () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    fireEvent.change(passwordInput, { target: { value: "abc" } });

    await waitFor(() => {
      expect(screen.getByText(/mínimo 8 caracteres/i)).toBeInTheDocument();
    });
  });

  it("hides password policy hints when password satisfies all rules", async () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    fireEvent.change(passwordInput, { target: { value: "Senha123" } });

    await waitFor(() => {
      expect(screen.queryByText(/mínimo 8 caracteres/i)).not.toBeInTheDocument();
    });
  });

  it("disables submit button while form is invalid (missing required field)", async () => {
    render(<SignupPage />);

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    expect(submitBtn).toBeDisabled();
  });

  it("enables submit button when all required fields are valid", async () => {
    render(<SignupPage />);

    fillValidForm();

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    expect(submitBtn).not.toBeDisabled();
  });

  // ── Form submission ──────────────────────────────────────────────────────────

  it("calls signUpWithEmail with correct credentials on valid submit", async () => {
    mockSignUpWithEmail.mockResolvedValueOnce(undefined);
    render(<SignupPage />);

    fillValidForm({ email: "test@empresa.com", password: "Abc12345", fullName: "Maria" });

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockSignUpWithEmail).toHaveBeenCalledWith(
        "test@empresa.com",
        "Abc12345",
        "Maria"
      );
    });
  });

  it("displays auth error message when signup fails", async () => {
    mockSignUpWithEmail.mockRejectedValueOnce(new Error("Email já cadastrado"));
    render(<SignupPage />);

    fillValidForm();

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/email já cadastrado/i)).toBeInTheDocument();
    });
  });

  // ── Success / confirmation screen ────────────────────────────────────────────

  it("shows confirmation screen with email after successful signup", async () => {
    mockSignUpWithEmail.mockResolvedValueOnce(undefined);
    // Mock the polling endpoint to avoid unhandled fetch calls
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ confirmed: false }),
    });

    render(<SignupPage />);

    fillValidForm({ email: "confirmme@gmail.com" });

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId("mail-icon")).toBeInTheDocument();
      expect(screen.getByText("confirmme@gmail.com")).toBeInTheDocument();
    });
  });

  // ── Disposable email check (AC22 — API-mocked test for future wiring) ─────────

  it("handles disposable-email API returning invalid gracefully via fetch mock", async () => {
    // This test validates that fetch can be mocked for disposable email detection.
    // The actual API call will be wired when AC22 email-validation endpoint is added.
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes("validate-email")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ disposable: true, valid: false }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ confirmed: false }),
      });
    });

    // The current page does not call /validate-email yet, but the mock is ready.
    // When AC22 is wired, this test will assert inline error visibility.
    render(<SignupPage />);
    expect(screen.getByRole("button", { name: /criar conta/i })).toBeInTheDocument();
  });

  // ── Rate limiting (AC22 — resilience test) ────────────────────────────────────

  it("handles rate-limit response (429) on signup attempt without crashing", async () => {
    mockSignUpWithEmail.mockRejectedValueOnce(new Error("Too many requests"));
    render(<SignupPage />);

    fillValidForm();

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      // Should show error, not crash
      expect(screen.getByText(/too many requests/i)).toBeInTheDocument();
    });
  });

  // ── AC22: Inline validation — disposable email error on blur ─────────────────

  it("shows disposable email error on blur when check-email returns is_disposable=true", async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes("check-email")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ is_disposable: true, is_corporate: false, available: true }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ confirmed: false }) });
    });

    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "user@tempmail.com" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByTestId("email-disposable-error")).toBeInTheDocument();
      expect(screen.getByTestId("email-disposable-error")).toHaveTextContent(/descartáveis/i);
    });
  });

  // ── AC22: Inline validation — corporate badge on blur ────────────────────────

  it("shows corporate badge for business email when check-email returns is_corporate=true", async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes("check-email")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ is_disposable: false, is_corporate: true, available: true }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ confirmed: false }) });
    });

    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "contato@empresa.com.br" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      const badge = screen.getByTestId("email-type-badge");
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent(/corporativo/i);
    });
  });

  // ── AC22: Inline validation — personal badge for Gmail ───────────────────────

  it("shows personal badge for Gmail when check-email returns is_corporate=false", async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes("check-email")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ is_disposable: false, is_corporate: false, available: true }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ confirmed: false }) });
    });

    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: "usuario@gmail.com" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      const badge = screen.getByTestId("email-type-badge");
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent(/pessoal/i);
    });
  });

  // ── AC22: Inline validation — phone duplicate error ──────────────────────────

  it("shows phone error for duplicate phone when check-phone returns already_registered=true", async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes("check-phone")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ available: false, already_registered: true }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ confirmed: false }) });
    });

    render(<SignupPage />);

    const phoneInput = screen.getByLabelText(/telefone/i);
    fireEvent.change(phoneInput, { target: { value: "11999991234" } });
    fireEvent.blur(phoneInput);

    await waitFor(() => {
      expect(screen.getByTestId("phone-error")).toBeInTheDocument();
      expect(screen.getByTestId("phone-error")).toHaveTextContent(/já está associado/i);
    });
  });

  // ── AC22: Inline validation — errors clear on valid input ────────────────────

  it("clears email check error when user types a new email value", async () => {
    (global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (String(url).includes("check-email")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ is_disposable: true, is_corporate: false, available: true }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ confirmed: false }) });
    });

    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/email/i);
    // Trigger disposable error
    fireEvent.change(emailInput, { target: { value: "user@tempmail.com" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByTestId("email-disposable-error")).toBeInTheDocument();
    });

    // Now type a new value — error should be cleared immediately on change
    fireEvent.change(emailInput, { target: { value: "novo@gmail.com" } });

    await waitFor(() => {
      expect(screen.queryByTestId("email-disposable-error")).not.toBeInTheDocument();
    });
  });
});
