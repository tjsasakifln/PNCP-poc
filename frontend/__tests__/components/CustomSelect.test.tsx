/**
 * CustomSelect Component Tests
 *
 * Tests custom select component with full keyboard accessibility
 * Issue #89 feat(frontend): substituir native form controls por custom
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { CustomSelect } from '@/app/components/CustomSelect';

// Mock scrollIntoView for JSDOM
Element.prototype.scrollIntoView = jest.fn();

describe('CustomSelect Component', () => {
  const mockOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2', description: 'Description for option 2' },
    { value: 'option3', label: 'Option 3' },
  ];

  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render with placeholder when no value selected', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
          placeholder="Select an option"
        />
      );

      expect(screen.getByText('Select an option')).toBeInTheDocument();
    });

    it('should render with selected value', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option1"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('Option 1')).toBeInTheDocument();
    });

    it('should render with label', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
          label="Test Label"
        />
      );

      expect(screen.getByText('Test Label')).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const button = screen.getByRole('combobox');
      expect(button).toBeDisabled();
    });
  });

  describe('Dropdown Interaction', () => {
    it('should open dropdown when clicked', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      expect(screen.getByRole('listbox')).toBeInTheDocument();
      expect(screen.getByText('Option 2')).toBeInTheDocument();
    });

    it('should close dropdown when clicking outside', () => {
      render(
        <div>
          <CustomSelect
            id="test-select"
            value=""
            options={mockOptions}
            onChange={mockOnChange}
          />
          <div data-testid="outside">Outside</div>
        </div>
      );

      // Open dropdown
      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      // Click outside
      const outside = screen.getByTestId('outside');
      fireEvent.mouseDown(outside);

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('should select option when clicked', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      // Open dropdown
      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      // Click option
      const option2 = screen.getByText('Option 2');
      fireEvent.click(option2);

      expect(mockOnChange).toHaveBeenCalledWith('option2');
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('should show option descriptions when provided', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      expect(screen.getByText('Description for option 2')).toBeInTheDocument();
    });

    it('should highlight selected option', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option2"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      const options = screen.getAllByRole('option');
      const option2 = options[1]; // Second option
      expect(option2).toHaveClass('bg-surface-1');
      expect(option2).toHaveClass('font-medium');
    });
  });

  describe('Keyboard Navigation', () => {
    it('should open dropdown with Enter key', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      button.focus();
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('should open dropdown with Space key', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange=        {mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      button.focus();
      fireEvent.keyDown(button, { key: ' ' });

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('should close dropdown with Escape key', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);
      expect(screen.getByRole('listbox')).toBeInTheDocument();

      fireEvent.keyDown(button, { key: 'Escape' });
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('should navigate down with ArrowDown', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option1"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      // First option should be highlighted initially (current value)
      // Press ArrowDown to go to second option
      fireEvent.keyDown(button, { key: 'ArrowDown' });

      // Verify aria-activedescendant is updated
      expect(button.getAttribute('aria-activedescendant')).toBe('test-select-option-1');
    });

    it('should navigate up with ArrowUp', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option2"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      fireEvent.keyDown(button, { key: 'ArrowUp' });

      expect(button.getAttribute('aria-activedescendant')).toBe('test-select-option-0');
    });

    it('should go to first option with Home key', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option3"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      fireEvent.keyDown(button, { key: 'Home' });

      expect(button.getAttribute('aria-activedescendant')).toBe('test-select-option-0');
    });

    it('should go to last option with End key', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option1"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      fireEvent.keyDown(button, { key: 'End' });

      expect(button.getAttribute('aria-activedescendant')).toBe('test-select-option-2');
    });

    it('should select highlighted option with Enter', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      // First option should be highlighted by default (index 0)
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith('option1');
      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('should close dropdown on Tab key', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      fireEvent.keyDown(button, { key: 'Tab' });

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have correct ARIA attributes', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      expect(button).toHaveAttribute('aria-haspopup', 'listbox');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-controls', 'test-select-listbox');
    });

    it('should update aria-expanded when opened', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('should have aria-activedescendant when option is highlighted', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option1"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-activedescendant', 'test-select-option-0');
    });

    it('should have role="option" on list items', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(3);
    });

    it('should have aria-selected on selected option', () => {
      render(
        <CustomSelect
          id="test-select"
          value="option2"
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      const option2 = screen.getAllByRole('option')[1];
      expect(option2).toHaveAttribute('aria-selected', 'true');
    });
  });

  describe('Visual States', () => {
    it('should rotate chevron icon when open', () => {
      const { container } = render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      const svg = button.querySelector('svg');

      expect(svg).not.toHaveClass('rotate-180');

      fireEvent.click(button);

      expect(svg).toHaveClass('rotate-180');
    });

    it('should apply disabled styles when disabled', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const button = screen.getByRole('combobox');
      expect(button).toHaveClass('disabled:bg-surface-1');
      expect(button).toHaveClass('disabled:cursor-not-allowed');
    });

    it('should not open when disabled', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
          disabled={true}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });
  });

  describe('Mouse Interaction', () => {
    it('should highlight option on mouse enter', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={mockOptions}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      const option2 = screen.getByText('Option 2').closest('li');
      fireEvent.mouseEnter(option2!);

      // Check if highlighted class is applied
      expect(option2).toHaveClass('bg-brand-blue-subtle');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty options array', () => {
      render(
        <CustomSelect
          id="test-select"
          value=""
          options={[]}
          onChange={mockOnChange}
        />
      );

      const button = screen.getByRole('combobox');
      fireEvent.click(button);

      const listbox = screen.getByRole('listbox');
      expect(listbox).toBeInTheDocument();
      expect(listbox.children).toHaveLength(0);
    });

    it('should handle value not in options', () => {
      render(
        <CustomSelect
          id="test-select"
          value="nonexistent"
          options={mockOptions}
          onChange={mockOnChange}
          placeholder="Select..."
        />
      );

      // Should show placeholder when value doesn't match any option
      expect(screen.getByText('Select...')).toBeInTheDocument();
    });
  });
});
