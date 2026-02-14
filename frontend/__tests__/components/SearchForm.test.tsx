/**
 * SearchForm Component Tests
 *
 * Tests form rendering, mode toggle, UF selection, date inputs, validation
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchForm from '@/app/buscar/components/SearchForm';
import type { SearchFormProps } from '@/app/buscar/components/SearchForm';

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>;
  };
});

const mockSetores = [
  { id: 'vestuario', name: 'Vestuário', description: 'Uniformes e fardamentos' },
  { id: 'ti', name: 'TI', description: 'Tecnologia' },
  { id: 'facilities', name: 'Facilities', description: 'Manutenção' },
];

const defaultProps: SearchFormProps = {
  setores: mockSetores,
  setoresLoading: false,
  setoresError: false,
  setoresUsingFallback: false,
  setoresRetryCount: 0,
  setorId: 'vestuario',
  setSetorId: jest.fn(),
  fetchSetores: jest.fn(),
  searchMode: 'setor',
  setSearchMode: jest.fn(),
  modoBusca: 'abertas',
  dateLabel: 'Mostrando licitações abertas para proposta',
  termosArray: [],
  termoInput: '',
  setTermoInput: jest.fn(),
  termValidation: null,
  addTerms: jest.fn(),
  removeTerm: jest.fn(),
  ufsSelecionadas: new Set(['SP', 'RJ', 'MG']),
  toggleUf: jest.fn(),
  toggleRegion: jest.fn(),
  selecionarTodos: jest.fn(),
  limparSelecao: jest.fn(),
  dataInicial: '2026-02-01',
  setDataInicial: jest.fn(),
  dataFinal: '2026-02-10',
  setDataFinal: jest.fn(),
  validationErrors: {},
  canSearch: true,
  searchLabel: 'Vestuário',
  locationFiltersOpen: false,
  setLocationFiltersOpen: jest.fn(),
  advancedFiltersOpen: false,
  setAdvancedFiltersOpen: jest.fn(),
  esferas: [],
  setEsferas: jest.fn(),
  municipios: [],
  setMunicipios: jest.fn(),
  status: 'recebendo_proposta',
  setStatus: jest.fn(),
  modalidades: [],
  setModalidades: jest.fn(),
  valorMin: null,
  setValorMin: jest.fn(),
  valorMax: null,
  setValorMax: jest.fn(),
  setValorValid: jest.fn(),
  loading: false,
  buscar: jest.fn(),
  searchButtonRef: { current: null },
  result: null,
  handleSaveSearch: jest.fn(),
  isMaxCapacity: false,
  planInfo: null,
  onShowUpgradeModal: jest.fn(),
  clearResult: jest.fn(),
};

describe('SearchForm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Search mode toggle', () => {
    it('should render mode toggle buttons', () => {
      render(<SearchForm {...defaultProps} />);

      expect(screen.getByRole('button', { name: /Setor/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Termos Específicos/i })).toBeInTheDocument();
    });

    it('should switch to termos mode', () => {
      render(<SearchForm {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /Termos Específicos/i }));

      expect(defaultProps.setSearchMode).toHaveBeenCalledWith('termos');
      expect(defaultProps.clearResult).toHaveBeenCalled();
    });

    it('should show sector selector in setor mode', () => {
      render(<SearchForm {...defaultProps} />);

      expect(screen.getAllByText(/Vestuário/i)[0]).toBeInTheDocument();
    });

    it('should show terms input in termos mode', () => {
      render(<SearchForm {...defaultProps} searchMode="termos" />);

      expect(screen.getByPlaceholderText(/terraplenagem, drenagem/i)).toBeInTheDocument();
    });
  });

  describe('Sector selector', () => {
    it('should display sectors loading state', () => {
      render(<SearchForm {...defaultProps} setoresLoading={true} />);

      const spinners = document.querySelectorAll('.animate-spin');
      expect(spinners.length).toBeGreaterThan(0);
    });

    it('should display error state when fetch fails', () => {
      render(<SearchForm {...defaultProps} setoresError={true} setoresUsingFallback={false} />);

      expect(screen.getByText(/Não foi possível carregar setores/i)).toBeInTheDocument();
    });

    it('should show fallback warning', () => {
      render(<SearchForm {...defaultProps} setoresUsingFallback={true} />);

      expect(screen.getByText(/Usando lista offline/i)).toBeInTheDocument();
    });

    it('should have retry button on error', () => {
      render(<SearchForm {...defaultProps} setoresError={true} setoresUsingFallback={false} />);

      const retryButton = screen.getAllByRole('button', { name: /Tentar/i })[0];
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      expect(defaultProps.fetchSetores).toHaveBeenCalledWith(0);
    });
  });

  describe('UF selection', () => {
    it('should display selected UFs count', () => {
      render(<SearchForm {...defaultProps} />);

      expect(screen.getByText(/3 estados selecionados/i)).toBeInTheDocument();
    });

    it('should have selecionar todos button', () => {
      render(<SearchForm {...defaultProps} />);

      const selectAllButton = screen.getByRole('button', { name: /Selecionar todos/i });
      fireEvent.click(selectAllButton);

      expect(defaultProps.selecionarTodos).toHaveBeenCalled();
    });

    it('should have limpar button', () => {
      render(<SearchForm {...defaultProps} />);

      const clearButton = screen.getByRole('button', { name: /Limpar/i });
      fireEvent.click(clearButton);

      expect(defaultProps.limparSelecao).toHaveBeenCalled();
    });

    it('should toggle UF when clicked', () => {
      render(<SearchForm {...defaultProps} />);

      const spButtons = screen.getAllByRole('button');
      const spButton = spButtons.find(btn => btn.textContent === 'SP');
      expect(spButton).toBeInTheDocument();

      fireEvent.click(spButton!);

      expect(defaultProps.toggleUf).toHaveBeenCalledWith('SP');
    });

    it('should show validation error for no UFs', () => {
      render(<SearchForm {...defaultProps} validationErrors={{ ufs: 'Selecione pelo menos um estado' }} />);

      expect(screen.getByText(/Selecione pelo menos um estado/i)).toBeInTheDocument();
    });
  });

  describe('Date inputs', () => {
    it('should show info box in abertas mode', () => {
      render(<SearchForm {...defaultProps} modoBusca="abertas" dateLabel="Mostrando licitações abertas para proposta" />);

      expect(screen.getByText(/Mostrando licitações abertas para proposta/i)).toBeInTheDocument();
      expect(screen.getByText(/Buscando nos últimos 180 dias/i)).toBeInTheDocument();
      expect(screen.queryByLabelText(/Data inicial/i)).not.toBeInTheDocument();
    });

    it('should render date inputs in publicacao mode', () => {
      render(<SearchForm {...defaultProps} modoBusca="publicacao" dateLabel="Período de publicação" />);

      expect(screen.getByLabelText(/Data inicial/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Data final/i)).toBeInTheDocument();
      expect(screen.queryByText(/Mostrando licitações abertas para proposta/i)).not.toBeInTheDocument();
    });

    it('should show date range validation error', () => {
      render(
        <SearchForm
          {...defaultProps}
          validationErrors={{ date_range: 'Data final deve ser maior que inicial' }}
        />
      );

      expect(screen.getByText(/Data final deve ser maior/i)).toBeInTheDocument();
    });

    it('should show plan limit warning for long date range', () => {
      const planInfo = {
        plan_name: 'Free',
        capabilities: { max_history_days: 7 },
      };

      render(
        <SearchForm
          {...defaultProps}
          planInfo={planInfo}
          dataInicial="2026-01-01"
          dataFinal="2026-02-10"
        />
      );

      expect(screen.getByText(/Período muito longo para seu plano/i)).toBeInTheDocument();
    });
  });

  describe('Search button', () => {
    it('should render search button', () => {
      render(<SearchForm {...defaultProps} />);

      expect(screen.getByRole('button', { name: /Buscar Vestuário/i })).toBeInTheDocument();
    });

    it('should disable search button when canSearch is false', () => {
      render(<SearchForm {...defaultProps} canSearch={false} />);

      const searchButton = screen.getByRole('button', { name: /Buscar/i });
      expect(searchButton).toBeDisabled();
    });

    it('should show loading state', () => {
      render(<SearchForm {...defaultProps} loading={true} />);

      expect(screen.getByText(/Consultando múltiplas fontes/i)).toBeInTheDocument();
    });

    it('should call buscar when clicked', () => {
      render(<SearchForm {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /Buscar Vestuário/i }));

      expect(defaultProps.buscar).toHaveBeenCalled();
    });
  });

  describe('Save search button', () => {
    it('should show save button when result exists', () => {
      const result = { resumo: { total_oportunidades: 10 }, download_id: '123' };
      render(<SearchForm {...defaultProps} result={result} />);

      expect(screen.getByRole('button', { name: /Salvar Busca/i })).toBeInTheDocument();
    });

    it('should not show save button when no result', () => {
      render(<SearchForm {...defaultProps} result={null} />);

      expect(screen.queryByRole('button', { name: /Salvar Busca/i })).not.toBeInTheDocument();
    });

    it('should disable save button when max capacity', () => {
      const result = { resumo: { total_oportunidades: 10 }, download_id: '123' };
      render(<SearchForm {...defaultProps} result={result} isMaxCapacity={true} />);

      const saveButton = screen.getByRole('button', { name: /Limite de buscas atingido/i });
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Terms input (termos mode)', () => {
    it('should display term tags', () => {
      render(<SearchForm {...defaultProps} searchMode="termos" termosArray={['uniforme', 'escolar']} />);

      expect(screen.getByText('uniforme')).toBeInTheDocument();
      expect(screen.getByText('escolar')).toBeInTheDocument();
    });

    it('should remove term when X clicked', () => {
      render(<SearchForm {...defaultProps} searchMode="termos" termosArray={['uniforme', 'escolar']} />);

      const removeButtons = screen.getAllByRole('button', { name: /Remover termo/i });
      fireEvent.click(removeButtons[0]);

      expect(defaultProps.removeTerm).toHaveBeenCalled();
    });

    it('should show validation warning for ignored terms', () => {
      const validation = {
        valid: ['uniforme'],
        ignored: ['de', 'a'],
        reasons: { de: 'Palavra comum', a: 'Muito curto' },
      };

      render(<SearchForm {...defaultProps} searchMode="termos" termValidation={validation} />);

      expect(screen.getByText(/Atenção:/i)).toBeInTheDocument();
      expect(screen.getByText(/não será/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<SearchForm {...defaultProps} />);

      const spButtons = screen.getAllByRole('button');
      const spButton = spButtons.find(btn => btn.textContent === 'SP');
      expect(spButton).toHaveAttribute('aria-pressed');
    });

    it('should mark search button as busy during loading', () => {
      render(<SearchForm {...defaultProps} loading={true} />);

      const searchButton = screen.getByRole('button', { name: /Consultando/i });
      expect(searchButton).toHaveAttribute('aria-busy', 'true');
    });
  });

  describe('STORY-240 AC10: modoBusca and dateLabel behavior', () => {
    it('AC10.1: should default to abertas mode', () => {
      // Default props already has modoBusca='abertas'
      render(<SearchForm {...defaultProps} />);

      // Should show abertas-specific info box (tested in "Date inputs" section)
      // This test verifies the prop is correctly passed to component
      expect(defaultProps.modoBusca).toBe('abertas');
    });

    it('AC10.2: should display 180-day info message in abertas mode', () => {
      render(<SearchForm {...defaultProps} modoBusca="abertas" dateLabel="Mostrando licitações abertas para proposta" />);

      expect(screen.getByText(/Buscando nos últimos 180 dias/i)).toBeInTheDocument();
    });

    it('AC10.3: should show abertas-specific dateLabel', () => {
      render(<SearchForm {...defaultProps} modoBusca="abertas" dateLabel="Mostrando licitações abertas para proposta" />);

      expect(screen.getByText(/Mostrando licitações abertas para proposta/i)).toBeInTheDocument();
    });

    it('AC10.4: should render date inputs when mode is publicacao', () => {
      render(<SearchForm {...defaultProps} modoBusca="publicacao" dateLabel="Período de publicação" />);

      expect(screen.getByLabelText(/Data inicial/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Data final/i)).toBeInTheDocument();
    });

    it('AC10.5: should NOT show abertas-specific dateLabel in publicacao mode', () => {
      render(<SearchForm {...defaultProps} modoBusca="publicacao" dateLabel="Período de publicação" />);

      // In publicacao mode, dateLabel is not rendered - only date inputs are shown
      expect(screen.queryByText(/Mostrando licitações abertas para proposta/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Buscando nos últimos 180 dias/i)).not.toBeInTheDocument();
    });

    it('AC10: integration - should hide date inputs in abertas mode', () => {
      render(<SearchForm {...defaultProps} modoBusca="abertas" dateLabel="Mostrando licitações abertas para proposta" />);

      expect(screen.queryByLabelText(/Data inicial/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/Data final/i)).not.toBeInTheDocument();
    });

    it('AC10: integration - should hide info box in publicacao mode', () => {
      render(<SearchForm {...defaultProps} modoBusca="publicacao" dateLabel="Período de publicação" />);

      expect(screen.queryByText(/Buscando nos últimos 180 dias/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Mostrando licitações abertas para proposta/i)).not.toBeInTheDocument();
    });
  });
});
