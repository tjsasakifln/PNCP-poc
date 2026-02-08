/**
 * DowngradeModal Component Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
 * Tests downgrade confirmation modal
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { DowngradeModal } from '@/components/subscriptions/DowngradeModal';

describe('DowngradeModal Component', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    expiryDate: '2027-02-07T00:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<DowngradeModal {...defaultProps} isOpen={false} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<DowngradeModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Downgrade para Plano Mensal')).toBeInTheDocument();
    });

    it('should display warning icon', () => {
      const { container } = render(<DowngradeModal {...defaultProps} />);

      expect(container).toContainHTML('⚠️');
    });

    it('should display formatted expiry date', () => {
      render(<DowngradeModal {...defaultProps} expiryDate="2027-02-07T00:00:00Z" />);

      // Date will be formatted based on locale - just check it contains the year
      const dateElements = screen.queryAllByText(/2027/);
      expect(dateElements.length).toBeGreaterThan(0);
    });

    it('should use default date when expiryDate not provided', () => {
      render(<DowngradeModal {...defaultProps} expiryDate={undefined} />);

      // Check for default year 2026
      const dateElements = screen.queryAllByText(/2026/);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  describe('Warning and Policy Messages', () => {
    it('should display out of guarantee period warning', () => {
      render(<DowngradeModal {...defaultProps} />);

      expect(screen.getByText(/Você está fora do período de garantia/)).toBeInTheDocument();
    });

    it('should explain no refund policy', () => {
      render(<DowngradeModal {...defaultProps} />);

      expect(screen.getByText(/Sem reembolso do valor pago/)).toBeInTheDocument();
    });

    it('should explain benefit retention', () => {
      render(<DowngradeModal {...defaultProps} />);

      expect(screen.getByText(/Você mantém todos os benefícios anuais até/)).toBeInTheDocument();
    });

    it('should explain conversion to monthly', () => {
      render(<DowngradeModal {...defaultProps} />);

      expect(screen.getByText(/sua assinatura será convertida para mensal/)).toBeInTheDocument();
    });
  });

  describe('Retained Benefits', () => {
    it('should display default retained benefits', () => {
      render(<DowngradeModal {...defaultProps} />);

      expect(screen.getByText(/Early access a novas features/)).toBeInTheDocument();
      expect(screen.getByText(/Busca proativa de oportunidades/)).toBeInTheDocument();
      expect(screen.getByText(/Análise IA de editais/)).toBeInTheDocument();
    });

    it('should display custom retained benefits', () => {
      const customBenefits = ['Benefit 1', 'Benefit 2'];
      render(<DowngradeModal {...defaultProps} retainedBenefits={customBenefits} />);

      expect(screen.getByText('Benefit 1')).toBeInTheDocument();
      expect(screen.getByText('Benefit 2')).toBeInTheDocument();
    });

    it('should show sparkle icon for each benefit', () => {
      const { container } = render(<DowngradeModal {...defaultProps} />);

      // Count sparkle emojis (one per benefit)
      const sparkles = container.innerHTML.match(/✨/g);
      expect(sparkles).not.toBeNull();
      expect(sparkles!.length).toBeGreaterThan(0);
    });
  });

  describe('Confirmation Checkbox', () => {
    it('should render confirmation checkbox', () => {
      render(<DowngradeModal {...defaultProps} />);

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
      expect(checkbox).not.toBeChecked();
    });

    it('should require checkbox to be checked', () => {
      render(<DowngradeModal {...defaultProps} />);

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('required');
    });

    it('should enable confirmation when checkbox is checked', () => {
      render(<DowngradeModal {...defaultProps} />);

      const checkbox = screen.getByRole('checkbox');
      const confirmButton = screen.getByText('Confirmar Downgrade');

      expect(confirmButton).toBeDisabled();

      fireEvent.click(checkbox);

      expect(confirmButton).not.toBeDisabled();
    });

    it('should display confirmation text with expiry date', () => {
      render(<DowngradeModal {...defaultProps} expiryDate="2027-02-07T00:00:00Z" />);

      const checkboxLabel = screen.getByText(/Entendo que não haverá reembolso/);
      expect(checkboxLabel).toBeInTheDocument();
      // Check date appears in the checkbox label text
      expect(checkboxLabel.textContent).toContain('2027');
    });
  });

  describe('User Interactions', () => {
    it('should call onClose when clicking close button', () => {
      render(<DowngradeModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Fechar modal');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when clicking backdrop', () => {
      const { container } = render(<DowngradeModal {...defaultProps} />);

      const backdrop = container.querySelector('.fixed.inset-0.bg-black');
      fireEvent.click(backdrop!);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when clicking Cancel button', () => {
      render(<DowngradeModal {...defaultProps} />);

      const cancelButton = screen.getByText('Cancelar');
      fireEvent.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onConfirm when clicking Confirm with checkbox checked', () => {
      render(<DowngradeModal {...defaultProps} />);

      const checkbox = screen.getByRole('checkbox');
      const confirmButton = screen.getByText('Confirmar Downgrade');

      fireEvent.click(checkbox);
      fireEvent.click(confirmButton);

      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    });

    it('should not call onConfirm when checkbox is not checked', () => {
      render(<DowngradeModal {...defaultProps} />);

      const confirmButton = screen.getByText('Confirmar Downgrade');
      fireEvent.click(confirmButton);

      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('should reset checkbox state when closing modal', () => {
      const { rerender } = render(<DowngradeModal {...defaultProps} />);

      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);
      expect(checkbox).toBeChecked();

      // Close modal
      const closeButton = screen.getByLabelText('Fechar modal');
      fireEvent.click(closeButton);

      // Reopen modal
      rerender(<DowngradeModal {...defaultProps} isOpen={false} />);
      rerender(<DowngradeModal {...defaultProps} isOpen={true} />);

      const newCheckbox = screen.getByRole('checkbox');
      expect(newCheckbox).not.toBeChecked();
    });
  });

  describe('Loading State', () => {
    it('should disable buttons when isLoading is true', () => {
      render(<DowngradeModal {...defaultProps} isLoading={true} />);

      const cancelButton = screen.getByText('Cancelar');
      const confirmButton = screen.getByRole('button', { name: /Processando/ });

      expect(cancelButton).toBeDisabled();
      expect(confirmButton).toBeDisabled();
    });

    it('should show loading spinner when isLoading', () => {
      const { container } = render(<DowngradeModal {...defaultProps} isLoading={true} />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show "Processando..." text when loading', () => {
      render(<DowngradeModal {...defaultProps} isLoading={true} />);

      expect(screen.getByText('Processando...')).toBeInTheDocument();
    });

    it('should not call onConfirm when loading', () => {
      render(<DowngradeModal {...defaultProps} isLoading={true} />);

      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);

      const confirmButton = screen.getByRole('button', { name: /Processando/ });
      fireEvent.click(confirmButton);

      expect(mockOnConfirm).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have correct ARIA attributes', () => {
      render(<DowngradeModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'downgrade-modal-title');
    });

    it('should have accessible title', () => {
      render(<DowngradeModal {...defaultProps} />);

      const title = screen.getByText('Downgrade para Plano Mensal');
      expect(title).toHaveAttribute('id', 'downgrade-modal-title');
    });

    it('should have accessible close button', () => {
      render(<DowngradeModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Fechar modal');
      expect(closeButton).toBeInTheDocument();
    });

    it('should have backdrop with aria-hidden', () => {
      const { container } = render(<DowngradeModal {...defaultProps} />);

      const backdrop = container.querySelector('[aria-hidden="true"]');
      expect(backdrop).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply warning styles to alert', () => {
      render(<DowngradeModal {...defaultProps} />);

      const warningAlert = screen.getByText(/Você está fora do período de garantia/).closest('div');
      expect(warningAlert).toHaveClass('bg-warning-subtle', 'border-warning');
    });

    it('should apply brand-blue styles to benefits section', () => {
      render(<DowngradeModal {...defaultProps} />);

      const benefitsSection = screen.getByText(/Benefícios que você manterá/).closest('div');
      expect(benefitsSection).toHaveClass('bg-brand-blue-subtle', 'border-brand-blue');
    });

    it('should animate modal appearance', () => {
      const { container } = render(<DowngradeModal {...defaultProps} />);

      const modal = container.querySelector('.animate-fade-in-up');
      expect(modal).toBeInTheDocument();
    });
  });
});
