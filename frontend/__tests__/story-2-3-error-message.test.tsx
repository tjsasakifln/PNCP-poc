/**
 * STORY-2.3 — Tests for ErrorMessage component + errorCatalog.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorMessage } from '@/components/ErrorMessage';
import { ERROR_MESSAGES, getHumanizedMessage } from '@/lib/errorCatalog';

// ── Mock mixpanel-browser at module level (no resetModules) ─────────────
const mockTrack = jest.fn();
jest.mock('mixpanel-browser', () => ({
  __esModule: true,
  default: {
    track: (...args: unknown[]) => mockTrack(...args),
  },
}));

beforeEach(() => {
  mockTrack.mockClear();
});

describe('STORY-2.3 — errorCatalog (AC1+AC2)', () => {
  it('catálogo tem pelo menos 20 entradas humanizadas', () => {
    expect(Object.keys(ERROR_MESSAGES).length).toBeGreaterThanOrEqual(20);
  });

  it('cada entrada tem title curto e body com causa+ação', () => {
    for (const [key, entry] of Object.entries(ERROR_MESSAGES)) {
      expect(entry.title.trim()).not.toBe('');
      expect(entry.body.trim()).not.toBe('');
      expect(entry.title.length).toBeLessThan(80);
      expect(entry.body.length).toBeGreaterThan(20);
      expect(key).toMatch(/^[a-z]+\.[a-z_]+$/);
    }
  });

  it('chaves cobrem categorias críticas', () => {
    const categories = new Set(Object.keys(ERROR_MESSAGES).map((k) => k.split('.')[0]));
    ['search', 'auth', 'network', 'billing', 'generic'].forEach((cat) => {
      expect(categories).toContain(cat);
    });
  });

  it('getHumanizedMessage retorna entrada existente', () => {
    const entry = getHumanizedMessage('search.timeout');
    expect(entry).not.toBeNull();
    expect(entry?.title.toLowerCase()).toContain('demor');
  });

  it('getHumanizedMessage retorna null para chave desconhecida', () => {
    expect(getHumanizedMessage('chave.inexistente')).toBeNull();
  });
});

describe('STORY-2.3 — <ErrorMessage> (AC3+AC4)', () => {
  it('renderiza title e body', () => {
    render(
      <ErrorMessage
        title="Falha"
        body="Não conseguimos completar a ação"
        telemetryKey="generic.unexpected"
      />
    );
    expect(screen.getByText('Falha')).toBeInTheDocument();
    expect(screen.getByText('Não conseguimos completar a ação')).toBeInTheDocument();
  });

  it('severity=error usa container vermelho e role="alert"', () => {
    render(
      <ErrorMessage title="X" body="Y" severity="error" telemetryKey="generic.unexpected" />
    );
    const el = screen.getByTestId('error-message');
    expect(el).toHaveAttribute('role', 'alert');
    expect(el).toHaveAttribute('aria-live', 'assertive');
    expect(el.className).toContain('bg-red-50');
  });

  it('severity=warning usa container amber e role="status"', () => {
    render(
      <ErrorMessage title="X" body="Y" severity="warning" telemetryKey="search.rate_limit" />
    );
    const el = screen.getByTestId('error-message');
    expect(el).toHaveAttribute('role', 'status');
    expect(el).toHaveAttribute('aria-live', 'polite');
    expect(el.className).toContain('bg-amber-50');
  });

  it('severity=info usa container azul', () => {
    render(<ErrorMessage title="X" body="Y" severity="info" telemetryKey="search.timeout" />);
    expect(screen.getByTestId('error-message').className).toContain('bg-blue-50');
  });

  it('action button dispara onClick', () => {
    const onClick = jest.fn();
    render(
      <ErrorMessage
        title="X"
        body="Y"
        telemetryKey="search.timeout"
        action={{ label: 'Tentar novamente', onClick }}
      />
    );
    fireEvent.click(screen.getByText('Tentar novamente'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('sentryEventId renderiza botão "Copiar código"', () => {
    render(
      <ErrorMessage
        title="X"
        body="Y"
        sentryEventId="abc123def456"
        telemetryKey="generic.unexpected"
      />
    );
    expect(screen.getByLabelText(/Copiar código de erro abc123def456/)).toBeInTheDocument();
  });

  it('AC4: emite mixpanel.track("error_message_shown") no mount', async () => {
    render(
      <ErrorMessage
        title="X"
        body="Y"
        severity="error"
        telemetryKey="search.timeout"
      />
    );
    await waitFor(() => {
      expect(mockTrack).toHaveBeenCalledWith(
        'error_message_shown',
        expect.objectContaining({
          error_type: 'search.timeout',
          severity: 'error',
        })
      );
    });
  });

  it('AC4: telemetria inclui pathname da página', async () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { pathname: '/buscar' },
    });
    render(<ErrorMessage title="X" body="Y" telemetryKey="search.timeout" />);
    await waitFor(() => {
      expect(mockTrack).toHaveBeenCalledWith(
        'error_message_shown',
        expect.objectContaining({ page: '/buscar' })
      );
    });
  });
});
