import { render, screen } from '@testing-library/react';
import DifferentialsGrid from '@/app/(landing)/components/DifferentialsGrid';

describe('DifferentialsGrid', () => {
  it('renders section title', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/diferenciais que importam/i)).toBeInTheDocument();
  });

  it('renders all 4 differential cards', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/economia de tempo/i)).toBeInTheDocument();
    expect(screen.getByText(/vantagem competitiva/i)).toBeInTheDocument();
    expect(screen.getByText(/dados confiáveis/i)).toBeInTheDocument();
    expect(screen.getByText(/praticidade/i)).toBeInTheDocument();
  });

  it('includes descriptions for each differential', () => {
    render(<DifferentialsGrid />);

    expect(screen.getByText(/filtros inteligentes processam 500k/i)).toBeInTheDocument();
    expect(screen.getByText(/alertas em tempo real para agir/i)).toBeInTheDocument();
    expect(screen.getByText(/múltiplas fontes oficiais/i)).toBeInTheDocument();
    expect(screen.getByText(/relatórios excel prontos/i)).toBeInTheDocument();
  });

  it('renders icons for each card', () => {
    const { container } = render(<DifferentialsGrid />);

    // Check for icon containers
    const iconContainers = container.querySelectorAll('.bg-blue-100');
    expect(iconContainers.length).toBeGreaterThanOrEqual(4);
  });
});
