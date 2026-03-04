/**
 * CRIT-052 AC2: EnhancedLoadingProgress reconnecting indicator tests.
 *
 * Verifies:
 * - "Reconectando..." indicator shown when isReconnecting=true
 * - Progress bar does not reset during reconnection
 * - SSE fallback indicator shown when sseDisconnected=true (existing behavior preserved)
 * - Real-time indicator shown when connected (existing behavior preserved)
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EnhancedLoadingProgress } from '../../components/EnhancedLoadingProgress';

describe('CRIT-052 AC2: Reconnecting indicator', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  it('should show "Reconectando..." when isReconnecting is true', () => {
    render(
      <EnhancedLoadingProgress
        currentStep={2}
        estimatedTime={60}
        stateCount={5}
        isReconnecting={true}
      />
    );

    expect(screen.getByTestId('sse-reconnecting-indicator')).toBeInTheDocument();
    expect(screen.getByText('Reconectando...')).toBeInTheDocument();
  });

  it('should not show fallback indicator when reconnecting', () => {
    render(
      <EnhancedLoadingProgress
        currentStep={2}
        estimatedTime={60}
        stateCount={5}
        isReconnecting={true}
        sseDisconnected={false}
      />
    );

    expect(screen.queryByTestId('sse-fallback-indicator')).not.toBeInTheDocument();
    expect(screen.getByTestId('sse-reconnecting-indicator')).toBeInTheDocument();
  });

  it('should show fallback indicator when sseDisconnected (not reconnecting)', () => {
    render(
      <EnhancedLoadingProgress
        currentStep={2}
        estimatedTime={60}
        stateCount={5}
        sseDisconnected={true}
        isReconnecting={false}
      />
    );

    expect(screen.getByTestId('sse-fallback-indicator')).toBeInTheDocument();
    expect(screen.queryByTestId('sse-reconnecting-indicator')).not.toBeInTheDocument();
  });

  it('should show real-time indicator when connected with SSE events', () => {
    render(
      <EnhancedLoadingProgress
        currentStep={2}
        estimatedTime={60}
        stateCount={5}
        sseEvent={{ stage: 'fetching', progress: 40, message: 'Analisando...', detail: {} }}
        isReconnecting={false}
        sseDisconnected={false}
      />
    );

    expect(screen.getByTestId('sse-realtime-indicator')).toBeInTheDocument();
    expect(screen.queryByTestId('sse-reconnecting-indicator')).not.toBeInTheDocument();
  });

  it('should maintain progress display during reconnection with prior SSE event', () => {
    render(
      <EnhancedLoadingProgress
        currentStep={2}
        estimatedTime={60}
        stateCount={5}
        statesProcessed={3}
        sseEvent={{ stage: 'fetching', progress: 55, message: 'Analisando...', detail: { uf_index: 3 } }}
        useRealProgress={true}
        isReconnecting={true}
      />
    );

    // Progress should show at least 55% (not reset to 0)
    const progressBar = screen.getByRole('progressbar');
    const progressValue = Number(progressBar.getAttribute('aria-valuenow'));
    expect(progressValue).toBeGreaterThanOrEqual(55);
  });

  it('should prioritize reconnecting indicator over fallback indicator', () => {
    // Edge case: both isReconnecting and sseDisconnected could theoretically be true
    render(
      <EnhancedLoadingProgress
        currentStep={2}
        estimatedTime={60}
        stateCount={5}
        isReconnecting={true}
        sseDisconnected={true}
      />
    );

    // Reconnecting takes priority
    expect(screen.getByTestId('sse-reconnecting-indicator')).toBeInTheDocument();
    expect(screen.queryByTestId('sse-fallback-indicator')).not.toBeInTheDocument();
  });
});
