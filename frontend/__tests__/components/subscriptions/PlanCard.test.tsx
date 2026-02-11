/**
 * PlanCard Component Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
 * Tests plan card with dynamic pricing calculation
 */

import { render, screen } from '@testing-library/react';
import { PlanCard } from '@/components/subscriptions/PlanCard';

describe('PlanCard Component', () => {
  const defaultProps = {
    id: 'consultor_agil',
    name: 'Consultor Ágil',
    monthlyPrice: 297,
    billingPeriod: 'monthly' as const,
    features: [
      'Busca ilimitada',
      'Exportar Excel',
      'Resumo IA',
    ],
  };

  describe('Monthly Pricing', () => {
    it('should display monthly price correctly', () => {
      render(<PlanCard {...defaultProps} />);

      expect(screen.getByText(/R\$\s*297,00/)).toBeInTheDocument();
      expect(screen.getByText('/mês')).toBeInTheDocument();
    });

    it('should not show savings badge when monthly', () => {
      render(<PlanCard {...defaultProps} />);

      expect(screen.queryByText(/Economize 20%/i)).not.toBeInTheDocument();
    });

    it('should not show monthly equivalent when monthly', () => {
      render(<PlanCard {...defaultProps} />);

      expect(screen.queryByText(/Equivalente a/i)).not.toBeInTheDocument();
    });
  });

  describe('Annual Pricing (20% Discount)', () => {
    it('should calculate annual price correctly (9.6x monthly)', () => {
      render(<PlanCard {...defaultProps} billingPeriod="annual" />);

      // 297 * 9.6 = 2,851.20 (may appear multiple times in the card)
      expect(screen.getAllByText(/R\$\s*2\.851,20/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('/ano')).toBeInTheDocument();
    });

    it('should show monthly equivalent', () => {
      render(<PlanCard {...defaultProps} billingPeriod="annual" />);

      // 2,851.20 / 12 = 237.60 (may appear multiple times)
      expect(screen.getAllByText(/R\$\s*237,60\/mês/).length).toBeGreaterThanOrEqual(1);
    });

    it('should show 20% savings badge', () => {
      render(<PlanCard {...defaultProps} billingPeriod="annual" />);

      expect(screen.getByText('Economize 20%')).toBeInTheDocument();
    });

    it('should calculate savings correctly in tooltip', () => {
      render(<PlanCard {...defaultProps} billingPeriod="annual" />);

      // Monthly: 297 * 12 = 3,564
      // Annual: 2,851.20
      // Savings: 712.80
      const tooltip = screen.getByText(/Você economiza:/);
      expect(tooltip).toBeInTheDocument();
      expect(screen.getByText(/R\$\s*712,80/)).toBeInTheDocument();
    });
  });

  describe('Different Plans - Annual Pricing', () => {
    it('should calculate Máquina annual price correctly', () => {
      render(
        <PlanCard
          {...defaultProps}
          id="maquina"
          name="Máquina"
          monthlyPrice={597}
          billingPeriod="annual"
        />
      );

      // 597 * 9.6 = 5,731.20 (may appear multiple times)
      expect(screen.getAllByText(/R\$\s*5\.731,20/).length).toBeGreaterThanOrEqual(1);
    });

    it('should calculate Sala de Guerra annual price correctly', () => {
      render(
        <PlanCard
          {...defaultProps}
          id="sala_guerra"
          name="Sala de Guerra"
          monthlyPrice={1497}
          billingPeriod="annual"
        />
      );

      // 1497 * 9.6 = 14,371.20 (may appear multiple times)
      expect(screen.getAllByText(/R\$\s*14\.371,20/).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Features Display', () => {
    it('should display all features', () => {
      render(<PlanCard {...defaultProps} />);

      expect(screen.getByText('Busca ilimitada')).toBeInTheDocument();
      expect(screen.getByText('Exportar Excel')).toBeInTheDocument();
      expect(screen.getByText('Resumo IA')).toBeInTheDocument();
    });

    it('should show checkmark icon for each feature', () => {
      const { container } = render(<PlanCard {...defaultProps} />);

      const checkmarks = container.querySelectorAll('svg');
      // At least 3 checkmarks (one per feature)
      expect(checkmarks.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Highlighting', () => {
    it('should apply highlighted styles when highlighted prop is true', () => {
      const { container } = render(<PlanCard {...defaultProps} highlighted={true} />);

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('border-brand-blue', 'shadow-lg', 'scale-105');
    });

    it('should not apply highlighted styles by default', () => {
      const { container } = render(<PlanCard {...defaultProps} />);

      const card = container.firstChild as HTMLElement;
      expect(card).not.toHaveClass('border-brand-blue');
      expect(card).toHaveClass('border-strong');
    });
  });

  describe('CTA Button', () => {
    it('should render button when onSelect is provided', () => {
      const mockOnSelect = jest.fn();
      render(<PlanCard {...defaultProps} onSelect={mockOnSelect} />);

      expect(screen.getByText('Selecionar Plano')).toBeInTheDocument();
    });

    it('should not render button when onSelect is not provided', () => {
      render(<PlanCard {...defaultProps} />);

      expect(screen.queryByText('Selecionar Plano')).not.toBeInTheDocument();
    });

    it('should call onSelect when button is clicked', () => {
      const mockOnSelect = jest.fn();
      render(<PlanCard {...defaultProps} onSelect={mockOnSelect} />);

      const button = screen.getByText('Selecionar Plano');
      button.click();

      expect(mockOnSelect).toHaveBeenCalledTimes(1);
    });

    it('should have highlighted button style when card is highlighted', () => {
      const mockOnSelect = jest.fn();
      render(<PlanCard {...defaultProps} onSelect={mockOnSelect} highlighted={true} />);

      const button = screen.getByText('Selecionar Plano');
      expect(button).toHaveClass('bg-brand-navy', 'text-white');
    });
  });

  describe('Price Formatting', () => {
    it('should format prices with BRL currency', () => {
      render(<PlanCard {...defaultProps} monthlyPrice={1234.56} />);

      expect(screen.getByText(/R\$/)).toBeInTheDocument();
      expect(screen.getByText(/1\.234,56/)).toBeInTheDocument();
    });

    it('should use comma as decimal separator', () => {
      render(<PlanCard {...defaultProps} monthlyPrice={297} />);

      // Brazilian format uses comma
      expect(screen.getByText(/297,00/)).toBeInTheDocument();
    });

    it('should use dot as thousands separator', () => {
      render(<PlanCard {...defaultProps} monthlyPrice={1497} billingPeriod="annual" />);

      // 1497 * 9.6 = 14,371.20 (may appear multiple times)
      expect(screen.getAllByText(/14\.371,20/).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Accessibility', () => {
    it('should have data-testid for identification', () => {
      render(<PlanCard {...defaultProps} />);

      expect(screen.getByTestId('plan-card-consultor_agil')).toBeInTheDocument();
    });

    it('should have aria-label on tooltip container', () => {
      render(<PlanCard {...defaultProps} billingPeriod="annual" />);

      // The tooltip container has a role and aria-label
      const tooltipTrigger = screen.getByRole('tooltip');
      expect(tooltipTrigger).toHaveAttribute('aria-label');
      expect(tooltipTrigger.getAttribute('aria-label')).toContain('Economia anual');
    });
  });
});
