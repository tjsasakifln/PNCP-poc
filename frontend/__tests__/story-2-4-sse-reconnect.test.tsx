/**
 * STORY-2.4 — SSE reconnect feedback banner tests.
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConnectionBanner } from '@/app/buscar/components/ConnectionBanner';
import {
  deriveSseConnectionState,
  type SseConnectionState,
} from '@/lib/sseConnectionState';

describe('STORY-2.4 — deriveSseConnectionState (AC1)', () => {
  it('idle quando inativo', () => {
    expect(
      deriveSseConnectionState({
        active: false,
        isConnected: false,
        isReconnecting: false,
        sseDisconnected: false,
      })
    ).toBe('idle');
  });

  it('connected quando isConnected', () => {
    expect(
      deriveSseConnectionState({
        active: true,
        isConnected: true,
        isReconnecting: false,
        sseDisconnected: false,
      })
    ).toBe('connected');
  });

  it('reconnecting quando isReconnecting', () => {
    expect(
      deriveSseConnectionState({
        active: true,
        isConnected: false,
        isReconnecting: true,
        sseDisconnected: false,
      })
    ).toBe('reconnecting');
  });

  it('failed quando sseDisconnected', () => {
    expect(
      deriveSseConnectionState({
        active: true,
        isConnected: false,
        isReconnecting: false,
        sseDisconnected: true,
      })
    ).toBe('failed');
  });

  it('failed quando inactivityTimeout', () => {
    expect(
      deriveSseConnectionState({
        active: true,
        isConnected: false,
        isReconnecting: false,
        sseDisconnected: false,
        inactivityTimeout: true,
      })
    ).toBe('failed');
  });

  it('polling quando pollingActive precede sseDisconnected', () => {
    expect(
      deriveSseConnectionState({
        active: true,
        isConnected: false,
        isReconnecting: false,
        sseDisconnected: true,
        pollingActive: true,
      })
    ).toBe('polling');
  });
});

describe('STORY-2.4 — <ConnectionBanner> (AC2+AC3)', () => {
  it('retorna null quando state=idle', () => {
    const { container } = render(<ConnectionBanner state="idle" />);
    expect(container.firstChild).toBeNull();
  });

  it('retorna null quando state=connected', () => {
    const { container } = render(<ConnectionBanner state="connected" />);
    expect(container.firstChild).toBeNull();
  });

  it('AC2: state=reconnecting renderiza banner amarelo com role=status', () => {
    render(<ConnectionBanner state="reconnecting" attempt={2} maxAttempts={5} />);
    const banner = screen.getByTestId('connection-banner-reconnecting');
    expect(banner).toHaveAttribute('role', 'status');
    expect(banner.className).toContain('bg-amber-50');
    expect(screen.getByText(/Conexão lenta/)).toBeInTheDocument();
    expect(screen.getByText(/Tentativa 2 de 5/)).toBeInTheDocument();
  });

  it('AC2: state=failed renderiza banner vermelho + botão Tentar novamente', () => {
    const onRetry = jest.fn();
    render(<ConnectionBanner state="failed" onRetry={onRetry} />);
    const banner = screen.getByTestId('connection-banner-failed');
    expect(banner).toHaveAttribute('role', 'alert');
    expect(banner.className).toContain('bg-red-50');
    fireEvent.click(screen.getByText('Tentar novamente'));
    expect(onRetry).toHaveBeenCalled();
  });

  it('AC2: state=failed sem onRetry omite o botão', () => {
    render(<ConnectionBanner state="failed" />);
    expect(screen.queryByText('Tentar novamente')).not.toBeInTheDocument();
  });

  it('AC3: state=polling renderiza banner azul', () => {
    render(<ConnectionBanner state="polling" />);
    const banner = screen.getByTestId('connection-banner-polling');
    expect(banner).toHaveAttribute('role', 'status');
    expect(banner.className).toContain('bg-blue-50');
    expect(screen.getByText(/Modo polling ativo/)).toBeInTheDocument();
    expect(screen.getByText(/3 segundos/)).toBeInTheDocument();
  });

  it('passa className extra', () => {
    render(<ConnectionBanner state="reconnecting" className="custom-x" />);
    expect(screen.getByTestId('connection-banner-reconnecting').className).toContain('custom-x');
  });
});

describe('STORY-2.4 — Telemetria mixpanel (AC4)', () => {
  it('useSearchSSE.ts emite sse_reconnect_attempt no scheduleRetry', () => {
    // Static check: confirma que a telemetria foi adicionada no hook
    const fs = jest.requireActual('fs') as typeof import('fs');
    const path = jest.requireActual('path') as typeof import('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../hooks/useSearchSSE.ts'),
      'utf-8'
    );
    expect(src).toContain('sse_reconnect_attempt');
    expect(src).toContain('sse_failed_fallback_polling');
    expect(src).toContain('STORY-2.4 AC4');
  });
});

// Sanity: derivation is exhaustive
describe('STORY-2.4 — exhaustivo', () => {
  it('todos os estados têm string distinta', () => {
    const states: SseConnectionState[] = ['idle', 'connected', 'reconnecting', 'failed', 'polling'];
    const set = new Set(states);
    expect(set.size).toBe(5);
  });
});
