/**
 * PlanosPage Component Tests
 *
 * Tests plan cards, checkout redirect, success/cancelled states
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import PlanosPage from '@/app/planos/page';

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

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock window.location
const originalLocation = window.location;

beforeEach(() => {
  jest.clearAllMocks();
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
        expect(screen.getByText(/Comece gratis com 3 buscas/i)).toBeInTheDocument();
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
        expect(backLink).toHaveAttribute('href', '/');
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
        expect(screen.getByText('Mensal')).toBeInTheDocument();
        expect(screen.getByText('Anual')).toBeInTheDocument();
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
        expect(screen.getByText('/mes')).toBeInTheDocument();
        expect(screen.getByText('/ano')).toBeInTheDocument();
      });
    });

    it('should highlight monthly plan as popular', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mais popular')).toBeInTheDocument();
      });
    });

    it('should show plan features', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getAllByText('Todos os setores').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Download Excel').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Resumo executivo IA').length).toBeGreaterThan(0);
      });
    });

    it('should show unlimited searches for subscription plans', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getAllByText('Buscas ilimitadas').length).toBe(2);
      });
    });

    it('should show search count for pack plans', async () => {
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('5 buscas')).toBeInTheDocument();
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
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ plans: mockPlans }),
      });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mensal')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /Assinar/i });
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
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ plans: mockPlans }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
        });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mensal')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /Assinar/i });
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
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ plans: mockPlans }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
        });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mensal')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /Assinar/i });
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
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ plans: mockPlans }),
        })
        .mockImplementationOnce(
          () => new Promise((resolve) => setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({ checkout_url: 'https://checkout.stripe.com/123' }),
          }), 100))
        );

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mensal')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /Assinar/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
      });

      expect(screen.getByRole('button', { name: /Redirecionando.../i })).toBeInTheDocument();
    });

    it('should show error alert on checkout failure', async () => {
      const mockAlert = jest.spyOn(window, 'alert').mockImplementation(() => {});

      const mockSession = { access_token: 'test-token-123' };
      mockUseAuth.mockReturnValue({
        session: mockSession,
        user: { id: '123' },
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ plans: mockPlans }),
        })
        .mockResolvedValueOnce({
          ok: false,
          json: () => Promise.resolve({ detail: 'Payment failed' }),
        });

      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText('Mensal')).toBeInTheDocument();
      });

      const subscribeButton = screen.getByRole('button', { name: /Assinar/i });
      await act(async () => {
        fireEvent.click(subscribeButton);
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Payment failed');
      });

      mockAlert.mockRestore();
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
});
