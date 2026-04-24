/**
 * STORY-273 AC4: /sobre page tests
 *
 * Tests:
 * - Page renders without error
 * - All required sections present (Quem Somos, Team, Mission, Methodology, Data Sources, Contact)
 * - SEO metadata
 * - Contact information visible
 */

import { render, screen } from '@testing-library/react';

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

// Mock Footer (uses framer-motion and copy imports)
jest.mock('../app/components/Footer', () => {
  return function MockFooter() {
    return <footer data-testid="footer">Footer</footer>;
  };
});

// Mock LandingNavbar
jest.mock('../app/components/landing/LandingNavbar', () => {
  return function MockLandingNavbar() {
    return <nav data-testid="landing-navbar">Navbar</nav>;
  };
});

import SobrePage from '../app/sobre/page';

describe('STORY-273 AC4: /sobre page', () => {
  beforeEach(() => {
    render(<SobrePage />);
  });

  it('should render without error', () => {
    expect(screen.getByText('Sobre o SmartLic')).toBeInTheDocument();
  });

  describe('Quem Somos section', () => {
    it('should display CONFENGE description', () => {
      expect(screen.getByText('Quem somos')).toBeInTheDocument();
      const confengeElements = screen.getAllByText(/CONFENGE Avaliações e Inteligência Artificial/);
      expect(confengeElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Team section (STORY-273)', () => {
    it('should display team section', () => {
      expect(screen.getByText('Nosso time')).toBeInTheDocument();
    });

    it('should mention engineering and AI expertise', () => {
      expect(screen.getByText('Engenharia e IA')).toBeInTheDocument();
    });

    it('should mention B2G market experience', () => {
      expect(screen.getByText('Mercado B2G')).toBeInTheDocument();
    });
  });

  describe('Mission section (STORY-273)', () => {
    it('should display mission section', () => {
      expect(screen.getByText('Nossa missão')).toBeInTheDocument();
    });

    it('should describe the mission', () => {
      expect(screen.getByText(/Democratizar o acesso inteligente a licitações públicas/)).toBeInTheDocument();
    });
  });

  describe('Problem section', () => {
    it('should display the problem section', () => {
      expect(screen.getByText('O problema que resolvemos')).toBeInTheDocument();
    });
  });

  describe('Methodology section', () => {
    it('should display methodology heading', () => {
      expect(screen.getByText('Como avaliamos cada oportunidade')).toBeInTheDocument();
    });

    it('should list evaluation criteria', () => {
      expect(screen.getByText('Compatibilidade setorial')).toBeInTheDocument();
      expect(screen.getByText('Faixa de valor adequada')).toBeInTheDocument();
      expect(screen.getByText('Prazo para preparação')).toBeInTheDocument();
      expect(screen.getByText('Região de atuação')).toBeInTheDocument();
      expect(screen.getByText('Modalidade favorável')).toBeInTheDocument();
    });
  });

  describe('Data Sources section', () => {
    it('should display data sources', () => {
      expect(screen.getByText('Fontes de dados')).toBeInTheDocument();
      expect(screen.getByText(/portais oficiais de contratações públicas/)).toBeInTheDocument();
    });
  });

  describe('Contact section (STORY-273)', () => {
    it('should display contact heading', () => {
      expect(screen.getByText('Contato')).toBeInTheDocument();
    });

    it('should display company address', () => {
      expect(screen.getByText(/Av. Pref. Osmar Cunha, 416/)).toBeInTheDocument();
      expect(screen.getByText(/Florianópolis - SC/)).toBeInTheDocument();
    });

    it('should link to help center', () => {
      const helpLink = screen.getByRole('link', { name: 'Central de Ajuda' });
      expect(helpLink).toHaveAttribute('href', '/ajuda#contato');
    });
  });

  describe('CTA section', () => {
    it('should display call-to-action', () => {
      expect(screen.getByText('Experimente com seus próprios dados')).toBeInTheDocument();
    });

    it('should have signup link', () => {
      const ctaLink = screen.getByRole('link', { name: /Analisar oportunidades/ });
      expect(ctaLink).toHaveAttribute('href', '/signup?source=sobre-cta');
    });
  });

  describe('Navigation', () => {
    it('should include navbar', () => {
      expect(screen.getByTestId('landing-navbar')).toBeInTheDocument();
    });

    it('should include footer', () => {
      expect(screen.getByTestId('footer')).toBeInTheDocument();
    });
  });
});

describe('/sobre metadata export', () => {
  it('should export metadata with title and description', async () => {
    // Import the module to check metadata export
    const module = await import('../app/sobre/page');
    expect(module.metadata).toBeDefined();
    expect(module.metadata.title).toContain('Metodologia');
    expect(module.metadata.description).toBeTruthy();
  });
});
