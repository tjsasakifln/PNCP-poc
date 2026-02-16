import { render, screen } from '@testing-library/react';
import StatsSection from '@/app/components/landing/StatsSection';

describe('StatsSection', () => {
  it('renders section title', () => {
    render(<StatsSection />);

    expect(screen.getByText(/Impacto real no mercado de licitações/i)).toBeInTheDocument();
  });

  it('renders hero stat 6M+', () => {
    render(<StatsSection />);

    expect(screen.getByText('R$ 2.3bi')).toBeInTheDocument();
    expect(screen.getByText(/em oportunidades\/mês/i)).toBeInTheDocument();
  });

  it('renders 3 supporting stats', () => {
    render(<StatsSection />);

    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText(/setores especializados/i)).toBeInTheDocument();

    expect(screen.getByText('27')).toBeInTheDocument();
    expect(screen.getByText(/estados cobertos/i)).toBeInTheDocument();

    expect(screen.getByText('Diário')).toBeInTheDocument();
    expect(screen.getByText(/monitoramento contínuo/i)).toBeInTheDocument();
  });

  it('uses hero number layout', () => {
    const { container } = render(<StatsSection />);

    // Hero number should be much larger (text-5xl sm:text-6xl lg:text-7xl)
    const heroNumber = container.querySelector('.text-5xl, .text-6xl, .text-7xl, .lg\\:text-7xl');
    expect(heroNumber).toBeInTheDocument();
  });

  it('uses design system tokens', () => {
    const { container } = render(<StatsSection />);

    // Check for brand colors
    expect(container.querySelector('.text-brand-navy')).toBeInTheDocument();
    expect(container.querySelector('.text-brand-blue')).toBeInTheDocument();
    expect(container.querySelector('.bg-brand-blue-subtle\\/50')).toBeInTheDocument();
  });

  it('uses tabular-nums for numerical data', () => {
    const { container } = render(<StatsSection />);

    const tabularNums = container.querySelectorAll('.tabular-nums');
    expect(tabularNums.length).toBeGreaterThan(0);
  });
});
