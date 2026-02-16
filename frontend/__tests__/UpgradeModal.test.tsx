/**
 * Tests for UpgradeModal component (GTM-002 Single Plan Model)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UpgradeModal } from '../app/components/UpgradeModal';

// Mock useAnalytics hook
const mockTrackEvent = jest.fn();
jest.mock('../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: mockTrackEvent,
    identifyUser: jest.fn(),
    resetUser: jest.fn(),
    trackPageView: jest.fn(),
  }),
}));

// Mock PlanToggle component
jest.mock('../components/subscriptions/PlanToggle', () => ({
  PlanToggle: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <div data-testid="plan-toggle">
      <button onClick={() => onChange('monthly')}>Mensal</button>
      <button onClick={() => onChange('semiannual')}>Semestral</button>
      <button onClick={() => onChange('annual')}>Anual</button>
      <span data-testid="current-period">{value}</span>
    </div>
  ),
  BillingPeriod: jest.fn(),
}));

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

describe('UpgradeModal - GTM-002 Single Plan Model', () => {
  const mockOnClose = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
    window.location.href = '';
  });

  describe('Modal visibility', () => {
    it('renders when isOpen is true', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('SmartLic Pro')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<UpgradeModal isOpen={false} onClose={mockOnClose} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('calls onClose when close button clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const closeButton = screen.getByLabelText(/Fechar modal/i);
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when Escape key pressed', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when backdrop clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      // The backdrop is the element with role="dialog"
      const backdrop = screen.getByRole('dialog');
      fireEvent.click(backdrop);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('does not close when clicking modal content', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      // Find the modal content (first child of backdrop)
      const backdrop = screen.getByRole('dialog');
      const modalContent = backdrop.querySelector('.bg-surface-0');

      if (modalContent) {
        fireEvent.click(modalContent);
        expect(mockOnClose).not.toHaveBeenCalled();
      }
    });
  });

  describe('Plan details rendering', () => {
    it('displays SmartLic Pro title', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText('SmartLic Pro')).toBeInTheDocument();
    });

    it('renders all 6 feature items', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText('1.000 análises por mês')).toBeInTheDocument();
      expect(screen.getByText('Exportação Excel completa')).toBeInTheDocument();
      expect(screen.getByText('Pipeline de acompanhamento')).toBeInTheDocument();
      expect(screen.getByText('Inteligência de decisão completa')).toBeInTheDocument();
      expect(screen.getByText('5 anos de histórico')).toBeInTheDocument();
      expect(screen.getByText('Cobertura nacional — 27 estados')).toBeInTheDocument();
    });

    it('displays footer with cancellation info', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText(/Cancele quando quiser/i)).toBeInTheDocument();
      expect(screen.getByText(/Sem contrato de fidelidade/i)).toBeInTheDocument();
    });
  });

  describe('Billing period toggle', () => {
    it('renders PlanToggle component', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByTestId('plan-toggle')).toBeInTheDocument();
    });

    it('starts with monthly billing period by default', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByTestId('current-period')).toHaveTextContent('monthly');
    });

    it('updates to semiannual when semiannual button clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Semestral'));

      expect(screen.getByTestId('current-period')).toHaveTextContent('semiannual');
    });

    it('updates to annual when annual button clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Anual'));

      expect(screen.getByTestId('current-period')).toHaveTextContent('annual');
    });
  });

  describe('Pricing display', () => {
    it('displays monthly price correctly (R$ 1.999/mês)', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText(/R\$\s*1\.999,00/)).toBeInTheDocument();
      expect(screen.getByText('/mês')).toBeInTheDocument();
    });

    it('updates price to semiannual (R$ 1.799/mês)', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Semestral'));

      expect(screen.getByText(/R\$\s*1\.799,00/)).toBeInTheDocument();
      expect(screen.getByText(/Total: R\$\s*10\.794,00/)).toBeInTheDocument();
      expect(screen.getByText(/por semestre/i)).toBeInTheDocument();
    });

    it('updates price to annual (R$ 1.599/mês)', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Anual'));

      expect(screen.getByText(/R\$\s*1\.599,00/)).toBeInTheDocument();
      expect(screen.getByText(/Total: R\$\s*19\.188,00/)).toBeInTheDocument();
      expect(screen.getByText(/por ano/i)).toBeInTheDocument();
    });

    it('does not show total price for monthly period', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.queryByText(/Total:/i)).not.toBeInTheDocument();
    });
  });

  describe('CTA button navigation', () => {
    it('redirects to /planos?billing=monthly when clicked (default)', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Começar Agora'));

      expect(window.location.href).toBe('/planos?billing=monthly');
    });

    it('redirects to /planos?billing=semiannual when semiannual selected', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Semestral'));
      fireEvent.click(screen.getByText('Começar Agora'));

      expect(window.location.href).toBe('/planos?billing=semiannual');
    });

    it('redirects to /planos?billing=annual when annual selected', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      fireEvent.click(screen.getByText('Anual'));
      fireEvent.click(screen.getByText('Começar Agora'));

      expect(window.location.href).toBe('/planos?billing=annual');
    });
  });

  describe('Analytics tracking', () => {
    it('tracks modal open event with source', () => {
      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          source="excel_button"
        />
      );

      expect(mockTrackEvent).toHaveBeenCalledWith(
        'upgrade_modal_opened',
        { source: 'excel_button' }
      );
    });

    it('tracks modal open event without source', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(mockTrackEvent).toHaveBeenCalledWith(
        'upgrade_modal_opened',
        { source: undefined }
      );
    });

    it('tracks CTA click with billing period and source', () => {
      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          source="quota_counter"
        />
      );

      fireEvent.click(screen.getByText('Semestral'));
      fireEvent.click(screen.getByText('Começar Agora'));

      expect(mockTrackEvent).toHaveBeenCalledWith(
        'upgrade_modal_cta_clicked',
        { billing_period: 'semiannual', source: 'quota_counter' }
      );
    });

    it('only tracks modal open once per render', () => {
      const { rerender } = render(
        <UpgradeModal isOpen={true} onClose={mockOnClose} source="test" />
      );

      expect(mockTrackEvent).toHaveBeenCalledTimes(1);

      // Re-render without changing isOpen
      rerender(<UpgradeModal isOpen={true} onClose={mockOnClose} source="test" />);

      // Should still only be called once
      expect(mockTrackEvent).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has aria-modal="true"', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
    });

    it('has aria-labelledby pointing to title', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const modal = screen.getByRole('dialog');
      const titleId = modal.getAttribute('aria-labelledby');

      expect(titleId).toBe('upgrade-modal-title');

      const title = document.getElementById(titleId!);
      expect(title).toHaveTextContent('SmartLic Pro');
    });

    it('locks body scroll when open', () => {
      const { unmount } = render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(document.body.style.overflow).toBe('hidden');

      unmount();

      // Should restore scroll on unmount
      expect(document.body.style.overflow).toBe('unset');
    });

    it('close button is keyboard accessible', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const closeButton = screen.getByLabelText(/Fechar modal/i);
      expect(closeButton.tagName).toBe('BUTTON');
    });

    it('CTA button is keyboard accessible', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const ctaButton = screen.getByText('Começar Agora');
      expect(ctaButton.tagName).toBe('BUTTON');
    });

    it('has proper SVG aria attributes for close icon', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const closeIcon = screen.getByRole('img', { name: /Fechar/i });
      expect(closeIcon).toBeInTheDocument();
      expect(closeIcon.tagName).toBe('svg');
    });
  });

  describe('Responsive design', () => {
    it('renders with max-w-lg constraint for modal width', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const backdrop = screen.getByRole('dialog');
      const modalContent = backdrop.querySelector('.bg-surface-0');

      expect(modalContent).toHaveClass('max-w-lg');
      expect(modalContent).toHaveClass('w-full');
    });

    it('renders with max-h-[90vh] for scrollable content', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const backdrop = screen.getByRole('dialog');
      const modalContent = backdrop.querySelector('.bg-surface-0');

      expect(modalContent).toHaveClass('max-h-[90vh]');
      expect(modalContent).toHaveClass('overflow-y-auto');
    });

    it('has responsive padding', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const backdrop = screen.getByRole('dialog');
      expect(backdrop).toHaveClass('p-4');
    });
  });

  describe('Button styling', () => {
    it('applies correct hover effects to CTA button', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const ctaButton = screen.getByText('Começar Agora');
      expect(ctaButton).toHaveClass('bg-brand-navy');
      expect(ctaButton).toHaveClass('text-white');
      expect(ctaButton).toHaveClass('hover:bg-brand-blue-hover');
      expect(ctaButton).toHaveClass('hover:-translate-y-0.5');
      expect(ctaButton).toHaveClass('hover:shadow-lg');
    });

    it('CTA button spans full width', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const ctaButton = screen.getByText('Começar Agora');
      expect(ctaButton).toHaveClass('w-full');
    });
  });

  describe('Feature list rendering', () => {
    it('renders checkmarks for all features', () => {
      const { container } = render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      // Count checkmark symbols (✓)
      const checkmarks = container.querySelectorAll('span.text-green-500');
      expect(checkmarks.length).toBe(6);
    });

    it('all feature items have proper flex layout', () => {
      const { container } = render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const featureItems = container.querySelectorAll('li.flex.items-start');
      expect(featureItems.length).toBe(6);
    });
  });
});
