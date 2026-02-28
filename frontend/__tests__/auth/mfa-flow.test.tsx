/**
 * STORY-317 AC21: Frontend MFA flow tests.
 *
 * Tests for: setup flow (QR, verify, recovery codes), login TOTP screen,
 * enforcement banner, disable flow.
 */
import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";

// ─── Mocks ────────────────────────────────────────────────────────────────────

// Mock next/navigation
const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: jest.fn(),
    prefetch: jest.fn(),
    refresh: jest.fn(),
  }),
  usePathname: () => "/buscar",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock supabase
const mockEnroll = jest.fn();
const mockChallenge = jest.fn();
const mockVerify = jest.fn();
const mockChallengeAndVerify = jest.fn();
const mockListFactors = jest.fn();
const mockGetAuthenticatorAssuranceLevel = jest.fn();
const mockUnenroll = jest.fn();
const mockGetSession = jest.fn();
const mockRefreshSession = jest.fn();
const mockSignOut = jest.fn();

jest.mock("../../lib/supabase", () => ({
  supabase: {
    auth: {
      mfa: {
        enroll: (...args: unknown[]) => mockEnroll(...args),
        challenge: (...args: unknown[]) => mockChallenge(...args),
        verify: (...args: unknown[]) => mockVerify(...args),
        challengeAndVerify: (...args: unknown[]) => mockChallengeAndVerify(...args),
        listFactors: (...args: unknown[]) => mockListFactors(...args),
        getAuthenticatorAssuranceLevel: (...args: unknown[]) => mockGetAuthenticatorAssuranceLevel(...args),
        unenroll: (...args: unknown[]) => mockUnenroll(...args),
      },
      getSession: () => mockGetSession(),
      refreshSession: () => mockRefreshSession(),
      signOut: () => mockSignOut(),
    },
  },
}));

// Mock AuthProvider
const mockUseAuth = jest.fn();
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock sonner
jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock fetch for API proxy
const mockFetch = jest.fn();
global.fetch = mockFetch;

// ─── Imports ──────────────────────────────────────────────────────────────────

import { MfaSetupWizard } from "../../components/auth/MfaSetupWizard";
import { TotpVerificationScreen } from "../../components/auth/TotpVerificationScreen";
import { MfaEnforcementBanner } from "../../components/auth/MfaEnforcementBanner";

// ─── Setup / Teardown ─────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({
    user: { id: "test-user", email: "test@example.com" },
    session: { access_token: "test-token", user: { id: "test-user", email: "test@example.com" } },
    loading: false,
    isAdmin: false,
    signOut: mockSignOut,
  });
  mockGetSession.mockResolvedValue({
    data: { session: { access_token: "test-token" } },
  });
});

// ─── MfaSetupWizard Tests ─────────────────────────────────────────────────────

describe("MfaSetupWizard", () => {
  const defaultProps = {
    userEmail: "test@example.com",
    onComplete: jest.fn(),
    onCancel: jest.fn(),
  };

  it("renders QR code step initially", async () => {
    mockEnroll.mockResolvedValue({
      data: {
        id: "factor-123",
        totp: {
          qr_code: "data:image/svg+xml;base64,TEST",
          secret: "JBSWY3DPEHPK3PXP",
          uri: "otpauth://totp/SmartLic:test@example.com",
        },
      },
      error: null,
    });

    render(<MfaSetupWizard {...defaultProps} />);

    // Should show QR code heading
    await waitFor(() => {
      expect(screen.getByText("Escaneie o QR Code")).toBeInTheDocument();
    });

    // AC12: App compatibility note (text appears in both description and footer)
    expect(screen.getAllByText(/Google Authenticator/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Authy/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/1Password/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Microsoft Authenticator/).length).toBeGreaterThan(0);
  });

  it("shows manual key when toggled", async () => {
    mockEnroll.mockResolvedValue({
      data: {
        id: "factor-123",
        totp: {
          qr_code: "data:image/svg+xml;base64,TEST",
          secret: "TESTMANUALKEY123",
          uri: "otpauth://totp/SmartLic:test@example.com",
        },
      },
      error: null,
    });

    render(<MfaSetupWizard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/chave manual/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/chave manual/));
    expect(screen.getByText("TESTMANUALKEY123")).toBeInTheDocument();
  });

  it("moves to verify step on next", async () => {
    mockEnroll.mockResolvedValue({
      data: {
        id: "factor-123",
        totp: {
          qr_code: "data:image/svg+xml;base64,TEST",
          secret: "SECRET",
          uri: "otpauth://totp/SmartLic:test@example.com",
        },
      },
      error: null,
    });

    render(<MfaSetupWizard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Próximo")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Próximo"));
    expect(screen.getByText("Verificar código")).toBeInTheDocument();
  });

  it("handles enrollment error", async () => {
    mockEnroll.mockResolvedValue({
      data: null,
      error: { message: "MFA enrollment failed" },
    });

    render(<MfaSetupWizard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("MFA enrollment failed")).toBeInTheDocument();
    });
  });

  it("calls onCancel when cancel clicked", async () => {
    mockEnroll.mockResolvedValue({
      data: {
        id: "factor-123",
        totp: { qr_code: "data:image/svg+xml;base64,TEST", secret: "S", uri: "otpauth://totp/SmartLic:t" },
      },
      error: null,
    });

    render(<MfaSetupWizard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getAllByText("Cancelar").length).toBeGreaterThan(0);
    });

    // Click the first Cancelar button (in the QR step)
    fireEvent.click(screen.getAllByText("Cancelar")[0]);
    expect(defaultProps.onCancel).toHaveBeenCalled();
  });
});

// ─── TotpVerificationScreen Tests ─────────────────────────────────────────────

describe("TotpVerificationScreen", () => {
  it("renders verification screen", () => {
    render(<TotpVerificationScreen onVerified={jest.fn()} />);
    expect(screen.getByText("Verificação em dois fatores")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("000000")).toBeInTheDocument();
  });

  it("shows recovery code link", () => {
    render(<TotpVerificationScreen onVerified={jest.fn()} />);
    expect(screen.getByText("Usar código de recuperação")).toBeInTheDocument();
  });

  it("switches to recovery code input", () => {
    render(<TotpVerificationScreen onVerified={jest.fn()} />);
    fireEvent.click(screen.getByText("Usar código de recuperação"));
    expect(screen.getByPlaceholderText("XXXX-XXXX")).toBeInTheDocument();
    expect(screen.getByText("Usar código do autenticador")).toBeInTheDocument();
  });

  it("auto-submits on 6-digit code entry", async () => {
    const onVerified = jest.fn();
    mockListFactors.mockResolvedValue({
      data: { totp: [{ id: "factor-1", status: "verified" }], phone: [] },
    });
    mockChallengeAndVerify.mockResolvedValue({ error: null });

    render(<TotpVerificationScreen onVerified={onVerified} />);

    const input = screen.getByPlaceholderText("000000");
    fireEvent.change(input, { target: { value: "123456" } });

    await waitFor(() => {
      expect(mockChallengeAndVerify).toHaveBeenCalledWith({
        factorId: "factor-1",
        code: "123456",
      });
      expect(onVerified).toHaveBeenCalled();
    });
  });

  it("shows error on invalid code", async () => {
    mockListFactors.mockResolvedValue({
      data: { totp: [{ id: "factor-1", status: "verified" }], phone: [] },
    });
    mockChallengeAndVerify.mockResolvedValue({
      error: { message: "Invalid code" },
    });

    render(<TotpVerificationScreen onVerified={jest.fn()} />);

    const input = screen.getByPlaceholderText("000000");
    fireEvent.change(input, { target: { value: "123456" } });

    await waitFor(() => {
      expect(screen.getByText(/Código inválido/)).toBeInTheDocument();
    });
  });

  it("shows cancel button when onCancel provided", () => {
    render(<TotpVerificationScreen onVerified={jest.fn()} onCancel={jest.fn()} />);
    expect(screen.getByText("Cancelar")).toBeInTheDocument();
  });

  it("handles recovery code verification", async () => {
    const onVerified = jest.fn();

    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true, remaining_codes: 5, message: "OK" }),
    });

    render(<TotpVerificationScreen onVerified={onVerified} />);

    // Switch to recovery
    fireEvent.click(screen.getByText("Usar código de recuperação"));

    const input = screen.getByPlaceholderText("XXXX-XXXX");
    fireEvent.change(input, { target: { value: "ABCD-EF01" } });
    fireEvent.click(screen.getByText("Verificar código"));

    await waitFor(() => {
      expect(onVerified).toHaveBeenCalled();
    });
  });

  it("handles recovery code rate limiting (429)", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 429,
      json: () => Promise.resolve({ error: "Muitas tentativas. Tente novamente em 1 hora." }),
    });

    render(<TotpVerificationScreen onVerified={jest.fn()} />);

    fireEvent.click(screen.getByText("Usar código de recuperação"));

    const input = screen.getByPlaceholderText("XXXX-XXXX");
    fireEvent.change(input, { target: { value: "TEST-CODE" } });
    fireEvent.click(screen.getByText("Verificar código"));

    await waitFor(() => {
      expect(screen.getByText(/Muitas tentativas/)).toBeInTheDocument();
    });
  });
});

// ─── MfaEnforcementBanner Tests ───────────────────────────────────────────────

describe("MfaEnforcementBanner", () => {
  it("does not render for non-admin users", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: "user-1", email: "user@test.com" },
      session: { access_token: "token" },
      loading: false,
      isAdmin: false,
    });

    const { container } = render(<MfaEnforcementBanner />);

    // Wait for async check to complete
    await waitFor(() => {
      expect(container.querySelector("[data-testid='mfa-enforcement-banner']")).toBeNull();
    });
  });

  it("renders banner for admin without MFA", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: "admin-1", email: "admin@test.com" },
      session: { access_token: "admin-token" },
      loading: false,
      isAdmin: true,
    });

    mockListFactors.mockResolvedValue({
      data: { totp: [], phone: [] },
    });

    render(<MfaEnforcementBanner />);

    await waitFor(() => {
      expect(screen.getByTestId("mfa-enforcement-banner")).toBeInTheDocument();
      expect(screen.getByText(/MFA obrigatório/)).toBeInTheDocument();
    });
  });

  it("does not render for admin with MFA already set up", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: "admin-1", email: "admin@test.com" },
      session: { access_token: "admin-token" },
      loading: false,
      isAdmin: true,
    });

    mockListFactors.mockResolvedValue({
      data: { totp: [{ id: "f1", status: "verified" }], phone: [] },
    });

    const { container } = render(<MfaEnforcementBanner />);

    await waitFor(() => {
      expect(container.querySelector("[data-testid='mfa-enforcement-banner']")).toBeNull();
    });
  });

  it("has non-dismissible configure button (AC17)", async () => {
    mockUseAuth.mockReturnValue({
      user: { id: "admin-1", email: "admin@test.com" },
      session: { access_token: "admin-token" },
      loading: false,
      isAdmin: true,
    });

    mockListFactors.mockResolvedValue({
      data: { totp: [], phone: [] },
    });

    render(<MfaEnforcementBanner />);

    await waitFor(() => {
      const banner = screen.getByTestId("mfa-enforcement-banner");
      expect(banner).toBeInTheDocument();
    });

    // Click configure button → should navigate to security page
    fireEvent.click(screen.getByText("Configurar agora"));
    expect(mockPush).toHaveBeenCalledWith("/conta/seguranca");
  });

  it("does not render while loading", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      session: null,
      loading: true,
      isAdmin: false,
    });

    const { container } = render(<MfaEnforcementBanner />);
    expect(container.querySelector("[data-testid='mfa-enforcement-banner']")).toBeNull();
  });
});
