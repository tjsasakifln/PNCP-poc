/**
 * SignupPage Component Tests
 *
 * Tests form submission, validation, success/error states
 * for the simplified 3-field signup form (GTM-FIX-019)
 * Updated: GTM-FIX-037 — removed confirmPassword, added email validation + form hint
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

// Mock useAnalytics hook
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
    identifyUser: jest.fn(),
  }),
  getStoredUTMParams: () => ({}),
}));

// Mock next/navigation (GTM-FIX-009: useRouter for redirect)
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
}));

// Mock sonner toast (GTM-FIX-009)
jest.mock('sonner', () => ({
  toast: { success: jest.fn(), error: jest.fn() },
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock InstitutionalSidebar
jest.mock('../../app/components/InstitutionalSidebar', () => {
  return function MockSidebar() {
    return <div data-testid="institutional-sidebar" />;
  };
});

// Helper to fill the simplified 3-field form (no confirmPassword — GTM-FIX-037 AC3)
async function fillForm(
  options: {
    name?: string;
    email?: string;
    password?: string;
  } = {}
) {
  const {
    name = 'John Doe',
    email = 'john@example.com',
    password = 'Password123',
  } = options;

  const nameInput = screen.getByLabelText(/Nome completo/i);
  const emailInput = screen.getByPlaceholderText(/seu@email.com/i);
  const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i);

  await act(async () => {
    fireEvent.change(nameInput, { target: { value: name } });
    fireEvent.change(emailInput, { target: { value: email } });
    fireEvent.change(passwordInput, { target: { value: password } });
  });
}

describe('SignupPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial render', () => {
    it('should render signup form', () => {
      render(<SignupPage />);

      expect(screen.getByRole('heading', { name: /Criar conta/i })).toBeInTheDocument();
    });

    it('should show subtitle about free trial', () => {
      render(<SignupPage />);

      expect(screen.getByText(/Experimente o SmartLic completo por 7 dias/i)).toBeInTheDocument();
    });

    it('should render simplified form fields (name, email, password — no confirm)', () => {
      render(<SignupPage />);

      expect(screen.getByLabelText(/Nome completo/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/seu@email.com/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i)).toBeInTheDocument();
      // GTM-FIX-037 AC3: Confirm password removed
      expect(screen.queryByPlaceholderText(/Digite a senha novamente/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/Confirmar senha/i)).not.toBeInTheDocument();
    });

    it('should NOT render removed fields (company, sector, phone, consent)', () => {
      render(<SignupPage />);

      expect(screen.queryByLabelText(/Empresa/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/Setor de atuação/i)).not.toBeInTheDocument();
      expect(screen.queryByPlaceholderText(/\(11\) 99999-9999/i)).not.toBeInTheDocument();
      expect(screen.queryByTestId('consent-scroll-box')).not.toBeInTheDocument();
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

    it('should show trial info box', () => {
      render(<SignupPage />);

      expect(screen.getByText(/Teste grátis por 7 dias/i)).toBeInTheDocument();
      expect(screen.getByText(/3 análises completas/i)).toBeInTheDocument();
      expect(screen.getByText(/Sem cartão de crédito/i)).toBeInTheDocument();
    });
  });

  describe('Form validation', () => {
    it('should have required email field', () => {
      render(<SignupPage />);

      const emailInput = screen.getByPlaceholderText(/seu@email.com/i);
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('type', 'email');
    });

    it('should have required password field with min length', () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i);
      expect(passwordInput).toHaveAttribute('required');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('minLength', '8');
    });

    it('should have required name field', () => {
      render(<SignupPage />);

      const nameInput = screen.getByLabelText(/Nome completo/i);
      expect(nameInput).toHaveAttribute('required');
    });

    it('should disable submit button when form is incomplete', async () => {
      render(<SignupPage />);

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });
      expect(submitButton).toBeDisabled();
    });

    it('should enable submit button when all fields are valid', async () => {
      render(<SignupPage />);

      await fillForm();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });
      expect(submitButton).not.toBeDisabled();
    });

    it('should show password policy feedback when password is weak', async () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i);

      await act(async () => {
        fireEvent.change(passwordInput, { target: { value: 'short' } });
      });

      expect(screen.getByText(/Mínimo 8 caracteres/i)).toBeInTheDocument();
      expect(screen.getByText(/Pelo menos 1 letra maiúscula/i)).toBeInTheDocument();
      expect(screen.getByText(/Pelo menos 1 número/i)).toBeInTheDocument();
    });
  });

  describe('GTM-FIX-037 AC1: Email validation on blur', () => {
    it('should NOT show email error before field is blurred', async () => {
      render(<SignupPage />);

      const emailInput = screen.getByPlaceholderText(/seu@email.com/i);

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'invalido' } });
      });

      expect(screen.queryByTestId('email-error')).not.toBeInTheDocument();
    });

    it('should show email error after blur with invalid email', async () => {
      render(<SignupPage />);

      const emailInput = screen.getByPlaceholderText(/seu@email.com/i);

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'invalido' } });
        fireEvent.blur(emailInput);
      });

      expect(screen.getByTestId('email-error')).toBeInTheDocument();
      expect(screen.getByText(/Digite um email válido/i)).toBeInTheDocument();
    });

    it('should NOT show email error with valid email after blur', async () => {
      render(<SignupPage />);

      const emailInput = screen.getByPlaceholderText(/seu@email.com/i);

      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
        fireEvent.blur(emailInput);
      });

      expect(screen.queryByTestId('email-error')).not.toBeInTheDocument();
    });

    it('should NOT show email error when field is empty after blur', async () => {
      render(<SignupPage />);

      const emailInput = screen.getByPlaceholderText(/seu@email.com/i);

      await act(async () => {
        fireEvent.blur(emailInput);
      });

      // Empty field should not show "invalid email" — only required validation applies
      expect(screen.queryByTestId('email-error')).not.toBeInTheDocument();
    });

    it('should disable submit button when email is invalid', async () => {
      render(<SignupPage />);

      await fillForm({ email: 'not-an-email' });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('GTM-FIX-037 AC2: Form hint when button disabled', () => {
    it('should NOT show form hint before any interaction', () => {
      render(<SignupPage />);

      expect(screen.queryByTestId('form-hint')).not.toBeInTheDocument();
    });

    it('should show form hint when form is touched but incomplete', async () => {
      render(<SignupPage />);

      const nameInput = screen.getByLabelText(/Nome completo/i);

      await act(async () => {
        fireEvent.change(nameInput, { target: { value: 'John' } });
      });

      expect(screen.getByTestId('form-hint')).toBeInTheDocument();
      expect(screen.getByText(/Preencha todos os campos corretamente para continuar/i)).toBeInTheDocument();
    });

    it('should NOT show form hint when form is completely valid', async () => {
      render(<SignupPage />);

      await fillForm();

      expect(screen.queryByTestId('form-hint')).not.toBeInTheDocument();
    });
  });

  describe('Form submission', () => {
    it('should call signUpWithEmail with 3 params (email, password, fullName)', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillForm({
        name: 'John Doe',
        email: 'john@example.com',
        password: 'Password123',
      });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockSignUpWithEmail).toHaveBeenCalledWith(
          'john@example.com',
          'Password123',
          'John Doe'
        );
      });
    });

    it('should show loading state during submission', async () => {
      mockSignUpWithEmail.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SignupPage />);

      await fillForm();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      expect(screen.getByRole('button', { name: /Criando conta.../i })).toBeInTheDocument();
    });
  });

  describe('Success state', () => {
    beforeEach(() => {
      // GTM-FIX-009: Mock fetch for polling
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ confirmed: false }),
      });
    });

    it('should show confirmation screen after signup', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillForm();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Confirme seu email/i)).toBeInTheDocument();
      });
    });

    it('should show email confirmation message with user email', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillForm({ email: 'john@example.com' });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Enviamos um link de confirmação para/i)).toBeInTheDocument();
        expect(screen.getByText(/john@example.com/i)).toBeInTheDocument();
      });
    });

    it('should show link to login page after success', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillForm();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
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

      await fillForm({ email: 'existing@example.com' });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument();
      });
    });

    it('should clear error on new submission', async () => {
      mockSignUpWithEmail
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce(undefined);

      render(<SignupPage />);

      await fillForm();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      // First submission - fails
      await act(async () => {
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

  describe('Password visibility toggle', () => {
    it('should hide password by default', () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should show password when toggle button is clicked', async () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i);
      const toggleButton = screen.getByRole('button', { name: /Mostrar senha/i });

      expect(passwordInput).toHaveAttribute('type', 'password');

      await act(async () => {
        fireEvent.click(toggleButton);
      });

      expect(passwordInput).toHaveAttribute('type', 'text');
    });

    it('should hide password again when toggle button is clicked twice', async () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiúscula, 1 número/i);
      const toggleButton = screen.getByRole('button', { name: /Mostrar senha/i });

      // First click - show password
      await act(async () => {
        fireEvent.click(toggleButton);
      });
      expect(passwordInput).toHaveAttribute('type', 'text');

      // Second click - hide password
      const hideButton = screen.getByRole('button', { name: /Ocultar senha/i });
      await act(async () => {
        fireEvent.click(hideButton);
      });
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should update aria-label based on visibility state', async () => {
      render(<SignupPage />);

      const toggleButton = screen.getByRole('button', { name: /Mostrar senha/i });
      expect(toggleButton).toHaveAttribute('aria-label', 'Mostrar senha');

      await act(async () => {
        fireEvent.click(toggleButton);
      });

      const hideButton = screen.getByRole('button', { name: /Ocultar senha/i });
      expect(hideButton).toHaveAttribute('aria-label', 'Ocultar senha');
    });
  });
});
