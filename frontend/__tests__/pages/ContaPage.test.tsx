/**
 * ContaPage Component Tests (DEBT-011 Updated)
 *
 * Tests account settings pages after decomposition:
 * - SegurancaPage: password change, auth states
 * - PerfilPage: profile display, user metadata
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock usePathname for layout (AC5)
jest.mock('next/navigation', () => ({
  usePathname: () => '/conta/perfil',
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
}));

// Mock PageHeader for layout
jest.mock('@/components/PageHeader', () => ({
  PageHeader: ({ title }: { title: string }) => <div data-testid="page-header">{title}</div>,
}));

// Mock ErrorBoundary for layout
jest.mock('@/components/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock useUser from UserContext
const mockSignOut = jest.fn();
const mockUser = {
  id: 'user-1',
  email: 'test@test.com',
  user_metadata: {
    full_name: 'Test User',
    name: 'Test',
  },
};
const mockSession = { access_token: 'mock-token' };

let mockUserData: Record<string, unknown> = {
  user: mockUser,
  session: mockSession,
  authLoading: false,
  isAdmin: false,
  sessionExpired: false,
  signOut: mockSignOut,
  planInfo: null,
  planLoading: false,
  planError: null,
  isFromCache: false,
  cachedAt: null,
  quota: null,
  quotaLoading: false,
  trial: { phase: 'active', daysLeft: 14, isExpired: false, isExpiring: false, isNewUser: false },
  refresh: jest.fn(),
};

jest.mock('@/contexts/UserContext', () => ({
  useUser: () => mockUserData,
}));

// Mock supabase (needed by SegurancaPage for MFA)
jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      mfa: {
        listFactors: jest.fn().mockResolvedValue({ data: { totp: [] } }),
        challengeAndVerify: jest.fn(),
        unenroll: jest.fn(),
      },
      refreshSession: jest.fn(),
    },
  },
}));

// Mock error-messages
jest.mock('@/lib/error-messages', () => ({
  getUserFriendlyError: (err: unknown) => (err instanceof Error ? err.message : String(err)),
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// Mock Button component
jest.mock('@/components/ui/button', () => ({
  Button: ({ children, disabled, loading, type, ...rest }: any) => (
    <button type={type || 'button'} disabled={disabled || loading} {...rest}>{loading && <svg className="animate-spin" aria-hidden="true" />}{children}</button>
  ),
  buttonVariants: jest.fn(),
}));

// Mock MfaSetupWizard
jest.mock('@/components/auth/MfaSetupWizard', () => ({
  MfaSetupWizard: () => null,
}));

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
  Toaster: () => null,
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock useProfileContext (FE-007 SWR migration)
// PerfilPage now calls useProfileContext which internally uses useAuth from AuthProvider.
// Mocking at module level prevents the AuthProvider dependency.
jest.mock('@/hooks/useProfileContext', () => ({
  useProfileContext: () => ({
    profileCtx: {},
    isLoading: false,
    error: null,
    updateCache: jest.fn(),
    mutate: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  jest.restoreAllMocks();
  jest.useFakeTimers();
  mockUserData = {
    user: mockUser,
    session: mockSession,
    authLoading: false,
    isAdmin: false,
    sessionExpired: false,
    signOut: mockSignOut,
    planInfo: null,
    planLoading: false,
    planError: null,
    isFromCache: false,
    cachedAt: null,
    quota: null,
    quotaLoading: false,
    trial: { phase: 'active', daysLeft: 14, isExpired: false, isExpiring: false, isNewUser: false },
    refresh: jest.fn(),
  };
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({}),
  });
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

// ═══ ContaLayout sidebar tests (AC5) ═══

describe('ContaLayout sidebar (AC5)', () => {
  let ContaLayout: any;

  beforeEach(async () => {
    const mod = await import('@/app/conta/layout');
    ContaLayout = mod.default;
  });

  it('should render sidebar navigation', () => {
    render(
      <ContaLayout>
        <div>Content</div>
      </ContaLayout>
    );
    expect(screen.getByTestId('conta-sidebar')).toBeInTheDocument();
  });

  it('should display all nav items', () => {
    render(
      <ContaLayout>
        <div>Content</div>
      </ContaLayout>
    );

    expect(screen.getAllByText(/Perfil/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Segurança/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Acesso/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Dados e LGPD/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Equipe/i).length).toBeGreaterThan(0);
  });

  it('should have correct hrefs for nav links', () => {
    render(
      <ContaLayout>
        <div>Content</div>
      </ContaLayout>
    );

    const links = screen.getAllByRole('link');
    const hrefs = links.map((l: HTMLElement) => l.getAttribute('href'));

    expect(hrefs).toContain('/conta/perfil');
    expect(hrefs).toContain('/conta/seguranca');
    expect(hrefs).toContain('/conta/plano');
    expect(hrefs).toContain('/conta/dados');
    expect(hrefs).toContain('/conta/equipe');
  });

  it('should render children content area', () => {
    render(
      <ContaLayout>
        <div data-testid="test-child">Hello</div>
      </ContaLayout>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });
});

// ═══ PerfilPage tests ═══

describe('PerfilPage', () => {
  let PerfilPage: any;

  beforeEach(async () => {
    const mod = await import('@/app/conta/perfil/page');
    PerfilPage = mod.default;
  });

  describe('Initial render', () => {
    it('should display profile data section', () => {
      render(<PerfilPage />);
      expect(screen.getByText(/Dados do perfil/i)).toBeInTheDocument();
      expect(screen.getAllByText(/^Email$/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/^Nome/i)).toBeInTheDocument();
    });

    it('should display user email', () => {
      render(<PerfilPage />);
      expect(screen.getByText('test@test.com')).toBeInTheDocument();
    });

    it('should display user name', () => {
      render(<PerfilPage />);
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });

  describe('Loading states', () => {
    it('should show loading state when auth is loading', () => {
      mockUserData = { ...mockUserData, authLoading: true };
      render(<PerfilPage />);
      expect(screen.getByText(/Carregando/i)).toBeInTheDocument();
    });
  });

  describe('Auth redirect', () => {
    it('should show login prompt when not authenticated', () => {
      mockUserData = { ...mockUserData, user: null, session: null };
      render(<PerfilPage />);
      expect(screen.getByText(/Faça login para acessar sua conta/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Ir para login/i })).toBeInTheDocument();
    });
  });

  describe('User metadata fallback', () => {
    it('should show dash when no name available', () => {
      mockUserData = {
        ...mockUserData,
        user: { ...mockUser, user_metadata: {} },
      };
      render(<PerfilPage />);
      const nameFields = screen.getAllByText('-');
      expect(nameFields.length).toBeGreaterThan(0);
    });
  });

  describe('Error state (AC6)', () => {
    it('should show toast error on profile save API failure', async () => {
      const { toast } = require('sonner');

      // Override useProfileContext mock to return profile data with edit button
      jest.requireMock('@/hooks/useProfileContext').useProfileContext = () => ({
        profileCtx: { ufs_atuacao: ['SP'], porte_empresa: 'EPP' },
        isLoading: false,
        error: null,
        updateCache: jest.fn(),
        mutate: jest.fn(),
      });

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: async () => ({ detail: 'Server error' }),
      });

      render(<PerfilPage />);

      // Click edit button
      const editBtn = screen.getByTestId('edit-profile-btn');
      fireEvent.click(editBtn);

      // Submit the form
      await waitFor(() => {
        expect(screen.getByTestId('save-profile-btn')).toBeInTheDocument();
      });

      fireEvent.submit(screen.getByTestId('save-profile-btn').closest('form')!);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith(
          expect.stringContaining('Erro ao salvar perfil')
        );
      });
    });
  });
});

// ═══ SegurancaPage tests ═══

describe('SegurancaPage', () => {
  let SegurancaPage: any;

  beforeEach(async () => {
    const mod = await import('@/app/conta/seguranca/page');
    SegurancaPage = mod.default;
  });

  describe('Password section', () => {
    it('should display password change heading', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Alterar senha/i })).toBeInTheDocument();
      });
    });

    it('should have new password input', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });
    });

    it('should have confirm password input', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText(/Confirmar nova senha/i)).toBeInTheDocument();
      });
    });

    it('should toggle password visibility', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });
      const newPasswordInput = screen.getByLabelText('Nova senha') as HTMLInputElement;
      expect(newPasswordInput.type).toBe('password');
      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      fireEvent.click(toggleButtons[0]);
      expect(newPasswordInput.type).toBe('text');
    });

    it('should have submit button', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Alterar senha/i })).toBeInTheDocument();
      });
    });
  });

  describe('Password validation', () => {
    it('should show error for short password', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });
      fireEvent.change(screen.getByLabelText('Nova senha'), { target: { value: '12345' } });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), { target: { value: '12345' } });
      fireEvent.submit(screen.getByLabelText('Nova senha').closest('form')!);
      await waitFor(() => {
        expect(screen.getByText(/Senha deve ter no mínimo 6 caracteres/i)).toBeInTheDocument();
      });
    });

    it('should show error for mismatched passwords', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });
      fireEvent.change(screen.getByLabelText('Nova senha'), { target: { value: 'password123' } });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), { target: { value: 'different123' } });
      fireEvent.submit(screen.getByLabelText('Nova senha').closest('form')!);
      await waitFor(() => {
        expect(screen.getByText(/As senhas não coincidem/i)).toBeInTheDocument();
      });
    });
  });

  describe('Password change submission', () => {
    it('should submit password change successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Nova senha'), { target: { value: 'newpassword123' } });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), { target: { value: 'newpassword123' } });
      fireEvent.submit(screen.getByLabelText('Nova senha').closest('form')!);

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls;
        const passwordCall = calls.find((c: string[]) => c[0] === '/api/change-password');
        expect(passwordCall).toBeDefined();
        expect(passwordCall[1]).toMatchObject({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer mock-token',
          }),
          body: JSON.stringify({ new_password: 'newpassword123' }),
        });
      });
    });

    it('should show success message', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Nova senha'), { target: { value: 'newpassword123' } });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), { target: { value: 'newpassword123' } });
      fireEvent.submit(screen.getByLabelText('Nova senha').closest('form')!);

      await waitFor(() => {
        expect(screen.getByText(/Senha alterada com sucesso/i)).toBeInTheDocument();
      });
    });

    it('should clear form after successful submission', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });

      const newPasswordInput = screen.getByLabelText('Nova senha') as HTMLInputElement;
      const confirmPasswordInput = screen.getByLabelText(/Confirmar nova senha/i) as HTMLInputElement;

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.submit(newPasswordInput.closest('form')!);

      await waitFor(() => {
        expect(newPasswordInput.value).toBe('');
        expect(confirmPasswordInput.value).toBe('');
      });
    });

    it('should call signOut after 2 seconds on success', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Nova senha'), { target: { value: 'newpassword123' } });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), { target: { value: 'newpassword123' } });
      fireEvent.submit(screen.getByLabelText('Nova senha').closest('form')!);

      await waitFor(() => {
        expect(screen.getByText(/Senha alterada com sucesso/i)).toBeInTheDocument();
      });

      jest.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled();
      });
    });

    it('should show error message on API failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: async () => ({ detail: 'Senha muito fraca' }),
      });

      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByLabelText('Nova senha')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Nova senha'), { target: { value: 'newpassword123' } });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), { target: { value: 'newpassword123' } });
      fireEvent.submit(screen.getByLabelText('Nova senha').closest('form')!);

      await waitFor(() => {
        expect(screen.getByText(/Senha muito fraca/i)).toBeInTheDocument();
      });
    });
  });

  describe('Warning message', () => {
    it('should display logout warning', async () => {
      render(<SegurancaPage />);
      await waitFor(() => {
        expect(screen.getByText(/você será desconectado/i)).toBeInTheDocument();
      });
    });
  });
});
