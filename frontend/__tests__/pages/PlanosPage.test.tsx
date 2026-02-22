/**
 * PlanosPage Component Tests — GTM-002 Single Plan Model
 *
 * Tests for SmartLic Pro single plan with billing period toggle
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import PlanosPage from '@/app/planos/page';
import { toast } from 'sonner';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// UX-339: Mock usePlan hook (now used by PlanosPage)
const mockUsePlan = jest.fn();
jest.mock('../../hooks/usePlan', () => ({
  usePlan: () => mockUsePlan(),
}));

// Mock useAnalytics hook
const mockTrackEvent = jest.fn();
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
    identifyUser: jest.fn(),
    resetUser: jest.fn(),
    trackPageView: jest.fn(),
  }),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock window.location
const originalLocation = window.location;

beforeEach(() => {
  jest.clearAllMocks();
  // Clear toast mocks
  (toast.error as jest.Mock).mockClear();
  (toast.success as jest.Mock).mockClear();
  mockTrackEvent.mockClear();
  // @ts-expect-error - mocking window.location
  delete window.location;
  window.location = {
    ...originalLocation,
    href: '',
    search: '',
  };
  mockUseAuth.mockReturnValue({
    session: null,
    user: null,
    isAdmin: false,
    loading: false,
  });
  // UX-339: Default usePlan mock (no plan for anonymous)
  mockUsePlan.mockReturnValue({
    planInfo: null,
    loading: false,
    error: null,
    refresh: jest.fn(),
  });
  // Mock /me endpoint for non-authenticated users
  mockFetch.mockResolvedValue({
    ok: false,
    status: 401,
  });
});

afterAll(() => {
  window.location = originalLocation;
});

describe('PlanosPage Component', () => {
  describe('Initial render', () => {
    it('should render page title', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Escolha Seu Nível de Compromisso/i })).toBeInTheDocument();
      });
    });

    it('should render subtitle', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/O SmartLic é um só/i)).toBeInTheDocument();
      });
    });

    it('should render SmartLic Pro plan card', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /SmartLic Pro/i })).toBeInTheDocument();
      });
    });

    it('should render plan description', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Inteligência de decisão completa para licitações/i)).toBeInTheDocument();
      });
    });

    it('should track page view on mount', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith('plan_page_viewed', { source: 'url' });
      });
    });
  });

  describe('Billing period toggle', () => {
    it('should render billing period toggle with 3 options', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        const radioGroup = screen.getByRole('radiogroup', { name: /Escolha seu nível de compromisso/i });
        expect(radioGroup).toBeInTheDocument();
      });

      // Check all 3 radio buttons exist
      expect(screen.getByRole('radio', { name: /Mensal/i })).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /Semestral.*Economize 10%/i })).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /Anual.*Economize 20%/i })).toBeInTheDocument();
    });

    it('should default to monthly billing period', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        const monthlyRadio = screen.getByRole('radio', { name: /Mensal/i });
        expect(monthlyRadio).toHaveAttribute('aria-checked', 'true');
      });

      // Default price should be monthly R$ 1.999
      expect(screen.getByText(/R\$\s*1\.999/)).toBeInTheDocument();
    });

    it('should change price when billing period changes', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/R\$\s*1\.999/)).toBeInTheDocument();
      });

      // Click semiannual toggle
      const semiannualRadio = screen.getByRole('radio', { name: /Semestral.*Economize 10%/i });
      fireEvent.click(semiannualRadio);

      await waitFor(() => {
        // Semiannual price should be R$ 1.799/mês
        expect(screen.getByText(/R\$\s*1\.799/)).toBeInTheDocument();
        // Check for multiple "Economize 10%" elements (toggle + badge)
        const saveElements = screen.getAllByText(/Economize 10%/);
        expect(saveElements.length).toBeGreaterThan(0);
      });
    });

    it('should show annual pricing when annual is selected', async () => {
      render(<PlanosPage />);

      // Click annual toggle
      const annualRadio = screen.getByRole('radio', { name: /Anual.*Economize 20%/i });
      fireEvent.click(annualRadio);

      await waitFor(() => {
        // Annual price should be R$ 1.599/mês
        expect(screen.getByText(/R\$\s*1\.599/)).toBeInTheDocument();
        // Check for multiple "Economize 20%" elements (toggle + badge)
        const saveElements = screen.getAllByText(/Economize 20%/);
        expect(saveElements.length).toBeGreaterThan(0);
      });
    });

    it('should show total billing amount for semiannual', async () => {
      render(<PlanosPage />);

      const semiannualRadio = screen.getByRole('radio', { name: /Semestral.*Economize 10%/i });
      fireEvent.click(semiannualRadio);

      await waitFor(() => {
        expect(screen.getByText(/Cobrado R\$\s*10\.794 a cada 6 meses/i)).toBeInTheDocument();
      });
    });

    it('should show total billing amount for annual', async () => {
      render(<PlanosPage />);

      const annualRadio = screen.getByRole('radio', { name: /Anual.*Economize 20%/i });
      fireEvent.click(annualRadio);

      await waitFor(() => {
        expect(screen.getByText(/Cobrado R\$\s*19\.188 por ano/i)).toBeInTheDocument();
      });
    });

    it('should pre-select billing period from URL param', async () => {
      window.location.search = '?billing=annual';

      render(<PlanosPage />);

      await waitFor(() => {
        const annualRadio = screen.getByRole('radio', { name: /Anual.*Economize 20%/i });
        expect(annualRadio).toHaveAttribute('aria-checked', 'true');
        expect(screen.getByText(/R\$\s*1\.599/)).toBeInTheDocument();
      });
    });

    it('should pre-select semiannual from URL param', async () => {
      window.location.search = '?billing=semiannual';

      render(<PlanosPage />);

      await waitFor(() => {
        const semiannualRadio = screen.getByRole('radio', { name: /Semestral.*Economize 10%/i });
        expect(semiannualRadio).toHaveAttribute('aria-checked', 'true');
        expect(screen.getByText(/R\$\s*1\.799/)).toBeInTheDocument();
      });
    });
  });

  describe('Features list', () => {
    it('should display all 7 features', async () => {
      render(<PlanosPage />);

      // Wait for page to render, then check features individually
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /SmartLic Pro/i })).toBeInTheDocument();
      });

      expect(screen.getByText(/1\.000 análises por mês/i)).toBeInTheDocument();
      expect(screen.getByText(/Exportação Excel completa/i)).toBeInTheDocument();
      expect(screen.getByText(/Pipeline de acompanhamento/i)).toBeInTheDocument();
      // This text appears in both plan description and features list - use getAllByText
      expect(screen.getAllByText(/Inteligência de decisão completa/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/5 anos de histórico/i)).toBeInTheDocument();
      expect(screen.getByText(/15 setores e 27 estados/i)).toBeInTheDocument();
      expect(screen.getByText(/Filtragem com 1\.000\+ regras/i)).toBeInTheDocument();
    });

    it('should show feature details', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Avalie oportunidades em todos os 27 estados/i)).toBeInTheDocument();
        expect(screen.getByText(/Relatórios detalhados para sua equipe/i)).toBeInTheDocument();
        expect(screen.getByText(/Gerencie oportunidades do início ao fim/i)).toBeInTheDocument();
      });
    });

    it('should show checkmark icons for all features', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        // Each feature should have a checkmark (✓)
        const features = screen.getAllByText('✓');
        expect(features.length).toBeGreaterThanOrEqual(7);
      });
    });
  });

  describe('CTA Button', () => {
    it('should render "Começar Agora" button', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Começar Agora/i })).toBeInTheDocument();
      });
    });

    it('should redirect to login if not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        session: null,
        user: null,
        isAdmin: false,
        loading: false,
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Começar Agora/i });
        fireEvent.click(ctaButton);
      });

      expect(window.location.href).toBe('/login');
    });

    it('should call checkout API when authenticated', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      // UX-339: Mock usePlan for trial user
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      // Mock /me endpoint returning regular user
      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      // UX-339: Trial user sees "Assinar agora" CTA
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Assinar agora/i })).toBeInTheDocument();
      });

      const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
      await act(async () => {
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/checkout?plan_id=smartlic_pro&billing_period=monthly'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token-123',
            }),
          })
        );
      });
    });

    it('should pass billing period to checkout API', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      // Switch to annual
      const annualRadio = screen.getByRole('radio', { name: /Anual.*Economize 20%/i });
      fireEvent.click(annualRadio);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('billing_period=annual'),
          expect.any(Object)
        );
      });
    });

    it('should redirect to checkout URL on success', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(window.location.href).toBe('https://checkout.stripe.com/123');
      });
    });

    it('should show loading state during checkout', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return new Promise((resolve) => setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          }), 100));
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Processando.../i })).toBeInTheDocument();
      });
    });

    it('should show error toast on checkout failure', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return Promise.resolve({
            ok: false,
            json: () => Promise.resolve({ detail: 'Payment failed' }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Payment failed');
      });
    });

    it('should show manage subscription button for active subscribers', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      // UX-339: Active subscriber sees "Gerenciar assinatura"
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'smartlic_pro', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'smartlic_pro', plan_name: 'SmartLic Pro', is_admin: false }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // Both banner and CTA show "Gerenciar assinatura"
        const buttons = screen.getAllByRole('button', { name: /Gerenciar assinatura/i });
        expect(buttons.length).toBeGreaterThanOrEqual(2);
        buttons.forEach(btn => expect(btn).not.toBeDisabled());
      });
    });
  });

  describe('FAQ Section', () => {
    it('should render FAQ section', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Perguntas Frequentes/i })).toBeInTheDocument();
      });
    });

    it('should render all 4 FAQ items', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Posso cancelar a qualquer momento\?/i)).toBeInTheDocument();
        expect(screen.getByText(/Existe contrato de fidelidade\?/i)).toBeInTheDocument();
        expect(screen.getByText(/O que acontece se eu cancelar\?/i)).toBeInTheDocument();
        expect(screen.getByText(/Como funciona a cobrança semestral e anual\?/i)).toBeInTheDocument();
      });
    });

    it('should toggle FAQ answer on click', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        // Initially, answers should be hidden
        expect(screen.queryByText(/Sim\. Sem contrato de fidelidade/i)).not.toBeInTheDocument();
      });

      const faqButton = screen.getByRole('button', { name: /Posso cancelar a qualquer momento\?/i });
      fireEvent.click(faqButton);

      await waitFor(() => {
        expect(screen.getByText(/Sim\. Sem contrato de fidelidade/i)).toBeInTheDocument();
      });

      // Click again to collapse
      fireEvent.click(faqButton);

      await waitFor(() => {
        expect(screen.queryByText(/Sim\. Sem contrato de fidelidade/i)).not.toBeInTheDocument();
      });
    });

    it('should close previous FAQ when opening new one', async () => {
      render(<PlanosPage />);

      // Open first FAQ
      const faq1 = screen.getByRole('button', { name: /Posso cancelar a qualquer momento\?/i });
      fireEvent.click(faq1);

      await waitFor(() => {
        expect(screen.getByText(/Sim\. Sem contrato de fidelidade/i)).toBeInTheDocument();
      });

      // Open second FAQ
      const faq2 = screen.getByRole('button', { name: /Existe contrato de fidelidade\?/i });
      fireEvent.click(faq2);

      await waitFor(() => {
        // Second answer should be visible
        expect(screen.getByText(/Não\. O SmartLic Pro funciona como acesso recorrente/i)).toBeInTheDocument();
        // First answer should be hidden
        expect(screen.queryByText(/Sim\. Sem contrato de fidelidade/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Subscriber status banner', () => {
    it('should show subscriber banner if user already has SmartLic Pro', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      // UX-339: Active subscriber
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'smartlic_pro', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'smartlic_pro', plan_name: 'SmartLic Pro', is_admin: false }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // UX-339: New banner text
        expect(screen.getByText(/Você possui acesso completo ao SmartLic/i)).toBeInTheDocument();
      });
    });

    it('should not show subscriber banner if user is on free trial', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.queryByTestId('status-banner-subscriber')).not.toBeInTheDocument();
      });
    });
  });

  describe('Status messages from URL', () => {
    it('should show success message when success param is present', async () => {
      window.location.search = '?success=true';

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Acesso ativado com sucesso! Bem-vindo ao SmartLic Pro/i)).toBeInTheDocument();
      });
    });

    it('should show cancelled message when cancelled param is present', async () => {
      window.location.search = '?cancelled=true';

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Processo cancelado/i)).toBeInTheDocument();
      });
    });
  });

  describe('Privileged user access', () => {
    it('should show privileged banner for admin users with full pricing visible', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: true,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'sala_guerra', plan_name: 'Sala de Guerra (Admin)', is_admin: true }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // UX-339: Now shows banner instead of overlay, pricing is visible
        expect(screen.getByText(/Você possui acesso completo ao SmartLic/i)).toBeInTheDocument();
        // Pricing card is now visible for admins too
        expect(screen.getByRole('heading', { name: /SmartLic Pro/i })).toBeInTheDocument();
      });
    });

    it('should show privileged banner for master plan users with pricing visible', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'master', plan_name: 'Master', is_admin: false }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // UX-339: Banner shows with full pricing below
        expect(screen.getByTestId('status-banner-privileged')).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: /SmartLic Pro/i })).toBeInTheDocument();
      });
    });

    it('should show link to /buscar in privileged banner', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: true,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'master', plan_name: 'Master', is_admin: true }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /Iniciar análise/i });
        expect(link).toHaveAttribute('href', '/buscar');
      });
    });
  });

  describe('Analytics tracking', () => {
    it('should track checkout_initiated event', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith('checkout_initiated', {
          plan_id: 'smartlic_pro',
          billing_period: 'monthly',
          source: 'planos_page',
        });
      });
    });

    it('should track checkout_failed event on error', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return Promise.resolve({
            ok: false,
            json: () => Promise.resolve({ detail: 'Checkout error' }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(mockTrackEvent).toHaveBeenCalledWith('checkout_failed', {
          plan_id: 'smartlic_pro',
          billing_period: 'monthly',
          error: 'Checkout error',
        });
      });
    });
  });

  describe('ROI Section', () => {
    it('should render ROI anchor message', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Uma única licitação ganha pode pagar um ano inteiro/i)).toBeInTheDocument();
      });
    });

    it('should show ROI comparison values', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/R\$\s*150\.000/)).toBeInTheDocument();
        expect(screen.getByText(/Oportunidade média/i)).toBeInTheDocument();
        expect(screen.getByText(/SmartLic Pro anual/i)).toBeInTheDocument();
      });
    });

    it('should show ROI multiplier', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Exemplo ilustrativo com base em oportunidades típicas do setor/i)).toBeInTheDocument();
      });
    });
  });

  describe('Bottom CTA', () => {
    it('should show link to continue with free trial', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /Continuar com período de avaliação/i });
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute('href', '/buscar');
      });
    });
  });

  describe('Stripe redirect overlay', () => {
    it('should show overlay during redirect to Stripe', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });
      mockUsePlan.mockReturnValue({
        planInfo: { plan_id: 'free_trial', subscription_status: 'active', trial_expires_at: null },
        loading: false, error: null, refresh: jest.fn(),
      });

      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          return new Promise((resolve) => setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          }), 100));
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /Assinar agora/i });
        fireEvent.click(ctaButton);
      });

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Redirecionando para o checkout/i })).toBeInTheDocument();
        expect(screen.getByText(/Você será redirecionado para o Stripe para concluir de forma segura/i)).toBeInTheDocument();
      });
    });
  });
});
