/**
 * AnnualBenefits Component Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
 * Updated UX-343: Legacy plans display as SmartLic Pro
 * Tests annual benefits display with conditional rendering
 */

import { render, screen } from '@testing-library/react';
import { AnnualBenefits } from '@/components/subscriptions/AnnualBenefits';

describe('AnnualBenefits Component', () => {
  describe('Conditional Rendering', () => {
    it('should not render when billing period is monthly', () => {
      const { container } = render(<AnnualBenefits billingPeriod="monthly" />);

      expect(container.firstChild).toBeNull();
    });

    it('should render when billing period is annual', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      expect(screen.getByTestId('annual-benefits')).toBeInTheDocument();
    });
  });

  describe('All Plans Benefits', () => {
    beforeEach(() => {
      render(<AnnualBenefits billingPeriod="annual" />);
    });

    it('should display section title', () => {
      expect(screen.getByText('Benefícios Exclusivos do Plano Anual')).toBeInTheDocument();
    });

    it('should display all plans benefits header', () => {
      expect(screen.getByText('Benefícios para Todos os Planos Anuais')).toBeInTheDocument();
    });

    it('should display Early Access benefit', () => {
      expect(screen.getByText('Early Access')).toBeInTheDocument();
      expect(screen.getByText(/Recebe novas features 2-4 semanas antes/)).toBeInTheDocument();
    });

    it('should display Busca Proativa benefit', () => {
      expect(screen.getByText('Busca Proativa')).toBeInTheDocument();
      expect(screen.getByText(/Sistema busca automaticamente/)).toBeInTheDocument();
    });

    it('should show status badges for all benefits', () => {
      // Early Access should be active
      expect(screen.getByText('Ativo')).toBeInTheDocument();

      // Busca Proativa should be coming soon
      const emBreveBadges = screen.getAllByText('Em breve');
      expect(emBreveBadges.length).toBeGreaterThan(0);
    });
  });

  describe('SmartLic Pro Exclusive Benefits', () => {
    it('should not show exclusive section when no planId provided', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      expect(screen.queryByText('Exclusivo SmartLic Pro')).not.toBeInTheDocument();
    });

    it('should show exclusive section for smartlic_pro plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      expect(screen.getByText('Exclusivo SmartLic Pro')).toBeInTheDocument();
    });

    it('should show exclusive section for legacy sala_guerra plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      expect(screen.getByText('Exclusivo SmartLic Pro')).toBeInTheDocument();
    });

    it('should show exclusive section for legacy consultor_agil plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="consultor_agil" />);

      expect(screen.getByText('Exclusivo SmartLic Pro')).toBeInTheDocument();
    });

    it('should show exclusive section for legacy maquina plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="maquina" />);

      expect(screen.getByText('Exclusivo SmartLic Pro')).toBeInTheDocument();
    });

    it('should display AI Edital Analysis benefit', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      expect(screen.getByText('Análise IA de Editais')).toBeInTheDocument();
      expect(screen.getByText(/IA avalia oportunidades/)).toBeInTheDocument();
    });

    it('should display Dashboard Executivo benefit', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      expect(screen.getByText('Dashboard Executivo')).toBeInTheDocument();
      expect(screen.getByText(/Gráficos de tendências/)).toBeInTheDocument();
    });

    it('should display Alertas Multi-Canal benefit', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      expect(screen.getByText('Alertas Multi-Canal')).toBeInTheDocument();
      expect(screen.getByText(/Telegram, Email, notificações/)).toBeInTheDocument();
    });

    it('should show crown icon for exclusive section', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      const exclusiveSection = screen.getByText('Exclusivo SmartLic Pro').closest('.border-2');
      expect(exclusiveSection).toHaveClass('border-brand-blue');
    });
  });

  describe('Early Adopter Message', () => {
    it('should display early adopter message', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      expect(screen.getByText(/Como early adopter/)).toBeInTheDocument();
      expect(screen.getByText(/você será notificado por email/)).toBeInTheDocument();
    });
  });

  describe('Feature Status Badges', () => {
    it('should show active badge for Early Access', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      const earlyAccessSection = screen.getByText('Early Access').closest('li');
      expect(earlyAccessSection).toContainHTML('Ativo');
    });

    it('should show coming soon badge for Busca Proativa', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      const buscaProativaSection = screen.getByText('Busca Proativa').closest('li');
      expect(buscaProativaSection).toContainHTML('Em breve');
    });

    it('should show future badge for Dashboard Executivo', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      const dashboardSection = screen.getByText('Dashboard Executivo').closest('li');
      expect(dashboardSection).toContainHTML('Futuro');
    });
  });

  describe('Plan Variations', () => {
    it('should show exclusive section for all paid plans', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="consultor_agil" />);

      expect(screen.getByTestId('annual-benefits')).toBeInTheDocument();
      // Legacy plans now show as SmartLic Pro
      expect(screen.getByText('Exclusivo SmartLic Pro')).toBeInTheDocument();
    });

    it('should render with all benefits for SmartLic Pro plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      expect(screen.getByTestId('annual-benefits')).toBeInTheDocument();
      expect(screen.getByText('Exclusivo SmartLic Pro')).toBeInTheDocument();

      // Should have both general and exclusive benefits
      expect(screen.getByText('Early Access')).toBeInTheDocument();
      expect(screen.getByText('Análise IA de Editais')).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply gradient background to SmartLic Pro section', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="smartlic_pro" />);

      const exclusiveHeading = screen.getByText('Exclusivo SmartLic Pro');
      const outerDiv = exclusiveHeading.closest('.bg-gradient-to-br');
      expect(outerDiv).toBeInTheDocument();
    });

    it('should apply border to general benefits section', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      const generalHeading = screen.getByText('Benefícios para Todos os Planos Anuais');
      const outerDiv = generalHeading.closest('.border');
      expect(outerDiv).toBeInTheDocument();
    });
  });
});
