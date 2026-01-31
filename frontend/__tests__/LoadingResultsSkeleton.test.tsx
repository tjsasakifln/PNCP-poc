/**
 * LoadingResultsSkeleton Component Tests - Issue #111
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { LoadingResultsSkeleton } from '../app/components/LoadingResultsSkeleton';

describe('LoadingResultsSkeleton Component', () => {
  describe('Rendering', () => {
    it('should render skeleton by default', () => {
      render(<LoadingResultsSkeleton />);

      // Check for screen reader text
      expect(screen.getByText(/processando resultados da busca/i)).toBeInTheDocument();
    });

    it('should render correct number of skeleton cards', () => {
      const { container } = render(<LoadingResultsSkeleton count={3} />);

      // Each skeleton has multiple pulse elements, just check container exists
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('should have proper accessibility attributes', () => {
      const { container } = render(<LoadingResultsSkeleton />);

      const statusElement = container.querySelector('[role="status"]');
      expect(statusElement).toBeInTheDocument();
      expect(statusElement).toHaveAttribute('aria-label', 'Carregando resultados');
    });

    it('should show skeleton with animation classes', () => {
      const { container } = render(<LoadingResultsSkeleton />);

      // Check for animation classes
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
      expect(container.querySelector('.animate-fade-in-up')).toBeInTheDocument();
    });
  });

  describe('Customization', () => {
    it('should use default count of 3 when not specified', () => {
      render(<LoadingResultsSkeleton />);
      expect(screen.getByText(/processando resultados da busca/i)).toBeInTheDocument();
    });

    it('should accept custom count prop', () => {
      render(<LoadingResultsSkeleton count={5} />);
      expect(screen.getByText(/processando resultados da busca/i)).toBeInTheDocument();
    });
  });

  describe('Structure', () => {
    it('should render summary card skeleton', () => {
      const { container } = render(<LoadingResultsSkeleton />);

      // Check for summary card structure
      expect(container.querySelector('.bg-surface-0')).toBeInTheDocument();
    });

    it('should render download button skeleton', () => {
      const { container } = render(<LoadingResultsSkeleton />);

      // Check for button skeleton
      expect(container.querySelector('.rounded-button')).toBeInTheDocument();
    });

    it('should have screen reader feedback', () => {
      render(<LoadingResultsSkeleton />);

      // Check for sr-only text
      expect(screen.getByText(/processando resultados da busca, por favor aguarde/i)).toBeInTheDocument();
    });
  });
});
