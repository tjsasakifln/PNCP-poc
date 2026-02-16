/**
 * Tests for QuotaBadge component
 *
 * Tests credits display, plan badges, admin badge, and formatting
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { QuotaBadge } from '../../app/components/QuotaBadge';

// Mock useAuth hook
const mockUseAuth = jest.fn();
jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock useQuota hook
const mockUseQuota = jest.fn();
jest.mock('../../hooks/useQuota', () => ({
  useQuota: () => mockUseQuota(),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return function MockLink({ children, href, className, title }: {
    children: React.ReactNode;
    href: string;
    className?: string;
    title?: string;
  }) {
    return <a href={href} className={className} title={title}>{children}</a>;
  };
});

describe('QuotaBadge Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Not logged in', () => {
    it('should return null when user is not logged in', () => {
      mockUseAuth.mockReturnValue({ user: null });
      mockUseQuota.mockReturnValue({ quota: null, loading: false });

      const { container } = render(<QuotaBadge />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Loading state', () => {
    it('should show skeleton loader while loading', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({ quota: null, loading: true });

      const { container } = render(<QuotaBadge />);

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });
  });

  describe('No quota info', () => {
    it('should return null when quota is null after loading', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({ quota: null, loading: false });

      const { container } = render(<QuotaBadge />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Admin users', () => {
    it('should show admin badge for admin users', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'admin-1' } });
      mockUseQuota.mockReturnValue({
        quota: { isAdmin: true },
        loading: false,
      });

      render(<QuotaBadge />);

      expect(screen.getByText('Admin')).toBeInTheDocument();
    });

    it('should have correct title for admin badge', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'admin-1' } });
      mockUseQuota.mockReturnValue({
        quota: { isAdmin: true },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByTitle('Acesso Administrativo');
      expect(badge).toBeInTheDocument();
    });

    it('should apply purple styling for admin badge', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'admin-1' } });
      mockUseQuota.mockReturnValue({
        quota: { isAdmin: true },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByText('Admin');
      // Check the badge element or its parent has the expected classes
      const badgeContainer = badge.closest('span');
      expect(badgeContainer?.className).toContain('purple');
    });
  });

  describe('Unlimited plan users', () => {
    it('should show plan name for unlimited users', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: { isAdmin: false, isUnlimited: true, planName: 'Máquina' },
        loading: false,
      });

      render(<QuotaBadge />);

      expect(screen.getByText('Máquina')).toBeInTheDocument();
    });

    it('should show correct title with plan name', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: { isAdmin: false, isUnlimited: true, planName: 'Consultor Ágil' },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByTitle('Plano Consultor Ágil');
      expect(badge).toBeInTheDocument();
    });

    it('should apply brand styling for unlimited badge', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: { isAdmin: false, isUnlimited: true, planName: 'Sala de Guerra' },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByText('Sala de Guerra');
      const badgeContainer = badge.closest('span');
      expect(badgeContainer?.className).toContain('brand');
    });
  });

  describe('Credit-based users - credits remaining', () => {
    it('should show credits count with "análises" suffix', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 5,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      expect(screen.getByText(/5 análises/)).toBeInTheDocument();
    });

    it('should show "análises" suffix for free users', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: true,
          creditsRemaining: 3,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      expect(screen.getByText(/3 análises/)).toBeInTheDocument();
    });

    it('should use singular "análise" in title when 1 credit remaining', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 1,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByTitle('1 análise restante');
      expect(badge).toBeInTheDocument();
    });

    it('should use plural "análises" in title when multiple credits remaining', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 10,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByTitle('10 análises restantes');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Low credits warning', () => {
    it('should apply warning styling when 1 credit remaining', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 1,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByText(/1 análises/);
      const badgeContainer = badge.closest('span');
      expect(badgeContainer?.className).toContain('warning');
    });

    it('should apply normal styling when more than 1 credit', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 5,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByText(/5 análises/);
      const badgeContainer = badge.closest('span');
      expect(badgeContainer?.className).toContain('surface');
      expect(badgeContainer?.className).not.toContain('warning');
    });
  });

  describe('Empty credits state', () => {
    it('should show "0 análises" when credits are exhausted', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 0,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      expect(screen.getByText('0 análises')).toBeInTheDocument();
    });

    it('should link to plans page when credits are exhausted', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 0,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/planos');
    });

    it('should show helpful title when credits are exhausted', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 0,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const link = screen.getByTitle('Suas análises acabaram. Clique para ver opções.');
      expect(link).toBeInTheDocument();
    });

    it('should apply error styling when credits are exhausted', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: 0,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      const badge = screen.getByText('0 análises');
      const badgeContainer = badge.closest('a');
      expect(badgeContainer?.className).toContain('error');
    });
  });

  describe('Edge cases', () => {
    it('should handle undefined creditsRemaining as 0', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: undefined,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      // Should show empty state (0 credits)
      expect(screen.getByText('0 análises')).toBeInTheDocument();
    });

    it('should handle null creditsRemaining as 0', () => {
      mockUseAuth.mockReturnValue({ user: { id: 'user-1' } });
      mockUseQuota.mockReturnValue({
        quota: {
          isAdmin: false,
          isUnlimited: false,
          isFreeUser: false,
          creditsRemaining: null,
        },
        loading: false,
      });

      render(<QuotaBadge />);

      // Should show empty state (0 credits)
      expect(screen.getByText('0 análises')).toBeInTheDocument();
    });
  });
});
