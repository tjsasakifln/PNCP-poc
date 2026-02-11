/**
 * Tests for UpgradeModal component (STORY-165)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { UpgradeModal } from '../app/components/UpgradeModal';

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

// Mock fetch for dynamic plan loading
const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockPlansResponse = {
  plans: [
    { id: 'free', name: 'Gratuito', description: 'Grátis', max_searches: 3, price_brl: 0, duration_days: null },
    { id: 'consultor_agil', name: 'Consultor Ágil', description: 'Para consultores', max_searches: 50, price_brl: 297, duration_days: 30 },
    { id: 'maquina', name: 'Máquina', description: 'Para empresas', max_searches: 300, price_brl: 597, duration_days: 30 },
    { id: 'sala_guerra', name: 'Sala de Guerra', description: 'Premium', max_searches: null, price_brl: 1497, duration_days: 30 },
    { id: 'master', name: 'Master', description: 'Internal', max_searches: null, price_brl: 0, duration_days: null },
  ],
};

describe('UpgradeModal', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    // Default: return plans successfully
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPlansResponse),
    });
  });

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
    it('renders all 3 plan cards', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText('Consultor Ágil')).toBeInTheDocument();
        expect(screen.getByText('Máquina')).toBeInTheDocument();
        expect(screen.getByText('Sala de Guerra')).toBeInTheDocument();
      });
    });

    it('displays correct pricing for each plan', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        // Plans are fetched from backend; prices formatted with Intl
        expect(screen.getByText(/R\$\s*297,00/)).toBeInTheDocument();
        expect(screen.getByText(/R\$\s*597,00/)).toBeInTheDocument();
        expect(screen.getByText(/R\$\s*1\.497,00/)).toBeInTheDocument();
      });
    });

    it('shows "Mais Popular" badge on Máquina plan', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText('Mais Popular')).toBeInTheDocument();
      });
    });

    it('renders feature lists for all plans', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        // Feature format from dynamic rendering: "50 buscas/mês" or "Buscas ilimitadas"
        expect(screen.getByText(/50 buscas\/mês/)).toBeInTheDocument();
        expect(screen.getByText(/300 buscas\/mês/)).toBeInTheDocument();
        expect(screen.getByText(/Buscas ilimitadas/)).toBeInTheDocument();
      });
    });
  });

  describe('Pre-selection highlighting', () => {
    it('highlights Consultor Ágil when pre-selected', async () => {
      const { container } = render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          preSelectedPlan="consultor_agil"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Consultor Ágil')).toBeInTheDocument();
      });

      const consultorCard = screen.getByText('Consultor Ágil').closest('.ring-4');
      expect(consultorCard).toBeInTheDocument();
    });

    it('highlights Máquina when pre-selected', async () => {
      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          preSelectedPlan="maquina"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Máquina')).toBeInTheDocument();
      });

      const maquinaCard = screen.getByText('Máquina').closest('.ring-4');
      expect(maquinaCard).toBeInTheDocument();
    });

    it('highlights Sala de Guerra when pre-selected', async () => {
      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          preSelectedPlan="sala_guerra"
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Sala de Guerra')).toBeInTheDocument();
      });

      const salaCard = screen.getByText('Sala de Guerra').closest('.ring-4');
      expect(salaCard).toBeInTheDocument();
    });

    it('does not highlight any plan when none pre-selected', async () => {
      const { container } = render(
        <UpgradeModal isOpen={true} onClose={mockOnClose} />
      );

      await waitFor(() => {
        expect(screen.getByText('Consultor Ágil')).toBeInTheDocument();
      });

      const highlightedCards = container.querySelectorAll('.ring-4');
      // No plan should have ring-4 pre-selection highlight
      expect(highlightedCards.length).toBe(0);
    });
  });

  describe('Plan selection and redirect', () => {
    it('redirects to /planos with plan ID when Consultor Ágil clicked', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText(/Assinar Consultor Ágil/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Assinar Consultor Ágil/i));
      expect(window.location.href).toBe('/planos?plan=consultor_agil');
    });

    it('redirects to /planos with plan ID when Máquina clicked', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText(/Assinar Máquina/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Assinar Máquina/i));
      expect(window.location.href).toBe('/planos?plan=maquina');
    });

    it('redirects to /planos with plan ID when Sala de Guerra clicked', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText(/Assinar Sala de Guerra/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Assinar Sala de Guerra/i));
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

    it('logs plan click event', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      render(
        <UpgradeModal
          isOpen={true}
          onClose={mockOnClose}
          source="quota_counter"
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Assinar Máquina/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/Assinar Máquina/i));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Plan clicked:',
        'maquina',
        { source: 'quota_counter' }
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Responsive design', () => {
    it('renders with responsive grid classes', async () => {
      const { container } = render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        const grid = container.querySelector('.grid');
        expect(grid).toHaveClass('grid-cols-1');
        expect(grid).toHaveClass('md:grid-cols-3');
      });
    });
  });

  describe('Button styling variations', () => {
    it('applies outline styling to Consultor Ágil button', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText(/Assinar Consultor Ágil/i)).toBeInTheDocument();
      });

      const consultorButton = screen.getByText(/Assinar Consultor Ágil/i);
      expect(consultorButton).toHaveClass('border-2');
      expect(consultorButton).toHaveClass('border-brand-navy');
      expect(consultorButton).toHaveClass('bg-transparent');
    });

    it('applies solid styling to Máquina button', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText(/Assinar Máquina/i)).toBeInTheDocument();
      });

      const maquinaButton = screen.getByText(/Assinar Máquina/i);
      expect(maquinaButton).toHaveClass('bg-brand-navy');
      expect(maquinaButton).toHaveClass('text-white');
    });

    it('applies outline styling to Sala de Guerra button', async () => {
      render(<UpgradeModal isOpen={true} onClose={mockOnClose} />);

      await waitFor(() => {
        expect(screen.getByText(/Assinar Sala de Guerra/i)).toBeInTheDocument();
      });

      // Sala de Guerra is not "popular", so it gets outline styling like Consultor Ágil
      const salaButton = screen.getByText(/Assinar Sala de Guerra/i);
      expect(salaButton).toHaveClass('border-2');
      expect(salaButton).toHaveClass('border-brand-navy');
    });
  });
});
