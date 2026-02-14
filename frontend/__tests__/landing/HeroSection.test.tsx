import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroSection from '@/app/components/landing/HeroSection';

describe('HeroSection', () => {
  it('renders headline with intelligence/curation positioning (AC1)', () => {
    render(<HeroSection />);

    expect(screen.getByText(/Seu Analista de Licitações/i)).toBeInTheDocument();
    expect(screen.getByText(/Movido por Inteligência Artificial/i)).toBeInTheDocument();
  });

  it('renders subheadline mentioning AI as differentiator (AC2)', () => {
    render(<HeroSection />);

    expect(screen.getByText(/IA analisa milhares de editais/i)).toBeInTheDocument();
    expect(screen.getByText(/Curadoria inteligente/i)).toBeInTheDocument();
  });

  it('renders primary CTA with results verb (AC3)', () => {
    render(<HeroSection />);

    const primaryCTA = screen.getByRole('button', { name: /Encontrar minhas oportunidades/i });
    expect(primaryCTA).toBeInTheDocument();
  });

  it('renders stats badges with trust signals (AC4)', () => {
    render(<HeroSection />);

    expect(screen.getByText(/bi mapeados/i)).toBeInTheDocument();
    expect(screen.getByText(/editais\/mês/i)).toBeInTheDocument();
    expect(screen.getByText(/estados cobertos/i)).toBeInTheDocument();
  });

  it('renders secondary CTA button with scroll functionality', () => {
    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /Como funciona/i });
    expect(secondaryCTA).toBeInTheDocument();
  });

  it('scrolls to section when secondary CTA is clicked', async () => {
    const user = userEvent.setup();

    const mockScrollIntoView = jest.fn();
    const mockElement = { scrollIntoView: mockScrollIntoView };
    jest.spyOn(document, 'getElementById').mockReturnValue(mockElement as any);

    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /Como funciona/i });
    await user.click(secondaryCTA);

    expect(document.getElementById).toHaveBeenCalledWith('como-funciona');
    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });
  });

  it('does NOT use forbidden terms (AC11)', () => {
    const { container } = render(<HeroSection />);
    const text = container.textContent || '';

    expect(text).not.toMatch(/economize.*tempo/i);
    expect(text).not.toMatch(/busca rápida/i);
    expect(text).not.toMatch(/ferramenta de busca/i);
    expect(text).not.toMatch(/planilha automatizada/i);
    expect(text).not.toMatch(/10h\/semana/i);
  });

  it('uses design system tokens for styling', () => {
    const { container } = render(<HeroSection />);

    expect(container.querySelector('.text-ink')).toBeInTheDocument();
    expect(container.querySelector('.text-gradient')).toBeInTheDocument();
  });
});
