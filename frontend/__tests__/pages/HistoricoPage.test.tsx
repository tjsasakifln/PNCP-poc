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

// Mock AlertNotificationBell (fetches /api/alerts — would consume the sessions mock)
jest.mock('../../app/components/AlertNotificationBell', () => ({
  AlertNotificationBell: () => null,
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

// Mock useSessions — replaces all global.fetch session logic
const mockUseSessions = jest.fn();
jest.mock('../../hooks/useSessions', () => ({
  useSessions: (opts: any) => mockUseSessions(opts),
}));

describe('HistoricoPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
    // Default: loading state
    mockUseSessions.mockReturnValue({
      sessions: [],
      total: 0,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });
  });

  describe('Loading state', () => {
    it('should show loading message during auth check', () => {
      mockUseAuth.mockReturnValue({
        session: null,
        loading: true,
      });

      render(<HistoricoPage />);

      // GTM-POLISH-001 AC1: Unified AuthLoadingScreen replaces generic "Carregando..."
      expect(screen.getByTestId('auth-loading-screen')).toBeInTheDocument();
    });

    it('should show loading skeletons while fetching', () => {
      mockUseAuth.mockReturnValue({
        session: { access_token: 'test-token-123' },
        loading: false,
      });
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 0,
        loading: true,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      // Should show skeleton loaders
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
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

    it('should call useSessions on mount', () => {
      render(<HistoricoPage />);

      expect(mockUseSessions).toHaveBeenCalledWith(
        expect.objectContaining({ page: 0 })
      );
    });

    it('should show page title in header', () => {
      render(<HistoricoPage />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
      expect(heading.textContent).toContain('Hist');
    });

    it('should show empty state when no sessions', () => {
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 0,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    it('should show link to make first search when empty', () => {
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 0,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      const searchLink = screen.getByRole('link', { name: /Fazer primeira análise/i });
      expect(searchLink).toBeInTheDocument();
      expect(searchLink).toHaveAttribute('href', '/buscar');
    });

    it('should display session list', () => {
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

      mockUseSessions.mockReturnValue({
        sessions: mockSessions,
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      expect(screen.getByText(/SP, RJ/)).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('Test summary')).toBeInTheDocument();
    });

    it('should format currency correctly', () => {
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

      mockUseSessions.mockReturnValue({
        sessions: mockSessions,
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      // Brazilian currency format
      expect(screen.getByText(/R\$/)).toBeInTheDocument();
    });

    it('should display custom keywords when present', () => {
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

      mockUseSessions.mockReturnValue({
        sessions: mockSessions,
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      expect(screen.getByText(/Termos:/)).toBeInTheDocument();
      expect(screen.getByText(/uniforme, camiseta/)).toBeInTheDocument();
    });

    it('should show total count in header', () => {
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 5,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);


      expect(screen.getByText(/5 análises realizadas/)).toBeInTheDocument();
    });

    it('should use singular form for 1 search', () => {
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);


      expect(screen.getByText(/1 análise realizada$/)).toBeInTheDocument();
    });

    it('should show Nova análise button', () => {
      render(<HistoricoPage />);

      const newSearchLink = screen.getByRole('link', { name: /Nova análise/i });
      expect(newSearchLink).toBeInTheDocument();
      expect(newSearchLink).toHaveAttribute('href', '/buscar');
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

    it('should not show pagination for single page', () => {
      mockUseSessions.mockReturnValue({
        sessions: generateMockSessions(5),
        total: 5,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);


      expect(screen.getByText('5 análises realizadas')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Anterior/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Pr/i })).not.toBeInTheDocument();
    });

    it('should show pagination for multiple pages', () => {
      mockUseSessions.mockReturnValue({
        sessions: generateMockSessions(20),
        total: 50,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      expect(screen.getByRole('button', { name: /Anterior/i })).toBeInTheDocument();
    });

    it('should disable previous button on first page', () => {
      mockUseSessions.mockReturnValue({
        sessions: generateMockSessions(20),
        total: 50,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      const prevButton = screen.getByRole('button', { name: /Anterior/i });
      expect(prevButton).toBeDisabled();
    });

    it('should enable next button when more pages exist', () => {
      mockUseSessions.mockReturnValue({
        sessions: generateMockSessions(20),
        total: 50,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      // Next button text is "Próximo" — match by partial text
      const nextButton = screen.getByRole('button', { name: /Pr/ });
      expect(nextButton).not.toBeDisabled();
    });

    it('should show current page number', () => {
      mockUseSessions.mockReturnValue({
        sessions: generateMockSessions(20),
        total: 50,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      expect(screen.getByText(/1 de 3/)).toBeInTheDocument();
    });

    it('should navigate to next page', async () => {
      mockUseSessions.mockReturnValue({
        sessions: generateMockSessions(20),
        total: 50,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      expect(screen.getByText(/1 de 3/)).toBeInTheDocument();

      // Next button has text "Próximo" — match by partial
      const nextButton = screen.getByRole('button', { name: /Pr/ });
      await act(async () => {
        fireEvent.click(nextButton);
      });

      // After clicking next, useSessions should be called with page: 1
      await waitFor(() => {
        expect(mockUseSessions).toHaveBeenCalledWith(
          expect.objectContaining({ page: 1 })
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

    it('should handle fetch error gracefully', () => {
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 0,
        loading: false,
        error: "Não foi possível carregar seu histórico.",
        errorTimestamp: new Date().toISOString(),
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      // Page shows ErrorStateWithRetry component with data-testid="error-state"
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });

    it('should handle network error', () => {
      mockUseSessions.mockReturnValue({
        sessions: [],
        total: 0,
        loading: false,
        error: "Não foi possível carregar seu histórico.",
        errorTimestamp: new Date().toISOString(),
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      // Page shows ErrorStateWithRetry component with data-testid="error-state"
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });
  });
});
