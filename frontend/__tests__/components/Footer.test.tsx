/**
 * Footer Component Tests
 * STORY-230 AC1-AC4: Footer navigation links
 * GTM-COPY-005 AC5: CNPJ, /sobre link, CONFENGE attribution
 *
 * Tests:
 * - AC1: "Central de Ajuda" links to /ajuda
 * - AC2: "Contato" links to /ajuda#contato (not /mensagens)
 * - AC3: Footer links consistent across pages
 * - AC4: All footer links accessible to unauthenticated users
 * - GTM-COPY-005 AC5: CNPJ visible, /sobre link, CONFENGE mention
 */

import { render, screen } from '@testing-library/react';
import Footer from '@/app/components/Footer';

describe('Footer Component', () => {
  beforeEach(() => {
    render(<Footer />);
  });

  describe('AC1: Central de Ajuda link', () => {
    it('should link to /ajuda', () => {
      const link = screen.getByText('Central de Ajuda');
      expect(link.closest('a')).toHaveAttribute('href', '/ajuda');
    });
  });

  describe('AC2: Contato link', () => {
    it('should link to /ajuda#contato, not /mensagens', () => {
      const link = screen.getByText('Contato');
      const anchor = link.closest('a');
      expect(anchor).toHaveAttribute('href', '/ajuda#contato');
      expect(anchor).not.toHaveAttribute('href', '/mensagens');
    });
  });

  describe('AC4: All footer links accessible to unauthenticated users', () => {
    it('should not have any links requiring authentication (/mensagens)', () => {
      const allLinks = screen.getAllByRole('link');
      const hrefs = allLinks.map((link) => link.getAttribute('href'));
      expect(hrefs).not.toContain('/mensagens');
    });

    it('should contain email link for direct contact', () => {
      const emailLink = screen.getByText('suporte@smartlic.tech');
      expect(emailLink.closest('a')).toHaveAttribute('href', 'mailto:suporte@smartlic.tech');
    });

    it('should render all expected sections', () => {
      expect(screen.getByText('Sobre')).toBeInTheDocument();
      expect(screen.getByText('Planos')).toBeInTheDocument();
      expect(screen.getByText('Suporte')).toBeInTheDocument();
      expect(screen.getByText('Legal')).toBeInTheDocument();
    });
  });

  describe('GTM-COPY-005 AC5: Credibility & Authority', () => {
    it('should link "Quem somos" to /sobre page', () => {
      const link = screen.getByText('Quem somos');
      expect(link.closest('a')).toHaveAttribute('href', '/sobre');
    });

    it('should link "Metodologia" to /sobre#metodologia', () => {
      const link = screen.getByText('Metodologia');
      expect(link.closest('a')).toHaveAttribute('href', '/sobre#metodologia');
    });

    it('should display CNPJ', () => {
      expect(screen.getByText(/52\.407\.089\/0001-09/)).toBeInTheDocument();
    });

    it('should display CONFENGE attribution', () => {
      const elements = screen.getAllByText(/CONFENGE/);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });
});
