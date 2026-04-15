/**
 * PipelinePage Component Tests — DEBT-111 AC2
 *
 * Tests pipeline page states: loading, kanban, trial expired read-only,
 * pipeline limit modal, error state, empty state, and auth redirect.
 */

import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';

// ============================================================================
// Mocks
// ============================================================================

const mockUser = { id: 'user-1', email: 'test@test.com' };
const mockSession = { access_token: 'mock-token' };

let mockAuthState = {
  user: mockUser,
  session: mockSession,
  loading: false,
};

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockAuthState,
}));

// usePipeline — controlled per test
let mockPipelineState = {
  items: [] as any[],
  loading: false,
  error: null as string | null,
  fetchItems: jest.fn(),
  updateItem: jest.fn(),
  removeItem: jest.fn(),
};

jest.mock('../../hooks/usePipeline', () => ({
  usePipeline: () => mockPipelineState,
}));

// usePlan — default: active pro
let mockPlanInfo: any = {
  plan_id: 'smartlic_pro',
  subscription_status: 'active',
};

jest.mock('../../hooks/usePlan', () => ({
  usePlan: () => ({ planInfo: mockPlanInfo }),
}));

// useTrialPhase — default: not limited
let mockTrialPhase = 'active';

jest.mock('../../hooks/useTrialPhase', () => ({
  useTrialPhase: () => ({ phase: mockTrialPhase }),
}));

// useIsMobile — default: desktop
let mockIsMobile = false;

jest.mock('../../hooks/useIsMobile', () => ({
  useIsMobile: () => mockIsMobile,
}));

// useAnalytics
const mockTrackEvent = jest.fn();
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));


// OnboardingTourButton — no-op render
jest.mock('../../components/OnboardingTourButton', () => ({
  OnboardingTourButton: () => null,
}));

// TrialUpsellCTA — no-op render
jest.mock('../../components/billing/TrialUpsellCTA', () => ({
  TrialUpsellCTA: () => null,
}));

// AuthLoadingScreen
jest.mock('../../components/AuthLoadingScreen', () => ({
  AuthLoadingScreen: () => <div data-testid="auth-loading-screen">Loading...</div>,
}));

// PageHeader
jest.mock('../../components/PageHeader', () => ({
  PageHeader: ({ title }: { title: string }) => <header>{title}</header>,
}));

// EmptyState
jest.mock('../../components/EmptyState', () => ({
  EmptyState: ({ title, ctaLabel, ctaHref }: any) => (
    <div data-testid="pipeline-empty-state">
      <p>{title}</p>
      <a href={ctaHref}>{ctaLabel}</a>
    </div>
  ),
}));

// ErrorStateWithRetry
jest.mock('../../components/ErrorStateWithRetry', () => ({
  ErrorStateWithRetry: ({ message, onRetry }: any) => (
    <div data-testid="pipeline-error-state">
      <p>{message}</p>
      <button onClick={onRetry}>Tentar novamente</button>
    </div>
  ),
}));

// PipelineKanban (dynamic import)
jest.mock('../../app/pipeline/PipelineKanban', () => ({
  PipelineKanban: ({ items }: any) => (
    <div data-testid="pipeline-kanban">
      {items.map((item: any) => (
        <div key={item.id} data-testid="pipeline-card">{item.objeto}</div>
      ))}
    </div>
  ),
  ReadOnlyKanban: ({ items }: any) => (
    <div data-testid="pipeline-readonly-kanban">
      {items.map((item: any) => (
        <div key={item.id} data-testid="pipeline-card-readonly">{item.objeto}</div>
      ))}
    </div>
  ),
}));

// PipelineMobileTabs
jest.mock('../../app/pipeline/PipelineMobileTabs', () => ({
  PipelineMobileTabs: () => <div data-testid="pipeline-mobile-tabs" />,
}));

// Button UI
jest.mock('../../components/ui/button', () => ({
  Button: ({ children, onClick, variant }: any) => (
    <button onClick={onClick} data-variant={variant}>{children}</button>
  ),
}));

// next/dynamic — resolve synchronously in tests to avoid skeleton-stuck state
jest.mock('next/dynamic', () => (fn: () => Promise<any>) => {
  // Execute the factory synchronously using a trick: return the cached mock module
  // PipelineKanban module is already mocked above, so we just return the right component
  const PipelineKanbanMock = require('../../app/pipeline/PipelineKanban');
  // The factory fn determines which export to use (PipelineKanban or ReadOnlyKanban)
  // We detect by inspecting the factory source string
  const factorySrc = fn.toString();
  const MockDynamic = (props: any) => {
    if (factorySrc.includes('ReadOnlyKanban')) {
      return <PipelineKanbanMock.ReadOnlyKanban {...props} />;
    }
    return <PipelineKanbanMock.PipelineKanban {...props} />;
  };
  MockDynamic.displayName = 'MockDynamic';
  return MockDynamic;
});

// Mock fetch globally
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: async () => ({}),
});

// ============================================================================
// Import page after all mocks are set up
// ============================================================================

import PipelinePage from '@/app/pipeline/page';

// ============================================================================
// Sample data
// ============================================================================

const sampleItems = [
  {
    id: 'item-1',
    user_id: 'user-1',
    pncp_id: 'pncp-1',
    objeto: 'Fornecimento de uniformes escolares',
    orgao: 'Prefeitura de SP',
    uf: 'SP',
    valor_estimado: 150000,
    data_encerramento: '2026-04-01',
    link_pncp: null,
    stage: 'descoberta' as const,
    notes: null,
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-03-01T00:00:00Z',
    version: 1,
  },
  {
    id: 'item-2',
    user_id: 'user-1',
    pncp_id: 'pncp-2',
    objeto: 'Limpeza e conservação de prédios',
    orgao: 'Governo do RJ',
    uf: 'RJ',
    valor_estimado: 300000,
    data_encerramento: '2026-04-15',
    link_pncp: null,
    stage: 'analise' as const,
    notes: null,
    created_at: '2026-03-02T00:00:00Z',
    updated_at: '2026-03-02T00:00:00Z',
    version: 1,
  },
];

// ============================================================================
// Tests
// ============================================================================

beforeEach(() => {
  jest.clearAllMocks();

  // Reset to defaults
  mockAuthState = { user: mockUser, session: mockSession, loading: false };
  mockPipelineState = {
    items: [],
    loading: false,
    error: null,
    fetchItems: jest.fn(),
    updateItem: jest.fn(),
    removeItem: jest.fn(),
  };
  mockPlanInfo = { plan_id: 'smartlic_pro', subscription_status: 'active' };
  mockTrialPhase = 'active';
  mockIsMobile = false;

  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({}),
  });
});

describe('PipelinePage', () => {
  describe('Loading skeleton', () => {
    it('renders loading skeleton while pipeline items are loading', () => {
      mockPipelineState = { ...mockPipelineState, loading: true, items: [] };

      render(<PipelinePage />);

      expect(screen.getByTestId('pipeline-skeleton')).toBeInTheDocument();
    });

    it('shows animate-pulse elements in skeleton', () => {
      mockPipelineState = { ...mockPipelineState, loading: true, items: [] };

      render(<PipelinePage />);

      const pulses = document.querySelectorAll('.animate-pulse');
      expect(pulses.length).toBeGreaterThan(0);
    });
  });

  describe('Loaded kanban board', () => {
    it('renders kanban board when items are loaded', async () => {
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByTestId('pipeline-kanban')).toBeInTheDocument();
      });
    });

    it('shows item count in header', async () => {
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByText(/2 itens no pipeline/i)).toBeInTheDocument();
      });
    });

    it('shows singular "item" when there is 1 item', async () => {
      mockPipelineState = { ...mockPipelineState, items: [sampleItems[0]], loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByText(/1 item no pipeline/i)).toBeInTheDocument();
      });
    });

    it('renders pipeline card contents', async () => {
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByText('Fornecimento de uniformes escolares')).toBeInTheDocument();
        expect(screen.getByText('Limpeza e conservação de prédios')).toBeInTheDocument();
      });
    });
  });

  describe('Trial expired read-only mode', () => {
    it('shows read-only alert when trial is expired and items exist', async () => {
      mockPlanInfo = { plan_id: 'free_trial', subscription_status: 'expired' };
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText(/trial expirou/i)).toBeInTheDocument();
        expect(screen.getByText(/modo leitura/i)).toBeInTheDocument();
      });
    });

    it('renders read-only kanban in trial expired mode', async () => {
      mockPlanInfo = { plan_id: 'free_trial', subscription_status: 'expired' };
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByTestId('pipeline-readonly-kanban')).toBeInTheDocument();
      });
    });

    it('shows link to plans in trial expired alert', async () => {
      mockPlanInfo = { plan_id: 'free_trial', subscription_status: 'expired' };
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /ver planos/i });
        expect(link).toHaveAttribute('href', '/planos');
      });
    });
  });

  describe('Pipeline limit modal', () => {
    it('shows pipeline limit banner when trial is limited and items at limit', async () => {
      mockTrialPhase = 'limited_access';
      const limitedItems = Array.from({ length: 5 }, (_, i) => ({
        ...sampleItems[0],
        id: `item-${i}`,
        objeto: `Item ${i}`,
      }));
      mockPipelineState = { ...mockPipelineState, items: limitedItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByTestId('pipeline-limit-banner')).toBeInTheDocument();
        expect(screen.getByText(/limite de 5 itens/i)).toBeInTheDocument();
      });
    });

    it('does not show limit banner when trial is not limited', async () => {
      mockTrialPhase = 'active';
      const limitedItems = Array.from({ length: 5 }, (_, i) => ({
        ...sampleItems[0],
        id: `item-${i}`,
        objeto: `Item ${i}`,
      }));
      mockPipelineState = { ...mockPipelineState, items: limitedItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.queryByTestId('pipeline-limit-banner')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error state', () => {
    it('renders skeleton when items are still loading (error not yet determined)', () => {
      // This test covers the "initial load in progress" state.
      // The internal initialLoadFailed state is set via useEffect after fetch completes;
      // during fetch, the skeleton is shown (loading=true, items=[]).
      mockPipelineState = {
        ...mockPipelineState,
        items: [],
        loading: true,
        error: null,
      };

      render(<PipelinePage />);

      expect(screen.getByTestId('pipeline-skeleton')).toBeInTheDocument();
    });

    it('calls fetchItems when retry is clicked after error', async () => {
      // Test the retry button by starting in error+stale-data mode (isReadOnlyError)
      // which directly renders the "Tentar novamente" button without internal state machine.
      const mockFetch = jest.fn();
      mockPipelineState = {
        ...mockPipelineState,
        items: sampleItems, // stale data exists
        loading: false,
        error: 'Erro de sincronização',
        fetchItems: mockFetch,
      };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /tentar novamente/i }));

      expect(mockFetch).toHaveBeenCalled();
    });

    it('shows read-only alert with retry when error occurs but stale data exists', async () => {
      mockPipelineState = {
        ...mockPipelineState,
        items: sampleItems,
        loading: false,
        error: 'Erro de sincronização',
      };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByText(/pipeline em modo leitura/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument();
      });
    });
  });

  describe('Empty state', () => {
    it('shows empty state when no pipeline items and no loading or error', async () => {
      mockPipelineState = { ...mockPipelineState, items: [], loading: false, error: null };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByTestId('pipeline-empty-state')).toBeInTheDocument();
        expect(screen.getByText(/aqui você acompanha suas oportunidades/i)).toBeInTheDocument();
      });
    });

    it('has link to /buscar in empty state', async () => {
      mockPipelineState = { ...mockPipelineState, items: [], loading: false, error: null };

      render(<PipelinePage />);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /buscar oportunidades/i });
        expect(link).toHaveAttribute('href', '/buscar');
      });
    });
  });

  describe('Auth states', () => {
    it('shows auth loading screen while auth is loading', () => {
      mockAuthState = { user: null as any, session: null as any, loading: true };

      render(<PipelinePage />);

      expect(screen.getByTestId('auth-loading-screen')).toBeInTheDocument();
    });

    it('shows login prompt when not authenticated', () => {
      mockAuthState = { user: null as any, session: null as any, loading: false };

      render(<PipelinePage />);

      expect(screen.getByText(/faça login para acessar seu pipeline/i)).toBeInTheDocument();
    });

    it('does not show kanban when not authenticated', () => {
      mockAuthState = { user: null as any, session: null as any, loading: false };

      render(<PipelinePage />);

      expect(screen.queryByTestId('pipeline-kanban')).not.toBeInTheDocument();
    });
  });

  describe('Mobile layout', () => {
    it('renders mobile tabs on mobile devices when items are loaded', async () => {
      mockIsMobile = true;
      mockPipelineState = { ...mockPipelineState, items: sampleItems, loading: false };

      render(<PipelinePage />);

      await waitFor(() => {
        expect(screen.getByTestId('pipeline-mobile-tabs')).toBeInTheDocument();
      });
    });
  });
});
