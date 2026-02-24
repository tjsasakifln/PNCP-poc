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

let fetchCallCount: number;
let fetchResponses: Array<{ sessions: MockSession[]; total: number }>;

function setupFetch(responses: Array<{ sessions: MockSession[]; total: number }>) {
  fetchCallCount = 0;
  fetchResponses = responses;
  global.fetch = jest.fn().mockImplementation(() => {
    const idx = Math.min(fetchCallCount, fetchResponses.length - 1);
    fetchCallCount++;
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        ...fetchResponses[idx],
        limit: 20,
        offset: 0,
      }),
    });
  });
}

// --- Tests ---

describe('UX-351: Historico Funcional', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockPush.mockClear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // =========================================================================
  // AC12: busca gera 1 entrada no historico
  // =========================================================================
  describe('AC12: Single entry per search', () => {
    test('renders exactly 1 card per session returned from API', async () => {
      const session = createSession({ id: 'unique-1', status: 'completed' });
      setupFetch([{ sessions: [session], total: 1 }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

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
      setupFetch([{ sessions, total: 2 }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

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
      setupFetch([{
        sessions: [createSession({ status: 'processing', resumo_executivo: null })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

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

      setupFetch([
        { sessions: [processingSession], total: 1 },
        { sessions: [completedSession], total: 1 },
      ]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      // Initially shows processing
      await waitFor(() => {
        expect(screen.getByTestId('status-badge-processing')).toBeInTheDocument();
      });

      // Advance timer to trigger poll (5s interval)
      await act(async () => {
        jest.advanceTimersByTime(5500);
      });

      // Should now show completed
      await waitFor(() => {
        expect(screen.getByTestId('status-badge-completed')).toBeInTheDocument();
      });
    });

    test('shows "Concluída" badge for completed status', async () => {
      setupFetch([{
        sessions: [createSession({ status: 'completed' })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-completed');
        expect(badge).toHaveTextContent(/Conclu/);
      });
    });

    test('shows "Falhou" badge for failed status', async () => {
      setupFetch([{
        sessions: [createSession({ status: 'failed', error_message: 'Teste de erro' })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-failed');
        expect(badge).toHaveTextContent('Falhou');
      });
    });

    test('shows "Tempo esgotado" badge for timed_out status', async () => {
      setupFetch([{
        sessions: [createSession({ status: 'timed_out', error_message: 'Timeout' })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const badge = screen.getByTestId('status-badge-timed_out');
        expect(badge).toHaveTextContent('Tempo esgotado');
      });
    });

    test('stops polling when all sessions are terminal', async () => {
      setupFetch([{
        sessions: [createSession({ status: 'completed' })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        expect(screen.getByTestId('status-badge-completed')).toBeInTheDocument();
      });

      // Advance timer — should NOT trigger additional fetches
      const callsBefore = (global.fetch as jest.Mock).mock.calls.length;
      await act(async () => {
        jest.advanceTimersByTime(15000);
      });
      const callsAfter = (global.fetch as jest.Mock).mock.calls.length;

      // No additional fetches (all terminal)
      expect(callsAfter).toBe(callsBefore);
    });
  });

  // =========================================================================
  // AC14: 27 UFs = "Todo o Brasil"
  // =========================================================================
  describe('AC14: UF display formatting', () => {
    test('shows "Todo o Brasil" when all 27 UFs selected', async () => {
      setupFetch([{
        sessions: [createSession({ ufs: ALL_27_UFS })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('Todo o Brasil');
      });
    });

    test('shows all UFs when 5 or fewer selected', async () => {
      setupFetch([{
        sessions: [createSession({ ufs: ['SP', 'RJ', 'MG'] })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP, RJ, MG');
      });
    });

    test('shows first 5 UFs + "outros" when more than 5 selected', async () => {
      setupFetch([{
        sessions: [createSession({ ufs: ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS', 'SC', 'GO'] })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP, RJ, MG, BA, PR + 3 outros');
      });
    });

    test('shows singular "outro" for exactly 6 UFs', async () => {
      setupFetch([{
        sessions: [createSession({ ufs: ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS'] })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const ufDisplay = screen.getByTestId('uf-display');
        expect(ufDisplay).toHaveTextContent('SP, RJ, MG, BA, PR + 1 outro');
      });
    });

    test('shows single UF normally', async () => {
      setupFetch([{
        sessions: [createSession({ ufs: ['SP'] })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

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
      setupFetch([{
        sessions: [createSession({
          status: 'failed',
          error_message: 'Server restart — retry recommended',
        })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        const errorEl = screen.getByTestId('error-message');
        expect(errorEl).toHaveTextContent('O servidor reiniciou. Tente novamente.');
      });
    });

    test('shows Portuguese error for timed_out with server restart', async () => {
      setupFetch([{
        sessions: [createSession({
          status: 'timed_out',
          error_message: 'Server restart during processing',
        })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      // UX-357: timed_out always shows the canonical timeout message regardless of error_message
      await waitFor(() => {
        const errorEl = screen.getByTestId('error-message');
        expect(errorEl).toHaveTextContent('A busca excedeu o tempo limite. Recomendamos tentar novamente.');
      });
    });
  });

  // =========================================================================
  // AC15: Regression checks
  // =========================================================================
  describe('AC15: Regression checks', () => {
    // AC15 tests do not use polling/timers — switch to real timers so waitFor
    // retry callbacks can fire (fake timers block waitFor's internal setTimeout).
    beforeEach(() => {
      jest.useRealTimers();
    });
    afterEach(() => {
      jest.useFakeTimers();
    });

    test('completed session shows result count and value', async () => {
      setupFetch([{
        sessions: [createSession({
          status: 'completed',
          total_filtered: 42,
          valor_total: 1500000,
        })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument();
        expect(screen.getByText('resultados')).toBeInTheDocument();
        expect(screen.getByText(/R\$/)).toBeInTheDocument();
      });
    });

    test('shows resumo_executivo for completed sessions', async () => {
      setupFetch([{
        sessions: [createSession({
          status: 'completed',
          resumo_executivo: 'Encontradas 42 oportunidades relevantes',
        })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('Encontradas 42 oportunidades relevantes')).toBeInTheDocument();
      });
    });

    test('shows custom_keywords when present', async () => {
      setupFetch([{
        sessions: [createSession({
          custom_keywords: ['uniformes', 'escolares'],
        })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        expect(screen.getByText(/Termos:/)).toBeInTheDocument();
        expect(screen.getByText(/uniformes, escolares/)).toBeInTheDocument();
      });
    });

    test('shows duration when available', async () => {
      setupFetch([{
        sessions: [createSession({ duration_ms: 12345 })],
        total: 1,
      }]);

      await act(async () => {
        render(<HistoricoPage />);
      });

      await waitFor(() => {
        expect(screen.getByText('12.3s')).toBeInTheDocument();
      });
    });
  });
});
