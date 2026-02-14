/**
 * PlanosPage Component Tests
 *
 * Tests plan cards, checkout redirect, success/cancelled states
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import PlanosPage from '@/app/planos/page';
import { toast } from 'sonner';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
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
});

afterAll(() => {
  window.location = originalLocation;
});

describe('PlanosPage Component', () => {
  describe('Initial render', () => {
    it('should render page title', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: [] }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Escolha seu plano/i })).toBeInTheDocument();
      });
    });

    it('should render subtitle', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: [] }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Comece gr[aá]tis com 3 buscas/i)).toBeInTheDocument();
      });
    });

    it('should show back link', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: [] }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const backLink = screen.getByRole('link', { name: /Voltar para buscas/i });
        expect(backLink).toBeInTheDocument();
        expect(backLink).toHaveAttribute('href', '/buscar');
      });
    });
  });

  describe('Loading state', () => {
    it('should show loading skeletons', async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ plans: [] }),
        }), 100))
      );

      render(<PlanosPage />);

      // Should show skeleton loaders
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Plan display', () => {
    const mockPlans = [
      {
        id: 'pack_5',
        name: 'Pacote 5',
        description: '5 buscas avulsas',
        max_searches: 5,
        price_brl: 49.90,
        duration_days: null,
      },
      {
        id: 'monthly',
        name: 'Mensal',
        description: 'Buscas ilimitadas por mes',
        max_searches: null,
        price_brl: 99.90,
        duration_days: 30,
      },
      {
        id: 'annual',
        name: 'Anual',
        description: 'Buscas ilimitadas por ano',
        max_searches: null,
        price_brl: 999.90,
        duration_days: 365,
      },
    ];

    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: mockPlans }),
      });
    });

    it('should display plan cards', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Pacote 5')).toBeInTheDocument();
        // "Mensal" and "Anual" appear in both PlanToggle and plan cards
        expect(screen.getAllByText('Mensal').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('Anual').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display plan descriptions', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('5 buscas avulsas')).toBeInTheDocument();
        expect(screen.getByText('Buscas ilimitadas por mes')).toBeInTheDocument();
        expect(screen.getByText('Buscas ilimitadas por ano')).toBeInTheDocument();
      });
    });

    it('should format prices in BRL', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        // Brazilian currency format
        expect(screen.getByText(/R\$\s*49,90/)).toBeInTheDocument();
        expect(screen.getByText(/R\$\s*99,90/)).toBeInTheDocument();
        expect(screen.getByText(/R\$\s*999,90/)).toBeInTheDocument();
      });
    });

    it('should show duration labels for subscription plans', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        // Duration labels appear as part of pricing: "/mês" or "/ano"
        // The PlanToggle also has "Mensal" and "Anual" buttons
        expect(screen.getAllByText(/\/m[eê]s/).length).toBeGreaterThan(0);
      });
    });

    it('should highlight maquina plan as popular', async () => {
      // Reset mock with plans including maquina
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plans: [
            ...mockPlans,
            {
              id: 'maquina',
              name: 'Maquina',
              description: 'Plano intermediario',
              max_searches: 300,
              price_brl: 597,
              duration_days: 30,
            },
          ],
        }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mais popular')).toBeInTheDocument();
      });
    });

    it('should show dynamic plan features based on plan capabilities', async () => {
      // Reset mock with new plan structure
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plans: [
            {
              id: 'consultor_agil',
              name: 'Consultor Agil',
              description: 'Plano basico',
              max_searches: 50,
              price_brl: 297,
              duration_days: 30,
            },
            {
              id: 'maquina',
              name: 'Maquina',
              description: 'Plano intermediario',
              max_searches: 300,
              price_brl: 597,
              duration_days: 30,
            },
          ],
        }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // Check for dynamic features (rendered with accent: mês)
        // Multiple elements may match (desktop list + mobile summary)
        expect(screen.getAllByText(/50 buscas\/m[eê]s/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/300 buscas\/m[eê]s/).length).toBeGreaterThan(0);
      });
    });

    it('should show Excel as blocked for consultor_agil plan', async () => {
      // Reset mock with consultor_agil plan
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plans: [
            {
              id: 'consultor_agil',
              name: 'Consultor Agil',
              description: 'Plano basico',
              max_searches: 50,
              price_brl: 297,
              duration_days: 30,
            },
          ],
        }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // The text should have line-through style (blocked Excel)
        const excelText = screen.getByText('Download Excel');
        expect(excelText).toHaveClass('line-through');
      });
    });

    it('should show Excel as available for maquina plan', async () => {
      // Reset mock with maquina plan
      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plans: [
            {
              id: 'maquina',
              name: 'Maquina',
              description: 'Plano intermediario',
              max_searches: 300,
              price_brl: 597,
              duration_days: 30,
            },
          ],
        }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // Excel should be available (no line-through)
        const excelText = screen.getByText('Download Excel');
        expect(excelText).not.toHaveClass('line-through');
      });
    });

    it('should filter out free and master plans', async () => {
      const plansWithFreeAndMaster = [
        ...mockPlans,
        { id: 'free', name: 'Free', description: 'Gratis', max_searches: 3, price_brl: 0, duration_days: null },
        { id: 'master', name: 'Master', description: 'Admin', max_searches: null, price_brl: 0, duration_days: null },
      ];

      mockFetch.mockReset();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: plansWithFreeAndMaster }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.queryByText('Free')).not.toBeInTheDocument();
        expect(screen.queryByText('Master')).not.toBeInTheDocument();
      });
    });
  });

  describe('Checkout flow', () => {
    const mockPlans = [
      {
        id: 'monthly',
        name: 'Mensal',
        description: 'Test plan',
        max_searches: null,
        price_brl: 99.90,
        duration_days: 30,
      },
    ];

    it('should redirect to login if not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        session: null,
        user: null,
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: mockPlans }),
      });

      render(<PlanosPage />);

      // Wait for plan name to appear (might conflict with toggle label "Mensal")
      await waitFor(() => {
        expect(screen.getByText('Test plan')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /^Assinar$/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
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

      // Mock endpoints: /me (returns regular user), /plans, /checkout
      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
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
        expect(screen.getByText('Test plan')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /^Assinar$/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/checkout?plan_id=monthly'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token-123',
            }),
          })
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

      // Mock endpoints: /me (returns regular user), /plans, /checkout
      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
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
        expect(screen.getByText('Test plan')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /^Assinar$/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
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

      let checkoutCalled = false;
      // Mock endpoints: /me (returns regular user), /plans, /checkout (delayed)
      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        if (url.includes('/checkout') && options?.method === 'POST') {
          checkoutCalled = true;
          return new Promise((resolve) => setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          }), 100));
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Test plan')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /^Assinar$/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
      });

      expect(screen.getByRole('button', { name: /Redirecionando.../i })).toBeInTheDocument();
    });

    it('should show error toast on checkout failure', async () => {
      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      // Mock endpoints: /me (returns regular user), /plans, /checkout (fails)
      mockFetch.mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plan_id: 'free_trial', plan_name: 'FREE Trial', is_admin: false }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
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
        expect(screen.getByText('Test plan')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /^Assinar$/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
      });

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Payment failed');
      });
    });
  });

  describe('Status messages from URL', () => {
    it('should show success message when success param is present', async () => {
      window.location.search = '?success=true';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: [] }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Pagamento realizado com sucesso/i)).toBeInTheDocument();
      });
    });

    it('should show cancelled message when cancelled param is present', async () => {
      window.location.search = '?cancelled=true';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: [] }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Pagamento cancelado/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error handling', () => {
    it('should handle fetch error gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      render(<PlanosPage />);

      // Should not crash, just show no plans
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Escolha seu plano/i })).toBeInTheDocument();
      });
    });

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<PlanosPage />);

      // Should not crash
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Escolha seu plano/i })).toBeInTheDocument();
      });
    });
  });

  describe('Privileged user access', () => {
    it('should show admin message for isAdmin users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: true,
        loading: false,
      });

      // Mock /me endpoint returning admin profile
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'sala_guerra',
              plan_name: 'Sala de Guerra (Admin)',
              is_admin: true
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: [] }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /administrador/i })).toBeInTheDocument();
      });

      // Should show admin link (with or without accent)
      expect(screen.getByRole('link', { name: /Gerenciar usu[aá]rios/i })).toBeInTheDocument();
    });

    it('should show master message for master plan users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      // Mock /me endpoint returning master profile (not admin, but master plan)
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'master',
              plan_name: 'Master',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: [] }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /acesso Master/i })).toBeInTheDocument();
      });

      // Should NOT show admin link for master users (with or without accent)
      expect(screen.queryByRole('link', { name: /Gerenciar usu[aá]rios/i })).not.toBeInTheDocument();
    });

    it('should show sala_guerra message for sala_guerra plan users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      // Mock /me endpoint returning sala_guerra profile
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'sala_guerra',
              plan_name: 'Sala de Guerra',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: [] }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Sala de Guerra/i })).toBeInTheDocument();
      });
    });

    it('should show pricing for regular users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      const mockPlans = [
        {
          id: 'monthly',
          name: 'Mensal',
          description: 'Test plan',
          max_searches: null,
          price_brl: 99.90,
          duration_days: 30,
        },
      ];

      // Mock /me endpoint returning regular user profile
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'free_trial',
              plan_name: 'FREE Trial',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      // Wait for both profile and plans to load, then check for pricing page
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Escolha seu plano/i })).toBeInTheDocument();
        expect(screen.getByText('Test plan')).toBeInTheDocument();
      });
    });

    it('should handle profile fetch error gracefully', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      const mockPlans = [
        {
          id: 'monthly',
          name: 'Mensal',
          description: 'Test plan',
          max_searches: null,
          price_brl: 99.90,
          duration_days: 30,
        },
      ];

      // Mock /me endpoint failing
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({ ok: false, status: 500 });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      // Should still show pricing page (graceful fallback)
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Escolha seu plano/i })).toBeInTheDocument();
      });
    });
  });

  describe('Upgrade/Downgrade for paying users', () => {
    const mockPlans = [
      {
        id: 'pack_5',
        name: 'Pacote 5',
        description: '5 buscas avulsas',
        max_searches: 5,
        price_brl: 49.90,
        duration_days: null,
      },
      {
        id: 'monthly',
        name: 'Mensal',
        description: 'Buscas ilimitadas por mes',
        max_searches: null,
        price_brl: 297,
        duration_days: 30,
      },
      {
        id: 'annual',
        name: 'Anual',
        description: 'Buscas ilimitadas por ano',
        max_searches: null,
        price_brl: 597,
        duration_days: 365,
      },
    ];

    it('should show "Gerenciar sua assinatura" title for paying users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'monthly',
              plan_name: 'Consultor Agil',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Gerenciar sua assinatura/i })).toBeInTheDocument();
      });
    });

    it('should show current plan banner for paying users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'monthly',
              plan_name: 'Consultor Agil',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Seu plano atual:/i)).toBeInTheDocument();
        expect(screen.getByText('Consultor Agil')).toBeInTheDocument();
      });
    });

    it('should show "Seu plano atual" badge and button on current plan card', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'monthly',
              plan_name: 'Mensal',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // Should have badge and button with "Seu plano atual"
        const elements = screen.getAllByText('Seu plano atual');
        expect(elements.length).toBe(2); // badge + button
      });
    });

    it('should show "Fazer upgrade" button for higher tier plans', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'pack_5',
              plan_name: 'Pacote 5',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const upgradeButtons = screen.getAllByRole('button', { name: /Fazer upgrade/i });
        expect(upgradeButtons.length).toBeGreaterThan(0);
      });
    });

    it('should show "Fazer downgrade" button for lower tier plans', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'annual',
              plan_name: 'Anual',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const downgradeButtons = screen.getAllByRole('button', { name: /Fazer downgrade/i });
        expect(downgradeButtons.length).toBeGreaterThan(0);
      });
    });

    it('should show downgrade warning text', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'annual',
              plan_name: 'Anual',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        // Should have at least one downgrade warning (pack_5 and monthly are lower than annual)
        const warnings = screen.getAllByText(/perdera recursos/i);
        expect(warnings.length).toBeGreaterThan(0);
      });
    });

    it('should disable current plan button', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'monthly',
              plan_name: 'Mensal',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const currentPlanButton = screen.getByRole('button', { name: /Seu plano atual/i });
        expect(currentPlanButton).toBeDisabled();
      });
    });

    it('should show link to account details for paying users', async () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token' },
        user: { id: '123' },
        isAdmin: false,
        loading: false,
      });

      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/me')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              plan_id: 'monthly',
              plan_name: 'Mensal',
              is_admin: false
            }),
          });
        }
        if (url.includes('/plans')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ plans: mockPlans }),
          });
        }
        return Promise.resolve({ ok: false });
      });

      render(<PlanosPage />);

      await waitFor(() => {
        const accountLink = screen.getByRole('link', { name: /Ver detalhes da conta/i });
        expect(accountLink).toBeInTheDocument();
        expect(accountLink).toHaveAttribute('href', '/conta');
      });
    });
  });
});
