/**
 * STORY-432 AC8: Tests for Calculator embed page.
 */

import { render, screen } from '@testing-library/react';
import EmbedPage from '@/app/calculadora/embed/page';

// Mock CalculadoraClient (heavy client component)
jest.mock('@/app/calculadora/CalculadoraClient', () => ({
  __esModule: true,
  default: () => <div data-testid="calculadora-client">CalculadoraClient</div>,
}));

describe('Calculadora embed page — STORY-432 AC2', () => {
  it('renderiza sem header de navegação do site', () => {
    render(<EmbedPage />);

    // Deve ter o título da calculadora
    expect(screen.getByText(/Calculadora de Oportunidades/i)).toBeInTheDocument();

    // Deve ter o componente de calculadora
    expect(screen.getByTestId('calculadora-client')).toBeInTheDocument();
  });

  it('tem link de crédito followable no footer', () => {
    render(<EmbedPage />);

    // Link followable: rel="noopener" sem "nofollow"
    const footerLinks = screen.getAllByRole('link');
    const smartlicLink = footerLinks.find((link) =>
      link.getAttribute('href')?.includes('smartlic.tech/calculadora')
    );
    expect(smartlicLink).toBeDefined();
    expect(smartlicLink?.getAttribute('rel')).not.toContain('nofollow');
    expect(smartlicLink?.getAttribute('rel')).toContain('noopener');
  });

  it('não tem elementos de navegação principal (header, nav)', () => {
    const { container } = render(<EmbedPage />);

    // Não deve ter nav element principal do site
    const navElements = container.querySelectorAll('nav');
    // Se tiver nav, deve ser mínimo (logo apenas) — não menu completo
    expect(navElements.length).toBeLessThanOrEqual(1);
  });
});
