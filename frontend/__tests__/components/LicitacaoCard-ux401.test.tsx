/**
 * UX-401: Tests for valor null/0 display and unified currency formatting.
 *
 * AC3: valor=null/undefined/0 shows "Valor não informado" with tooltip
 * AC4: Local formatCurrency removed, uses formatCurrencyBR from lib
 * AC6: "R$ 0" never appears for end user
 * AC7: Values above R$ 1 million use abbreviation ("R$ 3,5 mi")
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LicitacaoCard } from '@/app/components/LicitacaoCard';
import type { LicitacaoItem } from '@/app/types';

function makeLicitacao(overrides: Partial<LicitacaoItem> = {}): LicitacaoItem {
  return {
    pncp_id: "12345678000190-1-000001/2026",
    objeto: "Aquisição de materiais de escritório",
    orgao: "Prefeitura de São Paulo",
    uf: "SP",
    municipio: "São Paulo",
    valor: 150000,
    modalidade: "Pregão Eletrônico",
    data_publicacao: "2026-03-01",
    data_abertura: null,
    data_encerramento: null,
    link: "https://pncp.gov.br/app/editais/12345678000190/2026/1",
    ...overrides,
  };
}

// =============================================================================
// AC3: valor=null renders "Valor não informado"
// =============================================================================

describe('UX-401 AC3: Valor null/0 display', () => {
  it('shows "Valor não informado" when valor is null', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: null })} />);

    const element = screen.getByTestId('valor-nao-informado');
    expect(element).toHaveTextContent('Valor não informado');
  });

  it('shows "Valor não informado" when valor is 0', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 0 })} />);

    const element = screen.getByTestId('valor-nao-informado');
    expect(element).toHaveTextContent('Valor não informado');
  });

  it('shows "Valor não informado" when valor is undefined', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: undefined as unknown as null })} />);

    const element = screen.getByTestId('valor-nao-informado');
    expect(element).toHaveTextContent('Valor não informado');
  });

  it('applies muted text style for unavailable valor', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: null })} />);

    const element = screen.getByTestId('valor-nao-informado');
    expect(element).toHaveClass('text-ink-muted');
    expect(element).toHaveClass('text-sm');
  });
});

// =============================================================================
// AC4+AC7: Positive values use formatCurrencyBR with abbreviations
// =============================================================================

describe('UX-401 AC4+AC7: Currency formatting with abbreviations', () => {
  it('formats R$ 3,500,000 as "R$ 3,5 mi"', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 3500000 })} />);

    const element = screen.getByTestId('valor-display');
    expect(element).toHaveTextContent('R$ 3,5 mi');
  });

  it('formats R$ 45,000 as "R$ 45.000"', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 45000 })} />);

    const element = screen.getByTestId('valor-display');
    expect(element).toHaveTextContent('R$ 45.000');
  });

  it('formats R$ 150,000 correctly', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 150000 })} />);

    const element = screen.getByTestId('valor-display');
    expect(element).toHaveTextContent('R$ 150.000');
  });

  it('formats R$ 1,000,000,000 as "R$ 1,0 bi"', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 1000000000 })} />);

    const element = screen.getByTestId('valor-display');
    expect(element).toHaveTextContent('R$ 1,0 bi');
  });

  it('uses bold navy style for positive values', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 150000 })} />);

    const element = screen.getByTestId('valor-display');
    expect(element).toHaveClass('text-2xl');
    expect(element).toHaveClass('font-bold');
    expect(element).toHaveClass('text-brand-navy');
  });
});

// =============================================================================
// AC6: "R$ 0" never appears
// =============================================================================

describe('UX-401 AC6: "R$ 0" never displayed', () => {
  it('valor=0 never renders "R$ 0"', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: 0 })} />);

    // Should NOT find any element with "R$ 0" text
    const body = document.body.textContent || '';
    expect(body).not.toMatch(/R\$\s*0(?!\.\d)/);
  });

  it('valor=null never renders "R$ 0"', () => {
    render(<LicitacaoCard licitacao={makeLicitacao({ valor: null })} />);

    const body = document.body.textContent || '';
    expect(body).not.toMatch(/R\$\s*0(?!\.\d)/);
  });
});

// =============================================================================
// Snapshot: visual comparison of cards
// =============================================================================

describe('UX-401: Visual snapshot comparison', () => {
  it('card with valor=null renders correctly', () => {
    const { container } = render(
      <LicitacaoCard licitacao={makeLicitacao({ valor: null })} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('card with positive valor renders correctly', () => {
    const { container } = render(
      <LicitacaoCard licitacao={makeLicitacao({ valor: 250000 })} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
