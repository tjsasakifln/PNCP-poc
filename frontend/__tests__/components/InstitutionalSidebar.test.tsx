import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import InstitutionalSidebar from '../../app/components/InstitutionalSidebar';

describe('InstitutionalSidebar', () => {
  describe('Login Variant', () => {
    it('renders login variant headline', () => {
      render(<InstitutionalSidebar variant="login" />);

      const headline = screen.getByRole('heading', { level: 1 });
      expect(headline).toHaveTextContent('Descubra oportunidades de licitação antes da concorrência');
    });

    it('renders login variant subheadline', () => {
      render(<InstitutionalSidebar variant="login" />);

      expect(screen.getByText(/Acesse seu painel e encontre as melhores oportunidades/i)).toBeInTheDocument();
    });

    it('renders 5 benefits for login variant', () => {
      render(<InstitutionalSidebar variant="login" />);

      const benefits = screen.getAllByRole('listitem');
      expect(benefits).toHaveLength(5);
    });

    it('renders correct login benefits', () => {
      render(<InstitutionalSidebar variant="login" />);

      expect(screen.getByText('Monitoramento em tempo real de licitações')).toBeInTheDocument();
      expect(screen.getByText('Filtros por estado, valor e setor')).toBeInTheDocument();
      expect(screen.getByText('Resumo executivo gerado por IA')).toBeInTheDocument();
      expect(screen.getByText('Exportação de relatórios em Excel')).toBeInTheDocument();
      expect(screen.getByText('Histórico completo de buscas')).toBeInTheDocument();
    });

    it('renders login statistics', () => {
      render(<InstitutionalSidebar variant="login" />);

      expect(screen.getByText('27')).toBeInTheDocument();
      expect(screen.getByText('estados monitorados')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('setores pré-configurados')).toBeInTheDocument();
      expect(screen.getByText('24h')).toBeInTheDocument();
      expect(screen.getByText('atualização diária')).toBeInTheDocument();
    });
  });

  describe('Signup Variant', () => {
    it('renders signup variant headline', () => {
      render(<InstitutionalSidebar variant="signup" />);

      const headline = screen.getByRole('heading', { level: 1 });
      expect(headline).toHaveTextContent('Sua empresa a um passo das melhores oportunidades públicas');
    });

    it('renders signup variant subheadline', () => {
      render(<InstitutionalSidebar variant="signup" />);

      expect(screen.getByText(/Crie sua conta e comece a encontrar licitações/i)).toBeInTheDocument();
    });

    it('renders 5 benefits for signup variant', () => {
      render(<InstitutionalSidebar variant="signup" />);

      const benefits = screen.getAllByRole('listitem');
      expect(benefits).toHaveLength(5);
    });

    it('renders correct signup benefits', () => {
      render(<InstitutionalSidebar variant="signup" />);

      expect(screen.getByText('Comece grátis com 3 buscas completas')).toBeInTheDocument();
      expect(screen.getByText('Sem necessidade de cartão de crédito')).toBeInTheDocument();
      expect(screen.getByText('Configuração em menos de 2 minutos')).toBeInTheDocument();
      expect(screen.getByText('Suporte dedicado via WhatsApp')).toBeInTheDocument();
      expect(screen.getByText('Dados protegidos e conformidade LGPD')).toBeInTheDocument();
    });

    it('renders signup statistics', () => {
      render(<InstitutionalSidebar variant="signup" />);

      expect(screen.getByText('27')).toBeInTheDocument();
      expect(screen.getByText('estados cobertos')).toBeInTheDocument();
      expect(screen.getByText('1000+')).toBeInTheDocument();
      expect(screen.getByText('licitações/dia')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(screen.getByText('fonte oficial')).toBeInTheDocument();
    });
  });

  describe('PNCP Badge', () => {
    it('renders PNCP official badge link', () => {
      render(<InstitutionalSidebar variant="login" />);

      const link = screen.getByRole('link', { name: /Dados extraídos diretamente da API oficial do PNCP/i });
      expect(link).toBeInTheDocument();
    });

    it('PNCP badge opens in new tab', () => {
      render(<InstitutionalSidebar variant="login" />);

      const link = screen.getByRole('link', { name: /PNCP/i });
      expect(link).toHaveAttribute('target', '_blank');
    });

    it('PNCP badge has noopener noreferrer for security', () => {
      render(<InstitutionalSidebar variant="login" />);

      const link = screen.getByRole('link', { name: /PNCP/i });
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('PNCP badge links to correct URL', () => {
      render(<InstitutionalSidebar variant="login" />);

      const link = screen.getByRole('link', { name: /PNCP/i });
      expect(link).toHaveAttribute('href', 'https://pncp.gov.br');
    });

    it('PNCP badge has descriptive aria-label', () => {
      render(<InstitutionalSidebar variant="login" />);

      const link = screen.getByRole('link', { name: /Dados extraídos diretamente da API oficial do PNCP/i });
      expect(link).toHaveAccessibleName();
    });
  });

  describe('Custom className', () => {
    it('applies custom className to container', () => {
      const { container } = render(<InstitutionalSidebar variant="login" className="custom-class" />);

      const sidebar = container.firstChild as HTMLElement;
      expect(sidebar).toHaveClass('custom-class');
    });

    it('preserves default classes when custom className provided', () => {
      const { container } = render(<InstitutionalSidebar variant="login" className="custom-class" />);

      const sidebar = container.firstChild as HTMLElement;
      expect(sidebar.className).toContain('bg-gradient-to-br');
      expect(sidebar.className).toContain('custom-class');
    });
  });

  describe('Responsive Design', () => {
    it('has mobile-first responsive classes', () => {
      const { container } = render(<InstitutionalSidebar variant="login" />);

      const sidebar = container.firstChild as HTMLElement;
      expect(sidebar.className).toContain('md:');
    });

    it('has min-h-screen on mobile', () => {
      const { container } = render(<InstitutionalSidebar variant="login" />);

      const sidebar = container.firstChild as HTMLElement;
      expect(sidebar.className).toContain('min-h-screen');
    });
  });

  describe('Accessibility', () => {
    it('uses semantic HTML with heading hierarchy', () => {
      render(<InstitutionalSidebar variant="login" />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
    });

    it('uses unordered list for benefits', () => {
      render(<InstitutionalSidebar variant="login" />);

      const list = screen.getByRole('list');
      expect(list).toBeInTheDocument();
    });

    it('all list items have proper role', () => {
      render(<InstitutionalSidebar variant="login" />);

      const items = screen.getAllByRole('listitem');
      items.forEach(item => {
        expect(item).toHaveAttribute('class');
      });
    });
  });

  describe('Visual Consistency', () => {
    it('has gradient background classes', () => {
      const { container } = render(<InstitutionalSidebar variant="login" />);

      const sidebar = container.firstChild as HTMLElement;
      expect(sidebar.className).toContain('bg-gradient-to-br');
      expect(sidebar.className).toContain('from-[var(--brand-navy)]');
      expect(sidebar.className).toContain('to-[var(--brand-blue)]');
    });

    it('renders all SVG icons', () => {
      const { container } = render(<InstitutionalSidebar variant="login" />);

      const svgs = container.querySelectorAll('svg');
      // 5 benefits + 1 check icon in PNCP badge = 6 SVGs
      expect(svgs.length).toBeGreaterThanOrEqual(6);
    });
  });

  describe('Content Rendering', () => {
    it('does not render signup content in login variant', () => {
      render(<InstitutionalSidebar variant="login" />);

      expect(screen.queryByText('Comece grátis com 3 buscas completas')).not.toBeInTheDocument();
    });

    it('does not render login content in signup variant', () => {
      render(<InstitutionalSidebar variant="signup" />);

      expect(screen.queryByText('Monitoramento em tempo real do PNCP')).not.toBeInTheDocument();
    });
  });
});
