/**
 * Footer Component Tests
 * STORY-230 AC1-AC4: Footer navigation links
 * GTM-COPY-005 AC5: Address, /sobre link, CONFENGE attribution
 * REPO-011: "Soluções" column with 4 entries (#763)
 *
 * Tests:
 * - AC1: "Central de Ajuda" links to /ajuda
 * - AC2: "Contato" links to /ajuda#contato (not /mensagens)
 * - AC3: Footer links consistent across pages
 * - AC4: All footer links accessible to unauthenticated users
 * - GTM-COPY-005 AC5: Fiscal address visible, /sobre link, CONFENGE mention
 * - REPO-011: Soluções column renders 3 links + 1 disabled placeholder
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

    it('should not contain email link (email not yet configured)', () => {
      const allLinks = screen.getAllByRole('link');
      const mailtoLinks = allLinks.filter(
        (link) => link.getAttribute('href')?.startsWith('mailto:')
      );
      expect(mailtoLinks).toHaveLength(0);
    });

    it('should render all expected sections', () => {
      expect(screen.getByText('Sobre')).toBeInTheDocument();
      expect(screen.getByText('CONFENGE')).toBeInTheDocument();
      expect(screen.getByText('Suporte')).toBeInTheDocument();
      expect(screen.getByText('Legal')).toBeInTheDocument();
    });
  });

  describe('REPO-011: Soluções column', () => {
    it('should render the Soluções column heading', () => {
      expect(screen.getByText('Soluções')).toBeInTheDocument();
    });

    it('should render Consultoria CONFENGE instead of SaaS /planos', () => {
      const links = screen.getAllByRole('link', { name: /consultoria confenge/i });
      expect(links.length).toBeGreaterThanOrEqual(1);
      expect(links[0]).toHaveAttribute('href', '/consultoria-b2g');
    });

    it('should render Radar B2G link pointing to /consultoria-b2g?modalidade=radar', () => {
      const link = screen.getByRole('link', { name: 'Radar B2G' });
      expect(link).toHaveAttribute('href', '/consultoria-b2g?modalidade=radar');
    });

    it('should render Consultoria B2G link pointing to /consultoria-b2g', () => {
      const links = screen.getAllByRole('link', { name: 'Consultoria B2G' });
      const exactLink = links.find((l) => l.getAttribute('href') === '/consultoria-b2g');
      expect(exactLink).toBeDefined();
    });

    it('should render "Exemplos" as disabled text, not a link', () => {
      // Exemplos must NOT be an anchor/link element
      const exemplosLink = screen.queryByRole('link', { name: /exemplos/i });
      expect(exemplosLink).toBeNull();
      // But text must still be visible
      expect(screen.getByText(/exemplos/i)).toBeInTheDocument();
    });

    it('should preserve the transparency disclaimer section', () => {
      // The transparency section heading from STORY-173
      expect(screen.getByText('Transparência de Fontes de Dados')).toBeInTheDocument();
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

    it('should display fiscal address', () => {
      expect(screen.getByText(/Av\. Pref\. Osmar Cunha, 416/)).toBeInTheDocument();
    });

    it('should display CONFENGE attribution', () => {
      const elements = screen.getAllByText(/CONFENGE/);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });
});
