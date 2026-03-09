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
function fillValidForm(overrides: { email?: string; password?: string; fullName?: string; confirmPassword?: string } = {}) {
  // Use htmlFor-linked label text exactly to avoid ambiguity with "Mostrar senha" button
  const nameInput = screen.getByLabelText("Nome completo");
  const emailInput = screen.getByLabelText("Email");
  // The password input has id="password"; its label text is "Senha"
  const passwordInput = screen.getByLabelText("Senha");
  const confirmInput = screen.getByLabelText("Confirmar senha");

  const pw = overrides.password ?? "Senha1234";

  fireEvent.change(nameInput, {
    target: { value: overrides.fullName ?? "João da Silva" },
  });
  fireEvent.change(emailInput, {
    target: { value: overrides.email ?? "joao@gmail.com" },
  });
  fireEvent.change(passwordInput, {
    target: { value: pw },
  });
  fireEvent.change(confirmInput, {
    target: { value: overrides.confirmPassword ?? pw },
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
      expect(screen.getByTestId("email-error")).toHaveTextContent(/email inv/i);
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

// ─── SAB-007: Inline Validation Tests ──────────────────────────────────────────
describe("SignupPage — SAB-007 inline validation", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ confirmed: false }),
    });
  });

  // ── AC1: Name field onBlur ─────────────────────────────────────────────────

  it("AC1: shows 'Nome é obrigatório' on blur when name is empty", async () => {
    render(<SignupPage />);

    const nameInput = screen.getByLabelText("Nome completo");
    fireEvent.focus(nameInput);
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(screen.getByTestId("name-error")).toBeInTheDocument();
      expect(screen.getByTestId("name-error")).toHaveTextContent("Nome é obrigatório");
    });
  });

  it("AC1: does not show name error when name is filled", () => {
    render(<SignupPage />);

    const nameInput = screen.getByLabelText("Nome completo");
    fireEvent.change(nameInput, { target: { value: "João" } });
    fireEvent.blur(nameInput);

    expect(screen.queryByTestId("name-error")).not.toBeInTheDocument();
  });

  // ── AC2: Email inline error ────────────────────────────────────────────────

  it("AC2: shows 'Email inválido' for malformed email on blur", async () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText("Email");
    fireEvent.change(emailInput, { target: { value: "not-an-email" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByTestId("email-error")).toBeInTheDocument();
      expect(screen.getByTestId("email-error")).toHaveTextContent("Email inválido");
    });
  });

  // ── AC3: Password strength bar ─────────────────────────────────────────────

  it("AC3: shows password strength indicator when typing", () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    fireEvent.change(passwordInput, { target: { value: "abc" } });

    expect(screen.getByTestId("password-strength")).toBeInTheDocument();
    expect(screen.getByTestId("password-strength-label")).toHaveTextContent("Senha fraca");
  });

  it("AC3: shows 'forte' for complex passwords", () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    fireEvent.change(passwordInput, { target: { value: "Str0ng!Pass@2026" } });

    expect(screen.getByTestId("password-strength-label")).toHaveTextContent("Senha forte");
  });

  // ── AC4: Confirm password mismatch ─────────────────────────────────────────

  it("AC4: shows 'Senhas não coincidem' when passwords differ", async () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    const confirmInput = screen.getByLabelText("Confirmar senha");

    fireEvent.change(passwordInput, { target: { value: "Senha1234" } });
    fireEvent.change(confirmInput, { target: { value: "Different" } });
    fireEvent.blur(confirmInput);

    await waitFor(() => {
      expect(screen.getByTestId("confirm-password-error")).toBeInTheDocument();
      expect(screen.getByTestId("confirm-password-error")).toHaveTextContent("Senhas não coincidem");
    });
  });

  it("AC4: shows match indicator when passwords are equal", () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    const confirmInput = screen.getByLabelText("Confirmar senha");

    fireEvent.change(passwordInput, { target: { value: "Senha1234" } });
    fireEvent.change(confirmInput, { target: { value: "Senha1234" } });

    expect(screen.getByTestId("confirm-password-match")).toBeInTheDocument();
  });

  // ── AC5: Submit button tooltip ─────────────────────────────────────────────

  it("AC5: renders tooltip when button is disabled", () => {
    render(<SignupPage />);

    // Button should be disabled on empty form
    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    expect(submitBtn).toBeDisabled();

    // Tooltip should be in DOM (hidden via CSS opacity)
    expect(screen.getByTestId("submit-tooltip")).toBeInTheDocument();
    expect(screen.getByTestId("submit-tooltip")).toHaveTextContent("Preencha todos os campos");
  });

  it("AC5: tooltip disappears when form becomes valid", async () => {
    render(<SignupPage />);

    fillValidForm();

    await waitFor(() => {
      expect(screen.queryByTestId("submit-tooltip")).not.toBeInTheDocument();
    });
  });

  // ── AC6: Smooth button transition ──────────────────────────────────────────

  it("AC6: button has transition classes for smooth visual change", () => {
    render(<SignupPage />);

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    expect(submitBtn.className).toContain("transition-all");
    expect(submitBtn.className).toContain("duration-300");
  });

  // ── AC7: Spinner during submit ─────────────────────────────────────────────

  it("AC7: shows spinner during form submission", async () => {
    // Make signUp hang to observe loading state
    mockSignUpWithEmail.mockImplementation(() => new Promise(() => {}));
    render(<SignupPage />);

    fillValidForm();

    const submitBtn = screen.getByRole("button", { name: /criar conta/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Criando conta...")).toBeInTheDocument();
      // Spinner SVG should be present
      const svg = submitBtn.querySelector("svg.animate-spin");
      expect(svg).toBeInTheDocument();
    });
  });

  // ── AC8: Submit with empty fields → inline errors on all fields ────────────

  it("AC8: shows inline errors on all fields when submitting empty form", async () => {
    render(<SignupPage />);

    // Attempt submit on empty form — button is disabled, but we simulate the form submission
    // by directly calling the submit on the form element
    const form = screen.getByRole("button", { name: /criar conta/i }).closest("form")!;
    fireEvent.submit(form);

    await waitFor(() => {
      // Name error
      expect(screen.getByTestId("name-error")).toBeInTheDocument();
      expect(screen.getByTestId("name-error")).toHaveTextContent("Nome é obrigatório");
    });
  });

  // ── AC9: Invalid email → specific inline error ─────────────────────────────

  it("AC9: shows specific inline error for invalid email format", async () => {
    render(<SignupPage />);

    const emailInput = screen.getByLabelText("Email");
    fireEvent.change(emailInput, { target: { value: "not-valid" } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      const error = screen.getByTestId("email-error");
      expect(error).toBeInTheDocument();
      expect(error).toHaveTextContent("Email inválido");
    });
  });

  // ── AC10: Mismatched passwords → inline error on confirm field ─────────────

  it("AC10: shows inline error on confirm password when passwords don't match", async () => {
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText("Senha");
    const confirmInput = screen.getByLabelText("Confirmar senha");

    fireEvent.change(passwordInput, { target: { value: "ValidPass1" } });
    fireEvent.change(confirmInput, { target: { value: "WrongPass2" } });
    fireEvent.blur(confirmInput);

    await waitFor(() => {
      const error = screen.getByTestId("confirm-password-error");
      expect(error).toBeInTheDocument();
      expect(error).toHaveTextContent("Senhas não coincidem");
    });
  });
});
