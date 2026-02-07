'use client';

import { useInView } from '@/app/hooks/useInView';

interface FinalCTAProps {
  className?: string;
}

export default function FinalCTA({ className = '' }: FinalCTAProps) {
  const { ref, isInView } = useInView({ threshold: 0.3 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <div
        className={`bg-brand-navy rounded-card p-10 sm:p-14 text-center text-white transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight mb-4">
          Encontre licitações relevantes.
        </h2>

        <p
          className={`text-lg sm:text-xl mb-8 text-white/80 transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          3 consultas gratuitas para começar.
        </p>

        <div
          className={`flex flex-col sm:flex-row items-center justify-center gap-4 transition-all duration-500 delay-200 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <a
            href="/signup?source=landing-cta"
            className="w-full sm:w-auto bg-white text-brand-navy hover:bg-surface-1 font-bold px-8 py-4 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] text-center text-lg focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white/50"
          >
            Criar conta grátis — 3 consultas gratuitas
          </a>
        </div>

        <p
          className={`mt-6 text-sm text-white/60 transition-all duration-500 delay-300 ${
            isInView ? 'opacity-100' : 'opacity-0'
          }`}
        >
          Sem cartão. Sem compromisso.
        </p>
      </div>
    </section>
  );
}
