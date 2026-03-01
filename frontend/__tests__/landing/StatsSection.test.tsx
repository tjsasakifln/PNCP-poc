import { render, screen, waitFor } from '@testing-library/react';

// Mock useInView — jsdom has no IntersectionObserver
jest.mock('../../app/hooks/useInView', () => ({
  useInView: () => ({ ref: { current: null }, isInView: true }),
}));

import StatsSection from '@/app/components/landing/StatsSection';

describe('StatsSection', () => {
  it('renders section title', () => {
    render(<StatsSection />);

    expect(screen.getByText(/Impacto real no mercado de licitações/i)).toBeInTheDocument();
  });

  it('renders hero stat — 15 setores (with counter animation)', async () => {
    render(<StatsSection />);

    // Wait for counter animation to complete (1200ms)
    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getByText(/setores especializados/i)).toBeInTheDocument();
  });

  it('renders 3 supporting stats with counter animation (SAB-006 AC2/AC6)', async () => {
    render(<StatsSection />);

    // Wait for counter animation to complete
    await waitFor(() => {
      expect(screen.getByText('87%')).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByText(/de editais descartados/i)).toBeInTheDocument();

    expect(screen.getByText('1000+')).toBeInTheDocument();
    expect(screen.getByText(/regras de filtragem/i)).toBeInTheDocument();

    expect(screen.getByText('27')).toBeInTheDocument();
    expect(screen.getByText(/estados cobertos/i)).toBeInTheDocument();
  });

  it('starts counters at 0 before animation (SAB-006 AC6 — FOUC fix)', () => {
    render(<StatsSection />);

    // Initial render: counters start at 0 but section has opacity: 0 → no FOUC
    const zeros = screen.getAllByText('0');
    expect(zeros.length).toBeGreaterThan(0);
  });

  it('uses hero number layout', () => {
    const { container } = render(<StatsSection />);

    const heroNumber = container.querySelector('.text-5xl, .text-6xl, .text-7xl, .lg\\:text-7xl');
    expect(heroNumber).toBeInTheDocument();
  });

  it('uses design system tokens', () => {
    const { container } = render(<StatsSection />);

    expect(container.querySelector('.text-brand-navy')).toBeInTheDocument();
    expect(container.querySelector('.text-brand-blue')).toBeInTheDocument();
    expect(container.querySelector('.bg-brand-blue-subtle\\/50')).toBeInTheDocument();
  });

  it('uses tabular-nums for numerical data', () => {
    const { container } = render(<StatsSection />);

    const tabularNums = container.querySelectorAll('.tabular-nums');
    expect(tabularNums.length).toBeGreaterThan(0);
  });

  it('has accessible aria-labels for all stats', () => {
    render(<StatsSection />);

    expect(screen.getByRole('text', { name: '15 setores especializados' })).toBeInTheDocument();
    expect(screen.getByRole('text', { name: '87% de editais descartados' })).toBeInTheDocument();
    expect(screen.getByRole('text', { name: '1000+ regras de filtragem' })).toBeInTheDocument();
    expect(screen.getByRole('text', { name: '27 estados cobertos' })).toBeInTheDocument();
  });
});
