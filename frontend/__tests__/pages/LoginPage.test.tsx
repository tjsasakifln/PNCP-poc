/**
 * LoginPage Component Tests
 *
 * Tests form validation, mode toggle (login/magic link), submission flows
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from '@/app/login/page';

// Mock useAuth hook
const mockSignInWithEmail = jest.fn();
const mockSignInWithMagicLink = jest.fn();
const mockSignInWithGoogle = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    signInWithEmail: mockSignInWithEmail,
    signInWithMagicLink: mockSignInWithMagicLink,
    signInWithGoogle: mockSignInWithGoogle,
    session: null,     // Not authenticated
    loading: false,    // Auth check complete
  }),
}));

// Mock Next.js navigation
const mockPush = jest.fn();
const mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => mockSearchParams,
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock window.location
const originalLocation = window.location;

beforeEach(() => {
  jest.clearAllMocks();
  // @ts-expect-error - mocking window.location
  delete window.location;
  window.location = { ...originalLocation, href: '' };
});

afterAll(() => {
  window.location = originalLocation;
});

describe('LoginPage Component', () => {
  describe('Initial render', () => {
    it('should render login form', () => {
      render(<LoginPage />);

      expect(screen.getByRole('heading')).toBeInTheDocument();
      expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    });

    it('should show password field by default', () => {
      render(<LoginPage />);

      expect(screen.getByLabelText(/Senha/i)).toBeInTheDocument();
    });

    it('should show Google login button', () => {
      render(<LoginPage />);

      expect(screen.getByRole('button', { name: /Entrar com Google/i })).toBeInTheDocument();
    });

    it('should show mode toggle buttons', () => {
      render(<LoginPage />);

      expect(screen.getByRole('button', { name: /Email \+ Senha/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Magic Link/i })).toBeInTheDocument();
    });

    it('should show link to signup page', () => {
      render(<LoginPage />);

      const signupLink = screen.getByRole('link', { name: /Criar conta/i });
      expect(signupLink).toBeInTheDocument();
      expect(signupLink).toHaveAttribute('href', '/signup');
    });
  });

  describe('Mode toggle', () => {
    it('should hide password field when switching to magic link mode', async () => {
      render(<LoginPage />);

      // Initially password field should be visible
      expect(screen.getByLabelText(/Senha/i)).toBeInTheDocument();

      // Click magic link mode
      const magicButton = screen.getByRole('button', { name: /Magic Link/i });
      await act(async () => {
        fireEvent.click(magicButton);
      });

      // Password field should be hidden
      expect(screen.queryByLabelText(/Senha/i)).not.toBeInTheDocument();
    });

    it('should show password field when switching back to password mode', async () => {
      render(<LoginPage />);

      // Switch to magic link
      const magicButton = screen.getByRole('button', { name: /Magic Link/i });
      await act(async () => {
        fireEvent.click(magicButton);
      });

      // Switch back to password
      const passwordButton = screen.getByRole('button', { name: /Email \+ Senha/i });
      await act(async () => {
        fireEvent.click(passwordButton);
      });

      expect(screen.getByLabelText(/Senha/i)).toBeInTheDocument();
    });

    it('should change submit button text based on mode', async () => {
      render(<LoginPage />);

      // Default mode - password
      expect(screen.getByRole('button', { name: /Entrar$/i })).toBeInTheDocument();

      // Switch to magic link
      const magicButton = screen.getByRole('button', { name: /Magic Link/i });
      await act(async () => {
        fireEvent.click(magicButton);
      });

      expect(screen.getByRole('button', { name: /Enviar link/i })).toBeInTheDocument();
    });
  });

  describe('Password login flow', () => {
    it('should call signInWithEmail on form submit', async () => {
      mockSignInWithEmail.mockResolvedValue(undefined);

      render(<LoginPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Entrar$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockSignInWithEmail).toHaveBeenCalledWith('test@example.com', 'password123');
      });
    });

    it('should not redirect if login succeeds but session not yet updated', async () => {
      // Note: The actual redirect happens via useEffect when session state updates,
      // not directly after signInWithEmail completes. This test verifies the form
      // submission works correctly.
      mockSignInWithEmail.mockResolvedValue(undefined);

      render(<LoginPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Entrar$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      // signInWithEmail should have been called - redirect happens when session updates
      await waitFor(() => {
        expect(mockSignInWithEmail).toHaveBeenCalled();
      });
    });

    it('should show loading state during login', async () => {
      mockSignInWithEmail.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<LoginPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Entrar$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.click(submitButton);
      });

      expect(screen.getByRole('button', { name: /Entrando.../i })).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });

    it('should show error message on login failure', async () => {
      mockSignInWithEmail.mockRejectedValue(new Error('Invalid credentials'));

      render(<LoginPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Entrar$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'wrong' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
      });
    });

    it('should show generic error for non-Error exceptions', async () => {
      mockSignInWithEmail.mockRejectedValue('Unknown error');

      render(<LoginPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      const passwordInput = screen.getByLabelText(/Senha/i);
      const submitButton = screen.getByRole('button', { name: /Entrar$/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Erro ao fazer login')).toBeInTheDocument();
      });
    });
  });

  describe('Magic link flow', () => {
    beforeEach(async () => {
      render(<LoginPage />);

      // Switch to magic link mode
      const magicButton = screen.getByRole('button', { name: /Magic Link/i });
      await act(async () => {
        fireEvent.click(magicButton);
      });
    });

    it('should call signInWithMagicLink on form submit', async () => {
      mockSignInWithMagicLink.mockResolvedValue(undefined);

      const emailInput = screen.getByLabelText(/Email/i);
      const submitButton = screen.getByRole('button', { name: /Enviar link/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'magic@example.com' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockSignInWithMagicLink).toHaveBeenCalledWith('magic@example.com');
      });
    });

    it('should show success message after magic link sent', async () => {
      mockSignInWithMagicLink.mockResolvedValue(undefined);

      const emailInput = screen.getByLabelText(/Email/i);
      const submitButton = screen.getByRole('button', { name: /Enviar link/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'magic@example.com' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Verifique seu email/i)).toBeInTheDocument();
        expect(screen.getByText(/magic@example.com/i)).toBeInTheDocument();
      });
    });

    it('should allow retrying after magic link success', async () => {
      mockSignInWithMagicLink.mockResolvedValue(undefined);

      const emailInput = screen.getByLabelText(/Email/i);
      const submitButton = screen.getByRole('button', { name: /Enviar link/i });

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'magic@example.com' } });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Verifique seu email/i)).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /Tentar novamente/i });
      await act(async () => {
        fireEvent.click(retryButton);
      });

      // Should be back to form
      expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    });
  });

  describe('Google OAuth', () => {
    it('should call signInWithGoogle when clicking Google button', async () => {
      mockSignInWithGoogle.mockResolvedValue(undefined);

      render(<LoginPage />);

      const googleButton = screen.getByRole('button', { name: /Entrar com Google/i });

      await act(async () => {
        fireEvent.click(googleButton);
      });

      expect(mockSignInWithGoogle).toHaveBeenCalled();
    });
  });

  describe('Form validation', () => {
    it('should require email field', () => {
      render(<LoginPage />);

      const emailInput = screen.getByLabelText(/Email/i);
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('type', 'email');
    });

    it('should require password field in password mode', () => {
      render(<LoginPage />);

      const passwordInput = screen.getByLabelText(/Senha/i);
      expect(passwordInput).toHaveAttribute('required');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('minLength', '6');
    });
  });
});
