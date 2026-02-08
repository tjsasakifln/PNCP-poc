/**
 * TrustSignals Component Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
 * Tests trust signals, guarantees, and urgency elements
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { TrustSignals } from '@/components/subscriptions/TrustSignals';

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

describe('TrustSignals Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Social Proof Badge', () => {
    it('should display social proof with conversion rate', () => {
      render(<TrustSignals annualConversionRate={65} />);

      expect(screen.getByText(/Escolha de 65% dos nossos clientes/)).toBeInTheDocument();
    });

    it('should display custom conversion rate', () => {
      render(<TrustSignals annualConversionRate={72} />);

      expect(screen.getByText(/72%/)).toBeInTheDocument();
    });

    it('should not display social proof when rate is 0', () => {
      render(<TrustSignals annualConversionRate={0} />);

      expect(screen.queryByText(/Escolha de/)).not.toBeInTheDocument();
    });

    it('should show star emoji in social proof', () => {
      render(<TrustSignals annualConversionRate={65} />);

      const badge = screen.getByText(/Escolha de/).closest('div');
      expect(badge).toContainHTML('⭐');
    });
  });

  describe('Launch Offer', () => {
    it('should display launch offer when active', () => {
      render(<TrustSignals currentAnnualSignups={50} launchOfferLimit={100} />);

      expect(screen.getByText(/Oferta de Lançamento/i)).toBeInTheDocument();
      expect(screen.getByText(/Primeiros 100 assinantes/)).toBeInTheDocument();
    });

    it('should show remaining slots correctly', () => {
      render(<TrustSignals currentAnnualSignups={30} launchOfferLimit={100} />);

      expect(screen.getByText(/Restam apenas 70 vagas/)).toBeInTheDocument();
    });

    it('should not display launch offer when limit reached', () => {
      render(<TrustSignals currentAnnualSignups={100} launchOfferLimit={100} />);

      expect(screen.queryByText(/Oferta de Lançamento/i)).not.toBeInTheDocument();
    });

    it('should not display when signups exceed limit', () => {
      render(<TrustSignals currentAnnualSignups={150} launchOfferLimit={100} />);

      expect(screen.queryByText(/Oferta de Lançamento/i)).not.toBeInTheDocument();
    });

    it('should have aria-live for dynamic updates', () => {
      render(<TrustSignals currentAnnualSignups={50} launchOfferLimit={100} />);

      const launchOffer = screen.getByText(/Oferta de Lançamento/i).closest('[role="status"]');
      expect(launchOffer).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Early Bird Discount Code', () => {
    it('should display EARLYBIRD code when enabled', () => {
      render(<TrustSignals showEarlyBirdCode={true} />);

      expect(screen.getByText('EARLYBIRD')).toBeInTheDocument();
    });

    it('should not display code when disabled', () => {
      render(<TrustSignals showEarlyBirdCode={false} />);

      expect(screen.queryByText('EARLYBIRD')).not.toBeInTheDocument();
    });

    it('should copy code to clipboard when clicking Copiar', () => {
      render(<TrustSignals showEarlyBirdCode={true} />);

      const copyButton = screen.getByText('Copiar');
      fireEvent.click(copyButton);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('EARLYBIRD');
    });

    it('should display discount information', () => {
      render(<TrustSignals showEarlyBirdCode={true} />);

      expect(screen.getByText(/\+10% de desconto extra/)).toBeInTheDocument();
      expect(screen.getByText(/válido para os primeiros 50 usos/)).toBeInTheDocument();
    });
  });

  describe('Guarantees Section', () => {
    it('should display all three guarantees', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/Garantia de 30 dias/i)).toBeInTheDocument();
      expect(screen.getByText(/Segurança de nível bancário/i)).toBeInTheDocument();
      expect(screen.getByText(/Suporte prioritário/i)).toBeInTheDocument();
    });

    it('should display 30-day refund guarantee details', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/Cancele e receba reembolso integral/)).toBeInTheDocument();
    });

    it('should display security guarantee details', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/criptografia de ponta a ponta/)).toBeInTheDocument();
    });

    it('should display support guarantee details', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/Atendimento dedicado para assinantes anuais/)).toBeInTheDocument();
    });

    it('should show emoji icons for each guarantee', () => {
      const { container } = render(<TrustSignals />);

      expect(container).toContainHTML('💳'); // Refund
      expect(container).toContainHTML('🔒'); // Security
      expect(container).toContainHTML('📞'); // Support
    });
  });

  describe('Additional Trust Elements', () => {
    it('should display simple cancellation trust signal', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/Cancelamento online simples/)).toBeInTheDocument();
    });

    it('should display no hidden fees trust signal', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/Sem taxas ocultas/)).toBeInTheDocument();
    });

    it('should display LGPD compliance trust signal', () => {
      render(<TrustSignals />);

      expect(screen.getByText(/LGPD compliant/)).toBeInTheDocument();
    });

    it('should show checkmarks for trust signals', () => {
      const { container } = render(<TrustSignals />);

      const checkmarks = container.querySelectorAll('svg');
      expect(checkmarks.length).toBeGreaterThan(3); // At least 3 checkmarks
    });
  });

  describe('Component Integration', () => {
    it('should render with all props', () => {
      render(
        <TrustSignals
          annualConversionRate={68}
          currentAnnualSignups={45}
          launchOfferLimit={100}
          showEarlyBirdCode={true}
        />
      );

      expect(screen.getByTestId('trust-signals')).toBeInTheDocument();
      expect(screen.getByText(/68%/)).toBeInTheDocument();
      expect(screen.getByText(/Restam apenas 55 vagas/)).toBeInTheDocument();
      expect(screen.getByText('EARLYBIRD')).toBeInTheDocument();
    });

    it('should use default values when props not provided', () => {
      render(<TrustSignals />);

      // Default conversion rate: 65%
      expect(screen.getByText(/65%/)).toBeInTheDocument();

      // Default launch offer active (0 < 100)
      expect(screen.getByText(/Oferta de Lançamento/i)).toBeInTheDocument();

      // Default showEarlyBirdCode: true
      expect(screen.getByText('EARLYBIRD')).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      const { container } = render(<TrustSignals className="custom-class" />);

      const trustSignals = container.firstChild as HTMLElement;
      expect(trustSignals).toHaveClass('custom-class');
    });
  });

  describe('Visual States', () => {
    it('should apply success styling to social proof badge', () => {
      render(<TrustSignals annualConversionRate={65} />);

      const badge = screen.getByText(/65%/).closest('div');
      expect(badge).toHaveClass('bg-success-subtle', 'border-success');
    });

    it('should apply warning styling to launch offer', () => {
      render(<TrustSignals currentAnnualSignups={50} />);

      const launchOffer = screen.getByText(/Oferta de Lançamento/i).closest('div');
      expect(launchOffer).toHaveClass('bg-warning-subtle', 'border-warning');
    });

    it('should animate launch offer appearance', () => {
      render(<TrustSignals currentAnnualSignups={50} />);

      const launchOffer = screen.getByText(/Oferta de Lançamento/i).closest('div');
      expect(launchOffer).toHaveClass('animate-fade-in');
    });
  });
});
