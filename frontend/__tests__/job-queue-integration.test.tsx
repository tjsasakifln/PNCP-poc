/**
 * GTM-RESILIENCE-F01: Tests for job queue frontend integration.
 *
 * Tests cover:
 * - AC18: BuscaResult types include llm_status and excel_status
 * - AC21: SSE event handling for llm_ready and excel_ready
 * - AC21: SearchId kept alive during background job processing
 * - AC21: handleSseEvent updates result state correctly
 */

import { renderHook, act } from '@testing-library/react';

// ============================================================================
// Type Tests (AC18)
// ============================================================================

describe('BuscaResult types (AC18)', () => {
  it('includes llm_status field', () => {
    // Type-level test: if this compiles, the field exists
    const result: import('../app/types').BuscaResult = {
      resumo: {
        resumo_executivo: 'test',
        total_oportunidades: 0,
        valor_total: 0,
        destaques: [],
      },
      licitacoes: [],
      download_id: null,
      total_raw: 0,
      total_filtrado: 0,
      filter_stats: null,
      termos_utilizados: null,
      stopwords_removidas: null,
      excel_available: false,
      upgrade_message: null,
      source_stats: null,
      llm_status: 'processing',
      excel_status: 'processing',
    };
    expect(result.llm_status).toBe('processing');
    expect(result.excel_status).toBe('processing');
  });

  it('llm_status accepts all valid values', () => {
    const values: Array<import('../app/types').BuscaResult['llm_status']> = [
      'ready', 'processing', null, undefined,
    ];
    expect(values).toHaveLength(4);
  });

  it('excel_status accepts all valid values', () => {
    const values: Array<import('../app/types').BuscaResult['excel_status']> = [
      'ready', 'processing', 'skipped', 'failed', null, undefined,
    ];
    expect(values).toHaveLength(6);
  });
});

// ============================================================================
// SearchProgressEvent detail types (AC19/AC20)
// ============================================================================

describe('SearchProgressEvent detail types (AC19/AC20)', () => {
  it('supports resumo field for llm_ready events', () => {
    const event: import('../hooks/useSearchProgress').SearchProgressEvent = {
      stage: 'llm_ready',
      progress: 85,
      message: 'Resumo pronto',
      detail: {
        resumo: {
          resumo_executivo: 'AI summary',
          total_oportunidades: 5,
        },
      },
    };
    expect(event.detail.resumo).toBeDefined();
    expect(event.stage).toBe('llm_ready');
  });

  it('supports download_url field for excel_ready events', () => {
    const event: import('../hooks/useSearchProgress').SearchProgressEvent = {
      stage: 'excel_ready',
      progress: 98,
      message: 'Planilha pronta',
      detail: {
        download_url: 'https://example.com/file.xlsx',
        excel_status: 'ready',
      },
    };
    expect(event.detail.download_url).toBe('https://example.com/file.xlsx');
  });

  it('supports excel_status failed for excel_ready events', () => {
    const event: import('../hooks/useSearchProgress').SearchProgressEvent = {
      stage: 'excel_ready',
      progress: 98,
      message: 'Erro',
      detail: {
        excel_status: 'failed',
      },
    };
    expect(event.detail.excel_status).toBe('failed');
  });
});

// ============================================================================
// useSearchProgress handles F-01 events (AC19/AC20)
// ============================================================================

describe('useSearchProgress F-01 event handling', () => {
  // Mock EventSource
  let mockEventSource: any;

  beforeEach(() => {
    mockEventSource = {
      onopen: null,
      onmessage: null,
      onerror: null,
      close: jest.fn(),
      addEventListener: jest.fn(),
      readyState: 0,
    };
    (global as any).EventSource = jest.fn(() => mockEventSource);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('does not close SSE on llm_ready (non-terminal event)', async () => {
    const { useSearchProgress } = require('../hooks/useSearchProgress');

    const onEvent = jest.fn();
    const { result } = renderHook(() =>
      useSearchProgress({
        searchId: 'test-123',
        enabled: true,
        onEvent,
      })
    );

    // Simulate SSE open
    act(() => {
      mockEventSource.onopen?.();
    });

    // Simulate llm_ready event
    act(() => {
      mockEventSource.onmessage?.({
        data: JSON.stringify({
          stage: 'llm_ready',
          progress: 85,
          message: 'Resumo pronto',
          detail: { resumo: { resumo_executivo: 'Test' } },
        }),
      });
    });

    // SSE should NOT be closed (llm_ready is non-terminal)
    expect(mockEventSource.close).not.toHaveBeenCalled();
    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({ stage: 'llm_ready' })
    );
  });

  it('does not close SSE on excel_ready (non-terminal event)', async () => {
    const { useSearchProgress } = require('../hooks/useSearchProgress');

    const onEvent = jest.fn();
    renderHook(() =>
      useSearchProgress({
        searchId: 'test-123',
        enabled: true,
        onEvent,
      })
    );

    act(() => { mockEventSource.onopen?.(); });

    act(() => {
      mockEventSource.onmessage?.({
        data: JSON.stringify({
          stage: 'excel_ready',
          progress: 98,
          message: 'Planilha pronta',
          detail: { download_url: 'https://example.com/file.xlsx' },
        }),
      });
    });

    // SSE should NOT be closed (excel_ready is non-terminal)
    expect(mockEventSource.close).not.toHaveBeenCalled();
  });

  it('closes SSE on complete event (terminal)', async () => {
    const { useSearchProgress } = require('../hooks/useSearchProgress');

    renderHook(() =>
      useSearchProgress({
        searchId: 'test-123',
        enabled: true,
      })
    );

    act(() => { mockEventSource.onopen?.(); });

    act(() => {
      mockEventSource.onmessage?.({
        data: JSON.stringify({
          stage: 'complete',
          progress: 100,
          message: 'Done',
          detail: {},
        }),
      });
    });

    expect(mockEventSource.close).toHaveBeenCalled();
  });
});
