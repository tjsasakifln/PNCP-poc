/**
 * HistoricoPage Component Tests
 *
 * Tests session list, pagination, loading states, authentication
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import HistoricoPage from '@/app/historico/page';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Next.js navigation (required by PageHeader → MobileDrawer)
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn(), back: jest.fn() }),
  usePathname: () => '/historico',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

// Mock analytics hook (required by HistoricoPage directly)
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), resetUser: jest.fn() }),
}));

// Mock ThemeProvider (required by PageHeader → ThemeToggle)
jest.mock('../../app/components/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'light', setTheme: jest.fn() }),
}));

// Mock sub-components imported by PageHeader to avoid deep dependency chains
jest.mock('../../app/components/ThemeToggle', () => ({
  ThemeToggle: () => null,
}));

jest.mock('../../app/components/UserMenu', () => ({
  UserMenu: () => null,
}));

jest.mock('../../app/components/QuotaBadge', () => ({
  QuotaBadge: () => null,
}));

jest.mock('../../components/MobileDrawer', () => ({
  MobileDrawer: () => null,
}));

// Mock useQuota (used by QuotaBadge — already mocked above, but guard)
jest.mock('../../hooks/useQuota', () => ({
  useQuota: () => ({ quota: null, loading: false, refresh: jest.fn() }),
}));

// Mock error-messages (useSearch and historico page import these)
jest.mock('../../lib/error-messages', () => ({
  getUserFriendlyError: (msg: string) => msg,
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('HistoricoPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
  });

  describe('Loading state', () => {
    it('should show loading message during auth check', () => {
      mockUseAuth.mockReturnValue({
        session: null,
        loading: true,
      });

      render(<HistoricoPage />);

      expect(screen.getByText('Carregando...')).toBeInTheDocument();
    });
  });

  describe('Unauthenticated state', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: null,
        loading: false,
      });
    });

    it('should show login prompt when not authenticated', () => {
      render(<HistoricoPage />);

      // Page renders: "Fa\u00e7a login para ver seu hist\u00f3rico"
      // JSX unicode escapes in string literals are NOT decoded by SWC — they render
      // as literal backslash-u sequences. Match by partial text that is unambiguous.
      const loginPrompt = screen.getByText(/login para ver seu/i);
      expect(loginPrompt).toBeInTheDocument();
    });

    it('should show login link', () => {
      render(<HistoricoPage />);

      const loginLink = screen.getByRole('link', { name: /Ir para login/i });
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute('href', '/login');
    });
  });

  describe('Authenticated state', () => {
    const mockSession = {
      access_token: 'test-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
      });
    });

    it('should fetch sessions on mount', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/sessions'),
          expect.objectContaining({
            headers: { Authorization: 'Bearer test-token-123' },
          })
        );
      });
    });

    it('should show page title in header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      render(<HistoricoPage />);

      // PageHeader renders an h1 with title="Hist\u00f3rico" (JSX literal — backslash-u not decoded).
      // Use partial text match to avoid unicode escape issues.
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
      expect(heading.textContent).toContain('Hist');
    });

    it('should show loading skeletons while fetching', async () => {
      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ sessions: [], total: 0 }),
        }), 100))
      );

      render(<HistoricoPage />);

      // Should show skeleton loaders
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should show empty state when no sessions', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      render(<HistoricoPage />);

      // EmptyState component is shown with data-testid="empty-state"
      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      });
    });

    it('should show link to make first search when empty', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const searchLink = screen.getByRole('link', { name: /Fazer primeira busca/i });
        expect(searchLink).toBeInTheDocument();
        expect(searchLink).toHaveAttribute('href', '/buscar');
      });
    });

    it('should display session list', async () => {
      const mockSessions = [
        {
          id: '1',
          sectors: ['vestuario'],
          ufs: ['SP', 'RJ'],
          data_inicial: '2024-01-01',
          data_final: '2024-01-07',
          custom_keywords: null,
          total_raw: 100,
          total_filtered: 25,
          valor_total: 150000,
          resumo_executivo: 'Test summary',
          created_at: '2024-01-07T10:30:00Z',
          status: 'completed',
          error_message: null,
          error_code: null,
          duration_ms: null,
          pipeline_stage: null,
          started_at: '2024-01-07T10:30:00Z',
          response_state: 'live',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: mockSessions, total: 1 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/SP, RJ/)).toBeInTheDocument();
        expect(screen.getByText('25')).toBeInTheDocument();
        expect(screen.getByText('Test summary')).toBeInTheDocument();
      });
    });

    it('should format currency correctly', async () => {
      const mockSessions = [
        {
          id: '1',
          sectors: ['vestuario'],
          ufs: ['SP'],
          data_inicial: '2024-01-01',
          data_final: '2024-01-07',
          custom_keywords: null,
          total_raw: 100,
          total_filtered: 25,
          valor_total: 150000.50,
          resumo_executivo: null,
          created_at: '2024-01-07T10:30:00Z',
          status: 'completed',
          error_message: null,
          error_code: null,
          duration_ms: null,
          pipeline_stage: null,
          started_at: '2024-01-07T10:30:00Z',
          response_state: 'live',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: mockSessions, total: 1 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        // Brazilian currency format
        expect(screen.getByText(/R\$/)).toBeInTheDocument();
      });
    });

    it('should display custom keywords when present', async () => {
      const mockSessions = [
        {
          id: '1',
          sectors: ['vestuario'],
          ufs: ['SP'],
          data_inicial: '2024-01-01',
          data_final: '2024-01-07',
          custom_keywords: ['uniforme', 'camiseta'],
          total_raw: 100,
          total_filtered: 25,
          valor_total: 150000,
          resumo_executivo: null,
          created_at: '2024-01-07T10:30:00Z',
          status: 'completed',
          error_message: null,
          error_code: null,
          duration_ms: null,
          pipeline_stage: null,
          started_at: '2024-01-07T10:30:00Z',
          response_state: 'live',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: mockSessions, total: 1 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Termos:/)).toBeInTheDocument();
        expect(screen.getByText(/uniforme, camiseta/)).toBeInTheDocument();
      });
    });

    it('should show total count in header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 5 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/5 buscas realizadas/)).toBeInTheDocument();
      });
    });

    it('should use singular form for 1 search', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 1 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/1 busca realizada$/)).toBeInTheDocument();
      });
    });

    it('should show Nova busca button', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: [], total: 0 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const newSearchLink = screen.getByRole('link', { name: /Nova busca/i });
        expect(newSearchLink).toBeInTheDocument();
        expect(newSearchLink).toHaveAttribute('href', '/buscar');
      });
    });
  });

  describe('Pagination', () => {
    const mockSession = {
      access_token: 'test-token-123',
    };

    // Generate mock sessions for pagination tests
    const generateMockSessions = (count: number) =>
      Array.from({ length: count }, (_, i) => ({
        id: `${i + 1}`,
        sectors: ['vestuario'],
        ufs: ['SP'],
        data_inicial: '2024-01-01',
        data_final: '2024-01-07',
        custom_keywords: null,
        total_raw: 100,
        total_filtered: 25,
        valor_total: 150000,
        resumo_executivo: null,
        created_at: '2024-01-07T10:30:00Z',
        status: 'completed',
        error_message: null,
        error_code: null,
        duration_ms: null,
        pipeline_stage: null,
        started_at: '2024-01-07T10:30:00Z',
        response_state: 'live',
      }));

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
      });
    });

    it('should not show pagination for single page', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: generateMockSessions(5), total: 5 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        // Wait for data to load
        expect(screen.getByText('5 buscas realizadas')).toBeInTheDocument();
      });

      expect(screen.queryByRole('button', { name: /Anterior/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Pr/i })).not.toBeInTheDocument();
    });

    it('should show pagination for multiple pages', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: generateMockSessions(20), total: 50 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Anterior/i })).toBeInTheDocument();
      });
    });

    it('should disable previous button on first page', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: generateMockSessions(20), total: 50 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /Anterior/i });
        expect(prevButton).toBeDisabled();
      });
    });

    it('should enable next button when more pages exist', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: generateMockSessions(20), total: 50 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        // Next button text is "Pr\u00f3ximo" (JSX literal) — match by partial text
        const nextButton = screen.getByRole('button', { name: /Pr/ });
        expect(nextButton).not.toBeDisabled();
      });
    });

    it('should show current page number', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ sessions: generateMockSessions(20), total: 50 }),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/1 de 3/)).toBeInTheDocument();
      });
    });

    it('should navigate to next page', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ sessions: generateMockSessions(20), total: 50 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ sessions: generateMockSessions(20), total: 50 }),
        });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/1 de 3/)).toBeInTheDocument();
      });

      // Next button has text "Pr\u00f3ximo" (JSX literal) — match by partial
      const nextButton = screen.getByRole('button', { name: /Pr/ });
      await act(async () => {
        fireEvent.click(nextButton);
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('offset=20'),
          expect.anything()
        );
      });
    });
  });

  describe('Error handling', () => {
    const mockSession = {
      access_token: 'test-token-123',
    };

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        session: mockSession,
        loading: false,
      });
    });

    it('should handle fetch error gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        // Page shows ErrorStateWithRetry component with data-testid="error-state"
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });
    });

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<HistoricoPage />);

      await waitFor(() => {
        // Page shows ErrorStateWithRetry component with data-testid="error-state"
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });
    });
  });
});
