import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroSection from '@/app/components/landing/HeroSection';

// Mock next/image — render as plain img with all props
jest.mock('next/image', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: React.forwardRef((props: Record<string, unknown>, ref: React.Ref<HTMLImageElement>) => {
      const { priority, blurDataURL, placeholder, ...rest } = props;
      return React.createElement('img', {
        ...rest,
        ref,
        'data-priority': priority ? 'true' : undefined,
        'data-placeholder': placeholder,
      });
    }),
  };
});

describe('HeroSection', () => {
  it('renders headline with financial impact positioning (GTM-COPY-001 AC1)', () => {
    render(<HeroSection />);

    expect(screen.getByText(/Pare de perder dinheiro/i)).toBeInTheDocument();
    expect(screen.getByText(/com licitações erradas/i)).toBeInTheDocument();
  });

  it('renders subheadline explaining filtering mechanism (GTM-COPY-001 AC2)', () => {
    render(<HeroSection />);

    expect(screen.getByText(/O SmartLic analisa cada edital contra o perfil da sua empresa/i)).toBeInTheDocument();
    expect(screen.getByText(/justificativa objetiva/i)).toBeInTheDocument();
  });

  it('renders primary CTA with action verb (GTM-COPY-002 AC1)', () => {
    render(<HeroSection />);

    const primaryCTA = screen.getByRole('button', { name: /Ver oportunidades para meu setor/i });
    expect(primaryCTA).toBeInTheDocument();
  });

  it('renders secondary CTA linking to como-funciona (SAB-006 AC1)', () => {
    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /Ver como funciona/i });
    expect(secondaryCTA).toBeInTheDocument();
  });

  it('scrolls to como-funciona section when secondary CTA is clicked', async () => {
    const user = userEvent.setup();

    const mockScrollIntoView = jest.fn();
    const mockElement = { scrollIntoView: mockScrollIntoView };
    jest.spyOn(document, 'getElementById').mockReturnValue(mockElement as any);

    render(<HeroSection />);

    const secondaryCTA = screen.getByRole('button', { name: /Ver como funciona/i });
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
    // GTM-COPY-001 banned phrases
    expect(text).not.toMatch(/inteligência automatizada/i);
    expect(text).not.toMatch(/inovador/i);
  });

  it('uses design system tokens for styling', () => {
    const { container } = render(<HeroSection />);

    expect(container.querySelector('.text-ink')).toBeInTheDocument();
    expect(container.querySelector('.text-gradient')).toBeInTheDocument();
  });

  it('does NOT render stats badges (SAB-006 AC2 — stats consolidated into StatsSection)', () => {
    const { container } = render(<HeroSection />);
    const text = container.textContent || '';

    // Stats badges removed — these values should NOT appear in HeroSection
    expect(text).not.toMatch(/87%/);
    expect(text).not.toMatch(/UFs cobertas/i);
  });

  // ---- DEBT-125: Product Screenshot Tests ----

  describe('DEBT-125: Product Screenshot', () => {
    it('AC1: renders product screenshot in desktop layout', () => {
      const { container } = render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      expect(img).toBeInTheDocument();

      // 50/50 layout uses flex-row on lg breakpoint
      const flexContainer = container.querySelector('.lg\\:flex-row');
      expect(flexContainer).toBeInTheDocument();
    });

    it('AC3: screenshot shows buscar results page at correct dimensions', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      expect(img).toHaveAttribute('width', '1280');
      expect(img).toHaveAttribute('height', '800');
    });

    it('AC5: image uses next/image with priority for LCP optimization', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      expect(img).toHaveAttribute('data-priority', 'true');
    });

    it('AC6: image has descriptive Portuguese alt text', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic mostrando classificacao por IA e analise de viabilidade/i,
      });
      expect(img).toBeInTheDocument();
    });

    it('AC8: dark mode applies CSS filter for automatic darkening', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      // dark:brightness-[0.85] dark:contrast-[1.1]
      expect(img.className).toContain('dark:brightness-');
      expect(img.className).toContain('dark:contrast-');
    });

    it('renders browser chrome frame around screenshot', () => {
      const { container } = render(<HeroSection />);

      // Browser URL bar text
      expect(screen.getByText('smartlic.tech/buscar')).toBeInTheDocument();

      // Browser dots (red, yellow, green)
      const dots = container.querySelectorAll('.rounded-full');
      // 3 browser dots + 3 trust indicator dots = 6
      expect(dots.length).toBeGreaterThanOrEqual(6);
    });

    it('image uses blur placeholder', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      expect(img).toHaveAttribute('data-placeholder', 'blur');
    });

    it('image has responsive sizes attribute', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      expect(img).toHaveAttribute('sizes');
      expect(img.getAttribute('sizes')).toContain('50vw');
    });

    it('AC2: mobile layout stacks screenshot below headline (flex-col default)', () => {
      const { container } = render(<HeroSection />);

      // Default is flex-col (mobile), lg:flex-row (desktop)
      const flexContainer = container.querySelector('.flex-col.lg\\:flex-row');
      expect(flexContainer).toBeInTheDocument();
    });

    it('no CLS: image has explicit width and height', () => {
      render(<HeroSection />);

      const img = screen.getByRole('img', {
        name: /Tela de resultados do SmartLic/i,
      });
      expect(img).toHaveAttribute('width');
      expect(img).toHaveAttribute('height');
    });
  });
});
