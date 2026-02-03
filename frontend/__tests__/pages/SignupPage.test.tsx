/**
 * SignupPage Component Tests
 *
 * Tests form submission, validation, success/error states
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import SignupPage from '@/app/signup/page';

// Mock useAuth hook
const mockSignUpWithEmail = jest.fn();
const mockSignInWithGoogle = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    signUpWithEmail: mockSignUpWithEmail,
    signInWithGoogle: mockSignInWithGoogle,
  }),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

describe('SignupPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial render', () => {
    it('should render signup form', () => {
      render(<SignupPage />);

      expect(screen.getByRole('heading', { name: /Criar conta/i })).toBeInTheDocument();
    });

    it('should show subtitle about free searches', () => {
      render(<SignupPage />);

      expect(screen.getByText(/Comece com 3 buscas gratuitas/i)).toBeInTheDocument();
    });

    it('should render all form fields', () => {
      render(<SignupPage />);

      expect(screen.getByLabelText(/Nome completo/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Senha/i)).toBeInTheDocument();
    });

    it('should show Google signup button', () => {
      render(<SignupPage />);

      expect(screen.getByRole('button', { name: /Cadastrar com Google/i })).toBeInTheDocument();
    });

    it('should show link to login page', () => {
      render(<SignupPage />);

      const loginLink = screen.getByRole('link', { name: /Fazer login/i });
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute('href', '/login');
    });
  });

  describe('Form validation', () => {
    it('should have required email field', () => {
      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('type', 'email');
    });

    it('should have required password field with min length', () => {
      render(<SignupPage />);

      const passwordInput = screen.getByLabelText(/Senha/i);
      expect(passwordInput).toHaveAttribute('required');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('minLength', '6');
    });

    it('should have optional name field (not required)', () => {
      render(<SignupPage />);

      const nameInput = screen.getByLabelText(/Nome completo/i);
      expect(nameInput).not.toHaveAttribute('required');
    });
  });

  describe('Form submission', () => {
    it('should call signUpWithEmail with correct params', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      const nameInput = screen.getByLabelText(/Nome completo/i);
      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(nameInput, { target: { value: 'John Doe' } });
        fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockSignUpWithEmail).toHaveBeenCalledWith(
          'john@example.com',
          'password123',
          'John Doe'
        );
      });
    });

    it('should allow signup without name', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockSignUpWithEmail).toHaveBeenCalledWith(
          'john@example.com',
          'password123',
          ''
        );
      });
    });

    it('should show loading state during submission', async () => {
      mockSignUpWithEmail.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      expect(screen.getByRole('button', { name: /Criando conta.../i })).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Success state', () => {
    it('should show success message after signup', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Conta criada!/i)).toBeInTheDocument();
      });
    });

    it('should show email confirmation message', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Verifique seu email/i)).toBeInTheDocument();
        expect(screen.getByText(/john@example.com/i)).toBeInTheDocument();
      });
    });

    it('should show link to login page after success', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        const loginLink = screen.getByRole('link', { name: /Ir para login/i });
        expect(loginLink).toBeInTheDocument();
        expect(loginLink).toHaveAttribute('href', '/login');
      });
    });
  });

  describe('Error handling', () => {
    it('should show error message on signup failure', async () => {
      mockSignUpWithEmail.mockRejectedValue(new Error('Email already exists'));

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'existing@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument();
      });
    });

    it('should show generic error for non-Error exceptions', async () => {
      mockSignUpWithEmail.mockRejectedValue('Unknown error');

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Erro ao criar conta')).toBeInTheDocument();
      });
    });

    it('should clear error on new submission', async () => {
      mockSignUpWithEmail
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce(undefined);

      render(<SignupPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      // First submission - fails
      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      // Second submission - succeeds
      await act(async () => {
        fireEvent.click(submitButton);
      });

      // Error should be cleared during submission
      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
      });
    });
  });

  describe('Google OAuth', () => {
    it('should call signInWithGoogle when clicking Google button', async () => {
      mockSignInWithGoogle.mockResolvedValue(undefined);

      render(<SignupPage />);

      const googleButton = screen.getByRole('button', { name: /Cadastrar com Google/i });

      await act(async () => {
        fireEvent.click(googleButton);
      });

      expect(mockSignInWithGoogle).toHaveBeenCalled();
    });
  });
});
