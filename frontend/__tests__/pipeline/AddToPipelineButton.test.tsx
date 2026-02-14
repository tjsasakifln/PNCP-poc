/**
 * Tests for AddToPipelineButton component (STORY-250)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AddToPipelineButton } from '../../app/components/AddToPipelineButton';
import type { LicitacaoItem } from '../../app/types';

// Mock usePipeline hook
const mockAddItem = jest.fn();
jest.mock('../../hooks/usePipeline', () => ({
  usePipeline: () => ({
    addItem: mockAddItem,
    items: [],
    alerts: [],
    loading: false,
    error: null,
    total: 0,
    fetchItems: jest.fn(),
    fetchAlerts: jest.fn(),
    updateItem: jest.fn(),
    removeItem: jest.fn(),
  }),
}));

describe('AddToPipelineButton', () => {
  const mockLicitacao: LicitacaoItem = {
    pncp_id: "12345678-1-000001/2026",
    objeto: "Aquisição de uniformes",
    orgao: "Prefeitura de São Paulo",
    uf: "SP",
    municipio: "São Paulo",
    valor: 150000,
    modalidade: "Pregão Eletrônico",
    data_publicacao: "2026-02-01",
    data_abertura: "2026-02-15",
    data_encerramento: "2026-03-01",
    status_display: "Recebendo Proposta",
    link: "https://pncp.gov.br/app/editais/12345",
    relevance_score: 0.95,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Button states', () => {
    it('renders "Pipeline" button text in idle state', () => {
      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      expect(screen.getByRole('button', { name: /Pipeline/i })).toBeInTheDocument();
    });

    it('shows "Salvando..." during loading', async () => {
      let resolveAdd: (value: any) => void;
      const addPromise = new Promise((resolve) => {
        resolveAdd = resolve;
      });
      mockAddItem.mockReturnValue(addPromise);

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText('Salvando...')).toBeInTheDocument();
      });

      // Should show spinner
      const spinner = button.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();

      // Resolve the promise
      resolveAdd!({ id: 'test-id' });
    });

    it('shows "No pipeline" after successful save', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('No pipeline')).toBeInTheDocument();
      });
    });

    it('shows "Erro" when addItem throws generic error', async () => {
      mockAddItem.mockRejectedValue(new Error('Network error'));

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Erro')).toBeInTheDocument();
      });
    });

    it('shows "No pipeline" when addItem throws duplicate error', async () => {
      mockAddItem.mockRejectedValue(new Error('Esta licitação já está no seu pipeline.'));

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('No pipeline')).toBeInTheDocument();
      });
    });

    it('shows "Upgrade" when addItem throws plan-related error', async () => {
      mockAddItem.mockRejectedValue(new Error('Pipeline não disponível no seu plano.'));

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Upgrade')).toBeInTheDocument();
      });
    });

    it('button is disabled when status is loading', async () => {
      let resolveAdd: (value: any) => void;
      const addPromise = new Promise((resolve) => {
        resolveAdd = resolve;
      });
      mockAddItem.mockReturnValue(addPromise);

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toBeDisabled();
      });

      resolveAdd!({ id: 'test-id' });
    });

    it('button is disabled when status is saved', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toBeDisabled();
        expect(screen.getByText('No pipeline')).toBeInTheDocument();
      });
    });
  });

  describe('Data mapping', () => {
    it('calls addItem with correct data mapping', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockAddItem).toHaveBeenCalledWith({
          pncp_id: "12345678-1-000001/2026",
          objeto: "Aquisição de uniformes",
          orgao: "Prefeitura de São Paulo",
          uf: "SP",
          valor_estimado: 150000, // valor → valor_estimado
          data_encerramento: "2026-03-01",
          link_pncp: "https://pncp.gov.br/app/editais/12345", // link → link_pncp
          stage: "descoberta",
          notes: null,
        });
      });
    });

    it('handles null data_encerramento', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      const licitacaoSemEncerramento = { ...mockLicitacao, data_encerramento: undefined };

      render(<AddToPipelineButton licitacao={licitacaoSemEncerramento} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockAddItem).toHaveBeenCalledWith(
          expect.objectContaining({
            data_encerramento: null,
          })
        );
      });
    });
  });

  describe('Event handling', () => {
    it('stops event propagation when clicked', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      const handleClick = jest.fn();
      const { container } = render(
        <div onClick={handleClick}>
          <AddToPipelineButton licitacao={mockLicitacao} />
        </div>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockAddItem).toHaveBeenCalled();
      });

      // Parent click handler should not have been called
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('prevents default event behavior', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      const event = new MouseEvent('click', { bubbles: true, cancelable: true });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      button.dispatchEvent(event);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });

    it('does not trigger addItem when already saved', async () => {
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');

      // First click
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('No pipeline')).toBeInTheDocument();
      });

      expect(mockAddItem).toHaveBeenCalledTimes(1);

      // Second click (should be ignored)
      fireEvent.click(button);

      // Should still have only been called once
      expect(mockAddItem).toHaveBeenCalledTimes(1);
    });
  });

  describe('Status reset', () => {
    it('resets to idle after 3 seconds when saved', async () => {
      jest.useFakeTimers();
      mockAddItem.mockResolvedValue({ id: 'test-id' });

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('No pipeline')).toBeInTheDocument();
      });

      // Fast forward 3 seconds
      jest.advanceTimersByTime(3000);

      // Should reset to idle
      await waitFor(() => {
        expect(screen.getByText('Pipeline')).toBeInTheDocument();
      });

      jest.useRealTimers();
    });

    it('resets to idle after 4 seconds when error', async () => {
      jest.useFakeTimers();
      mockAddItem.mockRejectedValue(new Error('Network error'));

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('Erro')).toBeInTheDocument();
      });

      // Fast forward 4 seconds
      jest.advanceTimersByTime(4000);

      // Should reset to idle
      await waitFor(() => {
        expect(screen.getByText('Pipeline')).toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<AddToPipelineButton licitacao={mockLicitacao} className="custom-class" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('Title attribute', () => {
    it('shows default title in idle state', () => {
      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('title', 'Salvar no pipeline');
    });

    it('shows error message in title when upgrade status', async () => {
      const errorMsg = 'Pipeline não disponível no seu plano.';
      mockAddItem.mockRejectedValue(new Error(errorMsg));

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('title', errorMsg);
      });
    });

    it('shows error message in title when error status', async () => {
      const errorMsg = 'Network error';
      mockAddItem.mockRejectedValue(new Error(errorMsg));

      render(<AddToPipelineButton licitacao={mockLicitacao} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('title', errorMsg);
      });
    });
  });
});
