import { render, screen } from '@testing-library/react';
import StatsSection from '@/app/(landing)/components/StatsSection';

describe('StatsSection', () => {
  it('renders section title', () => {
    render(<StatsSection />);

    expect(screen.getByText(/números que falam por si/i)).toBeInTheDocument();
  });

  it('renders all 4 stat cards', () => {
    render(<StatsSection />);

    expect(screen.getByText('6M+')).toBeInTheDocument();
    expect(screen.getByText('500k')).toBeInTheDocument();
    expect(screen.getByText('12 setores')).toBeInTheDocument();
    expect(screen.getByText(/criado por servidores públicos/i)).toBeInTheDocument();
  });

  it('includes descriptive labels for stats', () => {
    render(<StatsSection />);

    expect(screen.getByText(/licitações\/ano publicadas no brasil/i)).toBeInTheDocument();
    expect(screen.getByText(/oportunidades mensais processadas/i)).toBeInTheDocument();
    expect(screen.getByText(/atendidos \+ em expansão/i)).toBeInTheDocument();
    expect(screen.getByText(/expertise insider/i)).toBeInTheDocument();
  });

  it('highlights "Criado por servidores públicos" stat', () => {
    const { container } = render(<StatsSection />);

    // Check for highlighted background (blue instead of white)
    const highlightedStat = container.querySelector('.bg-blue-600');
    expect(highlightedStat).toBeInTheDocument();
  });
});
