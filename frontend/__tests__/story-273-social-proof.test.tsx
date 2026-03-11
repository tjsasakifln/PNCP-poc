/**
 * STORY-273: Social Proof & Trust Signals — Integration Tests
 * SAB-006: Updated for condensed landing page (6 sections).
 *
 * Tests:
 * - AC3: Beta counter present on landing page (now inside FinalCTA)
 * - AC5: LGPD badge in Portuguese in Footer
 * - Regression: condensed landing page structure (SAB-006)
 *
 * NOTE: AC1 (TestimonialSection on landing) was superseded by SAB-006 —
 * section removed to achieve 5x viewport target. Component still exists.
 */

import { render, screen } from '@testing-library/react';
import React from 'react';

// ---- Mocks ----

// Mock framer-motion
jest.mock('framer-motion', () => {
  const React = require('react');
  const motion = new Proxy(
    {},
    {
      get: (_target: unknown, prop: string) =>
        React.forwardRef(
          (
            { children, ...props }: { children?: React.ReactNode; [key: string]: unknown },
            ref: React.Ref<HTMLElement>
          ) => {
            const safe: Record<string, unknown> = {};
            for (const [k, v] of Object.entries(props)) {
              if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
                safe[k] = v;
              }
            }
            return React.createElement(prop, { ...safe, ref }, children);
          }
        ),
    }
  );
  return { motion, AnimatePresence: ({ children }: { children: React.ReactNode }) => children };
});

// Mock animations lib
jest.mock('../lib/animations', () => ({
  useScrollAnimation: () => ({ ref: { current: null }, isVisible: true }),
  fadeInUp: {},
  staggerContainer: {},
  scaleIn: {},
}));

// Mock all landing page sections (SAB-006 condensed set)
jest.mock('../app/components/landing/LandingNavbar', () => {
  return function MockLandingNavbar() {
    return <nav data-testid="landing-navbar">Navbar</nav>;
  };
});

jest.mock('../app/components/landing/HeroSection', () => {
  return function MockHeroSection() {
    return <section data-testid="hero-section">Hero</section>;
  };
});

jest.mock('../app/components/landing/OpportunityCost', () => {
  return function MockOpportunityCost() {
    return <section data-testid="opportunity-cost">OpportunityCost</section>;
  };
});

jest.mock('../app/components/landing/BeforeAfter', () => {
  return function MockBeforeAfter() {
    return <section data-testid="before-after">BeforeAfter</section>;
  };
});

jest.mock('../app/components/landing/HowItWorks', () => {
  return function MockHowItWorks() {
    return <section data-testid="how-it-works">HowItWorks</section>;
  };
});

jest.mock('../app/components/landing/StatsSection', () => {
  return function MockStatsSection() {
    return <section data-testid="stats-section">StatsSection</section>;
  };
});

jest.mock('../app/components/landing/FinalCTA', () => {
  return function MockFinalCTA() {
    return (
      <section data-testid="final-cta">
        <p data-testid="beta-counter">
          Empresas de engenharia, TI, saúde, uniformes e facilities já analisam oportunidades com SmartLic
        </p>
        FinalCTA
      </section>
    );
  };
});

// Mock Footer (uses framer-motion and copy imports)
jest.mock('../app/components/Footer', () => {
  return function MockFooter() {
    return <footer data-testid="footer">Footer</footer>;
  };
});

// ---- Imports ----
import LandingPage from '../app/page';

// ---- Tests ----

describe('STORY-273 + SAB-006: Landing Page Social Proof Integration', () => {
  beforeEach(() => {
    render(<LandingPage />);
  });

  describe('AC3: Beta counter (SAB-006: absorbed into FinalCTA)', () => {
    it('should render the beta counter inside FinalCTA', () => {
      expect(screen.getByTestId('beta-counter')).toBeInTheDocument();
    });

    it('should display sector-based social proof message', () => {
      expect(screen.getByText(/Empresas de engenharia, TI, saúde, uniformes e facilities/)).toBeInTheDocument();
    });

    it('should use present continuous "já analisam" instead of past tense', () => {
      expect(screen.getByText(/já analisam oportunidades com SmartLic/)).toBeInTheDocument();
    });
  });

  describe('SAB-006: Condensed landing page structure', () => {
    it('should have exactly 6 content sections + navbar + footer', () => {
      expect(screen.getByTestId('landing-navbar')).toBeInTheDocument();
      expect(screen.getByTestId('hero-section')).toBeInTheDocument();
      expect(screen.getByTestId('opportunity-cost')).toBeInTheDocument();
      expect(screen.getByTestId('before-after')).toBeInTheDocument();
      expect(screen.getByTestId('how-it-works')).toBeInTheDocument();
      expect(screen.getByTestId('stats-section')).toBeInTheDocument();
      expect(screen.getByTestId('final-cta')).toBeInTheDocument();
      expect(screen.getByTestId('footer')).toBeInTheDocument();
    });

    it('should NOT contain removed sections', () => {
      expect(screen.queryByTestId('proof-of-value')).not.toBeInTheDocument();
      expect(screen.queryByTestId('analysis-carousel')).not.toBeInTheDocument();
      expect(screen.queryByTestId('value-prop')).not.toBeInTheDocument();
      expect(screen.queryByTestId('comparison-table')).not.toBeInTheDocument();
      expect(screen.queryByTestId('differentials-grid')).not.toBeInTheDocument();
      expect(screen.queryByTestId('data-sources')).not.toBeInTheDocument();
      expect(screen.queryByTestId('sectors-grid')).not.toBeInTheDocument();
      expect(screen.queryByTestId('trust-criteria')).not.toBeInTheDocument();
      // DEBT-122 AC1: TestimonialSection re-added to landing page
      expect(screen.queryByTestId('testimonial-section')).toBeInTheDocument();
    });

    it('should maintain correct section order: Hero → Problema → Solução → Como Funciona → Stats → Testimonials → CTA', () => {
      const main = screen.getByRole('main');
      const html = main.innerHTML;

      const heroIdx = html.indexOf('data-testid="hero-section"');
      const problemaIdx = html.indexOf('data-testid="opportunity-cost"');
      const solucaoIdx = html.indexOf('data-testid="before-after"');
      const comoIdx = html.indexOf('data-testid="how-it-works"');
      const statsIdx = html.indexOf('data-testid="stats-section"');
      const testimonialIdx = html.indexOf('data-testid="testimonial-section"');
      const ctaIdx = html.indexOf('data-testid="final-cta"');

      expect(heroIdx).toBeLessThan(problemaIdx);
      expect(problemaIdx).toBeLessThan(solucaoIdx);
      expect(solucaoIdx).toBeLessThan(comoIdx);
      expect(comoIdx).toBeLessThan(statsIdx);
      expect(statsIdx).toBeLessThan(testimonialIdx);
      expect(testimonialIdx).toBeLessThan(ctaIdx);
    });
  });
});

// ---- AC5: LGPD Badge Test (Footer) ----

// ---- AC5: LGPD Badge Test (Footer) — separate describe to avoid mock conflicts ----

describe('STORY-273 AC5: LGPD Badge in Portuguese', () => {
  beforeEach(() => {
    jest.resetModules();
  });

  it('should display LGPD badge in Portuguese in Footer', async () => {
    jest.unmock('../app/components/Footer');

    // Mock dependencies for real Footer rendering
    jest.mock('../lib/copy/valueProps', () => ({
      footer: {
        dataSource: 'Dados de fontes oficiais',
        disclaimer: 'Plataforma independente',
        trustBadge: 'Dados verificados',
      },
    }));

    jest.mock('../app/components/BackendStatusIndicator', () => ({
      useBackendStatusContext: () => ({ status: 'online' as const }),
    }));

    const { default: Footer } = await import('../app/components/Footer');

    // Use already-imported render/screen (cannot dynamically import @testing-library/react)
    render(React.createElement(Footer));

    expect(screen.getByText('Em conformidade com a LGPD')).toBeInTheDocument();
    expect(screen.queryByText('LGPD Compliant')).not.toBeInTheDocument();
  });
});
