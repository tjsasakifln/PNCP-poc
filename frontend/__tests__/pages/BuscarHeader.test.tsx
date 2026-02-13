/**
 * BuscarPage Header Tests
 * STORY-223 AC25-AC27: /buscar header auth state regression test
 *
 * Tests:
 * - AC25: During auth loading, page shows spinner
 * - AC26: After auth resolves with user, header shows UserMenu with avatar
 * - AC27: When not authenticated, header shows "Entrar" button
 */

// Set backend URL before imports (required by component)
process.env.NEXT_PUBLIC_BACKEND_URL = 'http://test-backend:8000';

import { render, screen, waitFor } from '@testing-library/react';
import BuscarPage from '@/app/buscar/page';

// Mock all the hooks and dependencies
const mockUseAuth = jest.fn();
const mockUsePlan = jest.fn();
const mockUseAnalytics = jest.fn();
const mockUseOnboarding = jest.fn();
const mockUseKeyboardShortcuts = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('../../hooks/usePlan', () => ({
  usePlan: () => mockUsePlan(),
}));

jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => mockUseAnalytics(),
}));

jest.mock('../../hooks/useOnboarding', () => ({
  useOnboarding: () => mockUseOnboarding(),
}));

jest.mock('../../hooks/useKeyboardShortcuts', () => ({
  useKeyboardShortcuts: () => mockUseKeyboardShortcuts(),
  getShortcutDisplay: () => 'Ctrl+K',
}));

// Mock Next.js components
jest.mock('next/link', () => {
  return function MockLink({ children, href, onClick }: { children: React.ReactNode; href: string; onClick?: () => void }) {
    return <a href={href} onClick={onClick}>{children}</a>;
  };
});

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock PullToRefresh component
jest.mock('react-simple-pull-to-refresh', () => {
  return function MockPullToRefresh({ children }: { children: React.ReactNode }) {
    return <div>{children}</div>;
  };
});

// Mock child components that have complex dependencies
jest.mock('../../app/components/ThemeToggle', () => ({
  ThemeToggle: () => <button>Theme Toggle</button>,
}));

jest.mock('../../app/components/SavedSearchesDropdown', () => ({
  SavedSearchesDropdown: () => <div>Saved Searches</div>,
}));

jest.mock('../../app/components/QuotaBadge', () => ({
  QuotaBadge: () => <div>Quota Badge</div>,
}));

jest.mock('../../app/components/PlanBadge', () => ({
  PlanBadge: () => <div>Plan Badge</div>,
}));

jest.mock('../../app/components/MessageBadge', () => ({
  MessageBadge: () => <div>Message Badge</div>,
}));

jest.mock('../../app/components/UpgradeModal', () => ({
  UpgradeModal: () => <div>Upgrade Modal</div>,
}));

jest.mock('../../app/buscar/components/SearchForm', () => {
  return function MockSearchForm() {
    return <div>Search Form</div>;
  };
});

jest.mock('../../app/buscar/components/SearchResults', () => {
  return function MockSearchResults() {
    return <div>Search Results</div>;
  };
});

// Mock the search hooks with minimal implementation
jest.mock('../../app/buscar/hooks/useSearchFilters', () => ({
  useSearchFilters: () => ({
    setores: [],
    setoresSelecionados: new Set(),
    estados: [],
    ufsSelecionadas: new Set(),
    municipio: '',
    dataInicial: '2026-01-01',
    dataFinal: '2026-01-31',
    valorMin: '',
    valorMax: '',
    canSearch: false,
    toggleSetor: jest.fn(),
    toggleEstado: jest.fn(),
    selecionarTodos: jest.fn(),
    limparSelecao: jest.fn(),
    setMunicipio: jest.fn(),
    setDataInicial: jest.fn(),
    setDataFinal: jest.fn(),
    setValorMin: jest.fn(),
    setValorMax: jest.fn(),
    setEstados: jest.fn(),
    setSetores: jest.fn(),
  }),
}));

jest.mock('../../app/buscar/hooks/useSearch', () => ({
  useSearch: () => ({
    result: null,
    loading: false,
    loadingStep: null,
    progress: null,
    statesProcessed: 0,
    buscar: jest.fn(),
    downloadExcel: jest.fn(),
    setResult: jest.fn(),
    restoreSearchStateOnMount: jest.fn(),
    handleLoadSearch: jest.fn(),
    cancelSearch: jest.fn(),
    estimateSearchTime: jest.fn(() => 30),
  }),
}));

describe('BuscarPage Header - Auth States', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock return values
    mockUsePlan.mockReturnValue({
      planInfo: null,
      loading: false,
    });

    mockUseAnalytics.mockReturnValue({
      trackEvent: jest.fn(),
      identifyUser: jest.fn(),
      resetUser: jest.fn(),
      trackPageView: jest.fn(),
    });

    mockUseOnboarding.mockReturnValue({
      shouldShowOnboarding: false,
      restartTour: jest.fn(),
    });

    mockUseKeyboardShortcuts.mockReturnValue(undefined);
  });

  describe('AC25: Auth loading state', () => {
    it('should show spinner during auth loading', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: true,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      // Should show loading spinner
      expect(screen.getByText('Carregando...')).toBeInTheDocument();

      // Should show spinner element
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();

      // Should NOT show header yet
      expect(screen.queryByText(/SmartLic/i)).not.toBeInTheDocument();
    });
  });

  describe('AC26: Authenticated user state', () => {
    it('should show UserMenu with avatar after auth resolves', async () => {
      const mockUser = {
        email: 'test@example.com',
        id: '123',
      };

      const mockSession = {
        access_token: 'token-123',
      };

      mockUseAuth.mockReturnValue({
        user: mockUser,
        session: mockSession,
        loading: false,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      // Should NOT show loading spinner
      expect(screen.queryByText('Carregando...')).not.toBeInTheDocument();

      // Should show the header with SmartLic logo (use getByRole to be specific)
      const logoLink = screen.getByRole('link', { name: /SmartLic/i });
      expect(logoLink).toBeInTheDocument();
      expect(logoLink).toHaveAttribute('href', '/');

      // Should show UserMenu avatar button (first letter of email)
      // UserMenu renders a button with the first letter of the email as text and title attribute
      const avatarButtons = screen.getAllByRole('button');
      const avatarButton = avatarButtons.find(btn => btn.getAttribute('title') === 'test@example.com');

      expect(avatarButton).toBeDefined();
      expect(avatarButton).toHaveTextContent('T');
    });

    it('should show all header elements for authenticated user', () => {
      mockUseAuth.mockReturnValue({
        user: { email: 'test@example.com', id: '123' },
        session: { access_token: 'token-123' },
        loading: false,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      // Should show logo (use role selector to avoid footer match)
      const logoLink = screen.getByRole('link', { name: /SmartLic/i });
      expect(logoLink).toBeInTheDocument();

      // Should show theme toggle
      expect(screen.getByText('Theme Toggle')).toBeInTheDocument();

      // Should show saved searches
      expect(screen.getByText('Saved Searches')).toBeInTheDocument();

      // Should show message badge
      expect(screen.getByText('Message Badge')).toBeInTheDocument();
    });
  });

  describe('AC27: Not authenticated state', () => {
    it('should show "Entrar" button when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: false,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      // Should show the header logo
      const logoLink = screen.getByRole('link', { name: /SmartLic/i });
      expect(logoLink).toBeInTheDocument();

      // Should show "Entrar" button from UserMenu
      const entrarLink = screen.getByRole('link', { name: /Entrar/i });
      expect(entrarLink).toBeInTheDocument();
      expect(entrarLink).toHaveAttribute('href', '/login');
    });

    it('should show "Criar conta" button when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: false,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      // Should show "Criar conta" button from UserMenu
      const criarContaLink = screen.getByRole('link', { name: /Criar conta/i });
      expect(criarContaLink).toBeInTheDocument();
      expect(criarContaLink).toHaveAttribute('href', '/signup');
    });

    it('should NOT show user avatar when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: false,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      // UserMenu should render links, not a button with avatar
      const entrarLink = screen.getByRole('link', { name: /Entrar/i });
      expect(entrarLink).toBeInTheDocument();

      // Should NOT have avatar button
      const buttons = screen.queryAllByRole('button');
      const avatarButton = buttons.find(btn => btn.className.includes('rounded-full'));
      expect(avatarButton).toBeUndefined();
    });
  });

  describe('Header consistency across states', () => {
    it('should always show SmartLic logo after loading completes', () => {
      const testCases = [
        { user: null, loading: false }, // Not logged in
        { user: { email: 'test@example.com', id: '123' }, loading: false }, // Logged in
      ];

      testCases.forEach(({ user, loading }) => {
        mockUseAuth.mockReturnValue({
          user,
          session: user ? { access_token: 'token' } : null,
          loading,
          isAdmin: false,
          signOut: jest.fn(),
        });

        const { unmount } = render(<BuscarPage />);

        const logoLink = screen.getByRole('link', { name: /SmartLic/i });
        expect(logoLink).toBeInTheDocument();
        expect(logoLink).toHaveAttribute('href', '/');

        unmount();
      });
    });

    it('should always show ThemeToggle after loading completes', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        session: null,
        loading: false,
        isAdmin: false,
        signOut: jest.fn(),
      });

      render(<BuscarPage />);

      expect(screen.getByText('Theme Toggle')).toBeInTheDocument();
    });
  });
});
