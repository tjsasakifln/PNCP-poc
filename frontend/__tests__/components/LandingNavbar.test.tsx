/**
 * LandingNavbar Component Tests
 * STORY-223 AC21-AC24: Auth-aware CTA rendering
 * DEBT-v3-S2 AC20: Updated for RSC + client island architecture.
 * REPO-010: Soluções dropdown + Consultoria nav item.
 *
 * LandingNavbar is now an RSC that delegates interactive parts to NavbarClientIsland.tsx.
 * Tests focus on the client islands (NavbarAuthCTA, NavSolucoesDropdown, NavbarMobileControls)
 * since RSCs render static HTML that is always present.
 *
 * Tests:
 * - AC21: Component uses useAuth hook (via NavbarAuthCTA)
 * - AC22: Logged-in user sees "Ir para Busca" button
 * - AC23: Not-logged-in user sees "Entrar" and "Comece Gratis" (UX-345)
 * - AC24: Loading state has no layout shift (placeholder rendered)
 * - REPO-010: Soluções dropdown renders 4 items, Consultoria link present
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { NavbarAuthCTA, NavScrollButton, NavSolucoesDropdown } from '@/app/components/landing/NavbarClientIsland';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ children, href, className, 'data-testid': dataTestId, role, onClick, ...props }: { children: React.ReactNode; href: string; className?: string; 'data-testid'?: string; role?: string; onClick?: () => void; [key: string]: unknown }) {
    return <a href={href} className={className} data-testid={dataTestId} role={role} onClick={onClick} {...props}>{children}</a>;
  };
});

describe('LandingNavbar — NavbarAuthCTA (client island)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('AC21: useAuth integration', () => {
    it('should call useAuth hook', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
      });

      render(<NavbarAuthCTA />);

      expect(mockUseAuth).toHaveBeenCalled();
    });
  });

  describe('AC24: Loading state - no layout shift', () => {
    it('should render placeholder div during loading to prevent layout shift', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
      });

      const { container } = render(<NavbarAuthCTA />);

      // Check for placeholder div with width
      const placeholder = container.querySelector('.w-\\[160px\\]');
      expect(placeholder).toBeInTheDocument();

      // Should NOT show Entrar or Comece Gratis during loading
      expect(screen.queryByRole('link', { name: /Entrar/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Comece Gratis/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Diagnóstico CONFENGE/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Ir para Busca/i })).not.toBeInTheDocument();
    });
  });

  describe('AC23: Not-logged-in user state (UX-345 updated copy)', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
      });
    });

    it('should show "Entrar" link when not authenticated', () => {
      render(<NavbarAuthCTA />);

      const entrarLink = screen.getByRole('link', { name: /Entrar/i });
      expect(entrarLink).toBeInTheDocument();
      expect(entrarLink).toHaveAttribute('href', '/login');
    });

    it('should show CONFENGE diagnostic CTA when not authenticated', () => {
      render(<NavbarAuthCTA />);

      const signupLink = screen.getByRole('link', { name: /Diagnóstico CONFENGE/i });
      expect(signupLink).toBeInTheDocument();
      expect(signupLink).toHaveAttribute('href', '/consultoria-b2g?cta=cta.home.diagnostico');
    });

    it('should NOT show "Ir para Busca" when not authenticated', () => {
      render(<NavbarAuthCTA />);

      expect(screen.queryByRole('link', { name: /Ir para Busca/i })).not.toBeInTheDocument();
    });
  });

  describe('AC22: Logged-in user state', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { email: 'test@example.com', id: '123' },
        loading: false,
      });
    });

    it('should show "Ir para Busca" button when authenticated', () => {
      render(<NavbarAuthCTA />);

      const buscarLink = screen.getByRole('link', { name: /Ir para Busca/i });
      expect(buscarLink).toBeInTheDocument();
      expect(buscarLink).toHaveAttribute('href', '/buscar');
    });

    it('should NOT show "Entrar" link when authenticated', () => {
      render(<NavbarAuthCTA />);

      expect(screen.queryByRole('link', { name: /Entrar/i })).not.toBeInTheDocument();
    });

    it('should NOT show "Comece Gratis" link when authenticated', () => {
      render(<NavbarAuthCTA />);

      expect(screen.queryByRole('link', { name: /Comece Gratis/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Diagnóstico CONFENGE/i })).not.toBeInTheDocument();
    });

    it('should maintain button styling consistency for logged-in state', () => {
      render(<NavbarAuthCTA />);

      const buscarLink = screen.getByRole('link', { name: /Ir para Busca/i });

      // Check that button has the primary CTA styling classes
      const className = buscarLink.className;
      expect(className).toContain('bg-brand-navy');
      expect(className).toContain('text-white');
      expect(className).toContain('rounded-button');
      expect(className).toContain('font-medium');
    });
  });
});

describe('LandingNavbar — NavScrollButton (client island)', () => {
  it('should render a scroll-to-section button with given label', () => {
    render(<NavScrollButton sectionId="como-funciona" label="Como Funciona" />);

    const btn = screen.getByRole('button', { name: /Como Funciona/i });
    expect(btn).toBeInTheDocument();
  });
});

describe('LandingNavbar — NavSolucoesDropdown (REPO-010)', () => {
  it('should render dropdown trigger with correct data-testid', () => {
    render(<NavSolucoesDropdown />);

    const trigger = screen.getByTestId('nav-solucoes-dropdown');
    expect(trigger).toBeInTheDocument();
    expect(trigger).toHaveTextContent('Soluções');
  });

  it('should have aria-haspopup and aria-expanded=false by default', () => {
    render(<NavSolucoesDropdown />);

    const trigger = screen.getByTestId('nav-solucoes-dropdown');
    expect(trigger).toHaveAttribute('aria-haspopup', 'true');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });

  it('should show 4 items when dropdown is opened', () => {
    render(<NavSolucoesDropdown />);

    const trigger = screen.getByTestId('nav-solucoes-dropdown');
    fireEvent.click(trigger);

    expect(screen.getByRole('menuitem', { name: /Licitações/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /Contratos/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /Empresas/i })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /Consultoria CONFENGE/i })).toBeInTheDocument();
  });

  it('should have correct hrefs for all dropdown items', () => {
    render(<NavSolucoesDropdown />);

    fireEvent.click(screen.getByTestId('nav-solucoes-dropdown'));

    expect(screen.getByRole('menuitem', { name: /Licitações/i })).toHaveAttribute('href', '/licitacoes');
    expect(screen.getByRole('menuitem', { name: /Contratos/i })).toHaveAttribute('href', '/contratos');
    expect(screen.getByRole('menuitem', { name: /Empresas/i })).toHaveAttribute('href', '/cnpj');
    expect(screen.getByRole('menuitem', { name: /Consultoria CONFENGE/i })).toHaveAttribute('href', '/consultoria-b2g');
  });

  it('should toggle aria-expanded when clicked', () => {
    render(<NavSolucoesDropdown />);

    const trigger = screen.getByTestId('nav-solucoes-dropdown');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');

    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });

  it('should close dropdown when a menu item is clicked', () => {
    render(<NavSolucoesDropdown />);

    fireEvent.click(screen.getByTestId('nav-solucoes-dropdown'));
    expect(screen.getByRole('menu')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('menuitem', { name: /Licitações/i }));
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});

describe('LandingNavbar — Static RSC elements', () => {
  // These test the RSC output. Since RSC imports client islands,
  // we test LandingNavbar as a whole (it renders fine in Jest since
  // there's no actual server boundary in test — all code runs in jsdom).
  // Import the full component for integration-level checks.
  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
    });
  });

  // We import dynamically to avoid module-level execution issues
  // with the RSC that imports client islands
  const LandingNavbar = require('@/app/components/landing/LandingNavbar').default;

  it('should always show SmartLic logo', () => {
    render(<LandingNavbar />);

    const logo = screen.getByRole('link', { name: /SmartLic/i });
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('href', '/');
    expect(logo).toHaveTextContent('SmartLic.tech');
  });

  it('should show Licitações link instead of Planos', () => {
    render(<LandingNavbar />);

    const licitacoesLink = screen.getByRole('link', { name: /^Licitações$/i });
    expect(licitacoesLink).toBeInTheDocument();
    expect(licitacoesLink).toHaveAttribute('href', '/licitacoes');
  });

  it('should show Consultoria link with correct data-testid (REPO-010)', () => {
    render(<LandingNavbar />);

    const consultoriaLink = screen.getByTestId('nav-consultoria');
    expect(consultoriaLink).toBeInTheDocument();
    expect(consultoriaLink).toHaveAttribute('href', '/consultoria-b2g');
    expect(consultoriaLink).toHaveTextContent('Consultoria');
  });

  it('should show Soluções dropdown trigger (REPO-010)', () => {
    render(<LandingNavbar />);

    // Multiple triggers may exist (desktop dropdown)
    const triggers = screen.getAllByTestId('nav-solucoes-dropdown');
    expect(triggers.length).toBeGreaterThanOrEqual(1);
    expect(triggers[0]).toHaveTextContent('Soluções');
  });

  it('should NOT show removed nav items (REPO-010)', () => {
    render(<LandingNavbar />);

    expect(screen.queryByRole('link', { name: /^Casos$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Suporte$/i })).not.toBeInTheDocument();
  });

  it('should render sticky header', () => {
    const { container } = render(<LandingNavbar />);

    const header = container.querySelector('header');
    expect(header).toHaveClass('sticky');
    expect(header).toHaveClass('top-0');
    expect(header).toHaveClass('z-50');
  });
});
