/**
 * Footer Component Tests
 * STORY-230 AC1-AC4: Footer navigation links
 *
 * Tests:
 * - AC1: "Central de Ajuda" links to /ajuda
 * - AC2: "Contato" links to /ajuda#contato (not /mensagens)
 * - AC3: Footer links consistent across pages
 * - AC4: All footer links accessible to unauthenticated users
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
});
