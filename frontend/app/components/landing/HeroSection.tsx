'use client';

import { useInView } from '@/app/hooks/useInView';

interface HeroSectionProps {
  className?: string;
}

export default function HeroSection({ className = '' }: HeroSectionProps) {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-32 bg-gradient-to-b from-brand-blue-subtle/40 to-transparent ${className}`}
    >
      <div
        className={`text-center max-w-4xl mx-auto transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        {/* Headline — Display weight, tighter tracking (STORY-173 AC1) */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display tracking-tighter text-ink leading-[1.1]">
          Encontre Oportunidades Relevantes
          <br />
          <span className="text-brand-blue">em 3 Minutos, Não em 8 Horas</span>
        </h1>

        {/* Subheadline — ink-secondary (STORY-173 AC1) */}
        <p className="text-lg sm:text-xl text-ink-secondary mt-6 font-medium leading-relaxed max-w-2xl mx-auto">
          Algoritmos inteligentes filtram milhares de licitações de múltiplas fontes
          <br className="hidden sm:block" />
          para entregar apenas o que importa para o seu negócio.
        </p>

        {/* CTA Buttons */}
        <div
          className={`flex flex-col sm:flex-row items-center justify-center gap-4 mt-10 transition-all duration-500 delay-150 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <a
            href="/signup?source=landing-cta"
            className="w-full sm:w-auto bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-8 py-4 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] text-center focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            Economize 10h/Semana Agora
          </a>
          <button
            onClick={() => scrollToSection('como-funciona')}
            className="w-full sm:w-auto border-2 border-brand-blue text-brand-blue hover:bg-brand-blue-subtle font-semibold px-8 py-4 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            Como funciona
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        {/* Trust Badges — (STORY-173 AC1) */}
        <div
          className={`mt-12 flex flex-wrap items-center justify-center gap-4 transition-all duration-500 delay-300 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-surface-1 border border-[var(--border)] rounded-full text-sm text-ink-secondary">
            <span className="text-lg">⚡</span>
            <span className="font-medium">160x Mais Rápido</span>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-surface-1 border border-[var(--border)] rounded-full text-sm text-ink-secondary">
            <span className="text-lg">🎯</span>
            <span className="font-medium">95% de Precisão</span>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-surface-1 border border-[var(--border)] rounded-full text-sm text-ink-secondary">
            <span className="text-lg">🌍</span>
            <span className="font-medium">PNCP + 27 Portais</span>
          </div>
        </div>
      </div>
    </section>
  );
}
