import { render, screen } from '@testing-library/react';
import OpportunityCost from '@/app/(landing)/components/OpportunityCost';

describe('OpportunityCost', () => {
  it('renders provocative headline', () => {
    render(<OpportunityCost />);

    expect(
      screen.getByText(/qual o custo de uma licitação não disputada/i)
    ).toBeInTheDocument();
  });

  it('renders 3 key points', () => {
    render(<OpportunityCost />);

    expect(screen.getByText(/500 mil oportunidades/i)).toBeInTheDocument();
    expect(screen.getByText(/despercebida/i)).toBeInTheDocument();
    expect(screen.getByText(/concorrente que venceu/i)).toBeInTheDocument();
  });

  it('has warning/alert visual styling', () => {
    const { container } = render(<OpportunityCost />);

    // Check for amber/warning background and border
    const alertBox = container.querySelector('.bg-amber-50');
    expect(alertBox).toBeInTheDocument();

    const alertBorder = container.querySelector('.border-amber-500');
    expect(alertBorder).toBeInTheDocument();
  });
});
