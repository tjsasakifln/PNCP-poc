import { render, screen } from '@testing-library/react';
import OpportunityCost from '@/app/components/landing/OpportunityCost';

describe('OpportunityCost', () => {
  it('renders headline about operating without strategic filter (GTM-COPY-001 AC8)', () => {
    render(<OpportunityCost />);

    expect(
      screen.getByText(/Continuar sem filtro estratégico é operar no escuro/i)
    ).toBeInTheDocument();
  });

  it('renders 3 bullet points quantifying financial risk (AC8)', () => {
    render(<OpportunityCost />);

    expect(screen.getByText(/Uma única licitação perdida por investir proposta no edital errado/i)).toBeInTheDocument();
    expect(screen.getByText(/R\$ 50\.000, R\$ 200\.000 ou mais/i)).toBeInTheDocument();
    expect(screen.getByText(/Sem filtro estratégico, você decide com base em intuição/i)).toBeInTheDocument();
    expect(screen.getByText(/O risco não é perder tempo/i)).toBeInTheDocument();
    expect(screen.getByText(/É perder dinheiro investindo proposta em licitações erradas/i)).toBeInTheDocument();
  });

  it('renders objective criteria contrast (GTM-COPY-004 AC6)', () => {
    render(<OpportunityCost />);

    expect(screen.getByText(/Com SmartLic, cada decisão é baseada em critérios objetivos documentados/i)).toBeInTheDocument();
  });

  it('does NOT use forbidden terms (AC11)', () => {
    const { container } = render(<OpportunityCost />);
    const text = container.textContent || '';

    expect(text).not.toMatch(/economize.*tempo/i);
    expect(text).not.toMatch(/horas perdidas/i);
    expect(text).not.toMatch(/busca rápida/i);
    expect(text).not.toMatch(/inteligência automatizada/i);
  });

  it('uses design system warning colors', () => {
    const { container } = render(<OpportunityCost />);

    expect(container.querySelector('.text-warning')).toBeInTheDocument();
    expect(container.querySelector('.text-yellow-600')).toBeInTheDocument();
  });

  it('has proper semantic structure', () => {
    render(<OpportunityCost />);

    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
  });
});
