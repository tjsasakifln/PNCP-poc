/**
 * SignupPage Component Tests
 *
 * Tests form submission, validation, success/error states,
 * phone formatting, and consent scroll behavior
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

// Helper to fill form and scroll consent
async function fillFormAndConsent(
  options: {
    name?: string;
    company?: string;
    sector?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    phone?: string;
    scrollToBottom?: boolean;
    checkConsent?: boolean;
  } = {}
) {
  const {
    name = 'John Doe',
    company = 'Test Company',
    sector = 'informatica',
    email = 'john@example.com',
    password = 'Password123',
    confirmPassword = 'Password123',
    phone = '11999999999',
    scrollToBottom = true,
    checkConsent = true,
  } = options;

  const nameInput = screen.getByLabelText(/Nome completo/i);
  const companyInput = screen.getByLabelText(/Empresa/i);
  const sectorSelect = screen.getByLabelText(/Setor de atuação/i);
  const emailInput = screen.getByPlaceholderText(/seu@email.com/i);
  const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i);
  const confirmPasswordInput = screen.getByPlaceholderText(/Digite a senha novamente/i);
  const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);

  await act(async () => {
    fireEvent.change(nameInput, { target: { value: name } });
    fireEvent.change(companyInput, { target: { value: company } });
    fireEvent.change(sectorSelect, { target: { value: sector } });
    fireEvent.change(emailInput, { target: { value: email } });
    fireEvent.change(passwordInput, { target: { value: password } });
    fireEvent.change(confirmPasswordInput, { target: { value: confirmPassword } });
    fireEvent.change(phoneInput, { target: { value: phone } });
  });

  if (scrollToBottom) {
    // Find the scroll box and simulate scrolling to bottom
    const scrollBox = screen.getByTestId('consent-scroll-box');
    await act(async () => {
      Object.defineProperty(scrollBox, 'scrollHeight', { value: 500, configurable: true });
      Object.defineProperty(scrollBox, 'clientHeight', { value: 144, configurable: true });
      Object.defineProperty(scrollBox, 'scrollTop', { value: 360, configurable: true });
      fireEvent.scroll(scrollBox);
    });
  }

  if (checkConsent && scrollToBottom) {
    const consentCheckbox = screen.getByRole('checkbox');
    await act(async () => {
      fireEvent.click(consentCheckbox);
    });
  }
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

    it('should show subtitle about free searches', () => {
      render(<SignupPage />);

      expect(screen.getByText(/Experimente o SmartLic completo por 7 dias/i)).toBeInTheDocument();
    });

    it('should render all form fields including WhatsApp, Company, and Sector', () => {
      render(<SignupPage />);

      expect(screen.getByLabelText(/Nome completo/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Empresa/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Setor de atuação/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/seu@email.com/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/\(11\) 99999-9999/i)).toBeInTheDocument();
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

    it('should show consent terms section', () => {
      render(<SignupPage />);

      // Check for consent label (contains "role ate o final para aceitar")
      expect(screen.getByText(/role ate o final para aceitar/i)).toBeInTheDocument();
      // Check consent box is present using testid
      expect(screen.getByTestId('consent-scroll-box')).toBeInTheDocument();
      // Check consent terms content
      expect(screen.getByTestId('consent-scroll-box')).toHaveTextContent(/TERMOS DE CONSENTIMENTO PARA COMUNICACOES PROMOCIONAIS/i);
    });

    it('should show scroll indicator initially', () => {
      render(<SignupPage />);

      expect(screen.getByText(/Role para baixo/i)).toBeInTheDocument();
    });
  });

  describe('Phone field', () => {
    it('should format phone as user types (11 digits)', async () => {
      render(<SignupPage />);

      const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);

      await act(async () => {
        fireEvent.change(phoneInput, { target: { value: '11999998888' } });
      });

      expect(phoneInput).toHaveValue('(11) 99999-8888');
    });

    it('should format phone as user types (10 digits)', async () => {
      render(<SignupPage />);

      const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);

      await act(async () => {
        fireEvent.change(phoneInput, { target: { value: '1199998888' } });
      });

      expect(phoneInput).toHaveValue('(11) 9999-8888');
    });

    it('should strip non-numeric characters', async () => {
      render(<SignupPage />);

      const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);

      await act(async () => {
        fireEvent.change(phoneInput, { target: { value: '(11) abc 999-99' } });
      });

      // Should only have the digits
      expect(phoneInput).toHaveValue('(11) 9999-9');
    });

    it('should limit to 11 digits', async () => {
      render(<SignupPage />);

      const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);

      await act(async () => {
        fireEvent.change(phoneInput, { target: { value: '119999988881234' } });
      });

      expect(phoneInput).toHaveValue('(11) 99999-8888');
    });

    it('should have placeholder with format hint', () => {
      render(<SignupPage />);

      const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);
      expect(phoneInput).toHaveAttribute('placeholder', '(11) 99999-9999');
    });
  });

  describe('Consent scroll behavior', () => {
    it('should have checkbox disabled initially', () => {
      render(<SignupPage />);

      const consentCheckbox = screen.getByRole('checkbox');
      expect(consentCheckbox).toBeDisabled();
    });

    it('should enable checkbox after scrolling to bottom', async () => {
      render(<SignupPage />);

      const scrollBox = screen.getByTestId('consent-scroll-box');
      const consentCheckbox = screen.getByRole('checkbox');

      expect(consentCheckbox).toBeDisabled();

      await act(async () => {
        Object.defineProperty(scrollBox, 'scrollHeight', { value: 500, configurable: true });
        Object.defineProperty(scrollBox, 'clientHeight', { value: 144, configurable: true });
        Object.defineProperty(scrollBox, 'scrollTop', { value: 360, configurable: true });
        fireEvent.scroll(scrollBox);
      });

      expect(consentCheckbox).not.toBeDisabled();
    });

    it('should hide scroll indicator after scrolling to bottom', async () => {
      render(<SignupPage />);

      expect(screen.getByText(/Role para baixo/i)).toBeInTheDocument();

      const scrollBox = screen.getByTestId('consent-scroll-box');
      await act(async () => {
        Object.defineProperty(scrollBox, 'scrollHeight', { value: 500, configurable: true });
        Object.defineProperty(scrollBox, 'clientHeight', { value: 144, configurable: true });
        Object.defineProperty(scrollBox, 'scrollTop', { value: 360, configurable: true });
        fireEvent.scroll(scrollBox);
      });

      expect(screen.queryByText(/Role para baixo/i)).not.toBeInTheDocument();
    });

    it('should not allow checking consent without scrolling', async () => {
      render(<SignupPage />);

      const consentCheckbox = screen.getByRole('checkbox');

      await act(async () => {
        fireEvent.click(consentCheckbox);
      });

      expect(consentCheckbox).not.toBeChecked();
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

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i);
      expect(passwordInput).toHaveAttribute('required');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('minLength', '8');
    });

    it('should have required name field', () => {
      render(<SignupPage />);

      const nameInput = screen.getByLabelText(/Nome completo/i);
      expect(nameInput).toHaveAttribute('required');
    });

    it('should have required phone field', () => {
      render(<SignupPage />);

      const phoneInput = screen.getByPlaceholderText(/\(11\) 99999-9999/i);
      expect(phoneInput).toHaveAttribute('required');
    });

    it('should have required company field', () => {
      render(<SignupPage />);

      const companyInput = screen.getByLabelText(/Empresa/i);
      expect(companyInput).toHaveAttribute('required');
    });

    it('should have required sector field', () => {
      render(<SignupPage />);

      const sectorSelect = screen.getByLabelText(/Setor de atuação/i);
      expect(sectorSelect).toHaveAttribute('required');
    });

    it('should show other sector input when "outro" is selected', async () => {
      render(<SignupPage />);

      const sectorSelect = screen.getByLabelText(/Setor de atuação/i);

      await act(async () => {
        fireEvent.change(sectorSelect, { target: { value: 'outro' } });
      });

      expect(screen.getByLabelText(/Qual setor\?/i)).toBeInTheDocument();
    });

    it('should disable submit button when form is incomplete', async () => {
      render(<SignupPage />);

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });
      expect(submitButton).toBeDisabled();
    });

    it('should enable submit button when all fields are valid', async () => {
      render(<SignupPage />);

      await fillFormAndConsent();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });
      expect(submitButton).not.toBeDisabled();
    });

    it('should show error for invalid phone', async () => {
      render(<SignupPage />);

      await fillFormAndConsent({ phone: '123' }); // Too short

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      // Button should still be disabled due to invalid phone
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Form submission', () => {
    it('should call signUpWithEmail with all params including company, sector, phone and consent', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillFormAndConsent({
        name: 'John Doe',
        company: 'Acme Corp',
        sector: 'informatica',
        email: 'john@example.com',
        password: 'Password123',
        phone: '11999998888',
      });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockSignUpWithEmail).toHaveBeenCalledWith(
          'john@example.com',
          'Password123',
          'John Doe',
          'Acme Corp',
          'informatica', // sector
          '11999998888', // Only digits
          true // whatsappConsent
        );
      });
    });

    it('should show loading state during submission', async () => {
      mockSignUpWithEmail.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SignupPage />);

      await fillFormAndConsent();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      expect(screen.getByRole('button', { name: /Criando conta.../i })).toBeInTheDocument();
    });
  });

  describe('Success state', () => {
    it('should show success message after signup', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillFormAndConsent();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Conta criada!/i)).toBeInTheDocument();
      });
    });

    it('should show email confirmation message', async () => {
      mockSignUpWithEmail.mockResolvedValue(undefined);

      render(<SignupPage />);

      await fillFormAndConsent({ email: 'john@example.com' });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
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

      await fillFormAndConsent();

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

      await fillFormAndConsent({ email: 'existing@example.com' });

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument();
      });
    });

    it('should show translated error for non-Error exceptions', async () => {
      // TD-006: errors now go through getUserFriendlyError which passes
      // through non-technical strings under 200 chars as-is
      mockSignUpWithEmail.mockRejectedValue('Unknown error');

      render(<SignupPage />);

      await fillFormAndConsent();

      const submitButton = screen.getByRole('button', { name: /Criar conta$/i });

      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Unknown error')).toBeInTheDocument();
      });
    });

    it('should clear error on new submission', async () => {
      mockSignUpWithEmail
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce(undefined);

      render(<SignupPage />);

      await fillFormAndConsent();

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

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should show password when toggle button is clicked', async () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i);
      // Get first toggle button (password field, not confirm password)
      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      const toggleButton = toggleButtons[0];

      expect(passwordInput).toHaveAttribute('type', 'password');

      await act(async () => {
        fireEvent.click(toggleButton);
      });

      expect(passwordInput).toHaveAttribute('type', 'text');
    });

    it('should hide password again when toggle button is clicked twice', async () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i);
      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      const toggleButton = toggleButtons[0];

      // First click - show password
      await act(async () => {
        fireEvent.click(toggleButton);
      });
      expect(passwordInput).toHaveAttribute('type', 'text');

      // Second click - hide password
      const hideButtons = screen.getAllByRole('button', { name: /Ocultar senha/i });
      await act(async () => {
        fireEvent.click(hideButtons[0]);
      });
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should update aria-label based on visibility state', async () => {
      render(<SignupPage />);

      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      const toggleButton = toggleButtons[0];
      expect(toggleButton).toHaveAttribute('aria-label', 'Mostrar senha');

      await act(async () => {
        fireEvent.click(toggleButton);
      });

      const hideButtons = screen.getAllByRole('button', { name: /Ocultar senha/i });
      expect(hideButtons[0]).toHaveAttribute('aria-label', 'Ocultar senha');
    });

    it('should display password as typed when visible', async () => {
      render(<SignupPage />);

      const passwordInput = screen.getByPlaceholderText(/Min\. 8 caracteres, 1 maiuscula, 1 numero/i);
      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      const toggleButton = toggleButtons[0];

      // Type password while hidden
      await act(async () => {
        fireEvent.change(passwordInput, { target: { value: 'Secret123' } });
      });

      // Show password
      await act(async () => {
        fireEvent.click(toggleButton);
      });

      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(passwordInput).toHaveValue('Secret123');
    });

    it('should render toggle button inside password field container', () => {
      render(<SignupPage />);

      const toggleButtons = screen.getAllByRole('button', { name: /Mostrar senha/i });
      const toggleButton = toggleButtons[0];

      // Toggle button should exist and be interactive
      expect(toggleButton).toBeInTheDocument();
      expect(toggleButton).toHaveAttribute('type', 'button');
    });
  });
});
