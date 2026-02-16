/**
 * GTM-005: AnalysisExamplesCarousel Tests
 *
 * Tests AC1-AC12 for the real analysis examples carousel.
 * IntersectionObserver and matchMedia are mocked globally in jest.setup.js.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnalysisExamplesCarousel from '@/app/components/landing/AnalysisExamplesCarousel';
import { ANALYSIS_EXAMPLES, SECTION_COPY } from '@/lib/data/analysisExamples';

// matchMedia override for mobile tests
function setMobile(isMobile: boolean) {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches: isMobile,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
}

describe('AnalysisExamplesCarousel', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    setMobile(false); // Desktop by default
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders the section header', () => {
    render(<AnalysisExamplesCarousel />);
    expect(screen.getByText(SECTION_COPY.title)).toBeInTheDocument();
    expect(screen.getByText(SECTION_COPY.subtitle)).toBeInTheDocument();
  });

  // AC3: Flow indicator
  it('renders the 3-step flow indicator', () => {
    render(<AnalysisExamplesCarousel />);
    SECTION_COPY.flow.forEach((step) => {
      // Some flow labels also appear in cards (e.g., "Analise SmartLic")
      expect(screen.getAllByText(step).length).toBeGreaterThanOrEqual(1);
    });
  });

  // AC1: Shows real examples
  it('renders analysis example cards with titles', () => {
    render(<AnalysisExamplesCarousel />);
    expect(screen.getByText(ANALYSIS_EXAMPLES[0].title)).toBeInTheDocument();
  });

  // AC2: Structured analysis data in cards
  it('renders analysis details for visible cards', () => {
    render(<AnalysisExamplesCarousel />);
    const firstExample = ANALYSIS_EXAMPLES[0];
    expect(screen.getByText(firstExample.analysis.timeline)).toBeInTheDocument();
  });

  // AC4: Actionable decisions
  it('renders decision justification', () => {
    render(<AnalysisExamplesCarousel />);
    const firstExample = ANALYSIS_EXAMPLES[0];
    expect(
      screen.getByText(firstExample.decision.justification)
    ).toBeInTheDocument();
  });

  // AC8: Dot navigation
  it('renders dot navigation buttons', () => {
    render(<AnalysisExamplesCarousel />);
    const dots = screen.getAllByRole('button', { name: /Ver exemplo/ });
    expect(dots.length).toBeGreaterThanOrEqual(1);
  });

  it('allows clicking dot navigation', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<AnalysisExamplesCarousel />);
    const dots = screen.getAllByRole('button', { name: /Ver exemplo/ });
    if (dots.length > 1) {
      await user.click(dots[1]);
    }
  });

  // AC7: Auto-scroll section
  it('has auto-scroll section with correct id', () => {
    const { container } = render(<AnalysisExamplesCarousel />);
    const section = container.querySelector('#analysis-examples');
    expect(section).toBeInTheDocument();
  });

  // AC10: Glass morphism — renders without error
  it('renders without errors (GlassCard integration)', () => {
    expect(() => render(<AnalysisExamplesCarousel />)).not.toThrow();
  });

  // AC5: Zero fictional testimonials
  it('does not contain fictional person names', () => {
    const { container } = render(<AnalysisExamplesCarousel />);
    const text = container.textContent || '';
    const bannedNames = [
      'Carlos Mendes',
      'Ana Paula Silva',
      'Roberto Santos',
      'Gerente Comercial',
      'Diretora de Vendas',
    ];
    bannedNames.forEach((name) => {
      expect(text).not.toContain(name);
    });
  });

  // All 5 examples rendered in DOM
  it('renders all 5 examples in the carousel track', () => {
    render(<AnalysisExamplesCarousel />);
    ANALYSIS_EXAMPLES.forEach((example) => {
      expect(screen.getByText(example.title)).toBeInTheDocument();
    });
  });

  // Category badges
  it('renders category badges', () => {
    render(<AnalysisExamplesCarousel />);
    expect(screen.getAllByText('Uniformes').length).toBeGreaterThanOrEqual(1);
  });

  // UF labels
  it('renders UF labels', () => {
    render(<AnalysisExamplesCarousel />);
    expect(screen.getAllByText('SP').length).toBeGreaterThanOrEqual(1);
  });

  // Currency formatting
  it('renders formatted currency values', () => {
    render(<AnalysisExamplesCarousel />);
    expect(screen.getByText('R$ 450K')).toBeInTheDocument();
    expect(screen.getByText('R$ 1.2M')).toBeInTheDocument();
  });
});

describe('AnalysisExamplesCarousel — Mobile', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    setMobile(true); // Mobile
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // AC9: Mobile shows 1 card (5 dots)
  it('renders 5 dot buttons on mobile', () => {
    render(<AnalysisExamplesCarousel />);
    const dots = screen.getAllByRole('button', { name: /Ver exemplo/ });
    expect(dots).toHaveLength(5);
  });
});
