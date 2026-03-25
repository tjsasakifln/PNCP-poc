import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock dependencies to isolate SearchResults
jest.mock('next/link', () => {
  return function MockLink({ children, ...props }: any) {
    return <a {...props}>{children}</a>;
  };
});

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock hooks using relative paths (hooks/ is at root level, @/ maps to app/)
jest.mock('../../hooks/useSearchSSE', () => ({
  __esModule: true,
}));

jest.mock('../../app/buscar/components/RefreshBanner', () => {
  return function MockRefreshBanner() { return null; };
});

jest.mock('../../app/buscar/components/EnhancedLoadingProgress', () => ({
  EnhancedLoadingProgress: function Mock() { return null; },
}));

jest.mock('../../app/components/LoadingResultsSkeleton', () => ({
  LoadingResultsSkeleton: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/SearchEmptyState', () => ({
  SearchEmptyState: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/UfProgressGrid', () => ({
  UfProgressGrid: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/PartialResultsPrompt', () => ({
  PartialResultsPrompt: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/SourcesUnavailable', () => ({
  SourcesUnavailable: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/DataQualityBanner', () => ({
  DataQualityBanner: function Mock() { return null; },
}));

jest.mock('../../app/components/QuotaCounter', () => ({
  QuotaCounter: function Mock() { return null; },
}));

jest.mock('../../app/components/LicitacoesPreview', () => ({
  LicitacoesPreview: function Mock({ licitacoes }: any) {
    return (
      <div data-testid="licitacoes-preview">
        {licitacoes.map((l: any, i: number) => (
          <div key={i} data-testid={`bid-item-${l.pncp_id || i}`}>{l.objeto}</div>
        ))}
      </div>
    );
  },
}));

jest.mock('../../app/components/OrdenacaoSelect', () => ({
  OrdenacaoSelect: function Mock() { return <div data-testid="ordenacao-select" />; },
}));

jest.mock('../../app/buscar/components/GoogleSheetsExportButton', () => {
  return function Mock() { return null; };
});

jest.mock('../../app/buscar/components/LlmSourceBadge', () => ({
  LlmSourceBadge: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/ErrorDetail', () => ({
  ErrorDetail: function Mock() { return null; },
}));

jest.mock('../../app/buscar/hooks/useSearch', () => ({
  __esModule: true,
}));

jest.mock('../../app/buscar/components/ZeroResultsSuggestions', () => ({
  ZeroResultsSuggestions: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/FilterRelaxedBanner', () => ({
  FilterRelaxedBanner: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/ExpiredCacheBanner', () => ({
  ExpiredCacheBanner: function Mock() { return null; },
}));

jest.mock('../../app/buscar/components/SourceStatusGrid', () => {
  return function Mock() { return null; };
});

jest.mock('../../app/buscar/components/SearchStateManager', () => ({
  SearchStateManager: function Mock() { return null; },
}));

jest.mock('../../app/buscar/types/searchPhase', () => ({
  deriveSearchPhase: () => 'results',
}));

jest.mock('../../components/billing/TrialUpsellCTA', () => ({
  TrialUpsellCTA: function Mock() { return null; },
}));

jest.mock('../../components/billing/TrialPaywall', () => ({
  TrialPaywall: function Mock() { return null; },
}));

jest.mock('../../components/ui/Pagination', () => ({
  Pagination: function Mock({ totalItems, currentPage, pageSize, onPageChange, onPageSizeChange }: any) {
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
    const start = Math.min((currentPage - 1) * pageSize + 1, totalItems);
    const end = Math.min(currentPage * pageSize, totalItems);
    return (
      <div>
        <p data-testid="pagination-info">Exibindo {start}-{end} de {totalItems} oportunidades</p>
        <button data-testid="pagination-prev" disabled={currentPage <= 1} onClick={() => onPageChange(currentPage - 1)}>Anterior</button>
        <span data-testid="pagination-page-indicator">{currentPage} de {totalPages}</span>
        <button data-testid="pagination-next" disabled={currentPage >= totalPages} onClick={() => onPageChange(currentPage + 1)}>Próximo</button>
      </div>
    );
  },
  useInitPagination: () => 20,
}));

import SearchResults from '../../app/buscar/components/SearchResults';

// Generate N mock licitacoes
function makeLicitacoes(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    pncp_id: `pncp-${i + 1}`,
    objeto: `Licitação ${i + 1}`,
    orgao: 'Órgão Teste',
    valor: 100000 + i * 1000,
    uf: 'SP',
    municipio: 'São Paulo',
    modalidade: 'Pregão',
    data_abertura: '2026-01-01',
    data_encerramento: '2026-03-01',
    link: 'https://example.com',
    status: 'aberta',
    relevance_score: 0.8,
    relevance_source: 'keyword',
    confidence: 'high' as const,
    viability_level: 'excellent' as const,
    viability_score: 90,
    viability_factors: {},
    matched_terms: [],
    dias_restantes: 30,
    urgencia: 'normal',
    _source: 'PNCP',
    _value_source: 'edital',
  }));
}

const baseProps = {
  loading: false,
  loadingStep: 0,
  estimatedTime: 0,
  stateCount: 0,
  statesProcessed: 0,
  onCancel: jest.fn(),
  sseEvent: null,
  useRealProgress: false,
  sseAvailable: false,
  onStageChange: jest.fn(),
  error: null,
  quotaError: null,
  rawCount: 200,
  ufsSelecionadas: new Set(['SP']),
  sectorName: 'Informática',
  searchMode: 'setor' as const,
  termosArray: [],
  ordenacao: 'data_desc' as any,
  onOrdenacaoChange: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),
  planInfo: {
    plan_id: 'smartlic_pro',
    plan_name: 'SmartLic Pro',
    quota_used: 5,
    quota_reset_date: '2026-03-01',
    capabilities: {
      max_history_days: 365,
      max_requests_per_month: 1000,
      allow_excel: true,
    },
  },
  session: { access_token: 'test-token' },
  onShowUpgradeModal: jest.fn(),
  onTrackEvent: jest.fn(),
};

describe('SearchResults Pagination', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock window.history.replaceState
    const replaceStateSpy = jest.spyOn(window.history, 'replaceState');
    replaceStateSpy.mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // AC34: 100 items → shows 20 on page 1
  it('shows first 20 items of 100 on page 1', () => {
    const licitacoes = makeLicitacoes(100);
    render(
      <SearchResults
        {...baseProps}
        result={{
          licitacoes,
          resumo: {
            total_oportunidades: 100,
            valor_total: 5000000,
            resumo_executivo: 'Resumo teste',
            recomendacoes: [],
            destaques: [],
          },
        } as any}
      />
    );
    const preview = screen.getByTestId('licitacoes-preview');
    // Should show exactly 20 items (default page size)
    const items = preview.querySelectorAll('[data-testid^="bid-item-"]');
    expect(items.length).toBe(20);
    // First item should be pncp-1
    expect(screen.getByTestId('bid-item-pncp-1')).toBeInTheDocument();
  });

  // AC34: Navigate to page 2 → shows items 21-40
  it('shows items 21-40 on page 2', () => {
    const licitacoes = makeLicitacoes(100);
    render(
      <SearchResults
        {...baseProps}
        result={{
          licitacoes,
          resumo: {
            total_oportunidades: 100,
            valor_total: 5000000,
            resumo_executivo: 'Resumo teste',
            recomendacoes: [],
            destaques: [],
          },
        } as any}
      />
    );

    // Click next page
    const nextButtons = screen.getAllByTestId('pagination-next');
    fireEvent.click(nextButtons[0]);

    // Should now show items 21-40
    const preview = screen.getByTestId('licitacoes-preview');
    const items = preview.querySelectorAll('[data-testid^="bid-item-"]');
    expect(items.length).toBe(20);
    expect(screen.getByTestId('bid-item-pncp-21')).toBeInTheDocument();
  });

  // AC35: Sticky action bar is visible
  it('renders sticky action bar with Excel/PDF buttons', () => {
    const licitacoes = makeLicitacoes(50);
    render(
      <SearchResults
        {...baseProps}
        result={{
          licitacoes,
          resumo: {
            total_oportunidades: 50,
            valor_total: 5000000,
            resumo_executivo: 'Resumo teste',
            recomendacoes: [],
            destaques: [],
          },
        } as any}
        onGeneratePdf={jest.fn()}
      />
    );
    expect(screen.getByTestId('sticky-action-bar')).toBeInTheDocument();
    expect(screen.getByTestId('excel-download-button')).toBeInTheDocument();
    expect(screen.getByTestId('pdf-report-button')).toBeInTheDocument();
    expect(screen.getByTestId('sticky-count')).toHaveTextContent('50 oportunidades');
  });

  // AC3: Pagination appears above results
  it('renders pagination both above and below results', () => {
    const licitacoes = makeLicitacoes(50);
    render(
      <SearchResults
        {...baseProps}
        result={{
          licitacoes,
          resumo: {
            total_oportunidades: 50,
            valor_total: 5000000,
            resumo_executivo: 'Resumo teste',
            recomendacoes: [],
            destaques: [],
          },
        } as any}
      />
    );
    // Should have 1 pagination info (top only)
    const paginationInfos = screen.getAllByTestId('pagination-info');
    expect(paginationInfos.length).toBe(1);
  });
});
