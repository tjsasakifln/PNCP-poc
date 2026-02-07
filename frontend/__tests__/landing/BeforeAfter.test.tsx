import { render, screen } from '@testing-library/react';
import BeforeAfter from '@/app/components/landing/BeforeAfter';

describe('BeforeAfter', () => {
  it('renders section title', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Transforme sua busca por licitações/i)).toBeInTheDocument();
  });

  it('renders "Busca Manual" card with negative points', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Busca Manual/i)).toBeInTheDocument();
    expect(screen.getByText(/8h\/dia/i)).toBeInTheDocument();
    expect(screen.getByText(/Editais perdidos/i)).toBeInTheDocument();
    expect(screen.getByText(/27 fontes fragmentadas/i)).toBeInTheDocument();
    expect(screen.getByText(/Sem histórico/i)).toBeInTheDocument();
  });

  it('renders "Com SmartLic" card with positive points', () => {
    render(<BeforeAfter />);

    expect(screen.getByText(/Com SmartLic/i)).toBeInTheDocument();
    expect(screen.getByText(/15min\/dia/i)).toBeInTheDocument();
    expect(screen.getByText(/Alertas em tempo real/i)).toBeInTheDocument();
    expect(screen.getByText(/Busca unificada/i)).toBeInTheDocument();
    expect(screen.getByText(/Histórico completo/i)).toBeInTheDocument();
  });

  it('uses asymmetric 40/60 layout', () => {
    const { container } = render(<BeforeAfter />);

    // Check for 5-column grid with 2+3 split
    expect(container.querySelector('.md\\:col-span-2')).toBeInTheDocument();
    expect(container.querySelector('.md\\:col-span-3')).toBeInTheDocument();
  });

  it('uses design system semantic colors', () => {
    const { container } = render(<BeforeAfter />);

    // "Busca Manual" has error colors
    expect(container.querySelector('.bg-error-subtle')).toBeInTheDocument();
    expect(container.querySelector('.text-error')).toBeInTheDocument();

    // "Com SmartLic" has brand/success colors
    expect(container.querySelector('.text-success')).toBeInTheDocument();
    expect(container.querySelector('.from-brand-blue-subtle')).toBeInTheDocument();
  });
});
