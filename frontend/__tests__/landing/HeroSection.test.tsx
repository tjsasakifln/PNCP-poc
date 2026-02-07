import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroSection from '@/app/components/landing/HeroSection';

describe('HeroSection', () => {
  it('renders headline with new copy', () => {
    render(<HeroSection />);

    expect(screen.getByText(/Licitações relevantes/i)).toBeInTheDocument();
    expect(screen.getByText(/Sem ruído/i)).toBeInTheDocument();
  });

  it('renders subheadline with stats', () => {
    render(<HeroSection />);

    expect(screen.getByText(/6 milhões de publicações por ano/i)).toBeInTheDocument();
    expect(screen.getByText(/Filtros inteligentes entregam/i)).toBeInTheDocument();
  });

  it('renders primary CTA button with new text', () => {
    render(<HeroSection />);

    const primaryCTA = screen.getByRole('link', { name: /Acessar busca/i });
    expect(primaryCTA).toBeInTheDocument();
    expect(primaryCTA).toHaveAttribute('href', '/buscar');
  });

  it('renders secondary CTA button with scroll functionality', () => {
    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /Como funciona/i });
    expect(secondaryCTA).toBeInTheDocument();
  });

  it('renders credibility badge with institutional copy', () => {
    render(<HeroSection />);

    expect(screen.getByText(/Dados do PNCP/i)).toBeInTheDocument();
    expect(screen.getByText(/Desenvolvido por servidores públicos/i)).toBeInTheDocument();
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
    expect(container.querySelector('.text-brand-blue')).toBeInTheDocument();
    expect(container.querySelector('.bg-brand-navy')).toBeInTheDocument();
  });
});
