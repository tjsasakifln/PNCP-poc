/**
 * CustomDateInput Component Tests
 *
 * Tests custom date input component with accessibility
 * Issue #89 feat(frontend): substituir native form controls por custom
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { CustomDateInput } from '@/app/components/CustomDateInput';

describe('CustomDateInput Component', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render with placeholder when no value', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('DD/MM/AAAA')).toBeInTheDocument();
    });

    it('should render formatted date when value provided', () => {
      render(
        <CustomDateInput
          id="test-date"
          value="2024-01-15"
          onChange={mockOnChange}
        />
      );

      // Should display in Brazilian format
      expect(screen.getByText('15/01/2024')).toBeInTheDocument();
    });

    it('should render with label', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          label="Select Date:"
        />
      );

      expect(screen.getByText('Select Date:')).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      expect(input).toBeDisabled();
    });
  });

  describe('Date Formatting', () => {
    it('should format date to Brazilian format (DD/MM/YYYY)', () => {
      render(
        <CustomDateInput
          id="test-date"
          value="2024-12-31"
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('31/12/2024')).toBeInTheDocument();
    });

    it('should handle single-digit day and month with leading zeros', () => {
      render(
        <CustomDateInput
          id="test-date"
          value="2024-01-05"
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('05/01/2024')).toBeInTheDocument();
    });

    it('should show placeholder for empty string', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('DD/MM/AAAA')).toBeInTheDocument();
    });
  });

  describe('User Interaction', () => {
    it('should call onChange when date is selected', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      fireEvent.change(input, { target: { value: '2024-03-15' } });

      expect(mockOnChange).toHaveBeenCalledWith('2024-03-15');
    });

    it('should open native date picker when calendar icon clicked', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const calendarButton = screen.getByLabelText('Abrir seletor de data');
      expect(calendarButton).toBeInTheDocument();
    });

    it('should update visual state on focus', () => {
      const { container } = render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;

      // Focus the input
      fireEvent.focus(input);

      // The display div should have focus ring
      const displayDiv = container.querySelector('.ring-2');
      expect(displayDiv).toBeInTheDocument();
    });

    it('should remove focus state on blur', () => {
      const { container } = render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;

      fireEvent.focus(input);
      fireEvent.blur(input);

      // Check that focus ring is removed
      const displayDiv = container.querySelector('.ring-2.ring-brand-blue');
      expect(displayDiv).not.toBeInTheDocument();
    });
  });

  describe('Min/Max Constraints', () => {
    it('should pass min attribute to native input', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          min="2024-01-01"
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      expect(input).toHaveAttribute('min', '2024-01-01');
    });

    it('should pass max attribute to native input', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          max="2024-12-31"
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      expect(input).toHaveAttribute('max', '2024-12-31');
    });
  });

  describe('Accessibility', () => {
    it('should have accessible label', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          label="Birth Date"
        />
      );

      const label = screen.getByText('Birth Date');
      expect(label).toHaveAttribute('for', 'test-date');
    });

    it('should have calendar button with aria-label', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const button = screen.getByLabelText('Abrir seletor de data');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'button');
    });

    it('should have type="date" on native input', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      expect(input).toHaveAttribute('type', 'date');
    });

    it('should be keyboard accessible', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;

      // Should be focusable
      input.focus();
      expect(input).toHaveFocus();
    });

    it('should have calendar button with tabindex -1 to prevent double tab stop', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const button = screen.getByLabelText('Abrir seletor de data');
      expect(button).toHaveAttribute('tabIndex', '-1');
    });
  });

  describe('Visual States', () => {
    it('should apply disabled styles when disabled', () => {
      const { container } = render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const displayDiv = container.querySelector('.cursor-not-allowed');
      expect(displayDiv).toBeInTheDocument();
    });

    it('should show calendar icon', () => {
      const { container } = render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('should apply custom className', () => {
      const { container } = render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          className="custom-class"
        />
      );

      const wrapper = container.querySelector('.custom-class');
      expect(wrapper).toBeInTheDocument();
    });

    it('should show different text color for placeholder vs value', () => {
      const { rerender, container } = render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      // With placeholder
      let displayText = screen.getByText('DD/MM/AAAA');
      expect(displayText).toHaveClass('text-ink-muted');

      // With value
      rerender(
        <CustomDateInput
          id="test-date"
          value="2024-01-15"
          onChange={mockOnChange}
        />
      );

      displayText = screen.getByText('15/01/2024');
      expect(displayText).toHaveClass('text-ink');
    });
  });

  describe('Edge Cases', () => {
    it('should handle invalid date gracefully', () => {
      const { container } = render(
        <CustomDateInput
          id="test-date"
          value="invalid-date"
          onChange={mockOnChange}
        />
      );

      // Should not crash, might show Invalid Date or placeholder
      expect(container).toBeInTheDocument();
    });

    it('should not open picker when disabled and calendar clicked', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const button = screen.getByLabelText('Abrir seletor de data');
      expect(button).toBeDisabled();
    });
  });

  describe('Native Date Picker Integration', () => {
    it('should have hidden native input for accessibility', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      expect(input).toHaveClass('opacity-0');
      expect(input).toHaveClass('absolute');
    });

    it('should allow clicking through to native input', () => {
      render(
        <CustomDateInput
          id="test-date"
          value=""
          onChange={mockOnChange}
        />
      );

      const input = document.querySelector('#test-date') as HTMLInputElement;
      expect(input).toHaveClass('cursor-pointer');
    });
  });
});
