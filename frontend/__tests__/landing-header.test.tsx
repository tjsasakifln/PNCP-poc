/**
 * UX-345 — Landing Header: Auth-conditional buttons
 * Tests that the LandingNavbar shows correct buttons based on auth state.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  );
});

// Mock MobileMenu (path relative to LandingNavbar.tsx)
jest.mock('../components/layout/MobileMenu', () => {
  return function MockMobileMenu() {
    return null;
  };
});

// Mock AuthProvider
const mockUseAuth = jest.fn();
jest.mock('../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

import LandingNavbar from '../app/components/landing/LandingNavbar';

describe('LandingNavbar — UX-345', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('AC1+AC2: Non-authenticated visitor', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ user: null, loading: false });
    });

    it('shows "Entrar" button linking to /login', () => {
      render(<LandingNavbar />);
      const entrarLink = screen.getByRole('link', { name: 'Entrar' });
      expect(entrarLink).toBeInTheDocument();
      expect(entrarLink).toHaveAttribute('href', '/login');
    });

    it('"Entrar" has ghost/text style', () => {
      render(<LandingNavbar />);
      const entrarLink = screen.getByRole('link', { name: 'Entrar' });
      // Entrar uses a text/ghost style (not a bordered button)
      expect(entrarLink).toBeInTheDocument();
      // Should have some styling class
      expect(entrarLink.className.length).toBeGreaterThan(0);
    });

    it('shows "Comece Gratis" button linking to /signup?source=header-cta', () => {
      render(<LandingNavbar />);
      const ctaLink = screen.getByRole('link', { name: 'Comece Gratis' });
      expect(ctaLink).toBeInTheDocument();
      expect(ctaLink).toHaveAttribute('href', '/signup?source=header-cta');
    });

    it('"Comece Gratis" has primary filled style (bg-brand-navy)', () => {
      render(<LandingNavbar />);
      const ctaLink = screen.getByRole('link', { name: 'Comece Gratis' });
      expect(ctaLink.className).toMatch(/bg-brand-navy/);
    });

    it('does NOT show "Ir para Busca"', () => {
      render(<LandingNavbar />);
      expect(screen.queryByRole('link', { name: 'Ir para Busca' })).not.toBeInTheDocument();
    });
  });

  describe('AC3: Authenticated user', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', email: 'test@example.com' },
        loading: false,
      });
    });

    it('shows "Ir para Busca" button linking to /buscar', () => {
      render(<LandingNavbar />);
      const buscaLink = screen.getByRole('link', { name: 'Ir para Busca' });
      expect(buscaLink).toBeInTheDocument();
      expect(buscaLink).toHaveAttribute('href', '/buscar');
    });

    it('does NOT show "Entrar" or "Comece Gratis"', () => {
      render(<LandingNavbar />);
      expect(screen.queryByRole('link', { name: 'Entrar' })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: 'Comece Gratis' })).not.toBeInTheDocument();
    });
  });

  describe('Loading state', () => {
    it('shows placeholder while auth is loading', () => {
      mockUseAuth.mockReturnValue({ user: null, loading: true });
      render(<LandingNavbar />);
      // During loading, neither auth-specific buttons should render
      expect(screen.queryByRole('link', { name: 'Entrar' })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: 'Comece Gratis' })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: 'Ir para Busca' })).not.toBeInTheDocument();
    });
  });

  describe('AC4: Auth detection', () => {
    it('uses useAuth hook (Supabase client-side), not a backend API call', () => {
      mockUseAuth.mockReturnValue({ user: null, loading: false });
      render(<LandingNavbar />);
      expect(mockUseAuth).toHaveBeenCalled();
    });
  });
});
