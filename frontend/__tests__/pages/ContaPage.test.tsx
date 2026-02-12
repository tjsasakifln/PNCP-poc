/**
 * ContaPage Component Tests
 *
 * Tests account settings page, password change, profile display
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ContaPage from '@/app/conta/page';

// Mock useAuth
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

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    user: mockUser,
    session: mockSession,
    loading: false,
    signOut: mockSignOut,
  }),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock fetch
global.fetch = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

describe('ContaPage', () => {
  describe('Initial render', () => {
    it('should render page title', () => {
      render(<ContaPage />);

      expect(screen.getByText('Minha Conta')).toBeInTheDocument();
    });

    it('should display user email', () => {
      render(<ContaPage />);

      expect(screen.getByText('test@test.com')).toBeInTheDocument();
    });

    it('should display user name', () => {
      render(<ContaPage />);

      expect(screen.getByText('Test User')).toBeInTheDocument();
    });

    it('should have back link to /buscar', () => {
      render(<ContaPage />);

      const backLink = screen.getByRole('link', { name: /Voltar/i });
      expect(backLink).toHaveAttribute('href', '/buscar');
    });

    it('should display profile data section', () => {
      render(<ContaPage />);

      expect(screen.getByText(/Dados do perfil/i)).toBeInTheDocument();
      expect(screen.getByText(/Email/i)).toBeInTheDocument();
      expect(screen.getByText(/Nome/i)).toBeInTheDocument();
    });

    it('should display password change section', () => {
      render(<ContaPage />);

      expect(screen.getByText(/Alterar senha/i)).toBeInTheDocument();
    });
  });

  describe('Password fields', () => {
    it('should have new password input', () => {
      render(<ContaPage />);

      expect(screen.getByLabelText(/Nova senha/i)).toBeInTheDocument();
    });

    it('should have confirm password input', () => {
      render(<ContaPage />);

      expect(screen.getByLabelText(/Confirmar nova senha/i)).toBeInTheDocument();
    });

    it('should toggle password visibility', () => {
      render(<ContaPage />);

      const newPasswordInput = screen.getByLabelText(/Nova senha/i) as HTMLInputElement;
      expect(newPasswordInput.type).toBe('password');

      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      fireEvent.click(toggleButtons[0]);

      expect(newPasswordInput.type).toBe('text');
    });

    it('should have submit button', () => {
      render(<ContaPage />);

      expect(screen.getByRole('button', { name: /Alterar senha/i })).toBeInTheDocument();
    });
  });

  describe('Password validation', () => {
    it('should show error for short password', async () => {
      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: '12345' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: '12345' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(screen.getByText(/Senha deve ter no mínimo 6 caracteres/i)).toBeInTheDocument();
      });
    });

    it('should show error for mismatched passwords', async () => {
      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: 'different123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(screen.getByText(/As senhas não coincidem/i)).toBeInTheDocument();
      });
    });
  });

  describe('Password change submission', () => {
    it('should submit password change successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: 'newpassword123' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: 'newpassword123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/change-password',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              Authorization: 'Bearer mock-token',
            }),
            body: JSON.stringify({ new_password: 'newpassword123' }),
          })
        );
      });
    });

    it('should show success message', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: 'newpassword123' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: 'newpassword123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(screen.getByText(/Senha alterada com sucesso/i)).toBeInTheDocument();
      });
    });

    it('should clear form after successful submission', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<ContaPage />);

      const newPasswordInput = screen.getByLabelText(/Nova senha/i) as HTMLInputElement;
      const confirmPasswordInput = screen.getByLabelText(/Confirmar nova senha/i) as HTMLInputElement;

      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(newPasswordInput.value).toBe('');
        expect(confirmPasswordInput.value).toBe('');
      });
    });

    it('should call signOut after 2 seconds on success', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: 'newpassword123' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: 'newpassword123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(screen.getByText(/Senha alterada com sucesso/i)).toBeInTheDocument();
      });

      jest.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalled();
      });
    });

    it('should show error message on API failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Senha muito fraca' }),
      });

      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: 'newpassword123' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: 'newpassword123' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Alterar senha/i }));

      await waitFor(() => {
        expect(screen.getByText(/Senha muito fraca/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading states', () => {
    it('should show loading state when auth is loading', () => {
      jest.spyOn(require('../../app/components/AuthProvider'), 'useAuth').mockReturnValue({
        user: null,
        session: null,
        loading: true,
        signOut: mockSignOut,
      });

      render(<ContaPage />);

      expect(screen.getByText(/Carregando/i)).toBeInTheDocument();
    });

    it('should disable submit button during submission', async () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, json: async () => ({}) }), 1000))
      );

      render(<ContaPage />);

      fireEvent.change(screen.getByLabelText(/Nova senha/i), {
        target: { value: 'newpassword123' },
      });
      fireEvent.change(screen.getByLabelText(/Confirmar nova senha/i), {
        target: { value: 'newpassword123' },
      });

      const submitButton = screen.getByRole('button', { name: /Alterar senha/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Alterando/i })).toBeInTheDocument();
      });
    });
  });

  describe('Auth redirect', () => {
    it('should show login prompt when not authenticated', () => {
      jest.spyOn(require('../../app/components/AuthProvider'), 'useAuth').mockReturnValue({
        user: null,
        session: null,
        loading: false,
        signOut: mockSignOut,
      });

      render(<ContaPage />);

      expect(screen.getByText(/Faça login para acessar sua conta/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Ir para login/i })).toBeInTheDocument();
    });
  });

  describe('Warning message', () => {
    it('should display logout warning', () => {
      render(<ContaPage />);

      expect(screen.getByText(/Ao alterar sua senha, voce sera desconectado/i)).toBeInTheDocument();
    });
  });

  describe('User metadata fallback', () => {
    it('should show dash when no name available', () => {
      jest.spyOn(require('../../app/components/AuthProvider'), 'useAuth').mockReturnValue({
        user: { ...mockUser, user_metadata: {} },
        session: mockSession,
        loading: false,
        signOut: mockSignOut,
      });

      render(<ContaPage />);

      const nameFields = screen.getAllByText('-');
      expect(nameFields.length).toBeGreaterThan(0);
    });
  });
});
