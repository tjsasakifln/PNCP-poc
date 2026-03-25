import { render, screen, waitFor } from '@testing-library/react';

// Mock useInView — jsdom has no IntersectionObserver
// Controllable via mockIsInView so individual tests can opt out of animation
let mockIsInView = true;
jest.mock('../../app/hooks/useInView', () => ({
  useInView: () => ({ ref: { current: null }, isInView: mockIsInView }),
}));

// STORY-351 AC7 / FE-007: Mock useDiscardRate SWR hook
// StatsSection now uses useDiscardRate from usePublicMetrics (SWR-based)
// instead of a direct global.fetch call.
let mockDiscardRate: number | null = null;
let mockDiscardLoading = false;
jest.mock('@/hooks/usePublicMetrics', () => ({
  useDiscardRate: () => ({
    discardRate: mockDiscardRate,
    isLoading: mockDiscardLoading,
    error: null,
  }),
  useDailyVolume: () => ({
    displayValue: null,
    isLoading: false,
    error: null,
  }),
}));

beforeEach(() => {
  mockDiscardRate = null;
  mockDiscardLoading = false;
  mockIsInView = true;
});

import StatsSection from '@/app/components/landing/StatsSection';

describe('StatsSection', () => {
  it('renders section title', () => {
    // mockDiscardRate = null → fallback
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

  it('renders dynamic discard rate from API (STORY-351 AC4/AC6)', async () => {
    mockDiscardRate = 91; // hook already applies Math.round
    render(<StatsSection />);

    // Wait for counter animation to complete
    await waitFor(() => {
      expect(screen.getByText('91%')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getByText(/de editais descartados/i)).toBeInTheDocument();
  });

  it('shows fallback "A maioria" when API returns no data (STORY-351 AC4)', async () => {
    mockDiscardRate = null; // null → show "A maioria" fallback
    render(<StatsSection />);

    await waitFor(() => {
      expect(screen.getByText('A maioria')).toBeInTheDocument();
    }, { timeout: 3000 });
    expect(screen.getByText(/de editais descartados/i)).toBeInTheDocument();
  });

  it('shows fallback "A maioria" when API fails (STORY-351 AC4)', async () => {
    mockDiscardRate = null; // error → hook returns null → fallback
    render(<StatsSection />);

    await waitFor(() => {
      expect(screen.getByText('A maioria')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('shows loading state before API responds (STORY-351 AC6)', () => {
    mockDiscardLoading = true; // Hook is loading
    render(<StatsSection />);

    // Loading pulse element should be present
    const pulseEl = document.querySelector('.animate-pulse');
    expect(pulseEl).toBeInTheDocument();
  });

  it('renders 3 supporting stats with counter animation (SAB-006 AC2/AC6)', async () => {
    mockDiscardRate = 88; // hook applies Math.round(87.5) = 88
    render(<StatsSection />);

    // Wait for counter animation to complete
    await waitFor(() => {
      expect(screen.getByText('88%')).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByText(/de editais descartados/i)).toBeInTheDocument();

    expect(screen.getByText('1000+')).toBeInTheDocument();
    expect(screen.getByText(/regras de filtragem/i)).toBeInTheDocument();

    expect(screen.getByText('27')).toBeInTheDocument();
    expect(screen.getByText(/estados cobertos/i)).toBeInTheDocument();
  });

  it('initializes counters with final values for SSR/SEO (UX-422 AC1)', () => {
    // UX-422: counters now start at final values (15, 1000, 27) for SSR/SEO,
    // then animate from 0 when IntersectionObserver fires.
    // Use isInView=false so the animation effect does not reset counters to 0.
    mockIsInView = false;
    render(<StatsSection />);

    // Initial render: counters show final values (not 0) — SSR-friendly
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('1000+')).toBeInTheDocument();
    expect(screen.getByText('27')).toBeInTheDocument();
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

  it('has accessible aria-labels for all stats', async () => {
    mockDiscardRate = null; // null → "A maioria" fallback
    render(<StatsSection />);

    // Wait for animation to settle
    await waitFor(() => {
      expect(screen.getByText('A maioria')).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByRole('text', { name: '15 setores especializados' })).toBeInTheDocument();
    expect(screen.getByRole('text', { name: 'A maioria dos editais descartados' })).toBeInTheDocument();
    expect(screen.getByRole('text', { name: '1000+ regras de filtragem' })).toBeInTheDocument();
    expect(screen.getByRole('text', { name: '27 estados cobertos' })).toBeInTheDocument();
  });

  it('has dynamic aria-label when API returns data (STORY-351)', async () => {
    mockDiscardRate = 92;
    render(<StatsSection />);

    await waitFor(() => {
      expect(screen.getByRole('text', { name: '92% de editais descartados' })).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
