/**
 * PlanToggle Component Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
 * Tests toggle component for switching billing periods
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { PlanToggle } from '@/components/subscriptions/PlanToggle';

describe('PlanToggle Component', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render both monthly and annual options', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      expect(screen.getByLabelText('Plano Mensal')).toBeInTheDocument();
      expect(screen.getByLabelText('Plano Anual')).toBeInTheDocument();
    });

    it('should highlight monthly when value is monthly', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      expect(monthlyButton).toHaveAttribute('aria-checked', 'true');
      expect(monthlyButton).toHaveClass('bg-brand-navy');
    });

    it('should highlight annual when value is annual', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      expect(annualButton).toHaveAttribute('aria-checked', 'true');
      expect(annualButton).toHaveClass('bg-brand-navy');
    });

    it('should show savings badge only when annual is selected', () => {
      const { rerender } = render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      expect(screen.queryByText(/Economize 20%/i)).not.toBeInTheDocument();

      rerender(<PlanToggle value="annual" onChange={mockOnChange} />);

      expect(screen.getByText(/Economize 20%/i)).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} disabled={true} />);

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      const annualButton = screen.getByLabelText('Plano Anual');

      expect(monthlyButton).toBeDisabled();
      expect(annualButton).toBeDisabled();
    });
  });

  describe('User Interactions', () => {
    it('should call onChange with annual when clicking annual button', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      fireEvent.click(annualButton);

      expect(mockOnChange).toHaveBeenCalledWith('annual');
    });

    it('should call onChange with monthly when clicking monthly button', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      fireEvent.click(monthlyButton);

      expect(mockOnChange).toHaveBeenCalledWith('monthly');
    });

    it('should not call onChange when disabled', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} disabled={true} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      fireEvent.click(annualButton);

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should toggle with Enter key', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      annualButton.focus();
      fireEvent.keyDown(annualButton, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith('annual');
    });

    it('should toggle with Space key', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      annualButton.focus();
      fireEvent.keyDown(annualButton, { key: ' ' });

      expect(mockOnChange).toHaveBeenCalledWith('annual');
    });

    it('should not toggle with other keys', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      annualButton.focus();
      fireEvent.keyDown(annualButton, { key: 'Tab' });

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('should not toggle with keyboard when disabled', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} disabled={true} />);

      const annualButton = screen.getByLabelText('Plano Anual');
      fireEvent.keyDown(annualButton, { key: 'Enter' });

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have correct ARIA attributes', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const radioGroup = screen.getByRole('radiogroup');
      expect(radioGroup).toHaveAttribute('aria-label', 'Alternar entre plano mensal e anual');

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      const annualButton = screen.getByLabelText('Plano Anual');

      expect(monthlyButton).toHaveAttribute('role', 'radio');
      expect(annualButton).toHaveAttribute('role', 'radio');
    });

    it('should have aria-checked on selected option', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      const annualButton = screen.getByLabelText('Plano Anual');

      expect(monthlyButton).toHaveAttribute('aria-checked', 'false');
      expect(annualButton).toHaveAttribute('aria-checked', 'true');
    });

    it('should have aria-live on savings badge', () => {
      render(<PlanToggle value="annual" onChange={mockOnChange} />);

      const badge = screen.getByText(/Economize 20%/i).closest('[role="status"]');
      expect(badge).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Visual States', () => {
    it('should apply transition classes', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      expect(monthlyButton).toHaveClass('transition-all', 'duration-300');
    });

    it('should show focus ring on focus', () => {
      render(<PlanToggle value="monthly" onChange={mockOnChange} />);

      const monthlyButton = screen.getByLabelText('Plano Mensal');
      expect(monthlyButton).toHaveClass('focus:ring-2', 'focus:ring-brand-blue');
    });
  });
});
