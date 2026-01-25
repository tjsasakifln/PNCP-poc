import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HomePage from '@/app/page';

// Mock fetch globally
global.fetch = jest.fn();

describe('HomePage - UF Selection and Date Range', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('UF Selection', () => {
    it('should render all 27 UF buttons', () => {
      render(<HomePage />);

      const expectedUFs = [
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
      ];

      expectedUFs.forEach(uf => {
        expect(screen.getByText(uf)).toBeInTheDocument();
      });
    });

    it('should have default UFs selected (SC, PR, RS)', () => {
      render(<HomePage />);

      const scButton = screen.getByText('SC');
      const prButton = screen.getByText('PR');
      const rsButton = screen.getByText('RS');

      expect(scButton).toHaveClass('bg-green-600');
      expect(prButton).toHaveClass('bg-green-600');
      expect(rsButton).toHaveClass('bg-green-600');
    });

    it('should toggle UF selection on click', () => {
      render(<HomePage />);

      const spButton = screen.getByText('SP');
      expect(spButton).not.toHaveClass('bg-green-600');

      fireEvent.click(spButton);
      expect(spButton).toHaveClass('bg-green-600');

      fireEvent.click(spButton);
      expect(spButton).not.toHaveClass('bg-green-600');
    });

    it('should select all UFs when "Selecionar todos" is clicked', () => {
      render(<HomePage />);

      const selectAllButton = screen.getByText('Selecionar todos');
      fireEvent.click(selectAllButton);

      expect(screen.getByText('27 estado(s) selecionado(s)')).toBeInTheDocument();
    });

    it('should clear all UFs when "Limpar" is clicked', () => {
      render(<HomePage />);

      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      expect(screen.getByText('0 estado(s) selecionado(s)')).toBeInTheDocument();
    });

    it('should display count of selected UFs', () => {
      render(<HomePage />);

      // Default: SC, PR, RS = 3
      expect(screen.getByText('3 estado(s) selecionado(s)')).toBeInTheDocument();

      const spButton = screen.getByText('SP');
      fireEvent.click(spButton);

      expect(screen.getByText('4 estado(s) selecionado(s)')).toBeInTheDocument();
    });
  });

  describe('Date Range', () => {
    it('should have default dates (last 7 days)', () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      // Check data_final is today
      const today = new Date().toISOString().split('T')[0];
      expect(dataFinalInput.value).toBe(today);

      // Check data_inicial is 7 days ago
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const expected = sevenDaysAgo.toISOString().split('T')[0];
      expect(dataInicialInput.value).toBe(expected);
    });

    it('should update dates on change', () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-01-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-15' } });

      expect(dataInicialInput.value).toBe('2024-01-01');
      expect(dataFinalInput.value).toBe('2024-01-15');
    });
  });

  describe('Validation - Min 1 UF', () => {
    it('should show error when no UF is selected', async () => {
      render(<HomePage />);

      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(screen.getByText('Selecione pelo menos um estado')).toBeInTheDocument();
      });
    });

    it('should disable submit button when no UF is selected', () => {
      render(<HomePage />);

      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Validation - Date Range Logic', () => {
    it('should show error when data_final < data_inicial', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-02-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-15' } });

      await waitFor(() => {
        expect(screen.getByText('Data final deve ser maior ou igual à data inicial')).toBeInTheDocument();
      });
    });

    it('should show error when date range > 30 days', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-01-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-02-15' } }); // 45 days

      await waitFor(() => {
        expect(screen.getByText(/Período máximo de 30 dias/)).toBeInTheDocument();
      });
    });

    it('should NOT show error when date range is exactly 30 days', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-01-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-31' } }); // 30 days

      await waitFor(() => {
        const errorMessage = screen.queryByText(/Período máximo de 30 dias/);
        expect(errorMessage).not.toBeInTheDocument();
      });
    });

    it('should disable submit button when date validation fails', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-02-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-15' } });

      const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('Inline Error Messages', () => {
    it('should display inline error for UF validation', async () => {
      render(<HomePage />);

      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      await waitFor(() => {
        const errorMessage = screen.getByText('Selecione pelo menos um estado');
        expect(errorMessage).toHaveClass('text-red-600');
      });
    });

    it('should display inline error for date range validation', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-02-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-15' } });

      await waitFor(() => {
        const errorMessage = screen.getByText('Data final deve ser maior ou igual à data inicial');
        expect(errorMessage).toHaveClass('text-red-600');
      });
    });
  });

  describe('Submit Button State', () => {
    it('should be enabled when form is valid', () => {
      render(<HomePage />);

      const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
      expect(submitButton).not.toBeDisabled();
    });

    it('should show loading state during API call', async () => {
      (global.fetch as jest.Mock).mockImplementationOnce(() =>
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({
            resumo: {
              resumo_executivo: 'Test summary',
              total_oportunidades: 10,
              valor_total: 100000,
              destaques: [],
              distribuicao_uf: {},
              alerta_urgencia: null
            },
            download_id: 'test-id'
          })
        }), 100))
      );

      render(<HomePage />);

      const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Buscando...')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Layout', () => {
    it('should use responsive flexbox for date inputs', () => {
      render(<HomePage />);

      const dataInicialContainer = screen.getByLabelText('Data inicial:').closest('div');
      const dataFinalContainer = screen.getByLabelText('Data final:').closest('div');

      expect(dataInicialContainer).toHaveClass('flex-1');
      expect(dataFinalContainer).toHaveClass('flex-1');
    });
  });

  describe('TypeScript Type Safety', () => {
    it('should handle API response with correct types', async () => {
      const mockResponse = {
        resumo: {
          resumo_executivo: 'Encontradas 5 licitações',
          total_oportunidades: 5,
          valor_total: 250000,
          destaques: ['Uniforme escolar em SC'],
          distribuicao_uf: { SC: 3, PR: 2 },
          alerta_urgencia: null
        },
        download_id: 'abc123'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<HomePage />);

      const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Encontradas 5 licitações')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });
  });
});
