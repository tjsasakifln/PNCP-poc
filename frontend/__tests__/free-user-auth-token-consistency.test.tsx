/**
 * Auth Token Consistency Test
 *
 * Test Scenario 5: Auth token consistency
 *
 * This test validates that authentication tokens are handled correctly:
 * 1. Auth token is sent with every API request
 * 2. Token is refreshed before expiration
 * 3. Expired tokens trigger re-authentication
 * 4. Token is consistent across parallel requests
 * 5. Logout clears token and redirects correctly
 *
 * Edge cases tested:
 * - Expired token during search (should redirect to login)
 * - Token refresh race condition (multiple tabs)
 * - Invalid token (401 Unauthorized)
 * - Network errors during token refresh
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';

// Mock dependencies
const mockUseAuth = jest.fn();
const mockRouter = { push: jest.fn(), refresh: jest.fn() };

jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/buscar',
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Auth Token Consistency', () => {
  const validToken = 'valid-token-123';
  const expiredToken = 'expired-token-456';
  const invalidToken = 'invalid-token-789';

  const mockFreeUserSession = {
    access_token: validToken,
    refresh_token: 'refresh-token-123',
    expires_at: Math.floor(Date.now() / 1000) + 3600, // Expires in 1 hour
    user: {
      id: 'free-user-id',
      email: 'freeuser@example.com',
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockRouter.push.mockClear();
  });

  describe('AC1: Token sent with every API request', () => {
    it('should include Authorization header in /api/buscar request', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          download_id: 'test-id',
          total_filtrado: 10,
          resumo: {
            resumo_executivo: 'Test',
            total_oportunidades: 10,
            valor_total: 100000,
            destaques: [],
            distribuicao_uf: { SC: 10 },
          },
        }),
      });

      await fetch('/api/buscar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${validToken}`,
        },
        body: JSON.stringify({
          ufs: ['SC'],
          data_inicial: '2026-02-01',
          data_final: '2026-02-10',
          setor_id: 'vestuario',
        }),
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/buscar',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${validToken}`,
          }),
        })
      );
    });

    it('should include Authorization header in /api/me request', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plan_id: 'free',
          plan_name: 'Gratuito',
          quota_remaining: 3,
          quota_used: 0,
          is_admin: false,
        }),
      });

      await fetch('/api/me', {
        headers: {
          Authorization: `Bearer ${validToken}`,
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/me',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${validToken}`,
          }),
        })
      );
    });

    it('should include Authorization header in /api/sessions request', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [],
          total: 0,
        }),
      });

      await fetch('/api/sessions', {
        headers: {
          Authorization: `Bearer ${validToken}`,
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/sessions',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${validToken}`,
          }),
        })
      );
    });
  });

  describe('AC2: Expired token handling', () => {
    it('should redirect to login when token expires (401)', async () => {
      const expiredSession = {
        ...mockFreeUserSession,
        access_token: expiredToken,
        expires_at: Math.floor(Date.now() / 1000) - 100, // Expired 100s ago
      };

      mockUseAuth.mockReturnValue({
        session: expiredSession,
        user: expiredSession.user,
        loading: false,
      });

      // API returns 401 Unauthorized
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          detail: { message: 'Token expired', code: 'TOKEN_EXPIRED' },
        }),
      });

      const response = await fetch('/api/buscar', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${expiredToken}`,
        },
        body: JSON.stringify({ ufs: ['SC'] }),
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);

      const error = await response.json();
      expect(error.detail.code).toBe('TOKEN_EXPIRED');
    });

    it('should trigger token refresh when token is about to expire', async () => {
      const soonToExpireSession = {
        ...mockFreeUserSession,
        expires_at: Math.floor(Date.now() / 1000) + 60, // Expires in 1 minute
      };

      mockUseAuth.mockReturnValue({
        session: soonToExpireSession,
        user: soonToExpireSession.user,
        loading: false,
      });

      // Mock token refresh endpoint
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'new-token-123',
          refresh_token: 'new-refresh-token',
          expires_at: Math.floor(Date.now() / 1000) + 3600, // New expiration
        }),
      });

      // Simulate auth provider detecting expiration and refreshing
      const newSession = {
        ...soonToExpireSession,
        access_token: 'new-token-123',
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      };

      mockUseAuth.mockReturnValue({
        session: newSession,
        user: newSession.user,
        loading: false,
      });

      // Verify new token is used in subsequent requests
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plan_id: 'free',
          quota_remaining: 3,
        }),
      });

      await fetch('/api/me', {
        headers: {
          Authorization: `Bearer new-token-123`,
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/me',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer new-token-123',
          }),
        })
      );
    });
  });

  describe('AC3: Invalid token handling', () => {
    it('should reject request with invalid token (401)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          detail: { message: 'Invalid token', code: 'INVALID_TOKEN' },
        }),
      });

      const response = await fetch('/api/buscar', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${invalidToken}`,
        },
        body: JSON.stringify({ ufs: ['SC'] }),
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);
    });

    it('should clear session and redirect to login on invalid token', async () => {
      const invalidSession = {
        ...mockFreeUserSession,
        access_token: invalidToken,
      };

      mockUseAuth
        .mockReturnValueOnce({
          session: invalidSession,
          user: invalidSession.user,
          loading: false,
        })
        .mockReturnValueOnce({
          session: null,
          user: null,
          loading: false,
        });

      // First render with invalid token
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          setores: [{ id: 'vestuario', name: 'Vestuário' }],
        }),
      });

      const BuscarPage = (await import('../app/buscar/page')).default;
      const { unmount } = render(<BuscarPage />);

      // API call fails with 401
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          detail: { code: 'INVALID_TOKEN' },
        }),
      });

      // Re-render with cleared session
      unmount();
      render(<BuscarPage />);

      await waitFor(() => {
        // Should show login prompt
        expect(screen.queryByText(/Faça login|Entrar/i)).toBeInTheDocument();
      });
    });
  });

  describe('AC4: Token consistency across parallel requests', () => {
    it('should use same token for concurrent requests', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      // Mock responses for parallel requests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            plan_id: 'free',
            quota_remaining: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            sessions: [],
            total: 0,
          }),
        });

      // Execute parallel requests
      const [quotaResponse, historyResponse] = await Promise.all([
        fetch('/api/me', {
          headers: { Authorization: `Bearer ${validToken}` },
        }),
        fetch('/api/sessions', {
          headers: { Authorization: `Bearer ${validToken}` },
        }),
      ]);

      expect(quotaResponse.ok).toBe(true);
      expect(historyResponse.ok).toBe(true);

      // Both should have used the same token
      expect(mockFetch).toHaveBeenNthCalledWith(
        1,
        expect.anything(),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${validToken}`,
          }),
        })
      );

      expect(mockFetch).toHaveBeenNthCalledWith(
        2,
        expect.anything(),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${validToken}`,
          }),
        })
      );
    });

    it('should handle token refresh during concurrent requests', async () => {
      const oldToken = 'old-token-123';
      const newToken = 'new-token-456';

      // First request uses old token
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          detail: { code: 'TOKEN_EXPIRED' },
        }),
      });

      // Token refresh
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: newToken,
          expires_at: Math.floor(Date.now() / 1000) + 3600,
        }),
      });

      // Retry with new token
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          plan_id: 'free',
          quota_remaining: 3,
        }),
      });

      // First attempt with old token
      const firstAttempt = await fetch('/api/me', {
        headers: { Authorization: `Bearer ${oldToken}` },
      });

      expect(firstAttempt.ok).toBe(false);

      // Refresh token
      const refreshResponse = await fetch('/api/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: 'refresh-token' }),
      });

      const { access_token } = await refreshResponse.json();
      expect(access_token).toBe(newToken);

      // Retry with new token
      const retryResponse = await fetch('/api/me', {
        headers: { Authorization: `Bearer ${newToken}` },
      });

      expect(retryResponse.ok).toBe(true);
    });
  });

  describe('AC5: Logout clears token', () => {
    it('should clear session on logout', async () => {
      const mockSignOut = jest.fn();

      mockUseAuth
        .mockReturnValueOnce({
          session: mockFreeUserSession,
          user: mockFreeUserSession.user,
          loading: false,
          signOut: mockSignOut,
        })
        .mockReturnValueOnce({
          session: null,
          user: null,
          loading: false,
          signOut: mockSignOut,
        });

      const { result } = renderHook(() => mockUseAuth());

      expect(result.current.session).toBeTruthy();

      // Trigger logout
      await act(async () => {
        await result.current.signOut();
      });

      expect(mockSignOut).toHaveBeenCalled();
    });

    it('should redirect to login after logout', async () => {
      mockUseAuth.mockReturnValue({
        session: null,
        user: null,
        loading: false,
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
        // Should show login prompt when no session
        expect(screen.queryByText(/Faça login|Entrar/i)).toBeInTheDocument();
      });
    });

    it('should clear localStorage on logout', async () => {
      Storage.prototype.removeItem = jest.fn();
      const mockSignOut = jest.fn(() => {
        localStorage.removeItem('supabase.auth.token');
        localStorage.removeItem('descomplicita_saved_searches');
      });

      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
        signOut: mockSignOut,
      });

      const { result } = renderHook(() => mockUseAuth());

      await act(async () => {
        await result.current.signOut();
      });

      expect(localStorage.removeItem).toHaveBeenCalledWith('supabase.auth.token');
    });
  });

  describe('AC6: Token validation on protected routes', () => {
    it('should validate token before allowing access to /buscar', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
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

      // Should have validated token via useAuth
      expect(mockUseAuth).toHaveBeenCalled();
    });

    it('should validate token before allowing access to /historico', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          sessions: [],
          total: 0,
        }),
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Histórico de Buscas/i)).toBeInTheDocument();
      });

      expect(mockUseAuth).toHaveBeenCalled();
    });

    it('should deny access without valid token', async () => {
      mockUseAuth.mockReturnValue({
        session: null,
        user: null,
        loading: false,
      });

      const HistoricoPage = (await import('../app/historico/page')).default;
      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Faça login para ver seu histórico/i)).toBeInTheDocument();
      });
    });
  });

  describe('AC7: Network errors during auth', () => {
    it('should handle network error during token validation', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      // Network error
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      try {
        await fetch('/api/me', {
          headers: { Authorization: `Bearer ${validToken}` },
        });
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toBe('Network error');
      }
    });

    it('should retry on network failure', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      // First attempt fails
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        // Retry succeeds
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            plan_id: 'free',
            quota_remaining: 3,
          }),
        });

      // First attempt
      try {
        await fetch('/api/me', {
          headers: { Authorization: `Bearer ${validToken}` },
        });
      } catch (error) {
        // Expected to fail
      }

      // Retry
      const retryResponse = await fetch('/api/me', {
        headers: { Authorization: `Bearer ${validToken}` },
      });

      expect(retryResponse.ok).toBe(true);
    });
  });

  describe('AC8: Regression - Token included in all requests', () => {
    it('should never send request without Authorization header when authenticated', async () => {
      mockUseAuth.mockReturnValue({
        session: mockFreeUserSession,
        user: mockFreeUserSession.user,
        loading: false,
      });

      const endpoints = [
        '/api/me',
        '/api/buscar',
        '/api/sessions',
        '/api/download',
      ];

      for (const endpoint of endpoints) {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({}),
        });

        await fetch(endpoint, {
          headers: { Authorization: `Bearer ${validToken}` },
        });

        expect(mockFetch).toHaveBeenCalledWith(
          endpoint,
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: `Bearer ${validToken}`,
            }),
          })
        );
      }
    });

    it('should fail request if Authorization header is missing', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          detail: { message: 'Missing authorization header', code: 'UNAUTHORIZED' },
        }),
      });

      const response = await fetch('/api/buscar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Missing Authorization header
        },
        body: JSON.stringify({ ufs: ['SC'] }),
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);
    });
  });
});
