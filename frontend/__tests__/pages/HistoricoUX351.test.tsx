/**
 * UX-351 — Historico Funcional: Salvamento, Status e Apresentacao
 *
 * Tests:
 *  AC12: busca gera 1 entrada no historico
 *  AC13: status atualiza corretamente (polling)
 *  AC14: 27 UFs = "Todo o Brasil"
 *  AC15: zero regressoes
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import HistoricoPage from '../../app/historico/page';

// --- Mocks ---

const mockAuthSession = { access_token: 'test-token-ux351' };

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: mockAuthSession,
    loading: false,
  }),
}));

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/historico',
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), resetUser: jest.fn() }),
}));

jest.mock('../../app/components/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'light', setTheme: jest.fn() }),
}));

// Mock components imported by PageHeader to avoid deep dependency chains
jest.mock('../../app/components/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle" />,
}));

jest.mock('../../app/components/UserMenu', () => ({
  UserMenu: () => <div data-testid="user-menu" />,
}));

jest.mock('../../app/components/QuotaBadge', () => ({
  QuotaBadge: () => <div data-testid="quota-badge" />,
}));

jest.mock('../../components/MobileDrawer', () => ({
  MobileDrawer: () => null,
}));

// Mock AlertNotificationBell (fetches /api/alerts — would consume the sessions mock)
jest.mock('../../app/components/AlertNotificationBell', () => ({
  AlertNotificationBell: () => null,
}));

jest.mock('../../hooks/useQuota', () => ({
  useQuota: () => ({ quota: null, loading: false, refresh: jest.fn() }),
}));

// Mock error-messages (pure functions, but mock to isolate)
jest.mock('../../lib/error-messages', () => ({
  getUserFriendlyError: (msg: string) => {
    // Simulate Portuguese translation for known patterns
    if (typeof msg === 'string' && msg.includes('Server restart')) {
      return 'O servidor reiniciou. Tente novamente.';
    }
    return typeof msg === 'string' ? msg : 'Erro desconhecido';
  },
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// Mock useSessions — replaces global.fetch session logic
const mockUseSessions = jest.fn();
jest.mock('../../hooks/useSessions', () => ({
  useSessions: (opts: any) => mockUseSessions(opts),
}));

// --- Helpers ---

interface MockSession {
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
  status: string;
  error_message: string | null;
  error_code: string | null;
  duration_ms: number | null;
  pipeline_stage: string | null;
  started_at: string;
  response_state: string | null;
}

function createSession(overrides: Partial<MockSession> = {}): MockSession {
  return {
    id: `session-${Math.random().toString(36).slice(2, 8)}`,
    sectors: ['informatica'],
    ufs: ['SP'],
    data_inicial: '2026-02-01',
    data_final: '2026-02-10',
    custom_keywords: null,
    total_raw: 50,
    total_filtered: 12,
    valor_total: 250000,
    resumo_executivo: 'Resumo teste',
    created_at: '2026-02-10T14:00:00Z',
    status: 'completed',
    error_message: null,
    error_code: null,
    duration_ms: 8000,
    pipeline_stage: 'persist',
    started_at: '2026-02-10T14:00:00Z',
    response_state: 'live',
    ...overrides,
  };
}

const ALL_27_UFS = [
  'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN',
  'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
];

// --- Tests ---

describe('UX-351: Historico Funcional', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPush.mockClear();
    // Default: empty sessions, not loading
    mockUseSessions.mockReturnValue({
      sessions: [],
      total: 0,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });
  });

  // =========================================================================
  // AC12: busca gera 1 entrada no historico
  // =========================================================================
  describe('AC12: Single entry per search', () => {
    test('renders exactly 1 card per session returned from API', async () => {
      const session = createSession({ id: 'unique-1', status: 'completed' });
      mockUseSessions.mockReturnValue({
        sessions: [session],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const badges = screen.getAllByTestId('status-badge-completed');
        expect(badges).toHaveLength(1);
      });
    });

    test('does not duplicate sessions with same search data', async () => {
      const sessions = [
        createSession({ id: 'a', status: 'completed', sectors: ['informatica'] }),
        createSession({ id: 'b', status: 'completed', sectors: ['saude'] }),
      ];
      mockUseSessions.mockReturnValue({
        sessions,
        total: 2,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const badges = screen.getAllByTestId('status-badge-completed');
        expect(badges).toHaveLength(2);
      });
    });
  });

  // =========================================================================
  // AC13: Status transitions update via polling
  // =========================================================================
  describe('AC13: Status updates via polling', () => {
    test('shows "Em andamento" for processing sessions', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ status: 'processing', resumo_executivo: null })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-processing');
        expect(badge).toHaveTextContent('Em andamento');
      });
    });

    test('transitions from processing to completed after poll', async () => {
      const processingSession = createSession({
        id: 'poll-test',
        status: 'processing',
        resumo_executivo: null,
      });
      const completedSession = createSession({
        id: 'poll-test',
        status: 'completed',
        resumo_executivo: 'Resultados prontos',
      });

      const processingReturn = {
        sessions: [processingSession],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
        silentRefresh: jest.fn(),
      };
      const completedReturn = {
        sessions: [completedSession],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
        silentRefresh: jest.fn(),
      };

      // All calls during first render return processing
      mockUseSessions.mockReturnValue(processingReturn);

      const { rerender } = render(<HistoricoPage />);

      // Initially shows processing
      await waitFor(() => {
        expect(screen.getByTestId('status-badge-processing')).toBeInTheDocument();
      });

      // Switch to completed for subsequent renders
      mockUseSessions.mockReturnValue(completedReturn);

      // Simulate poll by re-rendering
      await act(async () => {
        rerender(<HistoricoPage />);
      });

      // Should now show completed
      await waitFor(() => {
        expect(screen.getByTestId('status-badge-completed')).toBeInTheDocument();
      });
    });

    test('shows "Concluída" badge for completed status', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ status: 'completed' })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-completed');
        expect(badge).toHaveTextContent(/Conclu/);
      });
    });

    test('shows "Falhou" badge for failed status', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ status: 'failed', error_message: 'Teste de erro' })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-failed');
        expect(badge).toHaveTextContent('Falhou');
      });
    });

    test('shows "Tempo esgotado" badge for timed_out status', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ status: 'timed_out', error_message: 'Timeout' })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-timed_out');
        expect(badge).toHaveTextContent('Tempo esgotado');
      });
    });

    test('stops polling when all sessions are terminal', async () => {
      // useSessions called with refreshInterval=0 for terminal sessions
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ status: 'completed' })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByTestId('status-badge-completed')).toBeInTheDocument();
      });

      // Verify useSessions was called with refreshInterval 0 (no polling) after terminal state
      // The page sets pollInterval=0 when all sessions are terminal
      const lastCall = mockUseSessions.mock.calls[mockUseSessions.mock.calls.length - 1][0];
      expect(lastCall.refreshInterval).toBe(0);
    });
  });

  // =========================================================================
  // AC14: 27 UFs = "Todo o Brasil"
  // =========================================================================
  describe('AC14: UF display formatting', () => {
    test('shows "Todo o Brasil" when all 27 UFs selected', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ ufs: ALL_27_UFS })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('Todo o Brasil');
      });
    });

    test('shows all UFs when 5 or fewer selected', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ ufs: ['SP', 'RJ', 'MG'] })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP, RJ, MG');
      });
    });

    test('shows first 5 UFs + "outros" when more than 5 selected', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ ufs: ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS', 'SC', 'GO'] })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP, RJ, MG, BA, PR + 3 outros');
      });
    });

    test('shows singular "outro" for exactly 6 UFs', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ ufs: ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS'] })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP, RJ, MG, BA, PR + 1 outro');
      });
    });

    test('shows single UF normally', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ ufs: ['SP'] })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP');
      });
    });
  });

  // =========================================================================
  // AC6-AC7: Error messages in Portuguese
  // =========================================================================
  describe('AC6-AC7: Error messages in Portuguese', () => {
    test('translates "Server restart" to Portuguese', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({
          status: 'failed',
          error_message: 'Server restart — retry recommended',
        })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        const errorEl = screen.getByTestId('error-message');
        expect(errorEl).toHaveTextContent('O servidor reiniciou. Tente novamente.');
      });
    });

    test('shows Portuguese error for timed_out with server restart', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({
          status: 'timed_out',
          error_message: 'Server restart during processing',
        })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      // UX-357: timed_out always shows the canonical timeout message regardless of error_message
      await waitFor(() => {
        const errorEl = screen.getByTestId('error-message');
        expect(errorEl).toHaveTextContent('A análise excedeu o tempo limite. Recomendamos tentar novamente.');
      });
    });
  });

  // =========================================================================
  // AC15: Regression checks
  // =========================================================================
  describe('AC15: Regression checks', () => {
    test('completed session shows result count and value', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({
          status: 'completed',
          total_filtered: 42,
          valor_total: 1500000,
        })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument();
        expect(screen.getByText('resultados')).toBeInTheDocument();
        expect(screen.getByText(/R\$/)).toBeInTheDocument();
      });
    });

    test('shows resumo_executivo for completed sessions', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({
          status: 'completed',
          resumo_executivo: 'Encontradas 42 oportunidades relevantes',
        })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText('Encontradas 42 oportunidades relevantes')).toBeInTheDocument();
      });
    });

    test('shows custom_keywords when present', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({
          custom_keywords: ['uniformes', 'escolares'],
        })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText(/Termos:/)).toBeInTheDocument();
        expect(screen.getByText(/uniformes, escolares/)).toBeInTheDocument();
      });
    });

    test('shows duration when available', async () => {
      mockUseSessions.mockReturnValue({
        sessions: [createSession({ duration_ms: 12345 })],
        total: 1,
        loading: false,
        error: null,
        errorTimestamp: null,
        refresh: jest.fn(),
      });

      render(<HistoricoPage />);

      await waitFor(() => {
        expect(screen.getByText('12.3s')).toBeInTheDocument();
      });
    });
  });
});
