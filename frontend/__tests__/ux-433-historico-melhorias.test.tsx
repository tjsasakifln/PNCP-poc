/**
 * UX-433: Histórico mostra excesso de falhas e timeouts
 *
 * Tests:
 * - AC1: groupSessions groups by setor+UFs within 5-minute window
 * - AC2: "Apenas concluídas" filter disabled by default
 * - AC3: filter buttons show correct options
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { groupSessions, GroupedSession } from '../app/historico/session-utils';

// ──────────────────────────────────────────────────────────────────────────────
// Mock dependencies for component tests
// ──────────────────────────────────────────────────────────────────────────────
jest.mock('next/link', () => {
  return function MockLink({ children, ...props }: any) {
    return <a {...props}>{children}</a>;
  };
});
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/historico',
  useSearchParams: () => new URLSearchParams(),
}));
const stableSession = { access_token: 'test-token' };
jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => ({ session: stableSession, loading: false }),
}));
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));
jest.mock('../hooks/usePlan', () => ({
  usePlan: () => ({ planInfo: null }),
}));
jest.mock('../components/PageHeader', () => ({
  PageHeader: function Mock({ title }: any) { return <h1>{title}</h1>; },
}));
jest.mock('../components/EmptyState', () => ({
  EmptyState: function Mock() { return null; },
}));
jest.mock('../components/ErrorStateWithRetry', () => ({
  ErrorStateWithRetry: function Mock() { return null; },
}));
jest.mock('../components/AuthLoadingScreen', () => ({
  AuthLoadingScreen: function Mock() { return null; },
}));
jest.mock('../components/PageErrorBoundary', () => ({
  PageErrorBoundary: function Mock({ children }: any) { return <>{children}</>; },
}));
jest.mock('../lib/error-messages', () => ({
  getUserFriendlyError: (m: string) => m,
}));
jest.mock('../lib/constants/sector-names', () => ({
  getSectorDisplayName: (s: string) => s,
}));
jest.mock('../lib/format-currency', () => ({
  formatCurrencyBR: (v: number) => `R$ ${v}`,
}));
jest.mock('../lib/config', () => ({ APP_NAME: 'SmartLic' }));
jest.mock('sonner', () => ({ toast: { error: jest.fn() } }));

const mockUseSessions = jest.fn();
jest.mock('../hooks/useSessions', () => ({
  useSessions: (opts: any) => mockUseSessions(opts),
}));

import HistoricoPage from '../app/historico/page';

// ──────────────────────────────────────────────────────────────────────────────
// Fixtures
// ──────────────────────────────────────────────────────────────────────────────
const makeSession = (overrides: Partial<any> = {}) => ({
  id: 'sess-default',
  sectors: ['informatica'],
  ufs: ['SP', 'RJ'],
  data_inicial: '2026-01-01',
  data_final: '2026-01-10',
  custom_keywords: null,
  total_raw: 100,
  total_filtered: 10,
  valor_total: 50000,
  resumo_executivo: null,
  created_at: '2026-01-10T12:00:00Z',
  status: 'completed',
  error_message: null,
  error_code: null,
  duration_ms: 5000,
  pipeline_stage: null,
  started_at: '2026-01-10T12:00:00Z',
  response_state: null,
  download_available: false,
  ...overrides,
});

const emptySessionsReturn = {
  sessions: [],
  total: 0,
  loading: false,
  error: null,
  errorTimestamp: null,
  refresh: jest.fn(),
  silentRefresh: jest.fn(),
};

// ──────────────────────────────────────────────────────────────────────────────
// AC1: groupSessions unit tests (pure function)
// ──────────────────────────────────────────────────────────────────────────────
describe('groupSessions (AC1)', () => {
  it('returns empty array for empty input', () => {
    expect(groupSessions([])).toEqual([]);
  });

  it('returns single group for a single session', () => {
    const s = makeSession({ id: 'a' });
    const result = groupSessions([s]);
    expect(result).toHaveLength(1);
    expect(result[0].attempts).toBe(1);
    expect(result[0].representative.id).toBe('a');
  });

  it('groups sessions with same setor+UFs within 5 minutes', () => {
    const s1 = makeSession({ id: 'a', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:00:00Z' });
    const s2 = makeSession({ id: 'b', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:02:00Z', status: 'failed' });

    const result = groupSessions([s1, s2]);
    expect(result).toHaveLength(1);
    expect(result[0].attempts).toBe(2);
  });

  it('does NOT group sessions with different sectors', () => {
    const s1 = makeSession({ id: 'a', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:00:00Z' });
    const s2 = makeSession({ id: 'b', sectors: ['saude'], ufs: ['SP'], created_at: '2026-01-10T12:01:00Z' });

    const result = groupSessions([s1, s2]);
    expect(result).toHaveLength(2);
  });

  it('does NOT group sessions with different UFs', () => {
    const s1 = makeSession({ id: 'a', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:00:00Z' });
    const s2 = makeSession({ id: 'b', sectors: ['informatica'], ufs: ['RJ'], created_at: '2026-01-10T12:01:00Z' });

    const result = groupSessions([s1, s2]);
    expect(result).toHaveLength(2);
  });

  it('does NOT group sessions more than 5 minutes apart', () => {
    const s1 = makeSession({ id: 'a', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:00:00Z' });
    const s2 = makeSession({ id: 'b', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:06:00Z' });

    const result = groupSessions([s1, s2]);
    expect(result).toHaveLength(2);
  });

  it('uses completed session as representative even if failed session is more recent', () => {
    const failedRecent = makeSession({
      id: 'failed-recent',
      sectors: ['informatica'],
      ufs: ['SP'],
      created_at: '2026-01-10T12:02:00Z',
      status: 'failed',
    });
    const completedOlder = makeSession({
      id: 'completed-older',
      sectors: ['informatica'],
      ufs: ['SP'],
      created_at: '2026-01-10T12:00:00Z',
      status: 'completed',
    });

    // DESC order: failed (more recent) comes first
    const result = groupSessions([failedRecent, completedOlder]);
    expect(result).toHaveLength(1);
    expect(result[0].representative.id).toBe('completed-older');
    expect(result[0].representative.status).toBe('completed');
  });

  it('uses most recent session as representative when all have failed', () => {
    const older = makeSession({
      id: 'older',
      sectors: ['informatica'],
      ufs: ['SP'],
      created_at: '2026-01-10T12:00:00Z',
      status: 'failed',
    });
    const newer = makeSession({
      id: 'newer',
      sectors: ['informatica'],
      ufs: ['SP'],
      created_at: '2026-01-10T12:02:00Z',
      status: 'failed',
    });

    const result = groupSessions([newer, older]);
    expect(result).toHaveLength(1);
    expect(result[0].representative.id).toBe('newer');
  });

  it('UFs order does not affect grouping (sorted before comparison)', () => {
    const s1 = makeSession({ id: 'a', ufs: ['SP', 'RJ'], created_at: '2026-01-10T12:00:00Z' });
    const s2 = makeSession({ id: 'b', ufs: ['RJ', 'SP'], created_at: '2026-01-10T12:01:00Z' });

    const result = groupSessions([s1, s2]);
    expect(result).toHaveLength(1);
    expect(result[0].attempts).toBe(2);
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// AC2: Default filter is 'auto', not 'completed'
// ──────────────────────────────────────────────────────────────────────────────
describe('HistoricoPage filter (AC2)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSessions.mockReturnValue(emptySessionsReturn);
  });

  it('defaults to auto filter — useSessions receives hideOldFailures=true', () => {
    render(<HistoricoPage />);

    expect(mockUseSessions).toHaveBeenCalledWith(
      expect.objectContaining({
        hideOldFailures: true,
      })
    );
  });

  it('does NOT default to completed filter (AC2: desativado por padrão)', () => {
    render(<HistoricoPage />);

    const calls = mockUseSessions.mock.calls;
    // Should never be called with status='completed' on initial render
    const hasCompletedDefault = calls.some(([opts]: [any]) => opts.status === 'completed');
    expect(hasCompletedDefault).toBe(false);
  });

  it('renders "Recentes" filter button active by default', () => {
    render(<HistoricoPage />);

    const recentesBtn = screen.getByTestId('filter-auto');
    expect(recentesBtn.className).toContain('bg-[var(--brand-navy)]');
  });

  it('renders all three filter buttons', () => {
    render(<HistoricoPage />);

    expect(screen.getByTestId('filter-completed')).toBeInTheDocument();
    expect(screen.getByTestId('filter-all')).toBeInTheDocument();
    expect(screen.getByTestId('filter-auto')).toBeInTheDocument();
  });

  it('clicking "Apenas concluídas" passes status=completed to useSessions', () => {
    render(<HistoricoPage />);

    fireEvent.click(screen.getByTestId('filter-completed'));

    const lastCall = mockUseSessions.mock.calls[mockUseSessions.mock.calls.length - 1][0];
    expect(lastCall.status).toBe('completed');
  });

  it('clicking "Mostrar todas" passes hideOldFailures=false to useSessions (AC3)', () => {
    render(<HistoricoPage />);

    fireEvent.click(screen.getByTestId('filter-all'));

    const lastCall = mockUseSessions.mock.calls[mockUseSessions.mock.calls.length - 1][0];
    expect(lastCall.hideOldFailures).toBe(false);
  });
});

// ──────────────────────────────────────────────────────────────────────────────
// AC1: "N tentativas" badge rendering
// ──────────────────────────────────────────────────────────────────────────────
describe('HistoricoPage "N tentativas" badge (AC1)', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows "N tentativas" badge when multiple sessions are grouped', () => {
    mockUseSessions.mockReturnValue({
      sessions: [
        makeSession({ id: 'a', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:02:00Z', status: 'failed' }),
        makeSession({ id: 'b', sectors: ['informatica'], ufs: ['SP'], created_at: '2026-01-10T12:00:00Z', status: 'completed' }),
      ],
      total: 2,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    });

    render(<HistoricoPage />);

    expect(screen.getByTestId('attempts-badge')).toBeInTheDocument();
    expect(screen.getByTestId('attempts-badge')).toHaveTextContent('2 tentativas');
  });

  it('does NOT show "N tentativas" badge for single session', () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ id: 'solo', sectors: ['informatica'], ufs: ['SP'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
      silentRefresh: jest.fn(),
    });

    render(<HistoricoPage />);

    expect(screen.queryByTestId('attempts-badge')).not.toBeInTheDocument();
  });
});
