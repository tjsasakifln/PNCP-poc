import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroSection from '@/app/(landing)/components/HeroSection';

describe('HeroSection', () => {
  it('renders headline and subheadline', () => {
    render(<HeroSection />);

    expect(
      screen.getByText(/6\+ milhões de licitações por ano no Brasil/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/500 mil oportunidades mensais/i)).toBeInTheDocument();
  });

  it('renders primary CTA button', () => {
    render(<HeroSection />);

    const primaryCTA = screen.getByRole('link', { name: /começar busca gratuita/i });
    expect(primaryCTA).toBeInTheDocument();
    expect(primaryCTA).toHaveAttribute('href', '/signup');
  });

  it('renders secondary CTA button with scroll functionality', () => {
    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /ver como funciona/i });
    expect(secondaryCTA).toBeInTheDocument();
  });

  it('renders credibility badge', () => {
    render(<HeroSection />);

    expect(screen.getByText(/criado por servidores públicos/i)).toBeInTheDocument();
    expect(screen.getByText(/dados pncp \+ múltiplas fontes oficiais/i)).toBeInTheDocument();
  });

  it('scrolls to section when secondary CTA is clicked', async () => {
    const user = userEvent.setup();

    // Mock scrollIntoView
    const mockScrollIntoView = jest.fn();
    const mockElement = { scrollIntoView: mockScrollIntoView };
    jest.spyOn(document, 'getElementById').mockReturnValue(mockElement as any);

    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /ver como funciona/i });
    await user.click(secondaryCTA);

    expect(document.getElementById).toHaveBeenCalledWith('como-funciona');
    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start',
    });
  });
});
