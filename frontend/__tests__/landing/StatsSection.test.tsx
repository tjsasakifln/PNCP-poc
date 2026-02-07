import { render, screen } from '@testing-library/react';
import StatsSection from '@/app/components/landing/StatsSection';

describe('StatsSection', () => {
  it('renders section title', () => {
    render(<StatsSection />);

    expect(screen.getByText(/Números que falam por si/i)).toBeInTheDocument();
  });

  it('renders hero stat 6M+', () => {
    render(<StatsSection />);

    expect(screen.getByText('6M+')).toBeInTheDocument();
    expect(screen.getByText(/licitações\/ano/i)).toBeInTheDocument();
  });

  it('renders 3 supporting stats', () => {
    render(<StatsSection />);

    expect(screen.getByText('500k')).toBeInTheDocument();
    expect(screen.getByText(/\/mês processadas/i)).toBeInTheDocument();

    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText(/setores atendidos/i)).toBeInTheDocument();

    expect(screen.getByText('Servidores')).toBeInTheDocument();
    expect(screen.getByText(/públicos criadores/i)).toBeInTheDocument();
  });

  it('uses hero number layout', () => {
    const { container } = render(<StatsSection />);

    // Hero number should be much larger
    const heroNumber = container.querySelector('.text-6xl, .text-7xl, .text-8xl, .lg\\:text-8xl');
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
