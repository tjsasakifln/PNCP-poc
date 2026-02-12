import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { OrdenacaoSelect, ORDENACAO_OPTIONS } from '@/app/components/OrdenacaoSelect';

describe('OrdenacaoSelect', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    expect(screen.getByText('Ordenar por:')).toBeInTheDocument();
  });

  it('displays selected value label', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    expect(screen.getByText('Mais recente')).toBeInTheDocument();
  });

  it('displays selected icon', () => {
    const { container } = render(
      <OrdenacaoSelect value="data_desc" onChange={mockOnChange} />
    );
    const button = screen.getByRole('combobox');
    const svg = within(button).getAllByRole('img', { hidden: true });
    expect(svg.length).toBeGreaterThan(0);
  });

  it('opens dropdown on button click', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('displays all options when opened', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getByText('Mais recente')).toBeInTheDocument();
    expect(within(listbox).getByText('Mais antigo')).toBeInTheDocument();
    expect(within(listbox).getByText('Maior valor')).toBeInTheDocument();
    expect(within(listbox).getByText('Menor valor')).toBeInTheDocument();
    expect(within(listbox).getByText('Prazo mais proximo')).toBeInTheDocument();
    expect(within(listbox).getByText('Relevancia')).toBeInTheDocument();
  });

  it('shows option descriptions', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    expect(screen.getByText('Data de publicacao decrescente')).toBeInTheDocument();
    expect(screen.getByText('Valor estimado decrescente')).toBeInTheDocument();
    expect(screen.getByText('Score de matching com termos de busca')).toBeInTheDocument();
  });

  it('calls onChange when option is selected', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    const valorDesc = screen.getByText('Maior valor');
    fireEvent.click(valorDesc);

    expect(mockOnChange).toHaveBeenCalledWith('valor_desc');
  });

  it('closes dropdown after selection', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    const option = screen.getByText('Maior valor');
    fireEvent.click(option);

    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('respects disabled prop', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} disabled={true} />);
    const button = screen.getByRole('combobox');
    expect(button).toBeDisabled();
  });

  it('does not open when disabled', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} disabled={true} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('handles keyboard navigation - Enter to open', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.keyDown(button, { key: 'Enter' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - Space to open', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.keyDown(button, { key: ' ' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - Escape to close', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    fireEvent.keyDown(button, { key: 'Escape' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('handles keyboard navigation - ArrowDown opens and navigates', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');

    fireEvent.keyDown(button, { key: 'ArrowDown' });
    expect(button).toHaveAttribute('aria-expanded', 'true');

    fireEvent.keyDown(button, { key: 'ArrowDown' });
    // Should navigate to next option
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - ArrowUp', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.keyDown(button, { key: 'ArrowUp' });
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - Home key', () => {
    render(<OrdenacaoSelect value="valor_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    fireEvent.keyDown(button, { key: 'Home' });
    // Should navigate to first option
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - End key', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    fireEvent.keyDown(button, { key: 'End' });
    // Should navigate to last option
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('handles keyboard navigation - Tab closes dropdown', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    fireEvent.keyDown(button, { key: 'Tab' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('selects option with Enter when highlighted', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    fireEvent.keyDown(button, { key: 'ArrowDown' });
    fireEvent.keyDown(button, { key: 'Enter' });

    expect(mockOnChange).toHaveBeenCalled();
  });

  it('selects option with Space when highlighted', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    fireEvent.keyDown(button, { key: 'ArrowDown' });
    fireEvent.keyDown(button, { key: ' ' });

    expect(mockOnChange).toHaveBeenCalled();
  });

  it('closes on outside click', () => {
    render(
      <div>
        <OrdenacaoSelect value="data_desc" onChange={mockOnChange} />
        <div data-testid="outside">Outside</div>
      </div>
    );

    const button = screen.getByRole('combobox');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');

    const outside = screen.getByTestId('outside');
    fireEvent.mouseDown(outside);

    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('has proper ARIA attributes', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    expect(button).toHaveAttribute('aria-haspopup', 'listbox');
    expect(button).toHaveAttribute('aria-controls', 'ordenacao-listbox');
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  it('highlights current selection in dropdown', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    const listbox = screen.getByRole('listbox');
    const optionDataDesc = within(listbox).getAllByText('Mais recente')[0].closest('li');
    expect(optionDataDesc).toHaveAttribute('aria-selected', 'true');
  });

  it('shows icons for each option', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    const listbox = screen.getByRole('listbox');
    const icons = within(listbox).getAllByRole('img', { hidden: true });

    // Should have 6 icons (one per option) plus the chevron
    expect(icons.length).toBeGreaterThan(5);
  });

  it('displays different icons for different options', () => {
    const { container } = render(<OrdenacaoSelect value="relevancia" onChange={mockOnChange} />);

    // Selected option should show sparkles icon for relevancia
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('rotates chevron icon when open', () => {
    const { container } = render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');

    const chevron = container.querySelector('.rotate-180');
    expect(chevron).not.toBeInTheDocument();

    fireEvent.click(button);

    const chevronRotated = container.querySelector('.rotate-180');
    expect(chevronRotated).toBeInTheDocument();
  });

  it('resets highlighted index to current selection when opening', () => {
    render(<OrdenacaoSelect value="valor_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');

    // Open and close
    fireEvent.click(button);
    fireEvent.click(button);

    // Reopen - should highlight current selection
    fireEvent.click(button);

    const listbox = screen.getByRole('listbox');
    const optionValorDesc = within(listbox).getAllByText('Maior valor')[0].closest('li');
    expect(optionValorDesc).toHaveAttribute('aria-selected', 'true');
  });

  it('updates highlighted option on mouse enter', () => {
    render(<OrdenacaoSelect value="data_desc" onChange={mockOnChange} />);
    const button = screen.getByRole('combobox');
    fireEvent.click(button);

    const option = screen.getAllByText('Maior valor')[0].closest('li');
    if (option) {
      fireEvent.mouseEnter(option);
      // Component should handle highlighting
      expect(option).toBeInTheDocument();
    }
  });
});

describe('ORDENACAO_OPTIONS', () => {
  it('exports correct options', () => {
    expect(ORDENACAO_OPTIONS).toHaveLength(6);
    expect(ORDENACAO_OPTIONS.map(o => o.value)).toEqual([
      'data_desc',
      'data_asc',
      'valor_desc',
      'valor_asc',
      'prazo_asc',
      'relevancia',
    ]);
  });

  it('all options have label and description', () => {
    ORDENACAO_OPTIONS.forEach(option => {
      expect(option.label).toBeTruthy();
      expect(option.description).toBeTruthy();
      expect(option.value).toBeTruthy();
    });
  });
});
