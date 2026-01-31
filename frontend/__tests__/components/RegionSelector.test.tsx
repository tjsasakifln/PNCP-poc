/**
 * RegionSelector Component Tests
 *
 * Tests region-based UF selection with expand/collapse functionality
 * Target: 80%+ coverage
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { RegionSelector, REGIONS } from '@/app/components/RegionSelector';

describe('RegionSelector Component', () => {
  const mockOnToggleRegion = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all 5 regions', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      expect(screen.getByRole('button', { name: /Selecionar região Norte/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Nordeste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Centro-Oeste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Sudeste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Sul/i })).toBeInTheDocument();
    });

    it('should display region labels correctly', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      expect(screen.getByText('Norte')).toBeInTheDocument();
      expect(screen.getByText('Nordeste')).toBeInTheDocument();
      expect(screen.getByText('Centro-Oeste')).toBeInTheDocument();
      expect(screen.getByText('Sudeste')).toBeInTheDocument();
      expect(screen.getByText('Sul')).toBeInTheDocument();
    });

    it('should render buttons with default styling when none selected', () => {
      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const buttons = container.querySelectorAll('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('bg-surface-1');
        expect(button).toHaveClass('text-ink-secondary');
      });
    });
  });

  describe('Region Selection States', () => {
    it('should show fully selected state when all UFs in region are selected', () => {
      const selected = new Set(['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO']); // All Norte UFs
      render(<RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />);

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      expect(norteButton).toHaveClass('bg-brand-navy');
      expect(norteButton).toHaveClass('text-white');
    });

    it('should show partial selection state when some UFs in region are selected', () => {
      const selected = new Set(['AC', 'AM']); // 2 out of 7 Norte UFs
      render(<RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />);

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      expect(norteButton).toHaveClass('bg-brand-blue-subtle');
      expect(norteButton).toHaveClass('text-brand-blue');
    });

    it('should display count when region is partially selected', () => {
      const selected = new Set(['SC', 'PR']); // 2 out of 3 Sul UFs
      render(<RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />);

      expect(screen.getByText('Sul')).toBeInTheDocument();
      expect(screen.getByText('(2/3)')).toBeInTheDocument();
    });

    it('should not display count when region is fully selected', () => {
      const selected = new Set(['SC', 'PR', 'RS']); // All Sul UFs
      const { container } = render(
        <RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />
      );

      const sulButton = screen.getByText('Sul').closest('button');
      expect(sulButton?.textContent).not.toContain('(3/3)');
    });

    it('should not display count when region is not selected', () => {
      const selected = new Set(['SP']); // Only Sudeste
      const { container } = render(
        <RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />
      );

      const norteButton = screen.getByText('Norte').closest('button');
      expect(norteButton?.textContent).not.toContain('(0/7)');
    });
  });

  describe('User Interactions', () => {
    it('should call onToggleRegion with Norte UFs when Norte button clicked', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      fireEvent.click(norteButton);

      expect(mockOnToggleRegion).toHaveBeenCalledTimes(1);
      expect(mockOnToggleRegion).toHaveBeenCalledWith(['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO']);
    });

    it('should call onToggleRegion with Nordeste UFs when Nordeste button clicked', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const nordesteButton = screen.getByRole('button', { name: /Nordeste/i });
      fireEvent.click(nordesteButton);

      expect(mockOnToggleRegion).toHaveBeenCalledWith([
        'AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'
      ]);
    });

    it('should call onToggleRegion with Centro-Oeste UFs', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const centroOesteButton = screen.getByRole('button', { name: /Centro-Oeste/i });
      fireEvent.click(centroOesteButton);

      expect(mockOnToggleRegion).toHaveBeenCalledWith(['DF', 'GO', 'MT', 'MS']);
    });

    it('should call onToggleRegion with Sudeste UFs', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const sudesteButton = screen.getByRole('button', { name: /Sudeste/i });
      fireEvent.click(sudesteButton);

      expect(mockOnToggleRegion).toHaveBeenCalledWith(['ES', 'MG', 'RJ', 'SP']);
    });

    it('should call onToggleRegion with Sul UFs', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const sulButton = screen.getByRole('button', { name: /Sul/i });
      fireEvent.click(sulButton);

      expect(mockOnToggleRegion).toHaveBeenCalledWith(['PR', 'RS', 'SC']);
    });

    it('should allow clicking multiple regions', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      const sulButton = screen.getByRole('button', { name: /Sul/i });

      fireEvent.click(norteButton);
      fireEvent.click(sulButton);

      expect(mockOnToggleRegion).toHaveBeenCalledTimes(2);
    });
  });

  describe('Visual States', () => {
    it('should apply hover styles to unselected regions', () => {
      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      expect(norteButton).toHaveClass('hover:border-accent');
      expect(norteButton).toHaveClass('hover:text-brand-blue');
    });

    it('should show different styles for each selection state', () => {
      const selected = new Set(['AC', 'AM', 'SC', 'PR', 'RS']); // Partial Norte, Full Sul

      render(<RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />);

      // Full selection (Sul)
      const sulButton = screen.getByRole('button', { name: /Sul/i });
      expect(sulButton).toHaveClass('bg-brand-navy');
      expect(sulButton).toHaveClass('border-brand-navy');

      // Partial selection (Norte)
      const norteButton = screen.getByRole('button', { name: /Norte/i });
      expect(norteButton).toHaveClass('bg-brand-blue-subtle');
      expect(norteButton).toHaveClass('border-accent');

      // No selection (Nordeste)
      const nordesteButton = screen.getByRole('button', { name: /Nordeste/i });
      expect(nordesteButton).toHaveClass('bg-surface-1');
      expect(nordesteButton).toHaveClass('border-transparent');
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label for each region', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      expect(screen.getByRole('button', { name: /Selecionar região Norte/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Nordeste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Centro-Oeste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Sudeste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Selecionar região Sul/i })).toBeInTheDocument();
    });

    it('should have type="button" to prevent form submission', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });

    it('should be keyboard accessible', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const norteButton = screen.getByRole('button', { name: /Norte/i });

      // Buttons are inherently keyboard accessible - Enter/Space trigger click
      // Testing with direct click is sufficient for accessibility validation
      norteButton.focus();
      expect(norteButton).toHaveFocus();
      fireEvent.click(norteButton);

      expect(mockOnToggleRegion).toHaveBeenCalled();
    });
  });

  describe('REGIONS Export', () => {
    it('should export REGIONS constant with correct structure', () => {
      expect(REGIONS).toBeDefined();
      expect(Object.keys(REGIONS)).toHaveLength(5);
    });

    it('should have correct UFs for Norte region', () => {
      expect(REGIONS.norte.label).toBe('Norte');
      expect(REGIONS.norte.ufs).toEqual(['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO']);
    });

    it('should have correct UFs for Nordeste region', () => {
      expect(REGIONS.nordeste.label).toBe('Nordeste');
      expect(REGIONS.nordeste.ufs).toEqual(['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE']);
    });

    it('should have correct UFs for Centro-Oeste region', () => {
      expect(REGIONS.centro_oeste.label).toBe('Centro-Oeste');
      expect(REGIONS.centro_oeste.ufs).toEqual(['DF', 'GO', 'MT', 'MS']);
    });

    it('should have correct UFs for Sudeste region', () => {
      expect(REGIONS.sudeste.label).toBe('Sudeste');
      expect(REGIONS.sudeste.ufs).toEqual(['ES', 'MG', 'RJ', 'SP']);
    });

    it('should have correct UFs for Sul region', () => {
      expect(REGIONS.sul.label).toBe('Sul');
      expect(REGIONS.sul.ufs).toEqual(['PR', 'RS', 'SC']);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty selected set', () => {
      render(<RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('bg-surface-1');
      });
    });

    it('should handle all UFs selected', () => {
      const allUFs = new Set([
        ...REGIONS.norte.ufs,
        ...REGIONS.nordeste.ufs,
        ...REGIONS.centro_oeste.ufs,
        ...REGIONS.sudeste.ufs,
        ...REGIONS.sul.ufs,
      ]);

      render(<RegionSelector selected={allUFs} onToggleRegion={mockOnToggleRegion} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('bg-brand-navy');
      });
    });

    it('should handle invalid UFs in selected set', () => {
      const selected = new Set(['XX', 'YY', 'SC']); // XX and YY are invalid
      render(<RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />);

      // Sul should show partial (1/3)
      expect(screen.getByText('(1/3)')).toBeInTheDocument();

      // Invalid UFs should not affect other regions
      const norteButton = screen.getByRole('button', { name: /Norte/i });
      expect(norteButton).toHaveClass('bg-surface-1');
    });

    it('should handle single UF selection per region', () => {
      const selected = new Set(['AC']); // 1 out of 7 Norte UFs
      render(<RegionSelector selected={selected} onToggleRegion={mockOnToggleRegion} />);

      expect(screen.getByText('(1/7)')).toBeInTheDocument();
    });
  });

  describe('Layout and Styling', () => {
    it('should use flexbox layout with gap', () => {
      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const wrapper = container.querySelector('.flex.flex-wrap.gap-2');
      expect(wrapper).toBeInTheDocument();
    });

    it('should have margin bottom on container', () => {
      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const wrapper = container.querySelector('.mb-3');
      expect(wrapper).toBeInTheDocument();
    });

    it('should apply transition animations on hover', () => {
      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const buttons = container.querySelectorAll('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('transition-all');
        expect(button).toHaveClass('duration-200');
      });
    });

    it('should apply rounded button styling', () => {
      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const buttons = container.querySelectorAll('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('rounded-button');
      });
    });
  });

  describe('Click Animations - Issue #123', () => {
    it('should apply scale-95 class during click animation', () => {
      jest.useFakeTimers();

      const { container } = render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      fireEvent.click(norteButton);

      // Immediately after click, should have scale-95
      expect(norteButton).toHaveClass('scale-95');

      // After 200ms, animation should be removed
      jest.advanceTimersByTime(200);
      expect(norteButton).toHaveClass('scale-100');

      jest.useRealTimers();
    });

    it('should have hover:scale-105 class for unclicked buttons', () => {
      render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('hover:scale-105');
      });
    });

    it('should have active:scale-95 class for press state', () => {
      render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveClass('active:scale-95');
      });
    });

    it('should trigger callback after animation starts', () => {
      jest.useFakeTimers();

      render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const norteButton = screen.getByRole('button', { name: /Norte/i });
      fireEvent.click(norteButton);

      // Callback should be called immediately
      expect(mockOnToggleRegion).toHaveBeenCalledWith(['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO']);

      jest.useRealTimers();
    });

    it('should handle multiple rapid clicks gracefully', () => {
      jest.useFakeTimers();

      render(
        <RegionSelector selected={new Set()} onToggleRegion={mockOnToggleRegion} />
      );

      const norteButton = screen.getByRole('button', { name: /Norte/i });

      // Click multiple times rapidly
      fireEvent.click(norteButton);
      fireEvent.click(norteButton);
      fireEvent.click(norteButton);

      // All callbacks should be triggered
      expect(mockOnToggleRegion).toHaveBeenCalledTimes(3);

      jest.useRealTimers();
    });
  });
});
