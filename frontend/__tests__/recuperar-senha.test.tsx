/**
 * Tests for Forgot Password / Password Reset flow (STORY-229)
 *
 * AC15: Unit test for /recuperar-senha page rendering
 * AC16: Unit test for Supabase resetPasswordForEmail call
 * AC17: Unit test for success/error states
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';

// Mock next/navigation
const mockRouterPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockRouterPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock Supabase client
const mockResetPasswordForEmail = jest.fn();
const mockUpdateUser = jest.fn();
const mockGetSession = jest.fn();
const mockGetUser = jest.fn();
const mockOnAuthStateChange = jest.fn();

jest.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      resetPasswordForEmail: (...args: unknown[]) => mockResetPasswordForEmail(...args),
      updateUser: (...args: unknown[]) => mockUpdateUser(...args),
      getSession: () => mockGetSession(),
      getUser: () => mockGetUser(),
      onAuthStateChange: (callback: (event: string, session: unknown) => void) => {
        mockOnAuthStateChange(callback);
        return {
          data: {
            subscription: {
              unsubscribe: jest.fn(),
            },
          },
        };
      },
    },
  },
}));

// Mock AuthProvider
const mockSession = { user: { id: '123', email: 'test@test.com' }, access_token: 'token' };
let mockAuthLoading = false;
let mockAuthSession: typeof mockSession | null = null;

jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: mockAuthSession,
    loading: mockAuthLoading,
    user: mockAuthSession?.user || null,
    isAdmin: false,
    signInWithEmail: jest.fn(),
    signUpWithEmail: jest.fn(),
    signInWithMagicLink: jest.fn(),
    signInWithGoogle: jest.fn(),
    signOut: jest.fn(),
  }),
}));

// Mock InstitutionalSidebar
jest.mock('../app/components/InstitutionalSidebar', () => {
  return function MockSidebar() {
    return <div data-testid="institutional-sidebar" />;
  };
});

// Mock sonner
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock analytics
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    identifyUser: jest.fn(),
  }),
  getStoredUTMParams: jest.fn(() => ({})),
}));

import RecuperarSenhaPage from '../app/recuperar-senha/page';
import RedefinirSenhaPage from '../app/redefinir-senha/page';

describe('RecuperarSenhaPage (/recuperar-senha)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuthLoading = false;
    mockAuthSession = null;
    mockResetPasswordForEmail.mockResolvedValue({ error: null });
  });

  // AC15: Page rendering
  describe('Page rendering (AC15)', () => {
    it('renders email input and submit button', () => {
      render(<RecuperarSenhaPage />);

      expect(screen.getByText('Recuperar senha')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /enviar link de recuperação/i })).toBeInTheDocument();
    });

    it('renders back to login link (AC8)', () => {
      render(<RecuperarSenhaPage />);

      expect(screen.getByText('Voltar ao login')).toBeInTheDocument();
    });

    it('renders institutional sidebar', () => {
      render(<RecuperarSenhaPage />);

      expect(screen.getByTestId('institutional-sidebar')).toBeInTheDocument();
    });

    it('shows loading state while checking auth', () => {
      mockAuthLoading = true;
      render(<RecuperarSenhaPage />);

      expect(screen.getByText('Carregando...')).toBeInTheDocument();
    });

    it('redirects authenticated users to /buscar (AC9)', () => {
      mockAuthSession = mockSession;
      render(<RecuperarSenhaPage />);

      expect(mockRouterPush).toHaveBeenCalledWith('/buscar');
    });
  });

  // AC16: Supabase resetPasswordForEmail call
  describe('Supabase resetPasswordForEmail call (AC16)', () => {
    it('calls resetPasswordForEmail with correct email', async () => {
      render(<RecuperarSenhaPage />);

      const emailInput = screen.getByLabelText('Email');
      const submitButton = screen.getByRole('button', { name: /enviar link de recuperação/i });

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
          'user@example.com',
          expect.objectContaining({
            redirectTo: expect.stringContaining('/redefinir-senha'),
          })
        );
      });
    });

    it('shows loading spinner during submission', async () => {
      // Make the call take some time
      mockResetPasswordForEmail.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ error: null }), 100))
      );

      render(<RecuperarSenhaPage />);

      fireEvent.change(screen.getByLabelText('Email'), {
        target: { value: 'user@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: /enviar link de recuperação/i }));

      expect(await screen.findByText('Enviando...')).toBeInTheDocument();
    });
  });

  // AC17: Success/error states
  describe('Success and error states (AC17)', () => {
    it('shows success message after email sent (AC6)', async () => {
      render(<RecuperarSenhaPage />);

      fireEvent.change(screen.getByLabelText('Email'), {
        target: { value: 'user@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: /enviar link de recuperação/i }));

      await waitFor(() => {
        expect(screen.getByText(/link de recuperação enviado/i)).toBeInTheDocument();
        expect(screen.getByText('user@example.com')).toBeInTheDocument();
      });
    });

    it('shows error message on rate limit (AC7)', async () => {
      mockResetPasswordForEmail.mockResolvedValue({
        error: new Error('Email rate limit exceeded'),
      });

      render(<RecuperarSenhaPage />);

      fireEvent.change(screen.getByLabelText('Email'), {
        target: { value: 'user@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: /enviar link de recuperação/i }));

      await waitFor(() => {
        expect(screen.getByText(/muitas tentativas/i)).toBeInTheDocument();
      });
    });

    it('shows error message on network error (AC7)', async () => {
      mockResetPasswordForEmail.mockRejectedValue(new Error('fetch failed'));

      render(<RecuperarSenhaPage />);

      fireEvent.change(screen.getByLabelText('Email'), {
        target: { value: 'user@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: /enviar link de recuperação/i }));

      await waitFor(() => {
        expect(screen.getByText(/erro de conexão/i)).toBeInTheDocument();
      });
    });

    it('shows cooldown timer after successful send', async () => {
      render(<RecuperarSenhaPage />);

      fireEvent.change(screen.getByLabelText('Email'), {
        target: { value: 'user@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: /enviar link de recuperação/i }));

      await waitFor(() => {
        expect(screen.getByText(/reenviar em/i)).toBeInTheDocument();
      });
    });
  });
});

describe('RedefinirSenhaPage (/redefinir-senha)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockGetSession.mockResolvedValue({
      data: { session: mockSession },
    });
    mockUpdateUser.mockResolvedValue({ error: null });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows checking state initially', () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(<RedefinirSenhaPage />);

    expect(screen.getByText(/verificando link/i)).toBeInTheDocument();
  });

  it('shows password form when recovery session exists', async () => {
    jest.useRealTimers();
    render(<RedefinirSenhaPage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Nova senha' })).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirmar nova senha')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /atualizar senha/i })).toBeInTheDocument();
    jest.useFakeTimers();
  });

  it('validates minimum 8 characters (AC12)', async () => {
    jest.useRealTimers();
    render(<RedefinirSenhaPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Nova senha'), {
      target: { value: '1234567' },
    });

    expect(screen.getByText(/pelo menos 8 caracteres/i)).toBeInTheDocument();
    jest.useFakeTimers();
  });

  it('validates password confirmation match', async () => {
    jest.useRealTimers();
    render(<RedefinirSenhaPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Nova senha'), {
      target: { value: '12345678' },
    });
    fireEvent.change(screen.getByLabelText('Confirmar nova senha'), {
      target: { value: '12345679' },
    });

    expect(screen.getByText(/senhas não coincidem/i)).toBeInTheDocument();
    jest.useFakeTimers();
  });

  it('calls updateUser on valid submission', async () => {
    jest.useRealTimers();
    render(<RedefinirSenhaPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Nova senha'), {
      target: { value: 'newpassword123' },
    });
    fireEvent.change(screen.getByLabelText('Confirmar nova senha'), {
      target: { value: 'newpassword123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /atualizar senha/i }));

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({ password: 'newpassword123' });
    });
    jest.useFakeTimers();
  });

  it('shows success state after password update (AC13)', async () => {
    jest.useRealTimers();
    render(<RedefinirSenhaPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Nova senha'), {
      target: { value: 'newpassword123' },
    });
    fireEvent.change(screen.getByLabelText('Confirmar nova senha'), {
      target: { value: 'newpassword123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /atualizar senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/senha atualizada/i)).toBeInTheDocument();
    });
    jest.useFakeTimers();
  });

  it('shows error on update failure with retry (AC14)', async () => {
    jest.useRealTimers();
    mockUpdateUser.mockResolvedValue({
      error: { message: 'Password is too weak' },
    });

    render(<RedefinirSenhaPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText('Nova senha'), {
      target: { value: 'newpassword123' },
    });
    fireEvent.change(screen.getByLabelText('Confirmar nova senha'), {
      target: { value: 'newpassword123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /atualizar senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/senha muito fraca/i)).toBeInTheDocument();
    });

    // Retry is possible (button still exists)
    expect(screen.getByRole('button', { name: /atualizar senha/i })).toBeInTheDocument();
    jest.useFakeTimers();
  });

  it('shows invalid link error when no recovery session', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    render(<RedefinirSenhaPage />);

    // Advance past the 3s timeout
    act(() => {
      jest.advanceTimersByTime(4000);
    });

    await waitFor(() => {
      expect(screen.getByText(/link inválido/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/solicitar novo link/i)).toBeInTheDocument();
  });
});
