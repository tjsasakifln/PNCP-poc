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

    // Check for trial value data displayed in stats cards
    expect(screen.getByText('47')).toBeInTheDocument(); // total_opportunities
    expect(screen.getByText('3/3')).toBeInTheDocument(); // searches_executed
    // Check value is formatted as currency
    expect(screen.getByText(/12\.450\.000/)).toBeInTheDocument(); // total_value in BRL
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

    // The close handler in the component calls router.push('/planos')
    expect(mockPush).toHaveBeenCalledWith('/planos');
  });

  it('redirects to /planos with billing period on CTA click', () => {
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

    // Find the primary CTA button (contains "Continuar com SmartLic Pro")
    const ctaButton = screen.getByRole('button', { name: /Continuar com SmartLic Pro/i });
    fireEvent.click(ctaButton);

    // Default billing period is monthly
    expect(mockPush).toHaveBeenCalledWith('/planos?billing=monthly');
  });

  it('tracks analytics on view', () => {
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

    expect(mockTrackEvent).toHaveBeenCalledWith('trial_conversion_screen_viewed', {
      total_opportunities: 47,
      total_value: 12450000,
    });
  });

  it('shows anchor message about single bid value', () => {
    render(<TrialConversionScreen trialValue={mockTrialValue} onClose={jest.fn()} />);

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

  it('renders when daysRemaining is 1', () => {
    render(<TrialExpiringBanner daysRemaining={1} />);

    // Should show the expiry warning message
    expect(screen.getByText(/expira amanhã/i)).toBeInTheDocument();
  });

  it('does not render when daysRemaining > 1', () => {
    const { container } = render(<TrialExpiringBanner daysRemaining={3} />);

    // Should return null (no content)
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

    // Check text content
    expect(screen.getByText(/5 dias restantes/)).toBeInTheDocument();

    // Check for emerald color classes on the link element
    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link!.className).toContain('emerald');
  });

  it('shows amber/yellow colors for 3-4 days', () => {
    const { container } = render(<TrialCountdown daysRemaining={3} />);

    expect(screen.getByText(/3 dias restantes/)).toBeInTheDocument();

    const link = container.querySelector('a');
    expect(link).not.toBeNull();
    expect(link!.className).toContain('amber');
  });

  it('shows red colors with pulse for 1-2 days', () => {
    const { container } = render(<TrialCountdown daysRemaining={1} />);

    expect(screen.getByText(/1 dia restante$/)).toBeInTheDocument();

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
