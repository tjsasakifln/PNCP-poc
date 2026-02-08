/**
 * AnnualBenefits Component Tests
 *
 * STORY-171 AC7: Testes Unitários - Frontend
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

  describe('Sala de Guerra Exclusive Benefits', () => {
    it('should not show exclusive section for other plans', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="consultor_agil" />);

      expect(screen.queryByText('Exclusivo Sala de Guerra')).not.toBeInTheDocument();
      expect(screen.queryByText('Análise IA de Editais')).not.toBeInTheDocument();
    });

    it('should show exclusive section for Sala de Guerra plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      expect(screen.getByText('Exclusivo Sala de Guerra')).toBeInTheDocument();
    });

    it('should display AI Edital Analysis benefit for Sala de Guerra', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      expect(screen.getByText('Análise IA de Editais')).toBeInTheDocument();
      expect(screen.getByText(/GPT-4 analisa editais/)).toBeInTheDocument();
    });

    it('should display Dashboard Executivo benefit for Sala de Guerra', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      expect(screen.getByText('Dashboard Executivo')).toBeInTheDocument();
      expect(screen.getByText(/Gráficos de tendências/)).toBeInTheDocument();
    });

    it('should display Alertas Multi-Canal benefit for Sala de Guerra', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      expect(screen.getByText('Alertas Multi-Canal')).toBeInTheDocument();
      expect(screen.getByText(/WhatsApp, Telegram/)).toBeInTheDocument();
    });

    it('should show crown icon for exclusive section', () => {
      const { container } = render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      const exclusiveSection = screen.getByText('Exclusivo Sala de Guerra').closest('div');
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
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      const dashboardSection = screen.getByText('Dashboard Executivo').closest('li');
      expect(dashboardSection).toContainHTML('Futuro');
    });
  });

  describe('Plan Variations', () => {
    it('should render for Consultor Ágil plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="consultor_agil" />);

      expect(screen.getByTestId('annual-benefits')).toBeInTheDocument();
      expect(screen.queryByText('Exclusivo Sala de Guerra')).not.toBeInTheDocument();
    });

    it('should render for Máquina plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="maquina" />);

      expect(screen.getByTestId('annual-benefits')).toBeInTheDocument();
      expect(screen.queryByText('Exclusivo Sala de Guerra')).not.toBeInTheDocument();
    });

    it('should render with all benefits for Sala de Guerra plan', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      expect(screen.getByTestId('annual-benefits')).toBeInTheDocument();
      expect(screen.getByText('Exclusivo Sala de Guerra')).toBeInTheDocument();

      // Should have both general and exclusive benefits
      expect(screen.getByText('Early Access')).toBeInTheDocument();
      expect(screen.getByText('Análise IA de Editais')).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply gradient background to Sala de Guerra section', () => {
      render(<AnnualBenefits billingPeriod="annual" planId="sala_guerra" />);

      const exclusiveSection = screen.getByText('Exclusivo Sala de Guerra').closest('div');
      expect(exclusiveSection).toHaveClass('bg-gradient-to-br');
    });

    it('should apply border to general benefits section', () => {
      render(<AnnualBenefits billingPeriod="annual" />);

      const generalSection = screen.getByText('Benefícios para Todos os Planos Anuais').closest('div');
      expect(generalSection).toHaveClass('border');
    });
  });
});
