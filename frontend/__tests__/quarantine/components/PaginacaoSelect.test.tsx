import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  PaginacaoSelect,
  PaginationControls,
  PAGINACAO_OPTIONS,
} from '@/app/components/PaginacaoSelect';

describe('PaginacaoSelect', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    expect(screen.getByLabelText('Itens por pagina')).toBeInTheDocument();
  });

  it('displays selected value', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    expect(screen.getByText('20 por pagina')).toBeInTheDocument();
  });

  it('opens dropdown on button click', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('displays all options when opened', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);

    expect(screen.getByText('10 por pagina')).toBeInTheDocument();
    expect(screen.getByText('20 por pagina')).toBeInTheDocument();
    expect(screen.getByText('50 por pagina')).toBeInTheDocument();
    expect(screen.getByText('100 por pagina')).toBeInTheDocument();
  });

  it('calls onChange when option is selected', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);

    const option50 = screen.getByText('50 por pagina');
    fireEvent.click(option50);

    expect(mockOnChange).toHaveBeenCalledWith(50);
  });

  it('closes dropdown after selection', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    const option = screen.getByText('50 por pagina');
    fireEvent.click(option);

    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('respects disabled prop', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} disabled={true} />);
    const button = screen.getByLabelText('Itens por pagina');
    expect(button).toBeDisabled();
  });

  it('does not open when disabled', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} disabled={true} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('handles keyboard navigation - Enter to open', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.keyDown(button, { key: 'Enter' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - Space to open', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.keyDown(button, { key: ' ' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - Escape to close', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    fireEvent.keyDown(button, { key: 'Escape' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('handles keyboard navigation - ArrowDown', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.keyDown(button, { key: 'ArrowDown' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - ArrowUp', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.keyDown(button, { key: 'ArrowUp' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('shows totalItems when provided', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} totalItems={150} />);
    expect(screen.getByText(/de 150 resultados/)).toBeInTheDocument();
  });

  it('does not show totalItems indicator when totalItems is 0', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} totalItems={0} />);
    expect(screen.queryByText(/resultados/)).not.toBeInTheDocument();
  });

  it('closes on outside click', () => {
    render(
      <div>
        <PaginacaoSelect value={20} onChange={mockOnChange} />
        <div data-testid="outside">Outside</div>
      </div>
    );

    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    const outside = screen.getByTestId('outside');
    fireEvent.mouseDown(outside);

    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('has proper ARIA attributes', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    expect(button).toHaveAttribute('role', 'combobox');
    expect(button).toHaveAttribute('aria-haspopup', 'listbox');
    expect(button).toHaveAttribute('aria-controls', 'paginacao-listbox');
  });

  it('highlights current selection in dropdown', () => {
    render(<PaginacaoSelect value={20} onChange={mockOnChange} />);
    const button = screen.getByLabelText('Itens por pagina');
    fireEvent.click(button);

    const listbox = screen.getByRole('listbox');
    const option20 = within(listbox).getByText('20 por pagina').closest('li');
    expect(option20).toHaveAttribute('aria-selected', 'true');
  });
});

describe('PaginationControls', () => {
  const mockOnPageChange = jest.fn();
  const mockOnItemsPerPageChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(
      <PaginationControls
        currentPage={1}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByText(/Exibindo/)).toBeInTheDocument();
  });

  it('displays correct range info', () => {
    render(
      <PaginationControls
        currentPage={2}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByText(/Exibindo 21-40 de 100 resultados/)).toBeInTheDocument();
  });

  it('displays correct page indicator', () => {
    render(
      <PaginationControls
        currentPage={3}
        totalPages={10}
        itemsPerPage={20}
        totalItems={200}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByText(/3 \/ 10/)).toBeInTheDocument();
  });

  it('calls onPageChange when next button is clicked', () => {
    render(
      <PaginationControls
        currentPage={2}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    const nextButton = screen.getByLabelText('Proxima pagina');
    fireEvent.click(nextButton);
    expect(mockOnPageChange).toHaveBeenCalledWith(3);
  });

  it('calls onPageChange when previous button is clicked', () => {
    render(
      <PaginationControls
        currentPage={3}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    const prevButton = screen.getByLabelText('Pagina anterior');
    fireEvent.click(prevButton);
    expect(mockOnPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange when first button is clicked', () => {
    render(
      <PaginationControls
        currentPage={3}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    const firstButton = screen.getByLabelText('Primeira pagina');
    fireEvent.click(firstButton);
    expect(mockOnPageChange).toHaveBeenCalledWith(1);
  });

  it('calls onPageChange when last button is clicked', () => {
    render(
      <PaginationControls
        currentPage={2}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    const lastButton = screen.getByLabelText('Ultima pagina');
    fireEvent.click(lastButton);
    expect(mockOnPageChange).toHaveBeenCalledWith(5);
  });

  it('disables previous/first buttons on first page', () => {
    render(
      <PaginationControls
        currentPage={1}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByLabelText('Primeira pagina')).toBeDisabled();
    expect(screen.getByLabelText('Pagina anterior')).toBeDisabled();
  });

  it('disables next/last buttons on last page', () => {
    render(
      <PaginationControls
        currentPage={5}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByLabelText('Proxima pagina')).toBeDisabled();
    expect(screen.getByLabelText('Ultima pagina')).toBeDisabled();
  });

  it('includes PaginacaoSelect component', () => {
    render(
      <PaginationControls
        currentPage={1}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByLabelText('Itens por pagina')).toBeInTheDocument();
  });

  it('respects disabled prop', () => {
    render(
      <PaginationControls
        currentPage={2}
        totalPages={5}
        itemsPerPage={20}
        totalItems={100}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
        disabled={true}
      />
    );
    expect(screen.getByLabelText('Proxima pagina')).toBeDisabled();
    expect(screen.getByLabelText('Pagina anterior')).toBeDisabled();
  });

  it('handles last page with fewer items', () => {
    render(
      <PaginationControls
        currentPage={5}
        totalPages={5}
        itemsPerPage={20}
        totalItems={95}
        onPageChange={mockOnPageChange}
        onItemsPerPageChange={mockOnItemsPerPageChange}
      />
    );
    expect(screen.getByText(/Exibindo 81-95 de 95 resultados/)).toBeInTheDocument();
  });
});

describe('PAGINACAO_OPTIONS', () => {
  it('exports correct options', () => {
    expect(PAGINACAO_OPTIONS).toHaveLength(4);
    expect(PAGINACAO_OPTIONS.map(o => o.value)).toEqual([10, 20, 50, 100]);
  });
});
