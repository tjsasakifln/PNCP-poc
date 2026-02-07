import { render, screen } from '@testing-library/react';
import OpportunityCost from '@/app/components/landing/OpportunityCost';

describe('OpportunityCost', () => {
  it('renders institutional headline', () => {
    render(<OpportunityCost />);

    expect(
      screen.getByText(/Licitações não encontradas são contratos perdidos/i)
    ).toBeInTheDocument();
  });

  it('renders 3 key bullet points', () => {
    render(<OpportunityCost />);

    expect(screen.getByText(/500 mil/i)).toBeInTheDocument();
    expect(screen.getByText(/oportunidades\/mês/i)).toBeInTheDocument();
    expect(screen.getByText(/maioria passa despercebida/i)).toBeInTheDocument();
    expect(screen.getByText(/concorrente pode estar encontrando/i)).toBeInTheDocument();
  });

  it('uses design system warning colors', () => {
    const { container } = render(<OpportunityCost />);

    // Check for warning-subtle background using design tokens
    expect(container.querySelector('.bg-warning-subtle')).toBeInTheDocument();
    expect(container.querySelector('.border-warning')).toBeInTheDocument();
    expect(container.querySelector('.text-warning')).toBeInTheDocument();
  });

  it('has proper semantic structure', () => {
    render(<OpportunityCost />);

    // Check for heading
    expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
  });
});
