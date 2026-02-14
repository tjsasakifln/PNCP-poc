import { render, screen } from '@testing-library/react';
import OpportunityCost from '@/app/components/landing/OpportunityCost';

describe('OpportunityCost', () => {
  it('renders headline about missed opportunities, not hours (AC8)', () => {
    render(<OpportunityCost />);

    expect(
      screen.getByText(/Cada edital que passa é um contrato que vai para o concorrente/i)
    ).toBeInTheDocument();
  });

  it('renders 3 bullet points quantifying missed opportunities (AC8)', () => {
    render(<OpportunityCost />);

    expect(screen.getByText(/R\$ 2,3 bilhões/i)).toBeInTheDocument();
    expect(screen.getByText(/oportunidades mapeadas mensalmente/i)).toBeInTheDocument();
    expect(screen.getByText(/Editais relevantes vencem enquanto você ainda procura/i)).toBeInTheDocument();
    expect(screen.getByText(/Quem encontra primeiro, licita primeiro/i)).toBeInTheDocument();
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
