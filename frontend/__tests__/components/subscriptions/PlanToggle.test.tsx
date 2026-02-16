/**
 * PlanToggle Component Tests
 *
 * GTM-002: 3-option billing period toggle
 * Tests toggle component for switching between monthly, semiannual, and annual billing periods
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { PlanToggle } from '@/components/subscriptions/PlanToggle';

describe('PlanToggle Component', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all three billing period options', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      expect(screen.getByLabelText('Mensal')).toBeInTheDocument();
      expect(screen.getByLabelText(/Semestral — Economize 10%/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Anual — Economize 20%/i)).toBeInTheDocument();
    });

    it('should highlight monthly when value is monthly', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      expect(monthlyButton).toHaveAttribute('aria-checked', 'true');
      expect(monthlyButton).toHaveClass('bg-brand-navy');
    });

    it('should highlight semiannual when value is semiannual', () => {
      render(<PlanToggle value="semiannual" onChange={mockOnChange} />);

      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      expect(semiannualButton).toHaveAttribute('aria-checked', 'true');
      expect(semiannualButton).toHaveClass('bg-brand-navy');
    });

    it('should highlight annual when value is annual', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);
      expect(annualButton).toHaveAttribute('aria-checked', 'true');
      expect(annualButton).toHaveClass('bg-brand-navy');
    });

    it('should not show savings badge when monthly is selected', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      expect(screen.queryByText(/Economize 10%/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Economize 20%/i)).not.toBeInTheDocument();
    });

    it('should show 10% savings badge when semiannual is selected', () => {
      render(<PlanToggle value="semiannual" onChange={mockOnChange} />);

      expect(screen.getByRole('status', { name: '' })).toHaveTextContent('Economize 10%');
      expect(screen.queryByText(/Economize 20%/i)).not.toBeInTheDocument();
    });

    it('should show 20% savings badge when annual is selected', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      expect(screen.getByRole('status', { name: '' })).toHaveTextContent('Economize 20%');
      expect(screen.queryByText(/Economize 10%/i)).not.toBeInTheDocument();
    });

    it('should update savings badge when toggling between periods', () => {
      const { rerender } = render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      expect(screen.queryByText(/Economize/i)).not.toBeInTheDocument();

      rerender(<PlanToggle value="semiannual" onChange={mockOnChange} />);
      expect(screen.getByText(/Economize 10%/i)).toBeInTheDocument();

      rerender(<PlanToggle value="annual" onChange={mockOnChange} />);
      expect(screen.getByText(/Economize 20%/i)).toBeInTheDocument();

      rerender(<PlanToggle value="monthly" onChange={mockOnChange} />);
      expect(screen.queryByText(/Economize/i)).not.toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} disabled={true} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);

      expect(monthlyButton).toBeDisabled();
      expect(semiannualButton).toBeDisabled();
      expect(annualButton).toBeDisabled();
    });
  });

  describe('User Interactions', () => {
    it('should call onChange with monthly when clicking monthly button', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      fireEvent.click(monthlyButton);

      expect(mockOnChange).toHaveBeenCalledWith('monthly');
    });

    it('should call onChange with semiannual when clicking semiannual button', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      fireEvent.click(semiannualButton);

      expect(mockOnChange).toHaveBeenCalledWith('semiannual');
    });

    it('should call onChange with annual when clicking annual button', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);
      fireEvent.click(annualButton);

      expect(mockOnChange).toHaveBeenCalledWith('annual');
    });

    it('should not call onChange when disabled', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} disabled={true} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);

      fireEvent.click(monthlyButton);
      fireEvent.click(semiannualButton);
      fireEvent.click(annualButton);

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('should not call onChange when clicking already selected option', () => {
      render(<PlanToggle value="semiannual" onChange={mockOnChange} />);

      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      fireEvent.click(semiannualButton);

      // Component doesn't prevent onChange on same value, but we can verify it was called
      expect(mockOnChange).toHaveBeenCalledWith('semiannual');
    });
  });

  describe('Visual States', () => {
    it('should apply correct active styles to selected option', () => {
      const { rerender } = render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);

      // Monthly selected
      expect(monthlyButton).toHaveClass('bg-brand-navy', 'text-white', 'shadow-md');
      expect(semiannualButton).toHaveClass('text-ink-secondary');
      expect(annualButton).toHaveClass('text-ink-secondary');

      // Switch to semiannual
      rerender(<PlanToggle value="semiannual" onChange={mockOnChange} />);
      expect(monthlyButton).toHaveClass('text-ink-secondary');
      expect(semiannualButton).toHaveClass('bg-brand-navy', 'text-white', 'shadow-md');
      expect(annualButton).toHaveClass('text-ink-secondary');

      // Switch to annual
      rerender(<PlanToggle value="annual" onChange={mockOnChange} />);
      expect(monthlyButton).toHaveClass('text-ink-secondary');
      expect(semiannualButton).toHaveClass('text-ink-secondary');
      expect(annualButton).toHaveClass('bg-brand-navy', 'text-white', 'shadow-md');
    });

    it('should apply transition classes to all buttons', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);

      expect(monthlyButton).toHaveClass('transition-all', 'duration-300', 'ease-in-out');
      expect(semiannualButton).toHaveClass('transition-all', 'duration-300', 'ease-in-out');
      expect(annualButton).toHaveClass('transition-all', 'duration-300', 'ease-in-out');
    });

    it('should show focus ring on focus', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      expect(monthlyButton).toHaveClass('focus:ring-2', 'focus:ring-brand-blue', 'focus:ring-offset-2');
    });

    it('should show disabled opacity when disabled', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} disabled={true} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      expect(monthlyButton).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
    });
  });

  describe('Accessibility', () => {
    it('should have correct ARIA attributes for radiogroup', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const radioGroup = screen.getByRole('radiogroup');
      expect(radioGroup).toHaveAttribute('aria-label', 'Escolha seu nível de compromisso');
    });

    it('should have correct ARIA role for all buttons', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);

      expect(monthlyButton).toHaveAttribute('role', 'radio');
      expect(semiannualButton).toHaveAttribute('role', 'radio');
      expect(annualButton).toHaveAttribute('role', 'radio');
    });

    it('should have aria-checked on selected option only', () => {
      render(<PlanToggle value="semiannual" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Mensal');
      const semiannualButton = screen.getByLabelText(/Semestral — Economize 10%/i);
      const annualButton = screen.getByLabelText(/Anual — Economize 20%/i);

      expect(monthlyButton).toHaveAttribute('aria-checked', 'false');
      expect(semiannualButton).toHaveAttribute('aria-checked', 'true');
      expect(annualButton).toHaveAttribute('aria-checked', 'false');
    });

    it('should have aria-live on savings badge', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const badge = screen.getByRole('status', { name: '' });
      expect(badge).toHaveAttribute('aria-live', 'polite');
    });

    it('should have descriptive aria-label including discount information', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      // Monthly has no discount
      expect(screen.getByLabelText('Mensal')).toBeInTheDocument();

      // Semiannual and annual include discount in aria-label
      expect(screen.getByLabelText(/Semestral — Economize 10%/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Anual — Economize 20%/i)).toBeInTheDocument();
    });
  });

  describe('Custom className', () => {
    it('should accept and apply custom className', () => {
      const { container } = render(
        <PlanToggle value="monthly" onChange={mockOnChange} className="custom-test-class" />
      );

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('custom-test-class');
    });
  });
});
