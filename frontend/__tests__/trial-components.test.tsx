import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mocks first (before component imports)
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/buscar',
}));

const mockTrackEvent = jest.fn();
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));

jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => ({ session: { access_token: 'test-token' }, loading: false }),
}));

jest.mock('../hooks/usePlans', () => ({
  usePlans: () => ({ plans: null, error: null, isLoading: false }),
}));

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, whileHover, transition, ...rest }: any) => (
      <div className={className} data-testid="glass-card" {...rest}>
        {children}
      </div>
    ),
  },
}));

// Import components after mocks
import { TrialConversionScreen } from '../app/components/TrialConversionScreen';
import { TrialExpiringBanner } from '../app/components/TrialExpiringBanner';
import { TrialCountdown } from '../app/components/TrialCountdown';

const mockTrialValue = {
  total_opportunities: 47,
  total_value: 12450000,
  searches_executed: 3,
  avg_opportunity_value: 264893.62,
  top_opportunity: { title: "Uniformes escolares - SP", value: 850000 },
};

describe('TrialConversionScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with trial value data', () => {
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

    // Check for trial value data displayed in stats cards + comparison table
    expect(screen.getAllByText('47').length).toBeGreaterThanOrEqual(1); // total_opportunities (may appear in stats + table)
    // STORY-264 AC9: searches_executed no longer shows /3
    expect(screen.getByText('3')).toBeInTheDocument(); // searches_executed (no "/3")
    expect(screen.queryByText('3/3')).not.toBeInTheDocument(); // Old format removed
    // Check value is formatted as currency (may appear in stats + ROI message)
    expect(screen.getAllByText(/12\.450\.000/).length).toBeGreaterThanOrEqual(1); // total_value in BRL
  });

  it('renders alternative message when no data', () => {
    render(<TrialConversionScreen trialValue={null} onClose={jest.fn()} />);

    // With null data, should show the alternative hero text
    expect(screen.getByText(/Descubra oportunidades/i)).toBeInTheDocument();
  });

  it('shows loading skeleton when loading', () => {
    const { container } = render(
      <TrialConversionScreen trialValue={null} onClose={jest.fn()} loading={true} />
    );

    // Should have skeleton elements with animate-pulse
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('calls onClose and redirects to /planos on close button click', () => {
    const onClose = jest.fn();
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={onClose} />);

    // Find and click the close button (aria-label="Fechar")
    const closeButton = screen.getByLabelText('Fechar');
    fireEvent.click(closeButton);

    // The close handler redirects to /planos with billing period preserved
    expect(mockPush).toHaveBeenCalledWith('/planos?billing=monthly');
  });

  it('attempts direct checkout on CTA click', async () => {
    // P0 zero-churn: CTA now calls POST /api/billing directly
    const mockFetch = jest.fn().mockRejectedValue(new Error('test'));
    global.fetch = mockFetch;

    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

    const ctaButton = screen.getByRole('button', { name: /Continuar com SmartLic Pro/i });
    fireEvent.click(ctaButton);

    // Should attempt fetch then fallback to router.push
    await new Promise(r => setTimeout(r, 200));
    expect(mockFetch).toHaveBeenCalled();
    expect(mockPush).toHaveBeenCalledWith('/planos?billing=monthly');
  });

  it('tracks analytics on view', () => {
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

    expect(mockTrackEvent).toHaveBeenCalledWith('trial_conversion_screen_viewed', {
      total_opportunities: 47,
      total_value: 12450000,
    });
  });

  it('shows personalized ROI anchor message when trial has value data', () => {
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

    // Zero-churn P2 §4.2: personalized ROI replaces generic anchor when total_value > 0
    expect(screen.getByText(/Você analisou.*em oportunidades.*custo anual/i)).toBeInTheDocument();
  });

  it('shows generic anchor message when no value data', () => {
    const noValueData = { ...mockTrialValue, total_value: 0 };
    render(<TrialConversionScreen trialValue={noValueData} onClose={jest.fn()} />);

    expect(screen.getByText(/Uma única licitação ganha pode pagar o sistema por um ano inteiro/i)).toBeInTheDocument();
  });

  it('never uses forbidden copy words', () => {
    const { container } = render(
      <TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />
    );

    const text = container.textContent || '';
    const lowerText = text.toLowerCase();

    // GTM-002 copy rules: never use these words
    expect(lowerText).not.toMatch(/\bplano\b/);
    expect(lowerText).not.toMatch(/\bassinatura\b/);
    expect(lowerText).not.toContain('tier');
    expect(lowerText).not.toContain('pacote');
  });
});

describe('TrialExpiringBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders "termina hoje" when daysRemaining is 0', () => {
    render(<TrialExpiringBanner daysRemaining={0} />);

    // COPY-369 AC1: daysRemaining === 0 → "termina hoje"
    expect(screen.getByText(/acesso completo.*termina hoje/i)).toBeInTheDocument();
  });

  it('renders "termina amanhã" when daysRemaining is 1', () => {
    render(<TrialExpiringBanner daysRemaining={1} />);

    // COPY-369 AC1: daysRemaining === 1 → "termina amanhã"
    expect(screen.getByText(/acesso completo.*termina amanhã/i)).toBeInTheDocument();
  });

  it('renders "termina em 3 dias" when daysRemaining is 3', () => {
    render(<TrialExpiringBanner daysRemaining={3} />);

    // COPY-369 AC1: daysRemaining >= 2 → "termina em {N} dias"
    expect(screen.getByText(/acesso completo.*termina em 3 dias/i)).toBeInTheDocument();
  });

  it('renders "termina em 6 dias" when daysRemaining is 6', () => {
    render(<TrialExpiringBanner daysRemaining={6} />);

    // COPY-369 AC1: daysRemaining >= 2 → "termina em {N} dias"
    expect(screen.getByText(/acesso completo.*termina em 6 dias/i)).toBeInTheDocument();
  });

  it('shows updated subtext with pricing info (COPY-369 AC2)', () => {
    render(<TrialExpiringBanner daysRemaining={3} />);

    expect(screen.getByText(/R\$ 297\/mês/)).toBeInTheDocument();
  });

  it('does not render when daysRemaining > 6 (STORY-319: threshold from day 8)', () => {
    const { container } = render(<TrialExpiringBanner daysRemaining={7} />);

    // Should return null (no content) — STORY-319: shows from day 8 (6 days remaining)
    expect(container.firstChild).toBeNull();
  });

  it('dismisses on X click', () => {
    const { container } = render(<TrialExpiringBanner daysRemaining={1} />);

    // Find the dismiss button (aria-label="Dispensar")
    const dismissButton = screen.getByLabelText('Dispensar');
    fireEvent.click(dismissButton);

    // Banner should disappear
    expect(container.firstChild).toBeNull();
  });

  it('calls onConvert on CTA click', () => {
    const onConvert = jest.fn();
    render(<TrialExpiringBanner daysRemaining={1} onConvert={onConvert} />);

    // Find the CTA button
    const ctaButton = screen.getByRole('button', { name: /Continuar tendo vantagem/i });
    fireEvent.click(ctaButton);

    expect(onConvert).toHaveBeenCalledTimes(1);
  });

  it('tracks dismiss analytics', () => {
    render(<TrialExpiringBanner daysRemaining={1} />);

    const dismissButton = screen.getByLabelText('Dispensar');
    fireEvent.click(dismissButton);

    expect(mockTrackEvent).toHaveBeenCalledWith('trial_expiring_banner_dismissed', { days_remaining: 1 });
  });
});

describe('TrialCountdown', () => {
  it('shows green/emerald colors for 5+ days', () => {
    const { container } = render(<TrialCountdown daysRemaining={5} />);

    // STORY-264 AC7: "de acesso completo" instead of "restantes"
    expect(screen.getByText(/5 dias de acesso completo/)).toBeInTheDocument();

    // Check for emerald color classes on the link element
    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link!.className).toContain('emerald');
  });

  it('shows amber/yellow colors for 3-4 days', () => {
    const { container } = render(<TrialCountdown daysRemaining={3} />);

    expect(screen.getByText(/3 dias de acesso completo/)).toBeInTheDocument();

    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link!.className).toContain('amber');
  });

  it('shows red colors with pulse for 1-2 days', () => {
    const { container } = render(<TrialCountdown daysRemaining={1} />);

    expect(screen.getByText(/1 dia de acesso completo/)).toBeInTheDocument();

    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link!.className).toContain('red');

    // Check for pulse animation on the dot
    const pulseDot = container.querySelector('.animate-pulse');
    expect(pulseDot).not.toBeNull();
  });

  it('does not render for 0 days', () => {
    const { container } = render(<TrialCountdown daysRemaining={0} />);

    expect(container.firstChild).toBeNull();
  });

  it('links to /planos', () => {
    const { container } = render(<TrialCountdown daysRemaining={5} />);

    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link!.getAttribute('href')).toBe('/planos');
  });
});
