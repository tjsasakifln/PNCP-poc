/**
 * LandingNavbar Component Tests
 * STORY-223 AC21-AC24: Auth-aware CTA rendering
 *
 * Tests:
 * - AC21: Component uses useAuth hook
 * - AC22: Logged-in user sees "Ir para Busca" button
 * - AC23: Not-logged-in user sees "Entrar" and "Criar conta"
 * - AC24: Loading state has no layout shift (placeholder rendered)
 */

import { render, screen } from '@testing-library/react';
import LandingNavbar from '@/app/components/landing/LandingNavbar';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ children, href, className }: { children: React.ReactNode; href: string; className?: string }) {
    return <a href={href} className={className}>{children}</a>;
  };
});

describe('LandingNavbar Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('AC21: useAuth integration', () => {
    it('should call useAuth hook', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
      });

      render(<LandingNavbar />);

      expect(mockUseAuth).toHaveBeenCalled();
    });
  });

  describe('AC24: Loading state - no layout shift', () => {
    it('should render placeholder div during loading to prevent layout shift', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
      });

      const { container } = render(<LandingNavbar />);

      // Check for placeholder div with width
      const placeholder = container.querySelector('.w-\\[180px\\]');
      expect(placeholder).toBeInTheDocument();

      // Should NOT show Login or Criar conta during loading
      expect(screen.queryByRole('link', { name: /Login/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Criar conta/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Ir para Busca/i })).not.toBeInTheDocument();
    });
  });

  describe('AC23: Not-logged-in user state', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
      });
    });

    it('should show Login link when not authenticated', () => {
      render(<LandingNavbar />);

      const loginLink = screen.getByRole('link', { name: /Login/i });
      expect(loginLink).toBeInTheDocument();
      expect(loginLink).toHaveAttribute('href', '/login');
    });

    it('should show Criar conta link when not authenticated', () => {
      render(<LandingNavbar />);

      const signupLink = screen.getByRole('link', { name: /Criar conta/i });
      expect(signupLink).toBeInTheDocument();
      expect(signupLink).toHaveAttribute('href', '/signup?source=landing-cta');
    });

    it('should NOT show "Ir para Busca" when not authenticated', () => {
      render(<LandingNavbar />);

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
      render(<LandingNavbar />);

      const buscarLink = screen.getByRole('link', { name: /Ir para Busca/i });
      expect(buscarLink).toBeInTheDocument();
      expect(buscarLink).toHaveAttribute('href', '/buscar');
    });

    it('should NOT show Login link when authenticated', () => {
      render(<LandingNavbar />);

      expect(screen.queryByRole('link', { name: /^Login$/i })).not.toBeInTheDocument();
    });

    it('should NOT show Criar conta link when authenticated', () => {
      render(<LandingNavbar />);

      expect(screen.queryByRole('link', { name: /Criar conta/i })).not.toBeInTheDocument();
    });

    it('should maintain button styling consistency for logged-in state', () => {
      render(<LandingNavbar />);

      const buscarLink = screen.getByRole('link', { name: /Ir para Busca/i });

      // Check that button has the primary CTA styling classes
      const className = buscarLink.className;
      expect(className).toContain('bg-brand-navy');
      expect(className).toContain('text-white');
      expect(className).toContain('rounded-button');
      expect(className).toContain('font-semibold');
    });
  });

  describe('Common navigation elements', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
      });
    });

    it('should always show SmartLic logo', () => {
      render(<LandingNavbar />);

      // Note: Logo text has a space due to span: "SmartLic .tech"
      const logo = screen.getByRole('link', { name: /SmartLic/i });
      expect(logo).toBeInTheDocument();
      expect(logo).toHaveAttribute('href', '/');
      expect(logo).toHaveTextContent('SmartLic.tech');
    });

    it('should show Planos link', () => {
      render(<LandingNavbar />);

      const planosLink = screen.getByRole('link', { name: /^Planos$/i });
      expect(planosLink).toBeInTheDocument();
      expect(planosLink).toHaveAttribute('href', '/planos');
    });

    it('should show Como Funciona button', () => {
      render(<LandingNavbar />);

      const comoFuncionaBtn = screen.getByRole('button', { name: /Como Funciona/i });
      expect(comoFuncionaBtn).toBeInTheDocument();
    });
  });

  describe('Scroll behavior', () => {
    it('should render sticky header', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
      });

      const { container } = render(<LandingNavbar />);

      const header = container.querySelector('header');
      expect(header).toHaveClass('sticky');
      expect(header).toHaveClass('top-0');
      expect(header).toHaveClass('z-50');
    });
  });
});
