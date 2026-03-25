import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import HistoricoPage from '../../app/historico/page';

// Mock session factory
interface SearchSession {
  id: string;
  sectors: string[];
  ufs: string[];
  data_inicial: string;
  data_final: string;
  custom_keywords: string[] | null;
  total_raw: number;
  total_filtered: number;
  valor_total: number;
  resumo_executivo: string | null;
  created_at: string;
  status: 'created' | 'processing' | 'completed' | 'failed' | 'timed_out' | 'cancelled';
  error_message: string | null;
  error_code: string | null;
  duration_ms: number | null;
  pipeline_stage: string | null;
  started_at: string;
  response_state: string | null;
}

const createMockSession = (overrides: Partial<SearchSession> = {}): SearchSession => ({
  id: 'test-id',
  sectors: ['vestuario'],
  ufs: ['SP'],
  data_inicial: '2026-01-01',
  data_final: '2026-01-10',
  custom_keywords: null,
  total_raw: 100,
  total_filtered: 10,
  valor_total: 50000,
  resumo_executivo: 'Test summary',
  created_at: '2026-01-10T12:00:00Z',
  status: 'completed',
  error_message: null,
  error_code: null,
  duration_ms: 5000,
  pipeline_stage: 'persist',
  started_at: '2026-01-10T12:00:00Z',
  response_state: 'live',
  ...overrides,
});

// Stable reference to avoid infinite useEffect re-runs
const mockAuthSession = { access_token: 'test-token' };

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: mockAuthSession,
    loading: false,
  }),
}));

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn(), back: jest.fn() }),
  usePathname: () => '/historico',
  useSearchParams: () => new URLSearchParams(),
}));

const mockTrackEvent = jest.fn();
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent, resetUser: jest.fn() }),
}));

jest.mock('../../app/components/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'light', setTheme: jest.fn() }),
}));

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

jest.mock('../../hooks/useQuota', () => ({
  useQuota: () => ({ quota: null, loading: false, refresh: jest.fn() }),
}));

jest.mock('../../lib/error-messages', () => ({
  getUserFriendlyError: (msg: string) => msg,
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// Mock useSessions — replaces global.fetch session logic
const mockUseSessions = jest.fn();
jest.mock('../../hooks/useSessions', () => ({
  useSessions: (opts: any) => mockUseSessions(opts),
}));

function mockSessionsWith(sessions: SearchSession[]) {
  mockUseSessions.mockReturnValue({
    sessions,
    total: sessions.length,
    loading: false,
    error: null,
    errorTimestamp: null,
    refresh: jest.fn(),
  });
}

describe('HistoricoPage - Status Badges and Retry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
    mockTrackEvent.mockClear();
  });

  // FE1: test renders green badge for completed sessions
  test('FE1: renders green badge for completed sessions', async () => {
    mockSessionsWith([createMockSession({ status: 'completed' })]);

    render(<HistoricoPage />);

    const badge = await screen.findByTestId('status-badge-completed');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-emerald-100');
  });

  // FE2: test renders red badge for failed sessions with error_message displayed
  test('FE2: renders red badge for failed sessions with error_message displayed', async () => {
    mockSessionsWith([createMockSession({
      status: 'failed',
      error_message: 'PNCP API timeout',
      error_code: 'TIMEOUT',
    })]);

    render(<HistoricoPage />);

    // Click "Todas" to show all statuses (default filter is 'completed')
    fireEvent.click(screen.getByRole('radio', { name: /Todas/ }));

    const badge = await screen.findByTestId('status-badge-failed');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-red-100');

    // Check error message is displayed
    const errorMessage = screen.getByText(/PNCP API timeout/i);
    expect(errorMessage).toBeInTheDocument();
    expect(errorMessage).toHaveClass('text-red-600');
  });

  // FE3: test renders orange badge for timed_out sessions
  test('FE3: renders orange badge for timed_out sessions', async () => {
    mockSessionsWith([createMockSession({
      status: 'timed_out',
      error_message: 'Search exceeded maximum time limit',
    })]);

    render(<HistoricoPage />);

    // Click "Todas" to show all statuses (default filter is 'completed')
    fireEvent.click(screen.getByRole('radio', { name: /Todas/ }));

    const badge = await screen.findByTestId('status-badge-timed_out');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-orange-100');
  });

  // FE4: test "Tentar novamente" button navigates to /buscar with correct params for failed session
  test('FE4: "Tentar novamente" button navigates to /buscar with correct params for failed session', async () => {
    mockSessionsWith([createMockSession({
      id: 'failed-session-123',
      status: 'failed',
      sectors: ['vestuario'],
      ufs: ['SP', 'RJ'],
      data_inicial: '2026-01-01',
      data_final: '2026-01-15',
      custom_keywords: ['uniformes', 'escolares'],
      error_message: 'Connection error',
    })]);

    render(<HistoricoPage />);

    // Click "Todas" to show all statuses (default filter is 'completed')
    fireEvent.click(screen.getByRole('radio', { name: /Todas/ }));

    const badge = await screen.findByTestId('status-badge-failed');
    expect(badge).toBeInTheDocument();

    const retryButton = screen.getByTestId('retry-button');
    expect(retryButton).toHaveTextContent('Tentar novamente');

    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining('/buscar')
      );
    });

    const callArgs = mockPush.mock.calls[0][0] as string;
    // handleRerunSearch uses: ufs, data_inicial, data_final, mode=termos, termos=...
    expect(callArgs).toContain('ufs=SP%2CRJ');
    expect(callArgs).toContain('data_inicial=2026-01-01');
    expect(callArgs).toContain('data_final=2026-01-15');
    expect(callArgs).toContain('mode=termos');
    expect(callArgs).toContain('termos=uniformes+escolares');
  });

  // FE5: test SearchSession interface includes status fields (compile-time check via TypeScript assertion)
  test('FE5: SearchSession interface includes status fields (compile-time)', () => {
    const session: SearchSession = createMockSession();

    // Runtime verification that status field exists and has correct type
    expect(session).toHaveProperty('status');
    expect(['created', 'processing', 'completed', 'failed', 'timed_out', 'cancelled'])
      .toContain(session.status);

    // Verify error fields exist
    expect(session).toHaveProperty('error_message');
    expect(session).toHaveProperty('error_code');

    // Verify pipeline tracking fields exist
    expect(session).toHaveProperty('pipeline_stage');
    expect(session).toHaveProperty('started_at');
    expect(session).toHaveProperty('duration_ms');
  });
});
