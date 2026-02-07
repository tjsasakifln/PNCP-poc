import { render, screen } from '@testing-library/react';
import BeforeAfter from '@/app/(landing)/components/BeforeAfter';

describe('BeforeAfter', () => {
  it('renders section title', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/transforme sua busca por licitações/i)).toBeInTheDocument();
  });

  it('renders "Sem SmartLic" card with negative points', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/sem smartlic/i)).toBeInTheDocument();
    expect(screen.getByText(/8 horas/i)).toBeInTheDocument();
    expect(screen.getByText(/perdidos/i)).toBeInTheDocument();
    expect(screen.getByText(/fragmentada/i)).toBeInTheDocument();
  });

  it('renders "Com SmartLic" card with positive points', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/com smartlic/i)).toBeInTheDocument();
    expect(screen.getByText(/15 minutos/i)).toBeInTheDocument();
    expect(screen.getByText(/alertas em tempo real/i)).toBeInTheDocument();
    expect(screen.getByText(/unificada/i)).toBeInTheDocument();
  });

  it('uses visual contrast between before and after cards', () => {
    const { container } = render(<BeforeAfter />);

    // "Sem SmartLic" has gray background
    const beforeCard = container.querySelector('.bg-gray-100');
    expect(beforeCard).toBeInTheDocument();

    // "Com SmartLic" has blue gradient and border
    const afterCard = container.querySelector('.from-blue-50');
    expect(afterCard).toBeInTheDocument();
  });
});
