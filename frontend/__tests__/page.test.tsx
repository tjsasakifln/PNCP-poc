import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HomePage from '@/app/page';

// Mock fetch globally
global.fetch = jest.fn();

// Mock child components that aren't relevant to page-level tests
jest.mock('@/components/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle" />,
}));

jest.mock('@/components/RegionSelector', () => ({
  RegionSelector: () => <div data-testid="region-selector" />,
}));

jest.mock('@/components/LoadingProgress', () => ({
  LoadingProgress: () => <div data-testid="loading-progress">Carregando...</div>,
}));

jest.mock('@/components/EmptyState', () => ({
  EmptyState: ({ sectorName }: { sectorName?: string }) => (
    <div data-testid="empty-state">Nenhuma licitação de {sectorName?.toLowerCase() || 'licitações'} encontrada</div>
  ),
}));

describe('HomePage - UF Selection and Date Range', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Default: /api/setores fetch fails so fallback sectors are used
    (global.fetch as jest.Mock).mockRejectedValue(new Error('not found'));
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

      expect(scButton).toHaveClass('bg-brand-navy');
      expect(prButton).toHaveClass('bg-brand-navy');
      expect(rsButton).toHaveClass('bg-brand-navy');
    });

    it('should toggle UF selection on click', () => {
      render(<HomePage />);

      const spButton = screen.getByText('SP');
      expect(spButton).not.toHaveClass('bg-brand-navy');

      fireEvent.click(spButton);
      expect(spButton).toHaveClass('bg-brand-navy');

      fireEvent.click(spButton);
      expect(spButton).not.toHaveClass('bg-brand-navy');
    });

    it('should select all UFs when "Selecionar todos" is clicked', () => {
      render(<HomePage />);

      const selectAllButton = screen.getByText('Selecionar todos');
      fireEvent.click(selectAllButton);

      expect(screen.getByText('27 estados selecionados')).toBeInTheDocument();
    });

    it('should clear all UFs when "Limpar" is clicked', () => {
      render(<HomePage />);

      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      expect(screen.getByText('0 estados selecionados')).toBeInTheDocument();
    });

    it('should display count of selected UFs', () => {
      render(<HomePage />);

      // Default: SC, PR, RS = 3
      expect(screen.getByText('3 estados selecionados')).toBeInTheDocument();

      const spButton = screen.getByText('SP');
      fireEvent.click(spButton);

      expect(screen.getByText('4 estados selecionados')).toBeInTheDocument();
    });

    it('should display singular form for 1 state selected', () => {
      render(<HomePage />);

      // Clear all first
      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      // Select just one
      const scButton = screen.getByText('SC');
      fireEvent.click(scButton);

      expect(screen.getByText('1 estado selecionado')).toBeInTheDocument();
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

      // Fallback sector name: button says "Buscar Licitações" since sectors load async
      const submitButton = screen.getByRole('button', { name: /Buscar/ });
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

    it('should disable submit button when date validation fails', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-02-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-15' } });

      const submitButton = screen.getByRole('button', { name: /Buscar/ });

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('Inline Error Messages', () => {
    it('should display inline error for UF validation with error styling', async () => {
      render(<HomePage />);

      const clearButton = screen.getByText('Limpar');
      fireEvent.click(clearButton);

      await waitFor(() => {
        const errorMessage = screen.getByText('Selecione pelo menos um estado');
        expect(errorMessage).toHaveClass('text-error');
      });
    });

    it('should display inline error for date range validation with error styling', async () => {
      render(<HomePage />);

      const dataInicialInput = screen.getByLabelText('Data inicial:') as HTMLInputElement;
      const dataFinalInput = screen.getByLabelText('Data final:') as HTMLInputElement;

      fireEvent.change(dataInicialInput, { target: { value: '2024-02-01' } });
      fireEvent.change(dataFinalInput, { target: { value: '2024-01-15' } });

      await waitFor(() => {
        const errorMessage = screen.getByText('Data final deve ser maior ou igual à data inicial');
        expect(errorMessage).toHaveClass('text-error');
      });
    });
  });

  describe('Submit Button State', () => {
    it('should be enabled when form is valid', () => {
      render(<HomePage />);

      const submitButton = screen.getByRole('button', { name: /Buscar/ });
      expect(submitButton).not.toBeDisabled();
    });

    it('should show loading state during API call', async () => {
      // First call: /api/setores (rejected by beforeEach)
      // Second call: /api/buscar (delayed success)
      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('not found')) // setores
        .mockImplementationOnce(() =>
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
              download_id: 'test-id',
              total_raw: 100,
              total_filtrado: 10,
              filter_stats: null,
            })
          }), 100))
        );

      render(<HomePage />);

      const submitButton = screen.getByRole('button', { name: /Buscar/ });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Buscando...')).toBeInTheDocument();
      });
    });
  });

  describe('Header', () => {
    it('should render the DescompLicita logo', () => {
      render(<HomePage />);

      const logo = screen.getByAltText('DescompLicita');
      expect(logo).toBeInTheDocument();
    });

    it('should display "Busca Inteligente PNCP" text', () => {
      render(<HomePage />);

      expect(screen.getByText('Busca Inteligente PNCP')).toBeInTheDocument();
    });

    it('should have page title "Busca de Licitações"', () => {
      render(<HomePage />);

      expect(screen.getByRole('heading', { name: 'Busca de Licitações' })).toBeInTheDocument();
    });
  });

  describe('Responsive Layout', () => {
    it('should use grid layout for date inputs', () => {
      render(<HomePage />);

      // Find the section containing the date inputs
      const dataInicialLabel = screen.getByText('Data inicial:');
      const section = dataInicialLabel.closest('section');
      const gridContainer = section?.querySelector('.grid');
      expect(gridContainer).toBeInTheDocument();
      expect(gridContainer).toHaveClass('grid-cols-1');
      expect(gridContainer).toHaveClass('sm:grid-cols-2');
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
        download_id: 'abc123',
        total_raw: 50,
        total_filtrado: 5,
        filter_stats: null,
      };

      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('not found')) // setores
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse
        });

      render(<HomePage />);

      const submitButton = screen.getByRole('button', { name: /Buscar/ });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Encontradas 5 licitações')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });
  });

  describe('Results Display Section', () => {
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
      download_id: 'uuid-123-456',
      total_raw: 200,
      total_filtrado: 15,
      filter_stats: null,
    };

    beforeEach(() => {
      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('not found')) // setores
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockSuccessResponse
        });
    });

    describe('AC1: Conditional Rendering', () => {
      it('should NOT render results section when result is null', () => {
        // Override: only setores fetch, no buscar
        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock).mockRejectedValue(new Error('not found'));

        render(<HomePage />);

        expect(screen.queryByText('Destaques:')).not.toBeInTheDocument();
        expect(screen.queryByText(/Baixar Excel/i)).not.toBeInTheDocument();
        expect(screen.queryByText('valor total')).not.toBeInTheDocument();
      });

      it('should render results section when result is set', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });
      });
    });

    describe('AC2: Executive Summary Display', () => {
      it('should display resumo_executivo text', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Encontradas 15 licitações de uniformes totalizando R$ 450.000,00')).toBeInTheDocument();
        });
      });

      it('should display summary in brand-themed card', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const summaryText = screen.getByText(/Encontradas 15 licitações/i);
          const summaryCard = summaryText.closest('div');
          expect(summaryCard).toHaveClass('bg-brand-blue-subtle', 'border-accent');
        });
      });
    });

    describe('AC3: Statistics Display', () => {
      it('should display total_oportunidades as integer', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const totalElement = screen.getByText('15');
          expect(totalElement).toHaveClass('text-brand-navy');
          expect(screen.getByText('licitações')).toBeInTheDocument();
        });
      });

      it('should display valor_total with Brazilian currency formatting', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const valorTotalLabel = screen.getByText('valor total');
          const valueElement = valorTotalLabel.previousElementSibling;

          expect(valueElement).toHaveTextContent(/R\$ 450\.000/i);
          expect(valueElement).toHaveClass('text-brand-navy');
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

        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock)
          .mockRejectedValueOnce(new Error('not found'))
          .mockResolvedValueOnce({
            ok: true,
            json: async () => largeValueResponse
          });

        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/R\$ 1\.234\.567/i)).toBeInTheDocument();
        });
      });
    });

    describe('AC4: Urgency Alert Conditional', () => {
      it('should display urgency alert when alerta_urgencia is NOT null', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const alertText = screen.getByText(/Licitação com prazo em menos de 7 dias/i);
          expect(alertText).toBeInTheDocument();

          const alertBox = alertText.closest('div');
          expect(alertBox).toHaveClass('bg-warning-subtle');
          // "Atenção: " is aria-hidden, verify via role="alert"
          expect(alertBox).toHaveAttribute('role', 'alert');
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

        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock)
          .mockRejectedValueOnce(new Error('not found'))
          .mockResolvedValueOnce({
            ok: true,
            json: async () => noAlertResponse
          });

        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });

        expect(screen.queryByText(/Licitação com prazo/i)).not.toBeInTheDocument();
        expect(screen.queryByText('Atenção: ')).not.toBeInTheDocument();
      });
    });

    describe('AC5: Highlights List Conditional', () => {
      it('should display highlights when destaques array has items', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
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

        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock)
          .mockRejectedValueOnce(new Error('not found'))
          .mockResolvedValueOnce({
            ok: true,
            json: async () => noHighlightsResponse
          });

        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });

        expect(screen.queryByText('Destaques:')).not.toBeInTheDocument();
      });

      it('should render highlights as bulleted list', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const highlightsList = screen.getByText('Destaques:').nextElementSibling;
          expect(highlightsList?.tagName).toBe('UL');
          expect(highlightsList).toHaveClass('list-disc', 'list-inside');
        });
      });
    });

    describe('AC6: Download Button', () => {
      it('should render download button with correct text', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByRole('button', { name: /Baixar Excel/i });
          expect(downloadButton).toBeInTheDocument();
        });
      });

      it('should be enabled after results load', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByRole('button', { name: /Baixar Excel/i });
          expect(downloadButton).toBeEnabled();
        });
      });

      it('should display count in download button text (no emoji)', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByRole('button', { name: /Baixar Excel com 15 licitações/i });
          expect(downloadButton).toBeInTheDocument();
        });
      });

      it('should use brand-navy styling for download button', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByRole('button', { name: /Baixar Excel/i });
          expect(downloadButton).toHaveClass('bg-brand-navy', 'text-white');
        });
      });
    });

    describe('AC7: Styling Compliance', () => {
      it('should use brand theme for summary card', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const summaryText = screen.getByText(/Encontradas 15 licitações/i);
          const summaryCard = summaryText.closest('div');
          expect(summaryCard).toHaveClass('bg-brand-blue-subtle', 'border', 'border-accent', 'rounded-card');
        });
      });

      it('should use warning theme for urgency alert', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const alertBox = screen.getByText(/Licitação com prazo/i).closest('div');
          expect(alertBox).toHaveClass('bg-warning-subtle');
        });
      });

      it('should use brand-navy theme for download button', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const downloadButton = screen.getByRole('button', { name: /Baixar Excel/i });
          expect(downloadButton).toHaveClass('bg-brand-navy', 'text-white');
        });
      });
    });

    describe('AC8: Responsive Layout', () => {
      it('should use responsive spacing classes on results container', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const summaryText = screen.getByText(/Encontradas 15 licitações/i);
          const summaryCard = summaryText.closest('div[class*="bg-brand-blue-subtle"]');
          const resultsContainer = summaryCard?.parentElement;
          expect(resultsContainer).toHaveClass('mt-6', 'space-y-4');
        });
      });

      it('should use flexbox for statistics layout', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          const statsContainer = screen.getByText('15').closest('div')?.parentElement;
          expect(statsContainer).toHaveClass('flex', 'gap-4');
        });
      });
    });

    describe('Edge Cases', () => {
      it('should render EmptyState component when zero opportunities', async () => {
        const zeroResponse = {
          resumo: {
            resumo_executivo: 'Nenhuma licitação encontrada',
            total_oportunidades: 0,
            valor_total: 0,
            destaques: [],
            distribuicao_uf: {},
            alerta_urgencia: null
          },
          download_id: 'empty-id',
          total_raw: 0,
          total_filtrado: 0,
          filter_stats: null,
        };

        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock)
          .mockRejectedValueOnce(new Error('not found'))
          .mockResolvedValueOnce({
            ok: true,
            json: async () => zeroResponse
          });

        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByTestId('empty-state')).toBeInTheDocument();
          expect(screen.getByText(/Nenhuma licitação de/i)).toBeInTheDocument();
        });

        // Should NOT show inline stats like "0" and "R$ 0"
        expect(screen.queryByRole('button', { name: /Baixar Excel/i })).not.toBeInTheDocument();
      });

      it('should handle API error gracefully', async () => {
        (global.fetch as jest.Mock).mockReset();
        (global.fetch as jest.Mock)
          .mockRejectedValueOnce(new Error('not found')) // setores
          .mockResolvedValueOnce({
            ok: false,
            json: async () => ({ message: 'Backend unavailable' })
          });

        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(screen.getByText('Backend unavailable')).toBeInTheDocument();
        });

        expect(screen.queryByText(/Baixar Excel/i)).not.toBeInTheDocument();
      });

      it('should clear previous results on new search', async () => {
        render(<HomePage />);

        const submitButton = screen.getByRole('button', { name: /Buscar/ });

        // First search
        fireEvent.click(submitButton);
        await waitFor(() => {
          expect(screen.getByText(/Encontradas 15 licitações/i)).toBeInTheDocument();
        });

        // Second search with different response
        const newResponse = {
          resumo: {
            resumo_executivo: 'Encontradas 3 licitações',
            total_oportunidades: 3,
            valor_total: 50000,
            destaques: [],
            distribuicao_uf: { SP: 3 },
            alerta_urgencia: null
          },
          download_id: 'new-id',
          total_raw: 30,
          total_filtrado: 3,
          filter_stats: null,
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
