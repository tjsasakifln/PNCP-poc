import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroSection from '@/app/components/landing/HeroSection';

describe('HeroSection', () => {
  it('renders headline with new copy', () => {
    render(<HeroSection />);

    expect(screen.getByText(/Encontre Oportunidades Relevantes/i)).toBeInTheDocument();
    expect(screen.getByText(/em 3 Minutos/i)).toBeInTheDocument();
  });

  it('renders subheadline with stats', () => {
    render(<HeroSection />);

    expect(screen.getByText(/Algoritmos inteligentes filtram milhares de licitações/i)).toBeInTheDocument();
    expect(screen.getByText(/entregar apenas o que importa/i)).toBeInTheDocument();
  });

  it('renders primary CTA button with new text', () => {
    render(<HeroSection />);

    // Primary CTA is now a GradientButton (renders as <button>) not a link
    const primaryCTA = screen.getByRole('button', { name: /Economize 10h\/Semana Agora/i });
    expect(primaryCTA).toBeInTheDocument();
  });

  it('renders secondary CTA button with scroll functionality', () => {
    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /Como funciona/i });
    expect(secondaryCTA).toBeInTheDocument();
  });

  it('renders stats badges with values', () => {
    render(<HeroSection />);

    // Stats badges show Mais Rapido, Precisao, Portais
    expect(screen.getByText(/Mais Rápido/i)).toBeInTheDocument();
    expect(screen.getByText(/Precisão/i)).toBeInTheDocument();
    expect(screen.getByText(/Portais/i)).toBeInTheDocument();
  });

  it('scrolls to section when secondary CTA is clicked', async () => {
    const user = userEvent.setup();

    // Mock scrollIntoView
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

  it('uses design system tokens for styling', () => {
    const { container } = render(<HeroSection />);

    // Check for design token classes
    expect(container.querySelector('.text-ink')).toBeInTheDocument();
    expect(container.querySelector('.text-gradient')).toBeInTheDocument();
  });
});
