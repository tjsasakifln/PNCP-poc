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
        {/* Headline — Display weight, tighter tracking */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display tracking-tighter text-ink leading-[1.1]">
          Licitações relevantes.
          <br />
          <span className="text-brand-blue">Sem ruído.</span>
        </h1>

        {/* Subheadline — ink-secondary */}
        <p className="text-lg sm:text-xl text-ink-secondary mt-6 font-medium leading-relaxed max-w-2xl mx-auto">
          6 milhões de publicações por ano no Brasil.
          <br className="hidden sm:block" />
          Filtros inteligentes entregam o que importa para seu setor.
        </p>

        {/* CTA Buttons */}
        <div
          className={`flex flex-col sm:flex-row items-center justify-center gap-4 mt-10 transition-all duration-500 delay-150 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <a
            href="/buscar"
            className="w-full sm:w-auto bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-8 py-4 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] text-center focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            Acessar busca
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

        {/* Badge de Credibilidade — Simples e direto */}
        <div
          className={`mt-12 inline-flex items-center gap-2 px-4 py-2 bg-surface-1 border border-[var(--border)] rounded-full text-sm text-ink-secondary transition-all duration-500 delay-300 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <svg
            className="w-5 h-5 text-success"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <span>Dados do PNCP. Desenvolvido por servidores públicos.</span>
        </div>
      </div>
    </section>
  );
}
