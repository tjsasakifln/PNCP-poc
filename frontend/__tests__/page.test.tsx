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

  describe('Results Display Section (Issue #23)', () => {
    const mockSuccessResponse = {
      resumo: {
        resumo_executivo: 'Encontradas 15 licitações de uniformes totalizando R$ 450.000,00',
        total_oportunidades: 15,
        valor_total: 450000,
        destaques: [
          'Uniformes escolares - Secretaria de Educação SC - R$ 120.000',
          'Fardamento militar - PM-PR - R$ 85.000',
          'Jalecos - Hospital Municipal RS - R$ 45.000'
        ],
        distribuicao_uf: { SC: 6, PR: 5, RS: 4 },
        alerta_urgencia: 'Licitação com prazo em menos de 7 dias: Prefeitura de Florianópolis'
      },
      download_id: 'uuid-123-456'
    };

    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSuccessResponse
      });
    });

    describe('AC1: Conditional Rendering', () => {
      it('should NOT render results section when result is null', () => {
        render(<HomePage />);

        // Check that results-specific elements are NOT present
        expect(screen.queryByText('Destaques:')).not.toBeInTheDocument();
        expect(screen.queryByText(/Download Excel/i)).not.toBeInTheDocument();
        expect(screen.queryByText('valor total')).not.toBeInTheDocument();
      });

      it('should render results section when result is set', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });
      });
    });

    describe('AC2: Executive Summary Display', () => {
      it('should display resumo_executivo text', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Encontradas 15 licitações de uniformes totalizando R$ 450.000,00')).toBeInTheDocument();
        });
      });

      it('should display summary in green bordered card', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const summaryText = screen.getByText(/Encontradas 15 licitações/i);
          const summaryCard = summaryText.closest('div');
          expect(summaryCard).toHaveClass('bg-green-50', 'border-green-200');
        });
      });
    });

    describe('AC3: Statistics Display', () => {
      it('should display total_oportunidades as integer', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const totalElement = screen.getByText('15');
          expect(totalElement).toHaveClass('text-3xl', 'font-bold', 'text-green-700');
          expect(screen.getByText('licitações')).toBeInTheDocument();
        });
      });

      it('should display valor_total with Brazilian currency formatting', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          // toLocaleString("pt-BR") for 450000 = "450.000"
          // Find the value element by its label
          const valorTotalLabel = screen.getByText('valor total');
          const valueElement = valorTotalLabel.previousElementSibling;

          expect(valueElement).toHaveTextContent(/R\$ 450\.000/i);
          expect(valueElement).toHaveClass('text-3xl', 'font-bold', 'text-green-700');
        });
      });

      it('should format large values correctly', async () => {
        const largeValueResponse = {
          ...mockSuccessResponse,
          resumo: {
            ...mockSuccessResponse.resumo,
            valor_total: 1234567.89
          }
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => largeValueResponse
        });

        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          // toLocaleString("pt-BR") for 1234567.89 = "1.234.567,89"
          expect(screen.getByText(/R\$ 1\.234\.567/i)).toBeInTheDocument();
        });
      });
    });

    describe('AC4: Urgency Alert Conditional', () => {
      it('should display urgency alert when alerta_urgencia is NOT null', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const alertText = screen.getByText(/Licitação com prazo em menos de 7 dias/i);
          expect(alertText).toBeInTheDocument();

          const alertBox = alertText.closest('div');
          expect(alertBox).toHaveClass('bg-yellow-100', 'border-yellow-300', 'text-yellow-800');
          expect(screen.getByText(/⚠️/)).toBeInTheDocument();
        });
      });

      it('should NOT display urgency alert when alerta_urgencia is null', async () => {
        const noAlertResponse = {
          ...mockSuccessResponse,
          resumo: {
            ...mockSuccessResponse.resumo,
            alerta_urgencia: null
          }
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => noAlertResponse
        });

        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });

        expect(screen.queryByText(/Licitação com prazo/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/⚠️/)).not.toBeInTheDocument();
      });
    });

    describe('AC5: Highlights List Conditional', () => {
      it('should display highlights when destaques array has items', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Destaques:')).toBeInTheDocument();
          expect(screen.getByText(/Uniformes escolares - Secretaria de Educação SC/i)).toBeInTheDocument();
          expect(screen.getByText(/Fardamento militar - PM-PR/i)).toBeInTheDocument();
          expect(screen.getByText(/Jalecos - Hospital Municipal RS/i)).toBeInTheDocument();
        });
      });

      it('should NOT display highlights section when destaques array is empty', async () => {
        const noHighlightsResponse = {
          ...mockSuccessResponse,
          resumo: {
            ...mockSuccessResponse.resumo,
            destaques: []
          }
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => noHighlightsResponse
        });

        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });

        expect(screen.queryByText('Destaques:')).not.toBeInTheDocument();
      });

      it('should render highlights as bulleted list', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const highlightsList = screen.getByText('Destaques:').nextElementSibling;
          expect(highlightsList?.tagName).toBe('UL');
          expect(highlightsList).toHaveClass('list-disc', 'list-inside');
        });
      });
    });

    describe('AC6: Download Button', () => {
      it('should link to /api/download with correct query param', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadLink = screen.getByText(/Download Excel/i).closest('a');
          expect(downloadLink).toHaveAttribute('href', '/api/download?id=uuid-123-456');
        });
      });

      it('should have download attribute', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadLink = screen.getByText(/Download Excel/i).closest('a');
          expect(downloadLink).toHaveAttribute('download');
        });
      });

      it('should display count in download button text', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('📥 Download Excel (15 licitações)')).toBeInTheDocument();
        });
      });

      it('should use blue styling for download button', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByText(/Download Excel/i);
          expect(downloadButton).toHaveClass('bg-blue-600', 'hover:bg-blue-700');
        });
      });
    });

    describe('AC7: Styling Compliance', () => {
      it('should use green theme for summary card', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const summaryText = screen.getByText(/Encontradas 15 licitações/i);
          const summaryCard = summaryText.closest('div');
          expect(summaryCard).toHaveClass('p-4', 'bg-green-50', 'border', 'border-green-200', 'rounded');
        });
      });

      it('should use yellow theme for urgency alert', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const alertBox = screen.getByText(/Licitação com prazo/i).closest('div');
          expect(alertBox).toHaveClass('bg-yellow-100', 'border-yellow-300', 'text-yellow-800');
        });
      });

      it('should use blue theme for download button', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByText(/Download Excel/i);
          expect(downloadButton).toHaveClass('bg-blue-600', 'text-white', 'hover:bg-blue-700');
        });
      });
    });

    describe('AC8: Responsive Layout', () => {
      it('should use responsive spacing classes', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const resultsContainer = screen.getByText(/Encontradas 15 licitações/i).closest('div')?.parentElement;
          expect(resultsContainer).toHaveClass('mt-6', 'space-y-4');
        });
      });

      it('should use flexbox for statistics layout', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          const statsContainer = screen.getByText('15').closest('div')?.parentElement;
          expect(statsContainer).toHaveClass('flex', 'gap-6');
        });
      });
    });

    describe('Edge Cases', () => {
      it('should handle zero opportunities', async () => {
        const zeroResponse = {
          resumo: {
            resumo_executivo: 'Nenhuma licitação encontrada',
            total_oportunidades: 0,
            valor_total: 0,
            destaques: [],
            distribuicao_uf: {},
            alerta_urgencia: null
          },
          download_id: 'empty-id'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => zeroResponse
        });

        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Nenhuma licitação encontrada')).toBeInTheDocument();
          expect(screen.getByText('0')).toBeInTheDocument();
          expect(screen.getByText('R$ 0')).toBeInTheDocument();
        });
      });

      it('should handle API error gracefully', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          json: async () => ({ message: 'Backend unavailable' })
        });

        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Backend unavailable')).toBeInTheDocument();
        });

        expect(screen.queryByText(/Download Excel/i)).not.toBeInTheDocument();
      });

      it('should clear previous results on new search', async () => {
        render(<HomePage />);

        const submitButton = screen.getByText('🔍 Buscar Licitações de Uniformes');

        // First search
        fireEvent.click(submitButton);
        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });

        // Second search
        const newResponse = {
          resumo: {
            resumo_executivo: 'Encontradas 3 licitações',
            total_oportunidades: 3,
            valor_total: 50000,
            destaques: [],
            distribuicao_uf: { SP: 3 },
            alerta_urgencia: null
          },
          download_id: 'new-id'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => newResponse
        });

        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Encontradas 3 licitações')).toBeInTheDocument();
          expect(screen.queryByText(/Encontradas 15 licitações/i)).not.toBeInTheDocument();
        });
      });
    });
  });
});
