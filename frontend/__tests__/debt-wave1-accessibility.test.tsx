/**
 * DEBT Wave 1 PR1 — Accessibility Tests
 *
 * DEBT-FE-022: Protected layout main-content id
 * DEBT-FE-017: Login form aria-invalid + aria-describedby
 * DEBT-FE-002: SearchForm ARIA role="search"
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// ============================================================
// Mocks
// ============================================================

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/buscar',
}));

jest.mock('@/app/components/AuthProvider', () => ({
  useAuth: () => ({
    session: { user: { id: 'test', email: 'test@test.com', created_at: '2026-01-01' }, access_token: 'tok' },
    loading: false,
    signInWithEmail: jest.fn(),
    signInWithMagicLink: jest.fn(),
    signInWithGoogle: jest.fn(),
  }),
}));

jest.mock('@/hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: jest.fn(), identifyUser: jest.fn() }),
}));

jest.mock('sonner', () => ({ toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() } }));

jest.mock('@/lib/error-messages', () => ({
  translateAuthError: (msg: string) => msg,
  isTransientError: () => false,
  getMessageFromErrorCode: () => null,
}));

jest.mock('@/lib/config', () => ({ APP_NAME: 'SmartLic' }));

jest.mock('@/lib/supabase', () => ({
  supabase: { auth: { mfa: { getAuthenticatorAssuranceLevel: jest.fn().mockResolvedValue({ data: null }) } } },
}));

jest.mock('next/dynamic', () => () => () => null);

// Mock CustomSelect to avoid deep dependency chain
jest.mock('@/app/components/CustomSelect', () => ({
  CustomSelect: ({ id, value, placeholder }: { id: string; value: string; placeholder: string }) => (
    <select id={id} value={value} aria-label={placeholder} readOnly>
      <option value={value}>{value}</option>
    </select>
  ),
}));

// Mock lucide-react — return simple spans for all icons
jest.mock('lucide-react', () => {
  const handler: ProxyHandler<Record<string, unknown>> = {
    get: (_target, prop) => {
      if (typeof prop === 'string' && prop !== '__esModule') {
        return (props: Record<string, unknown>) => <span data-testid={`icon-${String(prop)}`} {...props} />;
      }
      return undefined;
    },
  };
  return new Proxy({}, handler);
});

// Mock SearchCustomizePanel to avoid deep dependency chain
jest.mock('@/app/buscar/components/SearchCustomizePanel', () => ({
  __esModule: true,
  default: () => <div data-testid="search-customize-panel" />,
}));

// ============================================================
// DEBT-FE-002: SearchForm ARIA
// ============================================================

import SearchForm from '@/app/buscar/components/SearchForm';
import SearchFormHeader from '@/app/buscar/components/SearchFormHeader';
import SearchFormActions from '@/app/buscar/components/SearchFormActions';

describe('DEBT-FE-002: SearchForm ARIA', () => {
  const baseProps = {
    setores: [{ id: 'eng', name: 'Engenharia', description: 'Eng desc' }],
    setoresLoading: false,
    setoresError: false,
    setoresUsingFallback: false,
    setoresUsingStaleCache: false,
    staleCacheAge: null,
    setoresRetryCount: 0,
    setorId: 'eng',
    setSetorId: jest.fn(),
    fetchSetores: jest.fn(),
    searchMode: 'setor' as const,
    setSearchMode: jest.fn(),
    termosArray: [] as string[],
    termoInput: '',
    setTermoInput: jest.fn(),
    termValidation: null,
    addTerms: jest.fn(),
    removeTerm: jest.fn(),
    loading: false,
    buscar: jest.fn(),
    searchButtonRef: { current: null },
    canSearch: true,
    searchLabel: 'Engenharia',
    result: null,
    handleSaveSearch: jest.fn(),
    isMaxCapacity: false,
    planInfo: null,
    onShowUpgradeModal: jest.fn(),
    clearResult: jest.fn(),
    customizeOpen: false,
    setCustomizeOpen: jest.fn(),
    ufsSelecionadas: new Set(['SP']),
    toggleUf: jest.fn(),
    toggleRegion: jest.fn(),
    selecionarTodos: jest.fn(),
    limparSelecao: jest.fn(),
    dataInicial: '2026-03-01',
    setDataInicial: jest.fn(),
    dataFinal: '2026-03-11',
    setDataFinal: jest.fn(),
    modoBusca: 'abertas' as const,
    dateLabel: '10 dias',
    locationFiltersOpen: false,
    setLocationFiltersOpen: jest.fn(),
    advancedFiltersOpen: false,
    setAdvancedFiltersOpen: jest.fn(),
    esferas: [] as string[],
    setEsferas: jest.fn(),
    municipios: '',
    setMunicipios: jest.fn(),
    status: 'recebendo_proposta',
    setStatus: jest.fn(),
    modalidades: [] as string[],
    setModalidades: jest.fn(),
    valorMin: '',
    setValorMin: jest.fn(),
    valorMax: '',
    setValorMax: jest.fn(),
    setValorValid: jest.fn(),
    validationErrors: {},
    showFirstUseTip: false,
    onDismissFirstUseTip: jest.fn(),
  };

  it('wraps search form with role="search" and aria-label', () => {
    const { container } = render(<SearchForm {...baseProps} />);

    const searchRegion = container.querySelector('[role="search"]');
    expect(searchRegion).toBeInTheDocument();
    expect(searchRegion).toHaveAttribute('aria-label', 'Buscar licitações');
  });
});

describe('DEBT-FE-002: SearchFormHeader toggle buttons', () => {
  it('has aria-pressed on search mode toggles', () => {
    render(
      <SearchFormHeader
        setores={[{ id: 'eng', name: 'Engenharia', description: 'desc' }]}
        setoresLoading={false}
        setoresError={false}
        setoresUsingFallback={false}
        setoresUsingStaleCache={false}
        staleCacheAge={null}
        setoresRetryCount={0}
        setorId="eng"
        setSetorId={jest.fn()}
        fetchSetores={jest.fn()}
        searchMode="setor"
        setSearchMode={jest.fn()}
        termosArray={[]}
        termoInput=""
        setTermoInput={jest.fn()}
        termValidation={null}
        addTerms={jest.fn()}
        removeTerm={jest.fn()}
        clearResult={jest.fn()}
      />
    );

    const setorButton = screen.getByRole('button', { name: /buscar por setor/i });
    const termosButton = screen.getByRole('button', { name: /buscar por termos/i });

    expect(setorButton).toHaveAttribute('aria-pressed', 'true');
    expect(termosButton).toHaveAttribute('aria-pressed', 'false');
  });
});

describe('DEBT-FE-002: SearchFormActions button', () => {
  it('has aria-label on search button', () => {
    render(
      <SearchFormActions
        loading={false}
        buscar={jest.fn()}
        searchButtonRef={{ current: null }}
        canSearch={true}
        searchLabel="Engenharia"
        searchMode="setor"
        termValidation={null}
        result={null}
        handleSaveSearch={jest.fn()}
        isMaxCapacity={false}
      />
    );

    const button = screen.getByRole('button', { name: /iniciar busca/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', 'Iniciar busca de licitações');
  });
});
