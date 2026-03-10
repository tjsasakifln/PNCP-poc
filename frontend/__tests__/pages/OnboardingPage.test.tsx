/**
 * OnboardingPage Component Tests — DEBT-111 AC2
 *
 * Tests 3-step onboarding wizard: CNAE input, UF selection, confirmation,
 * validation, navigation, and form submission.
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// ============================================================================
// Mocks
// ============================================================================

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: jest.fn(),
  }),
}));

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

// sonner toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// safeSetItem
jest.mock('../../lib/storage', () => ({
  safeSetItem: jest.fn(),
  safeGetItem: jest.fn().mockReturnValue(null),
}));

// Mock fetch globally
global.fetch = jest.fn();

// ============================================================================
// Import page after mocks
// ============================================================================

import OnboardingPage from '@/app/onboarding/page';

// ============================================================================
// Helpers
// ============================================================================

function setupFetchMocks({
  profileContext = {},
  firstAnalysis = { search_id: 'search-123' },
  profileSaveOk = true,
  firstAnalysisOk = true,
}: {
  profileContext?: Record<string, unknown>;
  firstAnalysis?: Record<string, unknown>;
  profileSaveOk?: boolean;
  firstAnalysisOk?: boolean;
} = {}) {
  (global.fetch as jest.Mock).mockImplementation((url: string, opts?: RequestInit) => {
    if (url.includes('profile-context') && opts?.method === 'PUT') {
      return Promise.resolve({
        ok: profileSaveOk,
        json: async () => ({}),
      });
    }
    if (url.includes('profile-context')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ context_data: profileContext }),
      });
    }
    if (url.includes('first-analysis')) {
      return Promise.resolve({
        ok: firstAnalysisOk,
        json: async () => firstAnalysis,
      });
    }
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
}

// ============================================================================
// Tests
// ============================================================================

beforeEach(() => {
  jest.clearAllMocks();
  mockAuthState = { user: mockUser, session: mockSession, loading: false };
  setupFetchMocks();
});

describe('OnboardingPage', () => {
  describe('Auth guard', () => {
    it('shows loading spinner when auth is loading', () => {
      mockAuthState = { user: null as any, session: null as any, loading: true };

      render(<OnboardingPage />);

      // Loading spinner uses animate-spin
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('redirects to /login when not authenticated', async () => {
      mockAuthState = { user: null as any, session: null as any, loading: false };

      render(<OnboardingPage />);

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/login');
      });
    });

    it('renders the form when user is authenticated', () => {
      render(<OnboardingPage />);

      expect(screen.getByText(/configure seu perfil estratégico/i)).toBeInTheDocument();
    });
  });

  describe('Progress bar', () => {
    it('shows step 1 of 3 initially', () => {
      render(<OnboardingPage />);

      expect(screen.getByText(/1 de 3/i)).toBeInTheDocument();
    });

    it('updates to step 2 when progressing', async () => {
      render(<OnboardingPage />);

      // Fill Step 1 fields
      const cnaeInput = screen.getByPlaceholderText(/ex: comércio de uniformes/i);
      fireEvent.change(cnaeInput, { target: { value: 'Uniformes escolares' } });

      const objetivoTextarea = screen.getByPlaceholderText(/ex: encontrar oportunidades/i);
      fireEvent.change(objetivoTextarea, { target: { value: 'Encontrar oportunidades de uniformes' } });

      const continueBtn = screen.getByTestId('btn-continuar');
      await act(async () => {
        fireEvent.click(continueBtn);
      });

      await waitFor(() => {
        expect(screen.getByText(/2 de 3/i)).toBeInTheDocument();
      });
    });
  });

  describe('Step 1: Business information', () => {
    it('renders CNAE input field', () => {
      render(<OnboardingPage />);

      expect(screen.getByPlaceholderText(/ex: comércio de uniformes/i)).toBeInTheDocument();
    });

    it('renders objective textarea', () => {
      render(<OnboardingPage />);

      expect(screen.getByPlaceholderText(/ex: encontrar oportunidades/i)).toBeInTheDocument();
    });

    it('renders Continuar button', () => {
      render(<OnboardingPage />);

      expect(screen.getByTestId('btn-continuar')).toBeInTheDocument();
      expect(screen.getByTestId('btn-continuar')).toHaveTextContent(/continuar/i);
    });

    it('renders skip button on step 1', () => {
      render(<OnboardingPage />);

      expect(screen.getByTestId('btn-pular')).toBeInTheDocument();
    });

    it('Continuar button is disabled when CNAE is empty', () => {
      render(<OnboardingPage />);

      const continueBtn = screen.getByTestId('btn-continuar');
      expect(continueBtn).toBeDisabled();
    });

    it('Continuar button is disabled when objective is empty but CNAE is filled', () => {
      render(<OnboardingPage />);

      const cnaeInput = screen.getByPlaceholderText(/ex: comércio de uniformes/i);
      fireEvent.change(cnaeInput, { target: { value: 'Uniformes escolares' } });

      const continueBtn = screen.getByTestId('btn-continuar');
      expect(continueBtn).toBeDisabled();
    });

    it('Continuar button is enabled when both CNAE and objective are filled', () => {
      render(<OnboardingPage />);

      const cnaeInput = screen.getByPlaceholderText(/ex: comércio de uniformes/i);
      fireEvent.change(cnaeInput, { target: { value: 'Uniformes escolares' } });

      const objetivoTextarea = screen.getByPlaceholderText(/ex: encontrar oportunidades/i);
      fireEvent.change(objetivoTextarea, { target: { value: 'Buscar uniformes acima de R$ 100k em SP' } });

      const continueBtn = screen.getByTestId('btn-continuar');
      expect(continueBtn).not.toBeDisabled();
    });

    it('skip button navigates to /buscar', () => {
      render(<OnboardingPage />);

      const skipBtn = screen.getByTestId('btn-pular');
      fireEvent.click(skipBtn);

      expect(mockPush).toHaveBeenCalledWith('/buscar');
    });

    it('shows CNAE autocomplete suggestions on focus', async () => {
      render(<OnboardingPage />);

      const cnaeInput = screen.getByPlaceholderText(/ex: comércio de uniformes/i);
      fireEvent.focus(cnaeInput);

      await waitFor(() => {
        expect(screen.getByText(/comércio varejista de artigos de vestuário/i)).toBeInTheDocument();
      });
    });

    it('fills CNAE when a suggestion is clicked', async () => {
      render(<OnboardingPage />);

      const cnaeInput = screen.getByPlaceholderText(/ex: comércio de uniformes/i);
      fireEvent.focus(cnaeInput);

      await waitFor(() => {
        expect(screen.getByText(/limpeza em prédios/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/limpeza em prédios/i));

      await waitFor(() => {
        expect((cnaeInput as HTMLInputElement).value).toContain('8121-4/00');
      });
    });
  });

  describe('Step 2: UF selection', () => {
    async function goToStep2() {
      render(<OnboardingPage />);

      const cnaeInput = screen.getByPlaceholderText(/ex: comércio de uniformes/i);
      fireEvent.change(cnaeInput, { target: { value: 'Uniformes escolares' } });

      const objetivoTextarea = screen.getByPlaceholderText(/ex: encontrar oportunidades/i);
      fireEvent.change(objetivoTextarea, {
        target: { value: 'Buscar uniformes acima de R$ 100k em São Paulo' },
      });

      const continueBtn = screen.getByTestId('btn-continuar');
      await act(async () => {
        fireEvent.click(continueBtn);
      });

      await waitFor(() => {
        expect(screen.getByText(/onde você atua/i)).toBeInTheDocument();
      });
    }

    it('renders UF selection step heading', async () => {
      await goToStep2();

      expect(screen.getByText(/onde você atua e qual valor ideal/i)).toBeInTheDocument();
    });

    it('renders UF buttons grouped by region', async () => {
      await goToStep2();

      // Check region buttons
      expect(screen.getByTestId('region-button-Norte')).toBeInTheDocument();
      expect(screen.getByTestId('region-button-Sudeste')).toBeInTheDocument();
      expect(screen.getByTestId('region-button-Sul')).toBeInTheDocument();

      // Check specific UF buttons
      expect(screen.getByTestId('uf-button-SP')).toBeInTheDocument();
      expect(screen.getByTestId('uf-button-RJ')).toBeInTheDocument();
      expect(screen.getByTestId('uf-button-RS')).toBeInTheDocument();
    });

    it('shows selected UF count', async () => {
      await goToStep2();

      expect(screen.getByText(/0 selecionados/i)).toBeInTheDocument();
    });

    it('Continuar button is disabled when no UF is selected', async () => {
      await goToStep2();

      expect(screen.getByTestId('btn-continuar')).toBeDisabled();
    });

    it('Continuar becomes enabled after selecting a UF', async () => {
      await goToStep2();

      fireEvent.click(screen.getByTestId('uf-button-SP'));

      await waitFor(() => {
        expect(screen.getByTestId('btn-continuar')).not.toBeDisabled();
      });
    });

    it('toggles UF selection on click', async () => {
      await goToStep2();

      const spButton = screen.getByTestId('uf-button-SP');
      fireEvent.click(spButton);

      await waitFor(() => {
        expect(screen.getByText(/1 selecionados/i)).toBeInTheDocument();
      });

      fireEvent.click(spButton);

      await waitFor(() => {
        expect(screen.getByText(/0 selecionados/i)).toBeInTheDocument();
      });
    });

    it('"Todos" button selects all UFs', async () => {
      await goToStep2();

      const todosBtn = screen.getByRole('button', { name: /^todos$/i });
      fireEvent.click(todosBtn);

      await waitFor(() => {
        expect(screen.getByText(/27 selecionados/i)).toBeInTheDocument();
      });
    });

    it('"Limpar" button deselects all UFs', async () => {
      await goToStep2();

      fireEvent.click(screen.getByRole('button', { name: /^todos$/i }));
      await waitFor(() => {
        expect(screen.getByText(/27 selecionados/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /limpar/i }));
      await waitFor(() => {
        expect(screen.getByText(/0 selecionados/i)).toBeInTheDocument();
      });
    });

    it('region button selects all UFs in that region', async () => {
      await goToStep2();

      fireEvent.click(screen.getByTestId('region-button-Sul'));

      await waitFor(() => {
        // Sul has PR, RS, SC = 3 UFs
        expect(screen.getByText(/3 selecionados/i)).toBeInTheDocument();
      });
    });

    it('renders value range selectors', async () => {
      await goToStep2();

      expect(screen.getByText(/faixa de valor ideal/i)).toBeInTheDocument();
      expect(screen.getByText(/valor mínimo/i)).toBeInTheDocument();
      expect(screen.getByText(/valor máximo/i)).toBeInTheDocument();
    });

    it('back button returns to step 1', async () => {
      await goToStep2();

      fireEvent.click(screen.getByTestId('btn-voltar'));

      await waitFor(() => {
        expect(screen.getByText(/1 de 3/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/ex: comércio de uniformes/i)).toBeInTheDocument();
      });
    });
  });

  describe('Step 3: Confirmation', () => {
    async function goToStep3() {
      render(<OnboardingPage />);

      // Step 1
      fireEvent.change(screen.getByPlaceholderText(/ex: comércio de uniformes/i), {
        target: { value: 'Uniformes escolares' },
      });
      fireEvent.change(screen.getByPlaceholderText(/ex: encontrar oportunidades/i), {
        target: { value: 'Buscar uniformes acima de R$ 100k' },
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId('btn-continuar'));
      });
      await waitFor(() => expect(screen.getByText(/onde você atua/i)).toBeInTheDocument());

      // Step 2 — select SP
      fireEvent.click(screen.getByTestId('uf-button-SP'));
      await waitFor(() => expect(screen.getByText(/1 selecionados/i)).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByTestId('btn-continuar'));
      });
      await waitFor(() => expect(screen.getByText(/pronto para começar/i)).toBeInTheDocument());
    }

    it('renders confirmation step heading', async () => {
      await goToStep3();

      expect(screen.getByText(/pronto para começar/i)).toBeInTheDocument();
    });

    it('shows segmento from step 1', async () => {
      await goToStep3();

      expect(screen.getByText(/segmento/i)).toBeInTheDocument();
      expect(screen.getByText('Uniformes escolares')).toBeInTheDocument();
    });

    it('shows selected UF', async () => {
      await goToStep3();

      expect(screen.getByText('SP')).toBeInTheDocument();
    });

    it('shows step 3 of 3', async () => {
      await goToStep3();

      expect(screen.getByText(/3 de 3/i)).toBeInTheDocument();
    });

    it('shows "Ver Minhas Oportunidades" on final step button', async () => {
      await goToStep3();

      expect(screen.getByTestId('btn-continuar')).toHaveTextContent(/ver minhas oportunidades/i);
    });

    it('back button from step 3 returns to step 2', async () => {
      await goToStep3();

      fireEvent.click(screen.getByTestId('btn-voltar'));

      await waitFor(() => {
        expect(screen.getByText(/2 de 3/i)).toBeInTheDocument();
        expect(screen.getByText(/onde você atua/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form submission', () => {
    async function completeAndSubmit() {
      render(<OnboardingPage />);

      // Step 1
      fireEvent.change(screen.getByPlaceholderText(/ex: comércio de uniformes/i), {
        target: { value: 'Uniformes escolares' },
      });
      fireEvent.change(screen.getByPlaceholderText(/ex: encontrar oportunidades/i), {
        target: { value: 'Buscar uniformes acima de R$ 100k' },
      });

      await act(async () => {
        fireEvent.click(screen.getByTestId('btn-continuar'));
      });
      await waitFor(() => expect(screen.getByText(/onde você atua/i)).toBeInTheDocument());

      // Step 2 — select SP
      fireEvent.click(screen.getByTestId('uf-button-SP'));
      await waitFor(() => expect(screen.getByText(/1 selecionados/i)).toBeInTheDocument());

      await act(async () => {
        fireEvent.click(screen.getByTestId('btn-continuar'));
      });
      await waitFor(() => expect(screen.getByText(/pronto para começar/i)).toBeInTheDocument());

      // Step 3 — submit
      await act(async () => {
        fireEvent.click(screen.getByTestId('btn-continuar'));
      });
    }

    it('navigates to /buscar with auto=true and search_id on success', async () => {
      setupFetchMocks({ firstAnalysis: { search_id: 'search-abc' } });

      await completeAndSubmit();

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/buscar?auto=true&search_id=search-abc');
      });
    });

    it('falls back to /buscar with ufs param when first-analysis fails', async () => {
      setupFetchMocks({ firstAnalysisOk: false });

      await completeAndSubmit();

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('/buscar?ufs='));
      });
    });

    it('saves profile context via PUT /api/profile-context', async () => {
      await completeAndSubmit();

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/profile-context',
          expect.objectContaining({ method: 'PUT' })
        );
      });
    });
  });

  describe('Existing context (returning user)', () => {
    it('shows "Atualizar Perfil" heading when context exists', async () => {
      setupFetchMocks({
        profileContext: {
          cnae: '8121-4/00',
          objetivo_principal: 'Limpeza em prédios públicos',
          ufs_atuacao: ['SP', 'RJ'],
          faixa_valor_min: 100000,
          faixa_valor_max: 500000,
        },
      });

      render(<OnboardingPage />);

      await waitFor(() => {
        expect(screen.getByText(/atualizar perfil estratégico/i)).toBeInTheDocument();
      });
    });
  });
});
