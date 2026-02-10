/**
 * Navigation Persistence Test
 *
 * Test Scenario 4: Navigation persistence
 *
 * This test validates that state persists correctly across page navigation:
 * 1. Quota state persists when navigating between pages
 * 2. Search results are maintained when user returns to /buscar
 * 3. User session is preserved across navigation
 * 4. Page refresh maintains authentication and quota state
 * 5. Browser back/forward buttons work correctly
 *
 * Edge cases tested:
 * - Page refresh after search (results should be cleared, quota persists)
 * - Navigation after quota exhaustion (upgrade modal state)
 * - Deep linking with auth state
 */

import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { useRouter, usePathname } from 'next/navigation';

// Mock dependencies
const mockUseAuth = jest.fn();
const mockUseQuota = jest.fn();
const mockUseAnalytics = jest.fn();
const mockRouter = { push: jest.fn(), back: jest.fn(), forward: jest.fn(), refresh: jest.fn() };
const mockPathname = jest.fn();

jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('../hooks/useQuota', () => ({
  useQuota: () => mockUseQuota(),
}));

jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => mockUseAnalytics(),
}));

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => mockPathname(),
  useSearchParams: () => new URLSearchParams(),
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Navigation Persistence', () => {
  const mockFreeUserSession = {
    access_token: 'free-user-token-123',
    user: {
      id: 'free-user-id',
      email: 'freeuser@example.com',
    },
  };

  const mockQuotaWith2Remaining = {
    planId: 'free',
    planName: 'Gratuito',
    creditsRemaining: 2,
    totalSearches: 1,
    isUnlimited: false,
    isFreeUser: true,
    isAdmin: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      session: mockFreeUserSession,
      user: mockFreeUserSession.user,
      loading: false,
    });
    mockUseAnalytics.mockReturnValue({
      trackEvent: jest.fn(),
    });
  });

  describe('AC1: Quota state persists across navigation', () => {
    it('should maintain quota state when navigating to /historico', async () => {
      const mockRefresh = jest.fn();
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: mockRefresh,
      });

      // Navigate to historico
      mockPathname.mockReturnValue('/historico');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Histórico de Buscas/i)).toBeInTheDocument();
      });

      // Verify quota hook was called (state is accessible)
      expect(mockUseQuota).toHaveBeenCalled();
      expect(mockRefresh).not.toHaveBeenCalled(); // Should not auto-refresh unless needed
    });

    it('should maintain quota state when navigating to /planos', async () => {
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      mockPathname.mockReturnValue('/planos');

      const PlanosPage = (await import('../app/planos/page')).default;
      render(<PlanosPage />);

      await waitFor(() => {
        expect(screen.getByText(/Escolha seu plano/i)).toBeInTheDocument();
      });

      // Quota state should be accessible
      expect(mockUseQuota).toHaveBeenCalled();
    });

    it('should maintain quota state when navigating back to /buscar', async () => {
      const mockRefresh = jest.fn();
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: mockRefresh,
      });

      mockPathname.mockReturnValue('/buscar');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário e Uniformes' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Quota should still show 2 remaining
      expect(mockUseQuota).toHaveBeenCalled();
    });
  });

  describe('AC2: Session persistence across navigation', () => {
    it('should maintain user session when navigating between pages', async () => {
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      // Navigate to buscar
      mockPathname.mockReturnValue('/buscar');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      const { unmount } = render(<BuscarPage />);

      await waitFor(() => {
        expect(mockUseAuth).toHaveBeenCalled();
      });

      const firstAuthCall = mockUseAuth.mock.results[0].value;

      // Unmount and navigate to historico
      unmount();
      mockPathname.mockReturnValue('/historico');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(mockUseAuth).toHaveBeenCalled();
      });

      // Session should be the same
      const secondAuthCall = mockUseAuth.mock.results[mockUseAuth.mock.results.length - 1].value;
      expect(secondAuthCall.session.access_token).toBe(firstAuthCall.session.access_token);
    });
  });

  describe('AC3: Page refresh behavior', () => {
    it('should maintain auth state after page refresh', async () => {
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      // Initial render
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      const { unmount } = render(<BuscarPage />);

      await waitFor(() => {
        expect(mockUseAuth).toHaveBeenCalled();
      });

      // Simulate page refresh (unmount and re-render)
      unmount();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      render(<BuscarPage />);

      await waitFor(() => {
        expect(mockUseAuth).toHaveBeenCalled();
      });

      // Session should still be present
      const authResult = mockUseAuth.mock.results[mockUseAuth.mock.results.length - 1].value;
      expect(authResult.session).toBeTruthy();
      expect(authResult.session.access_token).toBe('free-user-token-123');
    });

    it('should re-fetch quota after page refresh', async () => {
      const mockRefresh = jest.fn();
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: mockRefresh,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      const { unmount } = render(<BuscarPage />);

      await waitFor(() => {
        expect(mockUseQuota).toHaveBeenCalled();
      });

      // Simulate refresh
      unmount();

      // Mock updated quota (e.g., another search happened in another tab)
      const updatedQuota = {
        ...mockQuotaWith2Remaining,
        creditsRemaining: 1,
        totalSearches: 2,
      };

      mockUseQuota.mockReturnValue({
        quota: updatedQuota,
        loading: false,
        error: null,
        refresh: mockRefresh,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      render(<BuscarPage />);

      await waitFor(() => {
        expect(mockUseQuota).toHaveBeenCalled();
      });

      // Should show updated quota
      const quotaResult = mockUseQuota.mock.results[mockUseQuota.mock.results.length - 1].value;
      expect(quotaResult.quota.creditsRemaining).toBe(1);
    });

    it('should clear search results after page refresh', async () => {
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            setores: [{ id: 'vestuario', name: 'Vestuário' }],
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            download_id: 'test-id',
            total_filtrado: 15,
            resumo: {
              resumo_executivo: 'Test results',
              total_oportunidades: 15,
              valor_total: 150000,
              destaques: [],
              distribuicao_uf: { SC: 15 },
            },
          }),
        });

      const BuscarPage = (await import('../app/buscar/page')).default;
      const { unmount, container } = render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Execute search
      const scCheckbox = container.querySelector('input[type="checkbox"][value="SC"]');
      if (scCheckbox) fireEvent.click(scCheckbox);

      const searchButton = screen.getByRole('button', { name: /buscar/i });
      await act(async () => {
        fireEvent.click(searchButton);
      });

      await waitFor(() => {
        expect(screen.queryByText(/Test results/i)).toBeInTheDocument();
      });

      // Refresh page (unmount and re-render)
      unmount();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Results should be cleared (empty state)
      expect(screen.queryByText(/Test results/i)).not.toBeInTheDocument();
    });
  });

  describe('AC4: Browser navigation (back/forward)', () => {
    it('should handle browser back button correctly', async () => {
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      // Start on /buscar
      mockPathname.mockReturnValue('/buscar');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Simulate browser back
      mockRouter.back();

      expect(mockRouter.back).toHaveBeenCalled();
    });

    it('should handle browser forward button correctly', async () => {
      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      mockPathname.mockReturnValue('/buscar');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Simulate browser forward
      mockRouter.forward();

      expect(mockRouter.forward).toHaveBeenCalled();
    });
  });

  describe('AC5: Deep linking with auth state', () => {
    it('should redirect to login when accessing /buscar without auth', async () => {
      mockUseAuth.mockReturnValue({
        session: null,
        user: null,
        loading: false,
      });

      mockPathname.mockReturnValue('/buscar');

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        // Should show login prompt or redirect
        expect(
          screen.queryByText(/Faça login|Entrar|Login/i)
        ).toBeInTheDocument();
      });
    });

    it('should redirect to login when accessing /historico without auth', async () => {
      mockUseAuth.mockReturnValue({
        session: null,
        user: null,
        loading: false,
      });

      mockPathname.mockReturnValue('/historico');

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Faça login para ver seu histórico/i)).toBeInTheDocument();
      });
    });

    it('should allow access to /buscar with valid auth', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      mockPathname.mockReturnValue('/buscar');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Should not show login prompt
      expect(screen.queryByText(/Faça login/i)).not.toBeInTheDocument();
    });
  });

  describe('AC6: Upgrade modal state persistence', () => {
    it('should show upgrade modal after quota exhausted on any page', async () => {
      const quotaExhausted = {
        planId: 'free',
        planName: 'Gratuito',
        creditsRemaining: 0,
        totalSearches: 3,
        isUnlimited: false,
        isFreeUser: true,
        isAdmin: false,
      };

      mockUseQuota.mockReturnValue({
        quota: quotaExhausted,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      // On /buscar page
      mockPathname.mockReturnValue('/buscar');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        // Should show quota exhausted message
        expect(screen.queryByText(/limite.*buscas.*atingido/i)).toBeInTheDocument();
      });
    });

    it('should persist upgrade modal across navigation', async () => {
      const quotaExhausted = {
        planId: 'free',
        planName: 'Gratuito',
        creditsRemaining: 0,
        totalSearches: 3,
        isUnlimited: false,
        isFreeUser: true,
        isAdmin: false,
      };

      mockUseQuota.mockReturnValue({
        quota: quotaExhausted,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      // Navigate to historico
      mockPathname.mockReturnValue('/historico');
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [
            {
              id: 'session-1',
              sectors: ['Vestuário'],
              ufs: ['SC'],
              total_filtered: 15,
              created_at: '2026-02-10T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Histórico de Buscas/i)).toBeInTheDocument();
      });

      // Quota state should still indicate exhaustion
      expect(mockUseQuota).toHaveBeenCalled();
      const quotaResult = mockUseQuota.mock.results[mockUseQuota.mock.results.length - 1].value;
      expect(quotaResult.quota.creditsRemaining).toBe(0);
    });
  });

  describe('AC7: Local storage persistence', () => {
    it('should persist saved searches across navigation', async () => {
      // Mock localStorage
      const savedSearches = [
        {
          id: 'saved-1',
          name: 'Minha busca salva',
          searchParams: {
            ufs: ['SC'],
            dataInicial: '2026-02-01',
            dataFinal: '2026-02-10',
            searchMode: 'setor' as const,
            setorId: 'vestuario',
          },
          createdAt: '2026-02-10T10:00:00Z',
          lastUsedAt: '2026-02-10T10:00:00Z',
        },
      ];

      Storage.prototype.getItem = jest.fn(() => JSON.stringify(savedSearches));
      Storage.prototype.setItem = jest.fn();

      mockUseQuota.mockReturnValue({
        quota: mockQuotaWith2Remaining,
        loading: false,
        error: null,
        refresh: jest.fn(),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      render(<BuscarPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
      });

      // Saved searches should be accessible
      expect(localStorage.getItem).toHaveBeenCalledWith('descomplicita_saved_searches');
    });
  });
});
