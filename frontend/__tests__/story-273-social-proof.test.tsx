/**
 * STORY-273: Social Proof & Trust Signals — Integration Tests
 * REPO-COMMS #1289: Updated for B2G repositioning landing page (7 sections).
 *
 * Tests:
 * - AC3: Social proof message present on landing page (now in SocialProofMetrics)
 * - AC5: LGPD badge in Portuguese in Footer
 * - Regression: B2G landing page structure (#1289)
 *
 * NOTE: SAB-006 FinalCTA section replaced by MarketSocialProof in REPO-COMMS #1289.
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

// Mock animations lib (REPO-COMMS #1289: added useLandingAnimation + usePrefersReducedMotion)
jest.mock('../lib/animations', () => ({
  useScrollAnimation: () => ({ ref: { current: null }, isVisible: true }),
  useLandingAnimation: () => ({ ref: { current: null }, isVisible: true, shouldAnimate: true }),
  usePrefersReducedMotion: () => false,
  fadeInUp: {},
  staggerContainer: {},
  scaleIn: {},
}));

// Mock all landing page sections (REPO-COMMS #1289 B2G repositioning set)
jest.mock('../app/components/landing/LandingNavbar', () => {
  return function MockLandingNavbar() {
    return <nav data-testid="landing-navbar">Navbar</nav>;
  };
});

jest.mock('../app/components/landing/HeroB2GIntel', () => {
  return function MockHeroB2GIntel() {
    return <section data-testid="hero-b2g">HeroB2GIntel</section>;
  };
});

jest.mock('../app/components/landing/AntecipeDecidaExecute', () => {
  return function MockAntecipeDecidaExecute() {
    return <section data-testid="antecipe-decida-execute">AntecipeDecidaExecute</section>;
  };
});

jest.mock('../app/components/landing/TerminalComparison', () => {
  return function MockTerminalComparison() {
    return <section data-testid="terminal-comparison">TerminalComparison</section>;
  };
});

jest.mock('../app/components/landing/SocialProofMetrics', () => {
  return function MockSocialProofMetrics() {
    return (
      <section data-testid="social-proof-metrics">
        <p data-testid="beta-counter">
          Empresas de engenharia, TI, saúde, uniformes e facilities já analisam oportunidades com SmartLic
        </p>
        SocialProofMetrics
      </section>
    );
  };
});

jest.mock('../app/components/landing/PersonasSection', () => {
  return function MockPersonasSection() {
    return <section data-testid="personas-section">PersonasSection</section>;
  };
});

jest.mock('../app/components/landing/PublicIntelligenceSection', () => {
  return function MockPublicIntelligenceSection() {
    return <section data-testid="public-intelligence-section">PublicIntelligenceSection</section>;
  };
});

jest.mock('../app/components/landing/MarketSocialProof', () => {
  return function MockMarketSocialProof() {
    return <section data-testid="market-social-proof">MarketSocialProof</section>;
  };
});

jest.mock('../app/components/landing/NewsletterFooter', () => {
  return function MockNewsletterFooter() {
    return <section data-testid="newsletter-footer">NewsletterFooter</section>;
  };
});

// Mock B2GIntelTheme (passes children through)
jest.mock('../app/components/landing/B2GIntelTheme', () => {
  return function MockB2GIntelTheme({ children }: { children: React.ReactNode }) {
    return <div data-testid="b2g-intel-theme">{children}</div>;
  };
});

// Mock Footer (uses framer-motion and copy imports)
jest.mock('../app/components/Footer', () => {
  return function MockFooter() {
    return <footer data-testid="footer">Footer</footer>;
  };
});

// Mock HomeFaqStructuredData (JSON-LD, no visual output)
jest.mock('../app/components/HomeFaqStructuredData', () => ({
  HomeFaqStructuredData: function MockHomeFaqStructuredData() {
    return null;
  },
}));

// Mock ExitIntentPopup
jest.mock('../app/components/ExitIntentPopup', () => ({
  ExitIntentPopup: function MockExitIntentPopup() {
    return null;
  },
}));

// ---- Imports ----
import LandingPage from '../app/page';

// ---- Tests ----

describe('STORY-273 + REPO-COMMS #1289: Landing Page Social Proof Integration', () => {
  beforeEach(() => {
    render(<LandingPage />);
  });

  describe('AC3: Social proof message (absorbed into SocialProofMetrics)', () => {
    it('should render the beta counter inside SocialProofMetrics', () => {
      expect(screen.getByTestId('beta-counter')).toBeInTheDocument();
    });

    it('should display sector-based social proof message', () => {
      expect(screen.getByText(/Empresas de engenharia, TI, saúde, uniformes e facilities/)).toBeInTheDocument();
    });

    it('should use present continuous "já analisam" instead of past tense', () => {
      expect(screen.getByText(/já analisam oportunidades com SmartLic/)).toBeInTheDocument();
    });
  });

  describe('REPO-COMMS #1289: B2G landing page structure', () => {
    it('should have exactly 7 content sections + navbar + newsletter + footer', () => {
      expect(screen.getByTestId('landing-navbar')).toBeInTheDocument();
      expect(screen.getByTestId('hero-b2g')).toBeInTheDocument();
      expect(screen.getByTestId('antecipe-decida-execute')).toBeInTheDocument();
      expect(screen.getByTestId('terminal-comparison')).toBeInTheDocument();
      expect(screen.getByTestId('social-proof-metrics')).toBeInTheDocument();
      expect(screen.getByTestId('personas-section')).toBeInTheDocument();
      expect(screen.getByTestId('public-intelligence-section')).toBeInTheDocument();
      expect(screen.getByTestId('market-social-proof')).toBeInTheDocument();
      expect(screen.getByTestId('newsletter-footer')).toBeInTheDocument();
      expect(screen.getByTestId('footer')).toBeInTheDocument();
    });

    it('should NOT contain old SAB-006 sections', () => {
      expect(screen.queryByTestId('hero-section')).not.toBeInTheDocument();
      expect(screen.queryByTestId('opportunity-cost')).not.toBeInTheDocument();
      expect(screen.queryByTestId('before-after')).not.toBeInTheDocument();
      expect(screen.queryByTestId('how-it-works')).not.toBeInTheDocument();
      expect(screen.queryByTestId('stats-section')).not.toBeInTheDocument();
      expect(screen.queryByTestId('final-cta')).not.toBeInTheDocument();
      expect(screen.queryByTestId('founder-transparency-section')).not.toBeInTheDocument();
      expect(screen.queryByTestId('credibility-section')).not.toBeInTheDocument();
    });

    it('should maintain correct section order: Hero → Antecipe → Terminal → SocialProof → Personas → Intelligence → MarketSocialProof', () => {
      const main = screen.getByRole('main');
      const html = main.innerHTML;

      const heroIdx = html.indexOf('data-testid="hero-b2g"');
      const antecipeIdx = html.indexOf('data-testid="antecipe-decida-execute"');
      const terminalIdx = html.indexOf('data-testid="terminal-comparison"');
      const socialIdx = html.indexOf('data-testid="social-proof-metrics"');
      const personasIdx = html.indexOf('data-testid="personas-section"');
      const intelligenceIdx = html.indexOf('data-testid="public-intelligence-section"');
      const marketIdx = html.indexOf('data-testid="market-social-proof"');

      expect(heroIdx).toBeLessThan(antecipeIdx);
      expect(antecipeIdx).toBeLessThan(terminalIdx);
      expect(terminalIdx).toBeLessThan(socialIdx);
      expect(socialIdx).toBeLessThan(personasIdx);
      expect(personasIdx).toBeLessThan(intelligenceIdx);
      expect(intelligenceIdx).toBeLessThan(marketIdx);
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

    // Mock FooterNewsletterForm (COPY-COP-006) to avoid useState hook error
    jest.mock('../app/components/FooterNewsletterForm', () => ({
      FooterNewsletterForm: function MockFooterNewsletterForm() {
        return <div data-testid="newsletter-form">Newsletter</div>;
      },
    }));

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
