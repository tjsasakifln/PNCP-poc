/**
 * Regression Test: OAuth Google Callback Bug
 *
 * Bug: Login with Google redirects to homepage with ?code= parameter
 * instead of processing authentication and redirecting to /buscar.
 *
 * Root Cause: Flow type mismatch (implicit vs PKCE) and missing code exchange.
 *
 * This test ensures the callback handler properly processes OAuth authorization
 * codes from Google and exchanges them for a valid session.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import AuthCallbackPage from '../../app/auth/callback/page';
import { supabase } from '../../lib/supabase';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock Supabase client
jest.mock('../../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      getUser: jest.fn(),
      exchangeCodeForSession: jest.fn(),
      onAuthStateChange: jest.fn(),
    },
  },
}));

describe('AuthCallbackPage - OAuth Google Bug Regression', () => {
  const mockPush = jest.fn();
  const mockUnsubscribe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });

    // Mock window.location with both search and href
    delete (window as any).location;
    (window as any).location = { search: '', href: '' };
  });

  describe('PKCE Flow - Authorization Code Exchange', () => {
    it('should exchange authorization code for session (Google OAuth)', async () => {
      // Simulate Google OAuth callback with authorization code
      (window as any).location.search = '?code=0c41d9e0-6801-4bc3-8675-d26713161840';

      const mockSession = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        user: {
          id: 'user-123',
          email: 'user@example.com',
        },
      };

      // Mock successful code exchange
      (supabase.auth.exchangeCodeForSession as jest.Mock).mockResolvedValue({
        data: { session: mockSession },
        error: null,
      });

      render(<AuthCallbackPage />);

      // Should show loading state initially
      expect(screen.getByText(/processando autenticação/i)).toBeInTheDocument();

      // Should call exchangeCodeForSession with the authorization code
      await waitFor(() => {
        expect(supabase.auth.exchangeCodeForSession).toHaveBeenCalledWith(
          '0c41d9e0-6801-4bc3-8675-d26713161840'
        );
      });

      // Should show success state
      await waitFor(() => {
        expect(screen.getByText(/autenticação bem-sucedida/i)).toBeInTheDocument();
      });

      // Should redirect to /buscar after successful authentication (uses window.location.href)
      await waitFor(() => {
        expect(window.location.href).toBe('/buscar');
      }, { timeout: 1000 });
    });

    it('should handle code exchange error gracefully', async () => {
      (window as any).location.search = '?code=invalid-code';

      // Mock failed code exchange
      (supabase.auth.exchangeCodeForSession as jest.Mock).mockResolvedValue({
        data: { session: null },
        error: { message: 'Invalid authorization code' },
      });

      render(<AuthCallbackPage />);

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText(/falha na autenticação/i)).toBeInTheDocument();
        expect(screen.getByText(/invalid authorization code/i)).toBeInTheDocument();
      });

      // Should NOT redirect to /buscar
      expect(mockPush).not.toHaveBeenCalled();
    });

    it('should handle missing code parameter', async () => {
      (window as any).location.search = ''; // No code parameter

      // Mock getUser returning no user (component uses getUser instead of getSession)
      (supabase.auth.getUser as jest.Mock).mockResolvedValue({
        data: { user: null },
        error: null,
      });

      // Mock onAuthStateChange
      (supabase.auth.onAuthStateChange as jest.Mock).mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } },
      });

      render(<AuthCallbackPage />);

      // Should fall back to listening for auth state changes
      await waitFor(() => {
        expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling from OAuth Provider', () => {
    it('should display error when OAuth provider returns error', async () => {
      (window as any).location.search = '?error=access_denied&error_description=User+denied+access';

      render(<AuthCallbackPage />);

      // Should show error state immediately (no API calls)
      await waitFor(() => {
        expect(screen.getByText(/falha na autenticação/i)).toBeInTheDocument();
        expect(screen.getByText(/user denied access/i)).toBeInTheDocument();
      });

      // Should NOT attempt code exchange
      expect(supabase.auth.exchangeCodeForSession).not.toHaveBeenCalled();
    });
  });

  describe('Redirect After Authentication', () => {
    it('should redirect to /buscar after successful Google login', async () => {
      (window as any).location.search = '?code=valid-code-123';

      const mockSession = {
        access_token: 'token',
        user: { id: '123', email: 'test@example.com' },
      };

      (supabase.auth.exchangeCodeForSession as jest.Mock).mockResolvedValue({
        data: { session: mockSession },
        error: null,
      });

      render(<AuthCallbackPage />);

      // Wait for redirect (component uses window.location.href)
      await waitFor(() => {
        expect(window.location.href).toBe('/buscar');
      }, { timeout: 1000 });
    });
  });

  describe('Timeout Handling', () => {
    it('should timeout after 5 seconds if no session established', async () => {
      jest.useFakeTimers();

      (window as any).location.search = ''; // No code

      (supabase.auth.getUser as jest.Mock).mockResolvedValue({
        data: { user: null },
        error: null,
      });

      (supabase.auth.onAuthStateChange as jest.Mock).mockReturnValue({
        data: { subscription: { unsubscribe: mockUnsubscribe } },
      });

      const { container } = render(<AuthCallbackPage />);

      // Wait for initial render and async operations
      await waitFor(() => {
        expect(supabase.auth.onAuthStateChange).toHaveBeenCalled();
      });

      // Fast-forward 5 seconds
      jest.advanceTimersByTime(5000);

      // Run pending timers and promises
      await waitFor(() => {
        expect(mockUnsubscribe).toHaveBeenCalled();
      });

      // Verify error state is shown (timeout message)
      await waitFor(() => {
        const errorText = container.textContent;
        expect(errorText).toMatch(/timeout|erro/i);
      });

      jest.useRealTimers();
    });
  });
});
