import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock dependencies — session must be a STABLE reference to avoid
// infinite re-render loop (session is in useEffect deps)
jest.mock('next/link', () => {
  return function MockLink({ children, ...props }: any) {
    return <a {...props}>{children}</a>;
  };
});
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));
jest.mock('../../app/components/AuthProvider', () => {
  const stableSession = { access_token: 'test-token' };
  return {
    useAuth: () => ({
      session: stableSession,
      loading: false,
    }),
  };
});
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));
jest.mock('../../components/PageHeader', () => ({
  PageHeader: function Mock({ title }: any) { return <h1>{title}</h1>; },
}));
jest.mock('../../components/EmptyState', () => ({
  EmptyState: function Mock() { return null; },
}));
jest.mock('../../components/ErrorStateWithRetry', () => ({
  ErrorStateWithRetry: function Mock() { return null; },
}));
jest.mock('../../components/AuthLoadingScreen', () => ({
  AuthLoadingScreen: function Mock() { return null; },
}));
jest.mock('../../lib/error-messages', () => ({
  getUserFriendlyError: (m: string) => m,
}));
jest.mock('../../lib/constants/sector-names', () => ({
  getSectorDisplayName: (s: string) => s,
}));

// Mock useSessions — replaces global.fetch session logic
const mockUseSessions = jest.fn();
jest.mock('../../hooks/useSessions', () => ({
  useSessions: (opts: any) => mockUseSessions(opts),
}));

import HistoricoPage from '../../app/historico/page';

describe('Historico Pagination Buttons (AC28-AC32)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Return enough sessions for pagination (total > limit of 20)
    mockUseSessions.mockReturnValue({
      sessions: Array.from({ length: 20 }, (_, i) => ({
        id: `session-${i}`,
        sectors: ['informatica'],
        ufs: ['SP'],
        data_inicial: '2026-01-01',
        data_final: '2026-01-10',
        custom_keywords: null,
        total_raw: 100,
        total_filtered: 10,
        valor_total: 50000,
        resumo_executivo: 'Test',
        created_at: '2026-01-01T00:00:00Z',
        status: 'completed',
        error_message: null,
        error_code: null,
        duration_ms: 5000,
        pipeline_stage: null,
        started_at: '2026-01-01T00:00:00Z',
        response_state: null,
      })),
      total: 25,
      loading: false,
      error: null,
      errorTimestamp: null,
      refresh: jest.fn(),
    });
  });

  it('renders pagination buttons with improved styling', async () => {
    render(<HistoricoPage />);

    // Wait for pagination to appear (total=25, limit=20 -> 2 pages)
    const prevButton = await screen.findByTestId('historico-prev', {}, { timeout: 5000 });
    const nextButton = await screen.findByTestId('historico-next', {}, { timeout: 5000 });

    // AC29: WCAG AA disabled tokens (STORY-2.5: opacity-50 → ink-disabled/surface-disabled)
    expect(prevButton.className).toContain('disabled:bg-surface-disabled');
    expect(prevButton.className).toContain('disabled:text-ink-disabled');
    expect(nextButton.className).toContain('disabled:bg-surface-disabled');
    expect(nextButton.className).toContain('disabled:text-ink-disabled');

    // AC29: cursor-not-allowed
    expect(prevButton.className).toContain('disabled:cursor-not-allowed');

    // AC30: text-base (not text-sm)
    expect(prevButton.className).toContain('text-base');
    expect(nextButton.className).toContain('text-base');

    // AC30: px-4 py-2 (not px-3 py-1)
    expect(prevButton.className).toContain('px-4');
    expect(prevButton.className).toContain('py-2');

    // AC31: font-medium
    expect(prevButton.className).toContain('font-medium');
    expect(nextButton.className).toContain('font-medium');
  }, 10000);

  it('has aria labels for accessibility', async () => {
    render(<HistoricoPage />);

    const prevButton = await screen.findByTestId('historico-prev', {}, { timeout: 5000 });
    const nextButton = await screen.findByTestId('historico-next', {}, { timeout: 5000 });

    expect(prevButton).toHaveAttribute('aria-label', 'Página anterior');
    expect(nextButton).toHaveAttribute('aria-label', 'Próxima página');
  }, 10000);

  // AC38: Buttons are visible (contrast check)
  it('has sufficient text size and contrast for readability', async () => {
    render(<HistoricoPage />);

    const nextButton = await screen.findByTestId('historico-next', {}, { timeout: 5000 });
    // Verify text content is readable
    expect(nextButton).toHaveTextContent('Próximo');
    // Verify it has border for visibility
    expect(nextButton.className).toContain('border');
  }, 10000);
});
