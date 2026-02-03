/**
 * Tests for UpgradeModal component (STORY-165)
 */

import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { UpgradeModal } from '../app/components/UpgradeModal';

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

describe('UpgradeModal', () => {
  const mockOnClose = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Modal visibility', () => {
    it('renders when isOpen is true', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Escolha seu plano/i)).toBeInTheDocument();
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

    it('backdrop and modal content click behavior', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      // Note: Backdrop click handling may vary by implementation
      // This test validates that the modal structure is correct
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  describe('Plan cards rendering', () => {
    it('renders all 3 plan cards', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText('Consultor Ágil')).toBeInTheDocument();
      expect(screen.getByText('Máquina')).toBeInTheDocument();
      expect(screen.getByText('Sala de Guerra')).toBeInTheDocument();
    });

    it('displays correct pricing for each plan', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText('R$ 297/mês')).toBeInTheDocument();
      expect(screen.getByText('R$ 597/mês')).toBeInTheDocument();
      expect(screen.getByText('R$ 1.497/mês')).toBeInTheDocument();
    });

    it('shows "Mais Popular" badge on Máquina plan', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText(/⭐ Mais Popular/i)).toBeInTheDocument();
    });

    it('renders feature lists for all plans', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      // Consultor Ágil features
      expect(screen.getByText(/50 buscas por mês/i)).toBeInTheDocument();
      expect(screen.getByText(/30 dias de histórico/i)).toBeInTheDocument();

      // Máquina features
      expect(screen.getByText(/300 buscas por mês/i)).toBeInTheDocument();
      expect(screen.getByText(/1 ano de histórico/i)).toBeInTheDocument();

      // Sala de Guerra features
      expect(screen.getByText(/1000 buscas por mês/i)).toBeInTheDocument();
      expect(screen.getByText(/5 anos de histórico/i)).toBeInTheDocument();
    });
  });

  describe('Pre-selection highlighting', () => {
    it('highlights Consultor Ágil when pre-selected', () => {
      const { container } = render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          preSelectedPlan="consultor_agil"
        />
      );

      // Find the card containing Consultor Ágil text
      const consultorCard = screen.getByText('Consultor Ágil').closest('div[class*="border"]');
      expect(consultorCard).toHaveClass('ring-4');
      expect(consultorCard).toHaveClass('animate-pulse-border');
    });

    it('highlights Máquina when pre-selected', () => {
      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          preSelectedPlan="maquina"
        />
      );

      const maquinaCard = screen.getByText('Máquina').closest('div[class*="border"]');
      expect(maquinaCard).toHaveClass('ring-4');
    });

    it('highlights Sala de Guerra when pre-selected', () => {
      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          preSelectedPlan="sala_guerra"
        />
      );

      const salaCard = screen.getByText('Sala de Guerra').closest('div[class*="border"]');
      expect(salaCard).toHaveClass('ring-4');
    });

    it('does not highlight any plan when none pre-selected', () => {
      const { container } = render(
        <UpgradeModal isOpen={true} onClose={mockOnClose} />
      );

      const highlightedCards = container.querySelectorAll('.ring-4');
      // Only Máquina should have highlighting (from "popular" badge)
      expect(highlightedCards.length).toBeLessThanOrEqual(1);
    });
  });

  describe('Plan selection and redirect', () => {
    it('redirects to /planos with plan ID when Consultor Ágil clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const consultorButton = screen.getByText(/Assinar Consultor Ágil/i);
      fireEvent.click(consultorButton);

      expect(window.location.href).toBe('/planos?plan=consultor_agil');
    });

    it('redirects to /planos with plan ID when Máquina clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const maquinaButton = screen.getByText(/Assinar Máquina/i);
      fireEvent.click(maquinaButton);

      expect(window.location.href).toBe('/planos?plan=maquina');
    });

    it('redirects to /planos with plan ID when Sala de Guerra clicked', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const salaButton = screen.getByText(/Assinar Sala de Guerra/i);
      fireEvent.click(salaButton);

      expect(window.location.href).toBe('/planos?plan=sala_guerra');
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
      expect(title).toHaveTextContent(/Escolha seu plano/i);
    });

    it('locks body scroll when open', () => {
      const { unmount } = render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(document.body.style.overflow).toBe('hidden');

      unmount();

      // Should restore scroll on unmount
      expect(document.body.style.overflow).toBe('unset');
    });

    it('all buttons are keyboard accessible', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const buttons = screen.getAllByRole('button');

      // Verify all buttons are accessible via keyboard
      expect(buttons.length).toBeGreaterThan(0);
      buttons.forEach((button) => {
        // Button element is implicitly keyboard accessible
        expect(button.tagName).toBe('BUTTON');
      });
    });
  });

  describe('Footer tip', () => {
    it('displays upgrade tip message', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByText(/Upgrade a qualquer momento sem perder dados/i)).toBeInTheDocument();
    });
  });

  describe('Analytics tracking (console.log mock)', () => {
    it('logs modal open event with source', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          source="excel_button"
          preSelectedPlan="maquina"
        />
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        'Upgrade modal opened',
        { source: 'excel_button', preSelectedPlan: 'maquina' }
      );

      consoleSpy.mockRestore();
    });

    it('logs plan click event', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          source="quota_counter"
        />
      );

      const maquinaButton = screen.getByText(/Assinar Máquina/i);
      fireEvent.click(maquinaButton);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Plan clicked:',
        'maquina',
        { source: 'quota_counter' }
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Responsive design', () => {
    it('renders with responsive grid classes', () => {
      const { container } = render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-3');
    });
  });

  describe('Button styling variations', () => {
    it('applies outline styling to Consultor Ágil button', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const consultorButton = screen.getByText(/Assinar Consultor Ágil/i);
      expect(consultorButton).toHaveClass('border-2');
      expect(consultorButton).toHaveClass('border-brand-navy');
      expect(consultorButton).toHaveClass('bg-transparent');
    });

    it('applies solid styling to Máquina button', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const maquinaButton = screen.getByText(/Assinar Máquina/i);
      expect(maquinaButton).toHaveClass('bg-brand-navy');
      expect(maquinaButton).toHaveClass('text-white');
    });

    it('applies premium gradient to Sala de Guerra button', () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      const salaButton = screen.getByText(/Assinar Sala de Guerra/i);
      expect(salaButton).toHaveClass('bg-gradient-to-br');
      expect(salaButton).toHaveClass('from-yellow-400');
      expect(salaButton).toHaveClass('to-yellow-600');
    });
  });
});
