import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { OrgaoFilter, Orgao } from '@/app/components/OrgaoFilter';

describe('OrgaoFilter', () => {
  const mockOnChange = jest.fn();
  const mockOrgaos: Orgao[] = [
    { codigo: 'ms', nome: 'Ministerio da Saude', uf: 'DF' },
    { codigo: 'mec', nome: 'Ministerio da Educacao', uf: 'DF' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByLabelText('Buscar orgao')).toBeInTheDocument();
  });

  it('shows correct placeholder when no selection', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao') as HTMLInputElement;
    expect(input.placeholder).toBe('Buscar orgao...');
  });

  it('shows different placeholder when orgaos are selected', () => {
    render(
      <OrgaoFilter
        value={mockOrgaos}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao') as HTMLInputElement;
    expect(input.placeholder).toBe('Adicionar mais...');
  });

  it('shows disabled placeholder when disabled', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
        disabled={true}
      />
    );
    const input = screen.getByLabelText('Buscar orgao') as HTMLInputElement;
    expect(input.placeholder).toBe('Filtros desabilitados');
  });

  it('displays selected orgaos as badges', () => {
    render(
      <OrgaoFilter
        value={mockOrgaos}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByText('Ministerio da Saude')).toBeInTheDocument();
    expect(screen.getByText('Ministerio da Educacao')).toBeInTheDocument();
  });

  it('truncates long orgao names in badges', () => {
    const longOrgao: Orgao = {
      codigo: 'long',
      nome: 'A very long organization name that should be truncated to fit',
      uf: 'SP',
    };
    render(
      <OrgaoFilter
        value={[longOrgao]}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByText(/A very long organization name/)).toBeInTheDocument();
  });

  it('removes orgao when X button is clicked', () => {
    render(
      <OrgaoFilter
        value={mockOrgaos}
        onChange={mockOnChange}
      />
    );
    const removeButton = screen.getByLabelText('Remover Ministerio da Saude');
    fireEvent.click(removeButton);
    expect(mockOnChange).toHaveBeenCalledWith([mockOrgaos[1]]);
  });

  it('clears all orgaos when "Limpar todos" is clicked', () => {
    render(
      <OrgaoFilter
        value={mockOrgaos}
        onChange={mockOnChange}
      />
    );
    const clearButton = screen.getByText('Limpar todos');
    fireEvent.click(clearButton);
    expect(mockOnChange).toHaveBeenCalledWith([]);
  });

  it('does not show clear button when no orgaos selected', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.queryByText('Limpar todos')).not.toBeInTheDocument();
  });

  it('shows frequent orgaos when no search and no selection', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByText('Orgaos frequentes:')).toBeInTheDocument();
  });

  it('does not show frequent orgaos when disabled', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
        disabled={true}
      />
    );
    expect(screen.queryByText('Orgaos frequentes:')).not.toBeInTheDocument();
  });

  it('does not show frequent orgaos when there is a selection', () => {
    render(
      <OrgaoFilter
        value={mockOrgaos}
        onChange={mockOnChange}
      />
    );
    expect(screen.queryByText('Orgaos frequentes:')).not.toBeInTheDocument();
  });

  it('updates input value on change', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test' } });
    expect(input.value).toBe('Test');
  });

  it('handles keyboard navigation - ArrowDown', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(input).toBeInTheDocument();
  });

  it('handles keyboard navigation - ArrowUp', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    expect(input).toBeInTheDocument();
  });

  it('handles keyboard navigation - Escape', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input.value).toBe('');
  });

  it('handles Backspace to remove last orgao', () => {
    render(
      <OrgaoFilter
        value={mockOrgaos}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    fireEvent.keyDown(input, { key: 'Backspace' });
    expect(mockOnChange).toHaveBeenCalledWith([mockOrgaos[0]]);
  });

  it('shows helper text', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByText(/Filtre por orgaos\/entidades especificos/)).toBeInTheDocument();
  });

  it('respects disabled prop', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
        disabled={true}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    expect(input).toBeDisabled();
  });

  it('accepts availableOrgaos prop', () => {
    const availableOrgaos: Orgao[] = [
      { codigo: 'custom1', nome: 'Custom Orgao 1', uf: 'SP' },
      { codigo: 'custom2', nome: 'Custom Orgao 2', uf: 'RJ' },
    ];
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
        availableOrgaos={availableOrgaos}
      />
    );
    expect(screen.getByLabelText('Buscar orgao')).toBeInTheDocument();
  });

  it('has proper ARIA attributes', () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    expect(input).toHaveAttribute('aria-autocomplete', 'list');
    expect(input).toHaveAttribute('aria-controls', 'orgao-listbox');
  });

  it('opens dropdown on input focus with valid search', async () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    fireEvent.change(input, { target: { value: 'Min' } });

    // Wait for debounce
    await waitFor(() => {
      fireEvent.focus(input);
      expect(input).toHaveAttribute('aria-expanded', 'true');
    }, { timeout: 500 });
  });

  it('filters orgaos based on search term', async () => {
    render(
      <OrgaoFilter
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar orgao');
    fireEvent.change(input, { target: { value: 'Ministerio' } });
    fireEvent.focus(input);

    // Wait for debounce to complete
    await waitFor(() => {
      expect(input.value).toBe('Ministerio');
    }, { timeout: 500 });
  });
});
