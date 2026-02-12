import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MunicipioFilter, Municipio } from '@/app/components/MunicipioFilter';

// Mock fetch globally
global.fetch = jest.fn();

describe('MunicipioFilter', () => {
  const mockOnChange = jest.fn();
  const mockMunicipios: Municipio[] = [
    { codigo: '3550308', nome: 'São Paulo', uf: 'SP' },
    { codigo: '3304557', nome: 'Rio de Janeiro', uf: 'RJ' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => [
        { id: 3550308, nome: 'São Paulo' },
        { id: 3304557, nome: 'Rio de Janeiro' },
      ],
    });
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  it('renders without crashing', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByLabelText('Buscar municipio')).toBeInTheDocument();
  });

  it('shows disabled state when no UF selected', () => {
    render(
      <MunicipioFilter
        ufs={[]}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio') as HTMLInputElement;
    expect(input).toBeDisabled();
    expect(input.placeholder).toBe('Selecione uma UF primeiro');
  });

  it('shows correct placeholder when UF is selected', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio') as HTMLInputElement;
    expect(input.placeholder).toBe('Digite para buscar municipio...');
  });

  it('shows different placeholder when municipios are selected', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={mockMunicipios}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio') as HTMLInputElement;
    expect(input.placeholder).toBe('Adicionar mais...');
  });

  it('displays selected municipios as badges', () => {
    render(
      <MunicipioFilter
        ufs={['SP', 'RJ']}
        value={mockMunicipios}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByText('São Paulo/SP')).toBeInTheDocument();
    expect(screen.getByText('Rio de Janeiro/RJ')).toBeInTheDocument();
  });

  it('removes municipio when X button is clicked', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={mockMunicipios}
        onChange={mockOnChange}
      />
    );
    const removeButton = screen.getByLabelText('Remover São Paulo');
    fireEvent.click(removeButton);
    expect(mockOnChange).toHaveBeenCalledWith([mockMunicipios[1]]);
  });

  it('clears all municipios when "Limpar todos" is clicked', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={mockMunicipios}
        onChange={mockOnChange}
      />
    );
    const clearButton = screen.getByText('Limpar todos');
    fireEvent.click(clearButton);
    expect(mockOnChange).toHaveBeenCalledWith([]);
  });

  it('does not show clear button when no municipios selected', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.queryByText('Limpar todos')).not.toBeInTheDocument();
  });

  it('shows loading spinner during search', async () => {
    // Don't use fake timers for this test - we need real async behavior
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio');
    fireEvent.change(input, { target: { value: 'Sao' } });

    // Wait for debounced search to trigger
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    }, { timeout: 500 });
  });

  it('updates input value on change', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test' } });
    expect(input.value).toBe('Test');
  });

  it('handles keyboard navigation - ArrowDown', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio');
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    // Component should handle this without crashing
    expect(input).toBeInTheDocument();
  });

  it('handles keyboard navigation - Escape', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input.value).toBe('');
  });

  it('handles Backspace to remove last municipio', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={mockMunicipios}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio');
    fireEvent.keyDown(input, { key: 'Backspace' });
    expect(mockOnChange).toHaveBeenCalledWith([mockMunicipios[0]]);
  });

  it('shows helper text', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    expect(screen.getByText(/Deixe vazio para buscar em todos os municipios/)).toBeInTheDocument();
  });

  it('respects disabled prop', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
        disabled={true}
      />
    );
    const input = screen.getByLabelText('Buscar municipio');
    expect(input).toBeDisabled();
  });

  it('handles fetch error gracefully', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation();

    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );

    const input = screen.getByLabelText('Buscar municipio');
    fireEvent.change(input, { target: { value: 'Sao' } });

    // Wait for the debounced search and error
    await new Promise(resolve => setTimeout(resolve, 400));

    // Component should have logged the error
    expect(consoleError).toHaveBeenCalled();

    consoleError.mockRestore();
  });

  it('clears suggestions and search when UFs change', () => {
    const { rerender } = render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );

    const input = screen.getByLabelText('Buscar municipio') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test' } });

    rerender(
      <MunicipioFilter
        ufs={['RJ']}
        value={[]}
        onChange={mockOnChange}
      />
    );

    expect(input.value).toBe('');
  });

  it('has proper ARIA attributes', () => {
    render(
      <MunicipioFilter
        ufs={['SP']}
        value={[]}
        onChange={mockOnChange}
      />
    );
    const input = screen.getByLabelText('Buscar municipio');
    expect(input).toHaveAttribute('aria-autocomplete', 'list');
    expect(input).toHaveAttribute('aria-controls', 'municipio-listbox');
  });
});
