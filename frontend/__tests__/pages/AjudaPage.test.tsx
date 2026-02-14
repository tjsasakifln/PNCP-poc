/**
 * Ajuda Page Tests
 * STORY-230 AC5-AC8: FAQ page contact section auth-awareness
 *
 * Tests:
 * - AC5: "Enviar Mensagem" shows mailto for unauthenticated users
 * - AC5: "Enviar Mensagem" links to /mensagens for authenticated users
 * - AC6: mailto:suporte@smartlic.tech always visible
 * - AC7: Anonymous user can access /ajuda content
 * - AC8: Anonymous clicking "Contato" does NOT redirect to login
 */

import { render, screen } from '@testing-library/react';
import AjudaPage from '@/app/ajuda/page';

// Mock useAuth hook
const mockUseAuth = jest.fn();

jest.mock('../../app/components/AuthProvider', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ children, href, className }: { children: React.ReactNode; href: string; className?: string }) {
    return <a href={href} className={className}>{children}</a>;
  };
});

describe('AjudaPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('AC5: Unauthenticated user contact section', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ user: null, loading: false });
      render(<AjudaPage />);
    });

    it('should show "Enviar E-mail" button with mailto link', () => {
      const emailButton = screen.getByText('Enviar E-mail');
      expect(emailButton.closest('a')).toHaveAttribute('href', 'mailto:suporte@smartlic.tech');
    });

    it('should NOT show "Enviar Mensagem" link to /mensagens', () => {
      const allLinks = screen.getAllByRole('link');
      const mensagensLinks = allLinks.filter(
        (link) => link.getAttribute('href') === '/mensagens'
      );
      expect(mensagensLinks).toHaveLength(0);
    });
  });

  describe('AC5: Authenticated user contact section', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', email: 'test@example.com' },
        loading: false,
      });
      render(<AjudaPage />);
    });

    it('should show "Enviar Mensagem" link to /mensagens', () => {
      const msgButton = screen.getByText('Enviar Mensagem');
      expect(msgButton.closest('a')).toHaveAttribute('href', '/mensagens');
    });
  });

  describe('AC6: Email contact always visible', () => {
    it('should show suporte@smartlic.tech for unauthenticated users', () => {
      mockUseAuth.mockReturnValue({ user: null, loading: false });
      render(<AjudaPage />);
      const emailLinks = screen.getAllByText('suporte@smartlic.tech');
      expect(emailLinks.length).toBeGreaterThanOrEqual(1);
    });

    it('should show suporte@smartlic.tech for authenticated users', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', email: 'test@example.com' },
        loading: false,
      });
      render(<AjudaPage />);
      const emailLinks = screen.getAllByText('suporte@smartlic.tech');
      expect(emailLinks.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('AC7: Anonymous user access', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ user: null, loading: false });
      render(<AjudaPage />);
    });

    it('should render the FAQ page heading', () => {
      expect(screen.getByText('Central de Ajuda')).toBeInTheDocument();
    });

    it('should render FAQ categories', () => {
      expect(screen.getAllByText('Como Buscar').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Planos').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Pagamentos').length).toBeGreaterThanOrEqual(1);
    });

    it('should render search input', () => {
      expect(screen.getByPlaceholderText('Buscar nas perguntas frequentes...')).toBeInTheDocument();
    });
  });

  describe('AC8: Contact section has id="contato" anchor', () => {
    it('should have id="contato" on the contact section', () => {
      mockUseAuth.mockReturnValue({ user: null, loading: false });
      render(<AjudaPage />);
      const contactSection = document.getElementById('contato');
      expect(contactSection).toBeInTheDocument();
      expect(contactSection).toHaveTextContent('Ainda tem dúvidas?');
    });
  });
});
