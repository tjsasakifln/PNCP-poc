import { render, screen } from '@testing-library/react';
import OpportunityCost from '@/app/components/landing/OpportunityCost';

describe('OpportunityCost', () => {
  it('renders headline about missed opportunities, not hours (AC8)', () => {
    render(<OpportunityCost />);

    expect(
      screen.getByText(/Enquanto você busca, seu concorrente já está se posicionando/i)
    ).toBeInTheDocument();
  });

  it('renders 3 bullet points quantifying missed opportunities (AC8)', () => {
    render(<OpportunityCost />);

    expect(screen.getByText(/Uma única licitação perdida por falta de visibilidade pode custar/i)).toBeInTheDocument();
    expect(screen.getByText(/R\$ 50\.000, R\$ 200\.000 ou mais/i)).toBeInTheDocument();
    expect(screen.getByText(/Cada dia sem visibilidade completa é uma oportunidade que pode ir para outro/i)).toBeInTheDocument();
    expect(screen.getByText(/O custo de não usar SmartLic não é tempo/i)).toBeInTheDocument();
    expect(screen.getByText(/é dinheiro/i)).toBeInTheDocument();
  });

  it('does NOT use forbidden terms (AC11)', () => {
    const { container } = render(<OpportunityCost />);
    const text = container.textContent || '';

    expect(text).not.toMatch(/economize.*tempo/i);
    expect(text).not.toMatch(/horas perdidas/i);
    expect(text).not.toMatch(/busca rápida/i);
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
