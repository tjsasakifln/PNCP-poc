/**
 * EmptyState Component Tests
 *
 * Tests rendering of empty state UI
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from '@/app/components/EmptyState';

describe('EmptyState Component', () => {
  it('should render SVG icon', () => {
    const { container } = render(<EmptyState />);

    // Check for SVG icon
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('should display main message with sector name', () => {
    render(<EmptyState sectorName="Vestuário" />);

    const message = screen.getByText(/Nenhuma licitação de vestuário encontrada/i);
    expect(message).toBeInTheDocument();
  });

  it('should display default message when no rawCount', () => {
    render(<EmptyState />);

    const message = screen.getByText(/Não encontramos licitações publicadas no PNCP/i);
    expect(message).toBeInTheDocument();
  });

  it('should display suggestions section', () => {
    render(<EmptyState />);

    const suggestionsHeader = screen.getByText(/Sugestões para encontrar resultados/i);
    expect(suggestionsHeader).toBeInTheDocument();
  });

  it('should list suggestion items', () => {
    render(<EmptyState />);

    // Check for specific suggestion text
    const expandDates = screen.getByText(/Amplie o período/i);
    const moreStates = screen.getByText(/Selecione mais estados/i);
    const changeSector = screen.getByText(/Troque o setor/i);

    expect(expandDates).toBeInTheDocument();
    expect(moreStates).toBeInTheDocument();
    expect(changeSector).toBeInTheDocument();
  });

  it('should render adjust search button', () => {
    render(<EmptyState />);

    const button = screen.getByRole('button', { name: /Ajustar critérios de busca/i });
    expect(button).toBeInTheDocument();
  });

  it('should call onAdjustSearch when button clicked', () => {
    const mockAdjust = jest.fn();
    render(<EmptyState onAdjustSearch={mockAdjust} />);

    const button = screen.getByRole('button', { name: /Ajustar critérios de busca/i });
    fireEvent.click(button);

    expect(mockAdjust).toHaveBeenCalledTimes(1);
  });

  it('should display filter stats when provided', () => {
    const filterStats = {
      rejeitadas_keyword: 10,
      rejeitadas_valor: 5,
      rejeitadas_uf: 3,
    };

    render(<EmptyState rawCount={18} filterStats={filterStats} />);

    // Should show breakdown
    expect(screen.getByText(/Sem palavras-chave do setor/i)).toBeInTheDocument();
    expect(screen.getByText(/Fora da faixa de valor/i)).toBeInTheDocument();
    expect(screen.getByText(/Estado não selecionado/i)).toBeInTheDocument();
  });

  it('should use appropriate styling classes', () => {
    const { container } = render(<EmptyState />);

    // Check for container classes
    const emptyStateContainer = container.firstChild;
    expect(emptyStateContainer).toHaveClass('text-center');
    expect(emptyStateContainer).toHaveClass('animate-fade-in-up');
  });
});
