import { render, screen } from '@testing-library/react';
import DifferentialsGrid from '@/app/components/landing/DifferentialsGrid';

describe('DifferentialsGrid', () => {
  it('renders section title', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/Diferenciais que importam/i)).toBeInTheDocument();
  });

  it('renders subtitle about developers', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/Sistema desenvolvido por servidores públicos/i)).toBeInTheDocument();
  });

  it('renders 4 differential cards with new titles', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText('TEMPO')).toBeInTheDocument();
    expect(screen.getByText('PRECISÃO')).toBeInTheDocument();
    expect(screen.getByText('CONFIANÇA')).toBeInTheDocument();
    expect(screen.getByText('PRATICIDADE')).toBeInTheDocument();
  });

  it('renders bullet points for each differential', () => {
    render(<DifferentialsGrid />);

    // TEMPO bullets
    expect(screen.getByText(/500k oportunidades\/mês processadas/i)).toBeInTheDocument();
    expect(screen.getByText(/Resumos automáticos/i)).toBeInTheDocument();
    expect(screen.getByText(/Resultado em minutos/i)).toBeInTheDocument();

    // PRECISÃO bullets
    expect(screen.getByText(/Filtros por setor, estado, valor/i)).toBeInTheDocument();
    expect(screen.getByText(/Zero ruído/i)).toBeInTheDocument();

    // CONFIANÇA bullets
    expect(screen.getByText('Fonte: PNCP')).toBeInTheDocument();

    // PRATICIDADE bullets
    expect(screen.getByText(/Excel 1-clique/i)).toBeInTheDocument();
  });

  it('uses 1+3 asymmetric layout', () => {
    const { container } = render(<DifferentialsGrid />);

    // TEMPO card spans full width
    expect(container.querySelector('.lg\\:col-span-4')).toBeInTheDocument();

    // Other cards span 1 column each
    const smallCards = container.querySelectorAll('.lg\\:col-span-1');
    expect(smallCards.length).toBe(3);
  });

  it('uses design system colors', () => {
    const { container } = render(<DifferentialsGrid />);

    // Featured card uses brand-navy
    expect(container.querySelector('.bg-brand-navy')).toBeInTheDocument();

    // Other cards use surface-1
    expect(container.querySelector('.bg-surface-1')).toBeInTheDocument();
  });
});
