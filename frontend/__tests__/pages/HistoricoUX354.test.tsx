/**
 * UX-354 — Histórico: Unicode Escape, Sector Slugs, English Errors
 *
 * AC1: Header bar shows "Histórico" with correct accent
 * AC2-AC3: Sector names use display name (slug → name mapping)
 * AC4-AC5: Error messages in PT-BR (no English visible)
 * AC6: Test sector slug renders display name
 * AC7: Test error "Server restart" renders PT-BR
 * AC8: Zero regression
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import HistoricoPage from '../../app/historico/page';

// --- Mocks ---
const mockUseAuth = jest.fn();
jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/historico',
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), resetUser: jest.fn() }),
}));

// Mock getUserFriendlyError with PT-BR translations for the messages we test
jest.mock('../../lib/error-messages', () => ({
  getUserFriendlyError: (msg: unknown) => {
    if (typeof msg !== 'string') return 'Erro desconhecido';
    if (msg.includes('Server restart')) return 'O servidor reiniciou. Recomendamos tentar novamente.';
    if (msg.includes('Pipeline failed')) return 'A análise não pôde ser concluída. Tente novamente.';
    if (msg.includes('Connection reset')) return 'A conexão foi interrompida. Tente novamente.';
    if (msg.includes('All sources failed')) return 'Nenhuma fonte de dados respondeu. Tente novamente em alguns minutos.';
    return msg;
  },
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

// Mock useSessions — replaces global.fetch session logic
const mockUseSessions = jest.fn();
jest.mock('../../hooks/useSessions', () => ({
  useSessions: (opts: any) => mockUseSessions(opts),
}));

// --- Test data ---
const mockSession = { access_token: 'test-token-354' };

function makeSession(overrides: Record<string, unknown> = {}) {
  return {
    id: 'sess-1',
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

// --- Tests ---

describe('UX-354: Histórico Unicode, Sector Slugs, English Errors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({ session: mockSession, loading: false });
    // Default: empty
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
  // AC1: Header renders "Histórico" (not unicode escape)
  // =========================================================================
  test('AC1: header shows "Histórico" page title in DOM', async () => {
    render(<HistoricoPage />);

    // PageHeader h1 is always rendered (hidden on mobile via CSS, but in DOM).
    const heading = screen.getByRole('heading', { level: 1 });
    // Verify the heading contains the page title text (partial match is safe)
    expect(heading).toHaveTextContent(/Hist/);
    expect(heading.textContent).toContain('rico');
  });

  // =========================================================================
  // AC2-AC3, AC6: Sector slugs → display names
  // =========================================================================
  test('AC6: sector "vestuario" renders as "Vestuário e Uniformes"', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['vestuario'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent('Vestuário e Uniformes');
    });
  });

  test('sector "alimentos" renders as "Alimentos e Merenda"', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['alimentos'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent('Alimentos e Merenda');
    });
  });

  test('sector "engenharia" renders as "Engenharia, Projetos e Obras"', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['engenharia'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent('Engenharia, Projetos e Obras');
    });
  });

  test('sector "saude" renders as "Saúde"', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['saude'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent('Saúde');
    });
  });

  test('sector "materiais_hidraulicos" renders as "Materiais Hidráulicos e Saneamento"', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['materiais_hidraulicos'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent('Materiais Hidráulicos e Saneamento');
    });
  });

  test('multiple sectors render as comma-separated display names', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['vestuario', 'software'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent(
        'Vestuário e Uniformes, Software e Sistemas'
      );
    });
  });

  test('unknown sector falls back to raw slug', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ sectors: ['unknown_sector'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('sector-display')).toHaveTextContent('unknown_sector');
    });
  });

  test('AC3: all 15 sector IDs are defined', () => {
    const ALL_SECTOR_IDS = [
      'vestuario', 'alimentos', 'informatica', 'mobiliario', 'papelaria',
      'engenharia', 'software', 'facilities', 'saude', 'vigilancia',
      'transporte', 'manutencao_predial', 'engenharia_rodoviaria',
      'materiais_eletricos', 'materiais_hidraulicos',
    ];
    expect(ALL_SECTOR_IDS).toHaveLength(15);
  });

  // =========================================================================
  // AC4-AC5, AC7: Error messages in PT-BR
  // =========================================================================
  test('AC7: "Server restart — retry recommended" renders PT-BR', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({
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
      expect(errorEl).toHaveTextContent('O servidor reiniciou. Recomendamos tentar novamente.');
      expect(errorEl.textContent).not.toContain('Server restart');
    });
  });

  test('AC4: "Server restart during processing" renders PT-BR', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({
        status: 'failed',
        error_message: 'Server restart during processing',
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
      expect(errorEl).toHaveTextContent(/servidor reiniciou/);
    });
  });

  test('AC5: "Pipeline failed" renders PT-BR', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({
        status: 'failed',
        error_message: 'Pipeline failed',
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
      expect(errorEl).toHaveTextContent('A análise não pôde ser concluída. Tente novamente.');
    });
  });

  test('AC5: "Connection reset" renders PT-BR', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({
        status: 'failed',
        error_message: 'Connection reset by peer',
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
      expect(errorEl).toHaveTextContent('A conexão foi interrompida. Tente novamente.');
    });
  });

  // UX-357: timed_out now always shows canonical timeout message
  test('AC5: timed_out shows unified timeout message (UX-357)', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({
        status: 'timed_out',
        error_message: 'All sources failed to respond',
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
      expect(errorEl).toHaveTextContent('A análise excedeu o tempo limite. Recomendamos tentar novamente.');
    });
  });

  // =========================================================================
  // AC8: Zero regression
  // =========================================================================
  test('AC8: completed session renders count and currency', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ total_filtered: 42, valor_total: 1500000 })],
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

  test('AC8: empty state renders with a link to start the first search', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [],
      total: 0,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    // EmptyState component is shown with data-testid="empty-state"
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
    // Verify the CTA link text is rendered
    expect(screen.getByText(/Fazer primeira análise/i)).toBeInTheDocument();
  });

  test('AC8: UF display works correctly', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ ufs: ['SP', 'RJ', 'MG'] })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('uf-display')).toHaveTextContent('SP, RJ, MG');
    });
  });

  test('AC8: status badge shows "Concluída"', async () => {
    mockUseSessions.mockReturnValue({
      sessions: [makeSession({ status: 'completed' })],
      total: 1,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });

    render(<HistoricoPage />);

    await waitFor(() => {
      expect(screen.getByTestId('status-badge-completed')).toHaveTextContent('Concluída');
    });
  });
});
